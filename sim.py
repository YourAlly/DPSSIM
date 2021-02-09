# pylint: disable=no-member
import unit as u
from operator import methodcaller
import artifact_substats
import math
from reactions import React
import activeeffects as a
from action import Action
from action import Combos
from action import ComboAction
import enemy
import copy

# Creating a list of actions
class Sim:
    def __init__ (self, main,sup1,sup2,sup3,enemy,time):
        self.units = {main,sup1,sup2,sup3}
        self.enemy = enemy
        self.encounter_limit = time
        self.encounter_duration = 0
        self.turn_time = 0
        self.time_into_turn = 0
        self.last_action_time = 0
        self.damage = 0
        self.action_order = 0
        self.chosen_unit = None
        self.last_unit = None
        self.chosen_action = None
        self.last_action = None
        self.action_list = set()
        self.floating_actions= set()
        self.action_queue = []
        self.sorted_action_queue = []

        self.stamina = 250
        self.stamina_timer = 0

    ### Starts the sim, adds 1 to the turn number and updates the previous unit
    def start_sim(self):
        self.action_order += 1
        self.last_unit = copy.deepcopy(self.chosen_unit)
        self.last_action = copy.deepcopy(self.chosen_action)
        self.time_into_turn = 0

    ## Creates a new list of actions for the sim to base its choice off
    def update_action_list(self):
        self.action_list = set()
        types = {"skill", "burst"}
        for unit in self.units:
            for k in types:
                if Action(unit,k).available(self) == True:
                    self.action_list.add(Action(unit,k))
        for unit in self.units:
            for _,combo in Combos()._list(unit).items():
                if ComboAction(unit,combo).available(self) == True:
                    self.action_list.add(ComboAction(unit,combo))
        
    ## Checks for buffs/triggers and updates stats
    def check_buff(self,type2,action,extra):
        for key, trig_buff in copy.deepcopy(action.unit.triggerable_buffs).items():
            if trig_buff.field == "Yes" and self.chosen_unit == action.unit:
                if (action.type in trig_buff.trigger or 'any'in trig_buff.trigger) and trig_buff.live_cd == 0 and trig_buff.type2 == type2:
                    if trig_buff.duration == "Instant":
                        if trig_buff.share == "Yes":
                            for unit in self.units:
                                getattr(a.ActiveBuff(),trig_buff.method)(unit,self,extra)
                        else:
                            getattr(a.ActiveBuff(),trig_buff.method)(action.unit,self,extra)
                    else:
                        if trig_buff.share == "Yes":
                            for unit in self.units:
                                unit.active_buffs[key] = copy.deepcopy(trig_buff)
                                unit.update_stats(self)
                        else:
                            if key in self.chosen_unit.active_buffs and trig_buff.max_stacks > 0 and self.chosen_unit.active_buffs[key].stacks > 0:
                                self.chosen_unit.active_buffs[key].stacks = min(self.chosen_unit.active_buffs[key].max_stacks,self.chosen_unit.active_buffs[key].stacks + 1)
                                self.chosen_unit.active_buffs[key].time_remaining = self.chosen_unit.active_buffs[key].duration
                            else:
                                if trig_buff.max_stacks > 0:
                                    self.chosen_unit.active_buffs[key] = copy.deepcopy(self.chosen_unit.triggerable_buffs[key])
                                    self.chosen_unit.active_buffs[key].stacks += 1
                                    self.chosen_unit.update_stats(self)
                                else:
                                    self.chosen_unit.active_buffs[key] = copy.deepcopy(trig_buff)
                                    self.chosen_unit.update_stats(self)
            else:
                if trig_buff.field == "Yes" and self.chosen_unit != action.unit:
                    pass
                else:
                    if (action.type in trig_buff.trigger or 'any' in trig_buff.trigger) and trig_buff.live_cd == 0 and trig_buff.type2 == type2:
                        if trig_buff.duration == "Instant":
                            if trig_buff.share == "Yes":
                                for unit in self.units:
                                    getattr(a.ActiveBuff(),trig_buff.method)(unit,self,extra)
                            else:
                                getattr(a.ActiveBuff(),trig_buff.method)(action.unit,self,extra)
                        else:
                            if trig_buff.share == "Yes":
                                for unit in self.units:
                                        unit.active_buffs[key] = copy.deepcopy(trig_buff)
                                        unit.update_stats(self)
                            else:
                                self.chosen_unit.active_buffs[key] = copy.deepcopy(trig_buff)
                                self.chosen_unit.update_stats(self)

    ## Checks for debuffs/triggers and updates stats
    def check_debuff(self,type2,action):
        for key, trig_debuff in self.chosen_unit.triggerable_debuffs.items():
            if trig_debuff.trigger == self.chosen_action.type or trig_debuff.trigger == "any":
                if trig_debuff.type2 == type2:
                    self.enemy.active_debuffs[key] = trig_debuff
        self.enemy.update_stats

    ## Check if buffs ended for units. If they did, remove them
    def check_buff_end(self):
        for unit in self.units:
            ## Tartaglia Stance Check ##
            if unit.name == "Tartaglia":
                if "Tartaglia_Stance" in unit.active_buffs:
                    if unit.active_buffs["Tartaglia_Stance"].time_remaining <= 0:
                        unit.stance = "ranged"
                        if hasattr(unit,"c6_reset") == True:
                            if unit.c6_reset == True:
                                unit.current_skill_cd = 1
                                unit.c6_reset = False
                        else:
                            unit.current_skill_cd = 51
                        print("Tartaglia Stance Timed Out")

            unit.active_buffs = {k:unit.active_buffs[k] for k in unit.active_buffs if unit.active_buffs[k].time_remaining > 0}
            unit.update_stats(self)

            for buff in copy.deepcopy(unit.triggerable_buffs):
                if unit.triggerable_buffs[buff].temporary == "Yes":
                    if unit.triggerable_buffs[buff].time_remaining == 0:
                        del unit.triggerable_buffs[buff]

    ## Check if debuff ends for enemies. If they did, remove them
    def check_debuff_end(self):
        self.enemy.active_debuffs = {k:self.enemy.active_debuffs[k] for k in self.enemy.active_debuffs if self.enemy.active_debuffs[k].time_remaining > 0}
        self.enemy.update_stats(self)

    ## Chooses the best action from the action list. Currently does so based on the highest dps
    def choose_action(self):
        self.chosen_action = max(self.action_list, key=methodcaller('calculate_dps_snapshot',self))
        self.chosen_unit = self.chosen_action.unit
        if self.action_order == 1:
            self.last_unit = copy.deepcopy(self.chosen_unit)
            self.last_action = copy.deepcopy(self.chosen_action)

    ## Uses the action, adds either adds damage if it's instant or adds it to the dot_actions, puts action on cd
    def use_ability(self):
        self.check_buff("precast",self.chosen_action,None)

        self.chosen_action.action_type = "damage"
        self.floating_actions.add(self.chosen_action)
        energy_copy = copy.deepcopy(self.chosen_action)
        energy_copy.action_type = "energy"
        energy_copy.initial_time += 2
        energy_copy.time_remaining += 2
        self.floating_actions.add(energy_copy)

        if self.chosen_action.type == "skill":
            if self.chosen_unit.current_skill_charges > 0:
                self.chosen_unit.current_skill_charges -= 1
            else:
                self.chosen_unit.current_skill_cd = self.chosen_unit.live_skill_cd
        if self.chosen_action.type == "burst":
            self.chosen_unit.current_burst_cd = self.chosen_unit.live_burst_cd
            self.chosen_unit.current_energy = 0

        if self.chosen_action.type == "charged":
            self.stamina -= self.chosen_action.stamina_cost

        for unit in self.units:
            if hasattr(unit, "stance") == True:
                if unit.name == "Tartaglia" and unit.stance == "melee" and self.last_unit == unit and self.chosen_unit != unit:
                    if hasattr(unit,"c6_reset") == True:
                        if unit.c6_reset == True:
                            unit.current_skill_cd = 1
                            unit.c6_reset = False
                        else:
                            unit.current_skill_cd = (45 - copy.deepcopy(unit.active_buffs["Tartaglia Stance"].time_remaining))*2 + 6
                            unit.stance = "ranged"

        self.check_buff("postcast",self.chosen_action,None)
        
    ## Check how long the action took
    def check_turn_time(self):

        self.turn_time = self.chosen_action.minimum_time
        if self.action_order == 1:
            pass
        else:
            if self.last_unit.name != self.chosen_unit.name:
                self.turn_time += 0.12
                self.turn_time += (self.last_action.time_to_swap - self.last_action.minimum_time)
            else:
                if self.chosen_action == "burst":
                    self.turn_time += (self.last_action.time_to_burst - self.last_action.minimum_time)
                elif self.chosen_action == "skill":
                    self.turn_time += (self.last_action.time_to_skill - self.last_action.minimum_time)
                elif self.chosen_action == "combo":
                    self.turn_time += (self.last_action.time_to_attack - self.last_action.minimum_time)
    
    ## Reduce triggerable CDs by time interval
    def reduce_buff_times_cds(self,time_interval):
        for unit in self.units:
            for _, trig_buff in unit.triggerable_buffs.items():
                trig_buff.live_cd = max(0, trig_buff.live_cd - time_interval)
                if trig_buff.temporary == "Yes":
                    trig_buff.time_remaining = max(0, trig_buff.time_remaining - time_interval)
            for _, buff in unit.active_buffs.items():
                buff.time_remaining = max(0, buff.time_remaining - time_interval)

    ## Check which dot ticks occur in the turn time
    def create_action_queue_turn(self,time_into_turn):
        self.action_queue = []
        for action in self.floating_actions:
            times_till_ticks = []
            for i in range(action.ticks):
                times_till_ticks.append((i,action.tick_times[i] - (action.initial_time - action.time_remaining)))
            for i in range(action.ticks):
                if time_into_turn <= times_till_ticks[i][1] <= self.turn_time:
                    if action.tick_used[i] == "no":
                        self.action_queue.append((i,action,times_till_ticks[i][1]))

    ## Sort the dot ticks in order of when they tick
    def sort_action_turn(self):
        self.sorted_action_queue = sorted(self.action_queue, key=lambda i: i[2])

    ## Proccesses actions
    def process_action(self):
        new = self.sorted_action_queue.pop(0)
        if new[1].action_type == "damage":
            self.process_action_damage(new)
        elif new[1].action_type == "energy":
            self.process_action_energy(new)
        else:
            print("Error",new[1].unit.name)

    ## Hitlag
    def hitlag(self,unit_obj,action,tick):
        lag = self.enemy.hitlag / 60
        if action.hitlag == True:
            action.tick_times = [x+lag for x in action.tick_times]
            self.turn_time -= lag

    ## Attack Speed
    def attack_speed(self,unit_obj,action,tick):
        attack_speed = unit_obj.live_normal_speed

        if tick == 0:
            new_time = action.tick_times[0] / ( 1 + attack_speed )
            time_reduced = action.tick_times[0] - new_time
            action.tick_times = [x-time_reduced for x in action.tick_times]
        else:
            time_gap = action.tick_times[tick] - action.tick_times[tick-1]
            new_time_gap = time_gap / ( 1 + attack_speed)
            time_reduced = time_gap - new_time_gap
            action.tick_times = [x-time_reduced for x in action.tick_times]
            self.turn_time -= time_reduced

    ## Processes damage actions (ticks)
    def process_action_damage(self,new):
        tick = new[0]
        damage_action = new[1]
        damage_action.tick_used[tick] = "yes"
        self.last_action_time = copy.deepcopy(self.time_into_turn)
        self.time_into_turn = new[2]

        time_since_last_action = self.time_into_turn - self.last_action_time
        self.reduce_buff_times_cds (time_since_last_action)

        self.check_buff("pre_hit",damage_action,None)
        self.check_buff("midhit",damage_action,tick)

        damage_action_element_unit = damage_action.tick_units[tick]
        multiplier = 1
        if damage_action_element_unit > 0:
            reaction = getattr(React(),React().check(damage_action,self.enemy))(self,damage_action,self.enemy,damage_action_element_unit)
            reaction.append(damage_action)
            multiplier = reaction[0]
            self.check_buff("reaction",damage_action,reaction[1])

        self.enemy.update_units()
        instance_damage = damage_action.calculate_tick_damage(tick,self) * multiplier
        self.damage += instance_damage

        self.check_buff("on_hit",damage_action,None)
        self.check_debuff("on_hit", damage_action)

        self.check_buff_end()
        self.check_debuff_end()

    ## Proccesses the energy
    def process_action_energy(self,new):
        tick = new[0]
        energy_action = new[1]
        energy_action.tick_used[tick] = "yes"
        self.last_action_time = copy.deepcopy(self.time_into_turn)
        self.time_into_turn = new[2]

        time_since_last_action = self.time_into_turn - self.last_action_time
        self.reduce_buff_times_cds (time_since_last_action)
        particles = energy_action.particles / energy_action.ticks

        for unit in self.units:
            if unit == self.chosen_unit:
                if self.chosen_unit.element == energy_action.unit.element:
                    self.chosen_unit.current_energy += particles * 3 * (1+self.chosen_unit.recharge)
                else:
                    self.chosen_unit.current_energy += particles * 1 * (1+self.chosen_unit.recharge)
            else:
                if unit.element == energy_action.unit.element:
                    unit.current_energy += particles * 1.8 * (1+self.chosen_unit.recharge)
                else:
                    unit.current_energy += particles * 0.6 * (1+self.chosen_unit.recharge)

        self.check_buff("particle",energy_action,None)
        self.check_buff_end()
        self.check_debuff_end()

    ## Loops damage queue processing
    def process_loop(self):
        self.create_action_queue_turn(self.time_into_turn)
        while len(self.action_queue) > 0:
            self.sort_action_turn()
            self.process_action()
            self.create_action_queue_turn(self.time_into_turn)
               
    ## Lower cooldowns based on turn time
    def reduce_cd(self):
        for unit in self.units:
            unit.current_skill_cd = max(unit.current_skill_cd - self.turn_time,0)
            unit.current_burst_cd = max(unit.current_burst_cd - self.turn_time,0)

    ## Passes time
    def pass_turn_time(self):
        self.encounter_duration += self.turn_time
        for action in self.floating_actions:
            action.time_remaining -= self.turn_time
        self.floating_actions = {x for x in self.floating_actions if x.time_remaining > 0}

        for unit in self.units:
            for _, trig_buff in unit.triggerable_buffs.items():
                trig_buff.live_cd = max(0, trig_buff.live_cd - (self.turn_time-self.time_into_turn))
                if trig_buff.temporary == "Yes":
                    trig_buff.time_remaining = max(0, trig_buff.time_remaining - (self.turn_time-self.time_into_turn))
            for _, buff in unit.active_buffs.items():
                buff.time_remaining = max(0, buff.time_remaining - (self.turn_time-self.time_into_turn))

    ## Print status
    def status(self):
        if hasattr(self.chosen_unit,"stance") == True:
            stance = " (" + self.chosen_unit.stance + ")"
        else:
            stance = ""
        print("#" + str(self.action_order) + " Time:" + str(round(self.encounter_duration,2)) + " " + self.chosen_unit.name + stance + " used "
        + self.chosen_action.type)

    ## Turns on the sim (lol)
    def turn_on_sim(self):
        while self.encounter_duration < self.encounter_limit:
            self.start_sim()
            self.update_action_list()
            self.choose_action()
            self.use_ability()
            self.status()
            self.check_turn_time()
            self.process_loop()
            self.reduce_cd()
            self.pass_turn_time()
            self.check_buff_end()
            self.check_debuff_end()
        print(round(self.damage /self.encounter_duration),self.encounter_duration)

PyroArtifact = artifact_substats.ArtifactStats("pct_atk", "pyro_dmg", "crit_rate", "Perfect")
CryoArtifact = artifact_substats.ArtifactStats("pct_atk", "cryo_dmg", "crit_rate", "Perfect")
ElectroArtifact = artifact_substats.ArtifactStats("pct_atk", "electro_dmg", "crit_rate", "Perfect")
AnemoArtifact = artifact_substats.ArtifactStats("pct_atk", "anemo_dmg", "crit_rate", "Perfect")
HydroArtifact = artifact_substats.ArtifactStats("pct_atk", "hydro_dmg", "crit_rate", "Perfect")
PhysicalArtifact = artifact_substats.ArtifactStats("pct_atk", "physical_dmg", "crit_rate", "Perfect")

Main = u.Unit("Razor", 90, "Prototype Archaic", "Noblesse", 0, 1, 6, 6, 6, ElectroArtifact)
Support1 = u.Unit("Amber", 90, "Skyward Harp", "Noblesse", 0, 1, 6, 6, 6, PyroArtifact)
Support2 = u.Unit("Kaeya", 90, "Prototype Archaic", "Noblesse", 0, 1, 6, 6, 6, PyroArtifact)
Support3 = u.Unit("Lisa", 90, "Skyward Atlas", "Noblesse", 0, 1, 6, 6, 6, ElectroArtifact)
Monster = enemy.Enemy("Hilichurls", 90)

Test = Sim(Main,Support1,Support2,Support3,Monster,20)
Test.turn_on_sim()

a_set = set()


for key,combo in Combos()._list(Support2).items():
    print(key,combo)
# for key, x in Combos()._list(Main).items():
#     a_set.add(ComboAction(Main,x))
#     print(a_set)
