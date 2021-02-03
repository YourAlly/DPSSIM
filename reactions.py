#Turn dot reactions into damage/reactions

class React:
    def __init__(self):
        self.print = True

    def check(self,action,enemy):
        #Anemo
        if action.element == "Anemo":
            return "swirl"
        #Geo
        elif action.element == "Geo":
            return "crystallise"
        #Hydro
        elif action.element == "Hydro":
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
        elif action.element == "Cryo":
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
        elif action.element == "Electro":
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
        elif action.element == "Pyro":
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
    
    def swirl(self,sim,action,enemy,unit):
        enemy.units -= unit*0.5
        sim.damage += 722 * (1 + (( 4.44 * action.unit.elemental_mastery ) / ( 1400 + action.unit.elemental_mastery ))) * (1 - enemy.live_anemo_res )
        print(action.unit.name + " proced swirl")
        return 1

    def overload(self,sim,action,enemy,unit):
        enemy.units -= unit
        sim.damage += 2406 * (1 + (( 4.44 * action.unit.elemental_mastery ) / ( 1400 + action.unit.elemental_mastery ))) * (1 - enemy.live_pyro_res )
        print(action.unit.name + " proced overload")
        return 1

    def crystallise(self,sim,action,enemy,unit):
        enemy.units -= unit*0.5
        print(action.unit.name + " proced crystallise")
        return 1

    def superconduct(self,sim,action,enemy,unit):
        enemy.units -= unit
        sim.damage += 601 * (1 + (( 4.44 * action.unit.elemental_mastery ) / ( 1400 + action.unit.elemental_mastery ))) * (1 - enemy.live_cryo_res )
        print(action.unit.name + " proced superconduct")
        return 1

    def electro_charged(self,sim,action,enemy,unit):
        enemy.units -= unit
        sim.damage += 1443 * (1 + (( 4.44 * action.unit.elemental_mastery ) / ( 1400 + action.unit.elemental_mastery ))) * (1 - enemy.live_electro_res )
        print(action.unit.name + " proced electro_charged")
        return 1

    def frozen(self,sim,action,enemy,unit):
        print(action.unit.name + " proced frozen")
        return 1

    def vaporise2(self,sim,action,enemy,unit):
        enemy.units -= unit*2
        print(action.unit.name + " proc'd Vaporise for 2x damage")
        return 2 * (1 + (( 2.78 * action.unit.elemental_mastery ) / ( 1400 + action.unit.elemental_mastery )))

    def vaporise15(self,sim,action,enemy,unit):
        enemy.units -= unit*0.5
        print(action.unit.name + " proc'd Vaporise for 1.5x damage")
        return 1.5 * (1 + (( 2.78 * action.unit.elemental_mastery ) / ( 1400 + action.unit.elemental_mastery )))

    def melt2(self,sim,action,enemy,unit):
        enemy.units -= unit*2
        print(action.unit.name + " proc'd Melt for 2x damage")
        return 2 * (1 + (( 2.78 * action.unit.elemental_mastery ) / ( 1400 + action.unit.elemental_mastery )))

    def melt15(self,sim,action,enemy,unit):
        enemy.units -= unit*0.5
        print(action.unit.name + " proc'd Melt for 1.5x damage")
        return 1.5 * (1 + (( 2.78 * action.unit.elemental_mastery ) / ( 1400 + action.unit.elemental_mastery )))

    def enemyelectro(self,sim,action,enemy,unit):
        enemy.element = action.element
        enemy.units += unit*0.8
        print(action.unit.name + " applied electro")
        return 1
    
    def enemypyro(self,sim,action,enemy,unit):
        enemy.element = action.element
        enemy.units += unit*0.8
        print(action.unit.name + " applied pyro")
        return 1

    def enemycryo(self,sim,action,enemy,unit):
        enemy.element = action.element
        enemy.units += unit*0.8
        print(action.unit.name + " applied cryo")
        return 1

    def enemyhydro(self,sim,action,enemy,unit):
        enemy.element = action.element
        enemy.units += unit*0.8
        print(action.unit.name + " applied hydro")
        return 1

    def no_reaction(self,sim,action,enemy,unit):
        return 1