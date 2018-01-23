import hlt
import logging
import time
import random
from collections import OrderedDict
game = hlt.Game("Ganon-V7")
#logging.info("Starting GanonBot-V7")

MIN_NUM_DOCKED = 3                      # Minimum number of DOCKED ships that I accept
DELTA_NUM_SHIP_DOCKED = 4               # Max difference between my docked ships and the player with most docked
NUM_MAX_SHIP_DOCKED_SAME_PLANET = 4     # Max number of ships docked to the same planet

MAX_NUM_SHIP_SAME_TARGET = 3            # Number of ships with the same target

PCT_EXPLORERS = .20                                        # Percentage of EXPLORERS ships
PCT_SUPPORT = .50                                           # Percentage of SUPPORT ships
PCT_LONE = .10                                              # Percentage of rogue_one ships
PCT_ROGUE1 = 1 - PCT_EXPLORERS - PCT_SUPPORT - PCT_LONE    # Percentage of ROGUE1 ships

comandos = {'mining' : [],
            'lone_ranger' : [], # 15%
            'rogue_one': [],    # 15%
            'support': [],        # 45%
            'explorers': []}      # 25%
assigned_comando = []

class ship_plan():
    def __init__(self, id, planet=-1, ship=-1, position=hlt.entity.Position(-1, -1)):
        self.id = id
        self.target_planet = planet
        self.target_ship = ship
        self.position = position

    def __str__(self):
        return 'Plan Id: {} with Target Planet: {} and Target Ship: {}'.format(self.id, self.target_planet, self.target_ship)

    def __repr__(self):
        return self.__str__()
class need_help():
    def __init__(self, id, planet, enemy):
        self.shipid = id
        self.planetid = planet
        self.enemyid = enemy

    def __str__(self):
        return 'Ship needing help Id: {} in the planet: {} from the enemy: {}'.format(self.shipid, self.planetid, self.enemyid)

    def __repr__(self):
        return self.__str__()

my_ships_with_plans = {}
turn = 0


def mine_planet(ship, target_planet, game_map, my_ships_with_plans, command_queue):
    """

    :param ship:
    :param target_planet:
    :param game_map:
    :param my_ships_with_plans:
    :param command_queue:
    :return: type_mine -> 0 -> Is Docking, 1 -> Is flying
    """
    #logging.info("Let's MINE with ship %s to planet %s", ship.id, target_planet)
    type_mine = -1
    if ship.can_dock(target_planet):
        command_queue.append(ship.dock(target_planet))
        my_ships_with_plans[ship.id] = ship_plan(ship.id, planet=target_planet.id)
        #logging.info("SHIP PLANS1 %s %s", ship.id, my_ships_with_plans[ship.id])
        type_mine = 0
    else:
        navigate_command = ship.navigate(
            ship.closest_point_to(target_planet),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            ignore_ships=False)
        pos = ship.closest_point_to(target_planet)
        if navigate_command is None:
            navigate_command = ship.navigate(
                pos,
                game_map,
                max_corrections=180,
                speed=int(hlt.constants.MAX_SPEED),
                ignore_ships=False)
        if navigate_command:
            command_queue.append(navigate_command)
            my_ships_with_plans[ship.id] = ship_plan(ship.id, planet=target_planet.id)
            #logging.info("SHIP PLANS2 %s %s", ship.id, my_ships_with_plans[ship.id])
            type_mine = 1

    return type_mine


def attack_ship(ship, target_ship, all_ships_k, game_map, my_ships_with_plans, command_queue):
    #logging.info("Let's ATTACK with ship %s to ship %s", ship.id, target_ship)

    pos = ship.closest_point_to(target_ship)
    navigate_command = ship.navigate(
        pos,
        game_map,
        speed=int(hlt.constants.MAX_SPEED),
        angular_step=5,
        ignore_ships=False)
    if not navigate_command:
        logging.info("ATLETI!")
    if navigate_command:
        command_queue.append(navigate_command)
        my_ships_with_plans[ship.id] = ship_plan(ship.id, ship=target_ship.id)

    return True


def move_ship_to(ship, target, game_map, speed, my_ships_with_plans, command_queue):
    navigate_command = ship.navigate(
        target,
        game_map,
        max_corrections=180,
        speed=speed,
        ignore_ships=False)
    if not navigate_command:
        logging.info("ATLETI!")
    if navigate_command:
        command_queue.append(navigate_command)
        my_ships_with_plans[ship.id] = ship_plan(ship.id, position=target)

def rogue1_calc_pos(ship, new_pos, direction, max_x, min_x, max_y, min_y):
    navigating = False
    speed = int(hlt.constants.MAX_SPEED)
    if new_pos.x != -1:
        #logging.info("ATLETI1 %s %s %s %s", new_pos.x, new_pos.y, ship.x, ship.y)
        if not (int(new_pos.x - 1) <= int(ship.x) <= int(new_pos.x + 1)) or \
           not (int(new_pos.y - 1) <= int(ship.y) <= int(new_pos.y + 1)):
            #logging.info("ATLETI2: speed %s X- %s X+ %s Y- %s Y+ %s", speed, int(ship.x - speed), int(ship.x + speed), int(ship.y - speed), int(ship.y + speed))

            if direction == 'left' and (int(ship.x - speed) < min_x):
                speed = int(ship.x - min_x)
                #logging.info("Too close to X = 0 so adjusting speed %s", speed)
            elif direction == 'right' and (int(ship.x + speed) > max_x):
                speed = int(max_x - ship.x)
                #logging.info("Too close to X = MAX_X so adjusting speed %s", speed)
            elif direction == 'up' and (int(ship.y - speed) < min_y):
                speed = int(ship.y - min_y)
                #logging.info("Too close to Y = 0 so adjusting speed %s", speed)
            elif direction == 'down' and (int(ship.y + speed) > max_y):
                speed = int(max_y - ship.y)
                #logging.info("Too close to Y = MAX_Y so adjusting speed %s", speed)

            #logging.info("STILL NAVIGATING")
            navigating = True

        if not navigating:
            if int(ship.y) >= max_y - 1:
                if int(ship.x) <= min_x + 1:
                    direction = 'up'
                    new_pos.y = min_y
                else:
                    direction = 'left'
                    new_pos.x = min_x
            elif int(ship.y) <= min_y + 1:
                if int(ship.x) >= max_x - 1:
                    direction = 'down'
                    new_pos.y = max_y
                else:
                    direction = 'right'
                    new_pos.x = max_x
    else:
        if ship.y > max_y / 2:
            # Going down
            direction = 'down'
            new_pos.x = ship.x
            new_pos.y = max_y
        else:
            direction = 'up'
            new_pos.x = ship.x
            new_pos.y = 0
    #logging.info("I'm at (%s,%s) int INT (%s, %s) and WILL GO to (%s,%s) with direction = %s", ship.x, ship.y, int(ship.x), int(ship.y), new_pos.x, new_pos.y, direction)
    return [new_pos, direction, speed]

################ TURN START ###################
my_ships = [] # Just an initialization out of the game
info_my_ships = {}
rogue1_pos = {}

while True:
    time1 = time.time()
    game_map = game.update_map()
    player_id = game_map.get_me().id
    max_x = int(game_map.width - 1)
    min_x = 1
    max_y = int(game_map.height - 1)
    min_y = 1
    command_queue = []
    myself = game_map.my_id
    enemy_planets = {}
    enemy_docked = {}
    my_planets = []
    empty_planets = []
    targeted_planet = []
    ships_need_help = []
    big_planet = 0
    turn += 1

    ####### Planet Analysis
    #logging.info("Turn: %s Player: %s", turn, player_id)
    #logging.info("Analysing planets")
    for planet in game_map.all_planets():
        if planet.radius > big_planet:
            big_planet = planet.radius
        if planet.is_owned():
            if planet.owner.id != myself:
                if planet.owner.id in enemy_planets:
                    enemy_planets[planet.owner.id].append(planet.id)
                    enemy_docked[planet.owner.id] += len(planet.all_docked_ships())
                else:
                    enemy_planets[planet.owner.id] = [planet.id]
                    enemy_docked[planet.owner.id] = len(planet.all_docked_ships())
            else:
                my_planets.append(planet.id)
        else:
            empty_planets.append(planet.id)


    ####### Getting info from my ships
    ships_not_undocked = 0
    my_ships_t = game_map.get_me().all_ships()
    my_ships = []
    # We want to review first the DOCKED ships to verify if they are being attacked, so we "sort" my_ships
    for ship in my_ships_t:
        if ship.docking_status == ship.DockingStatus.UNDOCKED:
            my_ships.append(ship)
        else:
            ships_not_undocked += 1
            my_ships.insert(0, ship)

    #my_ships = game_map.get_me().all_ships()
    my_previous_info_ships = dict(info_my_ships)
    info_my_ships = {}
    for ship in my_ships:
        info_my_ships[ship.id] = ship

    all_ships = {}
    for ship in game_map._all_ships():
        all_ships[ship.id] = ship


    # Reviewing plans
    copy_d = dict(my_ships_with_plans)
    for shipid in copy_d:
        if shipid not in all_ships:
            my_ships_with_plans.pop(shipid)

    ####### Should I mine?
    max = 0
    for i in enemy_docked.values():
        if i > max:
            max = i

    planet_we_should_mine = None
    should_mine_planet = (max > ships_not_undocked + DELTA_NUM_SHIP_DOCKED) or (ships_not_undocked < MIN_NUM_DOCKED)
    #logging.info("Should you mine planet? %s  Look: Enemy MAX docked: %s Mine Docked: %s", should_mine_planet, max, ships_not_undocked )
    #should_mine_planet = (bool([a for a in enemy_planets.values() if len(a) > (len(my_planets) + 2)])) or len(my_planets) < MIN_NUM_DOCKED
    ##logging.info("Should you mine planet? %s  Look: %s", should_mine_planet, [a for a in enemy_planets.values() if len(a) > (len(my_planets) + 2)])

    # Checking comandos
    t_assigned_comando = assigned_comando[:]
    for shipid in t_assigned_comando:
        if shipid not in assigned_comando:
            assigned_comando.remove(shipid)
            for k,v in comandos.items():
                if shipid in v:
                    v.remove(shipid)
                    break

    for k, l_ship in comandos.items():
        for sid in l_ship:
            if sid not in all_ships:
                comandos[k].remove(sid)

    #logging.info("My planets: %s", my_planets)
    #logging.info("Empty planets: %s", empty_planets)
    #logging.info("Ememy planets: %s", enemy_planets)
    #logging.info("Enemy docked: %s", enemy_docked)
    #logging.info("Ship in comandos: %s", assigned_comando)
    #logging.info("Comandos: %s", comandos)
    #logging.info("All ships: %s", all_ships.keys())
    #logging.info("My plans: %s", my_ships_with_plans)

    for ship in my_ships:
        #logging.info("Ship %s", ship.id)

        # Calculating distances
        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
        ##logging.info("ATLETI: %s", entities_by_distance)
        # TODO: This should be done in one loop
        closest_empty_planets = []
        closest_enemy_ships = []
        closest_planets = []
        count = 0
        for dist, ent in entities_by_distance.items():
            count += 1
            if isinstance(ent[0], hlt.entity.Planet):
                closest_planets.append(ent[0])
                if not ent[0].is_owned() or ent[0].owner.id == player_id:
                    if count <= 3 and ent[0].radius == big_planet and ship.id not in my_ships_with_plans:
                        count = 4
                        # In case we should mine, this should be the planet
                        if should_mine_planet:
                            planet_we_should_mine = ent[0]
                    if not ent[0].is_owned():
                        closest_empty_planets.append(ent[0])

            elif isinstance(ent[0], hlt.entity.Ship) and ent[0] not in my_ships:
                closest_enemy_ships.append(ent[0])


        #closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]
        #closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in my_ships]
        #closest_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet)]

        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            #logging.info("Ship docked/docking")
            if ship.docking_status == ship.DockingStatus.DOCKED and ship.health < my_previous_info_ships[ship.id].health:
                #logging.info("This ship is being ATTACKED!!")
                # This ship is being attacked we need help!
                for dist, ent in entities_by_distance.items():
                    # I'd assum the closest ship will be the one attacking
                    if isinstance(ent[0], hlt.entity.Ship) and ent[0] not in my_ships:
                        he = need_help(ship.id, ship.planet, ent[0].id)
                        ships_need_help.append(he)
                        break
                    # If after going through the entities we can't find
            continue

        # If we are under attack, someone should help
        ship_helping = -1
        if len(ships_need_help) > 0:
            #logging.info("Ships who need help: %s", ships_need_help)
            count = 0
            for dist, ent in entities_by_distance.items():
                # If the ship is "close" to the one needing help, will help
                count += 1
                for sh in ships_need_help:
                    if (isinstance(ent[0], hlt.entity.Ship) and ent[0].id == sh.shipid) or \
                       (isinstance(ent[0], hlt.entity.Planet) and ent[0].id == sh.planetid):
                        #logging.info("This ship is close to the SHIP/PLANET who needs help")
                        # HELP SHIP
                        ship_helping = sh.enemyid
                        break
                if count >= 3:
                    break



        # Check if the ship already has any plan
        plan_executed = -1
        if ship.id in my_ships_with_plans and ship_helping == -1:
            if my_ships_with_plans[ship.id].target_planet > -1:
                #logging.info("This ship has plans to mine %s", my_ships_with_plans[ship.id].target_planet)

                # We need to check if the planet is empty or occupied by an enemy. If it's ocuppied, battle time
                planet_plan = game_map.get_planet(my_ships_with_plans[ship.id].target_planet)
                if (planet_plan.owner is None or planet_plan.owner.id == player_id) and not(planet_plan.is_full()):
                    plan_executed = mine_planet(ship, planet_plan, game_map, my_ships_with_plans, command_queue)
                    for k, v in comandos.items():
                        if ship.id in v:
                            comandos[k].remove(ship.id)
                            break
                    if plan_executed == 0:
                        comandos['mining'].append(ship.id)
                    else:
                        comandos['explorers'].append(ship.id)
                elif planet_plan.owner.id != player_id:
                    # Let's use ship_helping to specify that we need to attack that ship
                    ship_helping = planet_plan.all_docked_ships()[0].id
                    #logging.info("This planet is owned! Let's attack to one docked ship: %s", ship_helping)
            elif my_ships_with_plans[ship.id].position != hlt.entity.Position(-1, -1):
                #logging.info("This ship has plans to move to a position %s", my_ships_with_plans[ship.id].position)
                # For this kind of plan, we don't do anything else
                pass
            else:
                #logging.info("This ship has plans to attack %s", my_ships_with_plans[ship.id].target_ship)
                if should_mine_planet:
                    # We need to change plans
                    #logging.info("We need to change plans from attack to mine.")
                    pass
                else:
                    if my_ships_with_plans[ship.id].target_ship in all_ships:
                        plan_executed = attack_ship(ship, all_ships[my_ships_with_plans[ship.id].target_ship], all_ships.keys(), game_map, my_ships_with_plans, command_queue)
                    else:
                        #logging.info("Oh! The ship is gone!")
                        if ship.id in my_ships_with_plans:
                            my_ships_with_plans.pop(ship.id)

        if plan_executed == -1:  # NO PLAN. LET'S FIND ONE
            # Assign SHIP to COMANDO
            if ship.id not in assigned_comando:

                new_comando = random.choice(list(comandos))

                # First we check lone_ranger, then the rest to avoid a lone_ranger change in case of should_mine = True
                if new_comando == 'lone_ranger' and len(comandos['lone_ranger']) < ((len(my_ships) - len(comandos['mining'])) * PCT_LONE) and len(my_planets) > 0:
                    comandos['lone_ranger'].append(ship.id)
                    assigned_comando.append(ship.id)
                    #logging.info("This SHIP is lone_ranger")
                elif (new_comando == 'explorers' and len(comandos['explorers']) < ((len(my_ships) - len(comandos['mining'])) * PCT_EXPLORERS)) or should_mine_planet:
                    comandos['explorers'].append(ship.id)
                    assigned_comando.append(ship.id)
                    #logging.info("This SHIP is EXPLORER")
                elif new_comando == 'rogue_one' and len(comandos['rogue_one']) < ((len(my_ships) - len(comandos['mining'])) * PCT_ROGUE1):
                    comandos['rogue_one'].append(ship.id)
                    assigned_comando.append(ship.id)
                    #logging.info("This SHIP is a rogue_one")
                else:
                    #elif new_comando == 'support' and len(comandos['support']) < (len(my_ships) * PCT_SUPPORT):
                    # By "Default" SUPPORT
                    comandos['support'].append(ship.id)
                    assigned_comando.append(ship.id)
                    #logging.info("This SHIP is SUPPORT")

            we_have_a_plan = False
            planet_already_targeted = False
            if len(closest_empty_planets) > 0 and ship_helping == -1:
                '''
                If there is at least one empty planet, let's check how it's going:
                    - If the ship is a explorer -> Mining
                    - If I have no planets -> Mining
                    - If I have "much" fewer planets -> Mining
                '''

                if (ship.id in comandos['explorers'] or should_mine_planet) and ship.id not in comandos['lone_ranger']:
                    #logging.info("New MINE plan!")

                    # Check if we have a big planet, let's try to get more from it
                    count = 0
                    #logging.info("Let check if I should dock in my own planet")
                    pc = closest_planets[0]
                    if pc.owner is not None and pc.owner.id == player_id:
                        #logging.info("Checking radius and MAX")
                        if pc.radius == big_planet and \
                           len(pc.all_docked_ships()) < NUM_MAX_SHIP_DOCKED_SAME_PLANET and \
                           not pc.is_full():
                            #logging.info("Yes! We should dock in my own planet")
                            target_planet = pc
                            we_have_a_plan = True

                    if not we_have_a_plan:
                        count = 0
                        if planet_we_should_mine is not None:
                            #logging.info('1')
                            target_planet = planet_we_should_mine
                        else:
                            #logging.info('2')
                            target_planet = closest_empty_planets[0]
                        #logging.info("Ship assigned to planet: %s", target_planet)
                        for tp in closest_empty_planets:
                            # I'm going to check which of the three closest planets is better to go
                            count += 1
                            planet_already_targeted = False
                            #logging.info('Checking planet: %s', tp)
                            for sid, plans in my_ships_with_plans.items():
                                if sid != ship.id and plans.target_planet == tp.id:
                                    #logging.info('Someone going to this planet')
                                    # If someones is already going to this planet but is one big planet with free "spots", let's go
                                    if tp.radius == big_planet and len(tp.all_docked_ships()) + 1 < tp.num_docking_spots:
                                        #logging.info('But is a big planet, worthy to go!')
                                        # If somoeone if going there is a posibility to crash both ships
                                        # Halite is making too much mistakes even with ignore_ships = False
                                        # So we "modify" where is the planet, to calculate a new direction
                                        tp.x = tp.x + random.uniform(-2, 2)
                                        tp.y = tp.y + random.uniform(-2, 2)
                                    else:
                                        planet_already_targeted = True
                                    break
                            if not planet_already_targeted:
                                #logging.info('No one is going to this planet')
                                if tp.radius > target_planet.radius:
                                    #logging.info('This planet is better')
                                    target_planet = tp
                            if count >= 3:
                                break

                    if not planet_already_targeted:
                        we_have_a_plan = True
                        plan_executed = mine_planet(ship, target_planet, game_map, my_ships_with_plans, command_queue)
                        for k, v in comandos.items():
                            if ship.id in v:
                                comandos[k].remove(ship.id)
                                break
                        if plan_executed == 0:
                            comandos['mining'].append(ship.id)
                        else:
                            comandos['explorers'].append(ship.id)

            # ATTACK!
            if not we_have_a_plan:

                #TODO: We have to check the different COMANDOS!!!!
                if ship.id in comandos['lone_ranger']:
                    #logging.info("We have one LONE RANGER!")

                    if ship.id not in rogue1_pos:
                        rogue1_pos[ship.id] = [hlt.entity.Position(-1, -1), '0']

                    new_pos = rogue1_pos[ship.id][0]
                    direction = rogue1_pos[ship.id][1]

                    navigating = False
                    speed = int(hlt.constants.MAX_SPEED)

                    l = rogue1_calc_pos(ship, new_pos, direction, max_x, min_x, max_y, min_y)
                    rogue1_pos[ship.id] = [l[0], l[1]]
                    speed = l[2]
                    move_ship_to(ship, l[0], game_map, speed, my_ships_with_plans, command_queue)
                elif len(closest_enemy_ships) > 0:
                    if ship_helping != -1:
                        #logging.info("Going to help")
                        target_ship = all_ships[ship_helping]
                    else:
                        if ship.id in comandos['rogue_one']:
                            #logging.info("We have one ROGUE ONE!")
                            for planet in closest_planets:
                                if planet.owner is not None and planet.owner.id != player_id:
                                    target_ship = planet.all_docked_ships()[0]
                                    break
                        else:
                            target_ship = closest_enemy_ships[0]

                    #logging.info("ATTACK plan against %s", target_ship.id)
                    count = 0
                    for shipid, plan in my_ships_with_plans.items():
                        if plan.target_ship == target_ship.id:
                            count += 1
                        if count >= 3:
                            break
                    if count >= 3:
                        if len(closest_enemy_ships) > 1:
                            target_ship = closest_enemy_ships[1]
                            #logging.info("Too many ships already targeting this one. Let's find another: %s", target_ship.id)

                    attack_ship(ship, target_ship, all_ships.keys(), game_map, my_ships_with_plans, command_queue)
                    for k, v in comandos.items():
                        if ship.id in v:
                            comandos[k].remove(ship.id)
                            break
                    comandos['support'].append(ship.id)

    game.send_command_queue(command_queue)
    time2 = time.time()
    #logging.info("------------------------END TURN %0.3f ms", (time2-time1)*1000.0 )

    # TURN END
# GAME END