from core.read_data import buff_dict
from effects.misc import ActiveBuff
import copy

class React:
    def __init__(self):
        self.print = True

    def check(self,action,tick,enemy):
        #Anemo
        if action.tick_element[tick] == "Anemo":
            if enemy.units > 0:
                return "swirl"
            else:
                return "no_reaction"
        #Geo
        elif action.tick_element[tick] == "Geo":
            if enemy.units > 0:
                return "crystallise"
            else:
                return "no_reaction"

        #Hydro
        elif action.tick_element[tick] == "Hydro":
            if enemy.element == "None":
                return "enemyhydro"
            elif enemy.element == "Pyro":
                return "vaporise2"
            elif enemy.element == "Electro":
                return "electro_charged"
            elif enemy.element == "Cryo":
                return "frozen"
            else:
                return "no_reaction"
        #Cryo
        elif action.tick_element[tick] == "Cryo":
            if enemy.element == "None":
                enemy.element = "Cryo"
                return "enemycryo"
            if enemy.element == "Hydro":
                return "frozen"
            if enemy.element == "Pyro":
                return "melt15"
            if enemy.element == "Electro":
                return "superconduct"
            else:
                return "no_reaction"
        #Electro
        elif action.tick_element[tick] == "Electro":
            if enemy.element == "None":
                return "enemyelectro"
            if enemy.element == "Hydro":
                return "electro_charged"
            if enemy.element == "Pyro":
                return "overload"
            if enemy.element == "Cryo":
                return "superconduct"
            else:
                return "no_reaction"    
        #Pyro
        elif action.tick_element[tick] == "Pyro":
            if enemy.element == "None":
                return "enemypyro"
            if enemy.element == "Hydro":
                return "vaporise15"
            if enemy.element == "Cryo":
                return "melt2"
            if enemy.element == "Electro":
                return "overload"
            else:
                return "no_reaction"

        else:
            return "no_reaction"
    
    def swirl(self,action,tick,enemy,unit,sim):
        enemy.units -= unit*0.5
        sim.damage += 722 * (1 + (( 4.44 * action.unit.ele_m ) / ( 1400 + action.unit.ele_m ))) * (1 - enemy.live_anemo_res )
        print(action.unit.character + " proced swirl")
        return [1, ["swirl",enemy.element]]

    def overload(self,action,tick,enemy,unit,sim):
        enemy.units -= unit
        sim.damage += 2406 * (1 + (( 4.44 * action.unit.ele_m ) / ( 1400 + action.unit.ele_m ))) * (1 - enemy.live_pyro_res )
        print(action.unit.character + " proced overload")
        return [1, ["overload"]]

    def crystallise(self,action,tick,enemy,unit,sim):
        enemy.units -= unit*0.5
        print(action.unit.character + " proced crystallise")
        for unit in sim.units:
            unit.active_buffs["Shield"] = copy.copy(buff_dict["Shield"])
            unit.active_buffs["Shield"].source = ActiveBuff()
        return [1, ["crystallise",enemy.element]]

    def superconduct(self,action,tick,enemy,unit,sim):
        enemy.units -= unit
        sim.damage += 601 * (1 + (( 4.44 * action.unit.ele_m ) / ( 1400 + action.unit.ele_m ))) * (1 - enemy.live_cryo_res )
        print(action.unit.character + " proced superconduct")
        return [1, ["superconduct"]]

    def electro_charged(self,action,tick,enemy,unit,sim):
        enemy.units -= unit
        sim.damage += 1443 * (1 + (( 4.44 * action.unit.ele_m ) / ( 1400 + action.unit.ele_m ))) * (1 - enemy.live_electro_res )
        print(action.unit.character + " proced electro_charged")
        return [1, ["electro_charged"]]

    def frozen(self,action,tick,enemy,unit,sim):
        print(action.unit.character + " proced frozen")
        return [1, ["frozen"]]

    def vaporise2(self,action,tick,enemy,unit,sim):
        enemy.units -= unit*2
        print(action.unit.character + " proc'd Vaporise for 2x damage")
        return [2 * (1 + (( 2.78 * action.unit.ele_m ) / ( 1400 + action.unit.ele_m ))), ["vaporise"]]

    def vaporise15(self,action,tick,enemy,unit,sim):
        enemy.units -= unit*0.5
        print(action.unit.character + " proc'd Vaporise for 1.5x damage")
        return [1.5 * (1 + (( 2.78 * action.unit.ele_m ) / ( 1400 + action.unit.ele_m ))), ["vaporise"]]

    def melt2(self,action,tick,enemy,unit,sim):
        enemy.units -= unit*2
        print(action.unit.character + " proc'd Melt for 2x damage")
        return [2 * (1 + (( 2.78 * action.unit.ele_m ) / ( 1400 + action.unit.ele_m ))), ["melt"]]

    def melt15(self,action,tick,enemy,unit,sim):
        enemy.units -= unit*0.5
        print(action.unit.character + " proc'd Melt for 1.5x damage")
        return [1.5 * (1 + (( 2.78 * action.unit.ele_m ) / ( 1400 + action.unit.ele_m ))), ["melt"]]

    def enemyelectro(self,action,tick,enemy,unit,sim):
        enemy.element = action.tick_element[tick]
        enemy.units += unit*0.8
        print(action.unit.character + " applied electro")
        return [1, ["none"]]
    
    def enemypyro(self,action,tick,enemy,unit,sim):
        enemy.element = action.tick_element[tick]
        enemy.units += unit*0.8
        print(action.unit.character + " applied pyro")
        return [1, ["none"]]

    def enemycryo(self,action,tick,enemy,unit,sim):
        enemy.element = action.tick_element[tick]
        enemy.units += unit*0.8
        print(action.unit.character + " applied cryo")
        return [1, ["none"]]

    def enemyhydro(self,action,tick,enemy,unit,sim):
        enemy.element = action.tick_element[tick]
        enemy.units += unit*0.8
        print(action.unit.character + " applied hydro")
        return [1, ["none"]]

    def no_reaction(self,action,tick,enemy,unit,sim):
        return [1, ["none"]]