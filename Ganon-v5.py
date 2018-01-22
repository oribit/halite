import hlt
import logging
import time
from collections import OrderedDict
game = hlt.Game("Ganon-V5")
logging.info("Starting GanonBot-V5")

NUM_MAX_SHIP_DOCKED_SAME_PLANET = 4
PCT_EXPLORERS = .20
PCT_SUPPORT = .45
PCT_LONE = .20
PCT_SUICIDE = 1 - PCT_EXPLORERS - PCT_SUPPORT - PCT_LONE

comandos = {'mining' : [],
            'suicide_squad' : [], # 15%
            'lone_ranger': [],    # 15%
            'support': [],        # 45%
            'explorers': []}      # 25%
assigned_comando = []

class ship_plan():
    def __init__(self, id, planet=-1, ship=-1):
        self.id = id
        self.target_planet = planet
        self.target_ship = ship

    def __str__(self):
        return 'Id: {}, Target Planet: {}, Target Ship: {}'.format(self.id, self.target_planet, self.target_ship)

class need_help():
    def __init__(self, id, planet, enemy):
        self.shipid = id
        self.planetid = planet
        self.enemyid = enemy

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
    logging.info("Let's MINE with ship %s to planet %s", ship.id, target_planet)
    type_mine = -1
    if ship.can_dock(target_planet):
        command_queue.append(ship.dock(target_planet))
        my_ships_with_plans[ship.id] = ship_plan(ship.id, planet=target_planet.id)
        logging.info("SHIP PLANS1 %s %s", ship.id, my_ships_with_plans[ship.id])
        type_mine = 0
    else:
        navigate_command = ship.navigate(
            ship.closest_point_to(target_planet),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            ignore_ships=False)
        if navigate_command is None:
            navigate_command = ship.navigate(
                ship.closest_point_to(target_planet),
                game_map,
                max_corrections=180,
                speed=int(hlt.constants.MAX_SPEED),
                ignore_ships=False)
        if navigate_command:
            command_queue.append(navigate_command)
            my_ships_with_plans[ship.id] = ship_plan(ship.id, planet=target_planet.id)
            logging.info("SHIP PLANS2 %s %s", ship.id, my_ships_with_plans[ship.id])
            type_mine = 1

    return type_mine


def attack_ship(ship, target_ship, all_ships_k, game_map, my_ships_with_plans, command_queue):
    logging.info("Let's ATTACK with ship %s to ship %s", ship.id, target_ship)

    navigate_command = ship.navigate(
        ship.closest_point_to(target_ship),
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



################ TURN START ###################
my_ships = [] # Just an initialization out of the game
info_my_ships = {}

while True:
    time1 = time.time()
    game_map = game.update_map()
    player_id = game_map.get_me().id
    command_queue = []
    myself = game_map.my_id
    enemy_planets = {}
    my_planets = []
    empty_planets = []
    targeted_planet = []
    ships_need_help = []
    big_planet = 0
    turn += 1

    # Planet Analysis
    logging.info("Turn: %s Player: %s", turn, player_id)
    logging.info("Analysing planets")
    for planet in game_map.all_planets():
        if planet.radius > big_planet:
            big_planet = planet.radius
        if planet.is_owned():
            if planet.owner.id != myself:
                if planet.owner.id in enemy_planets:
                    enemy_planets[planet.owner.id].append(planet.id)
                else:
                    enemy_planets[planet.owner.id] = [planet.id]
            else:
                my_planets.append(planet.id)
        else:
            empty_planets.append(planet.id)
    should_mine_planet = (bool([a for a in enemy_planets.values() if len(a) > (len(my_planets) + 2)])) or len(my_planets) <= 3
    logging.info("Should you mine planet? %s  Look: %s", should_mine_planet, [a for a in enemy_planets.values() if len(a) > (len(my_planets) + 2)])

    # Getting info from my ships
    my_ships_t = game_map.get_me().all_ships()
    my_ships = []
    # We want to review first the DOCKED ships to verify if they are being attacked, so we "sort" my_ships
    for ship in my_ships_t:
        if ship.docking_status == ship.DockingStatus.UNDOCKED:
            my_ships.append(ship)
        else:
            my_ships.insert(0, ship)

    #my_ships = game_map.get_me().all_ships()
    my_previous_info_ships = dict(info_my_ships)
    info_my_ships = {}
    for ship in my_ships:
        info_my_ships[ship.id] = ship

    all_ships = {}
    for ship in game_map._all_ships():
        all_ships[ship.id] = ship

    t_assigned_comando = assigned_comando[:]
    for shipid in t_assigned_comando:
        #logging.info("SHIP IN COMANDO %s", ship)
        #logging.info("AAA: %s", [a for a in my_ships if a.id == ship.id])
        #logging.info("BBB: %s", not bool([a for a in my_ships if a.id == ship.id]))
        if shipid not in assigned_comando:
            #logging.info("ATLETI %s", ship)
            assigned_comando.remove(shipid)
            for k,v in comandos.items():
                if shipid in v:
                    v.remove(shipid)
                    break

    for k, l_ship in comandos.items():
        for sid in l_ship:
            if sid not in all_ships:
                comandos[k].remove(sid)

    logging.info("My planets: %s", my_planets)
    logging.info("Empty planets: %s", empty_planets)
    logging.info("Ememy planets: %s", enemy_planets)
    logging.info("Ship in comandos: %s", assigned_comando)
    logging.info("Comandos: %s", comandos)
    logging.info("All ships: %s", all_ships.keys())
    logging.info("Ship needing help: %s", ships_need_help)

    for ship in my_ships:
        logging.info("Ship %s", ship.id)

        # Calculating distances
        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
        #logging.info("ATLETI: %s", entities_by_distance)
        # TODO: This should be done in one loop
        closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in my_ships]
        closest_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet)]

        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            logging.info("Ship docked/docking")
            if ship.docking_status == ship.DockingStatus.DOCKED and ship.health < my_previous_info_ships[ship.id].health:
                logging.info("This ship is being ATTACKED!!")
                # This ship is being attacked we need help!
                for dist, ent in entities_by_distance.items():
                    # I'd assum the closest ship will be the one attacking
                    if isinstance(ent, hlt.entity.Ship) and ent not in my_ships:
                        he = need_help(ship.id, ship.planet, ent.id)
                        ships_need_help.append(he)
                        break
                    # If after going through the entities we can't find
            continue

        # If we are under attack, someone should help
        ship_helping = -1
        if len(ships_need_help) > 0:
            logging.info("Ships who need help: %s", ships_need_help)
            count = 0
            for dist, ent in entities_by_distance.items():
                # If the ship is "close" to the one needing help, will help
                count += 1
                for sh in ships_need_help:
                    if (isinstance(ent, hlt.entity.Ship) and ent.id == sh.shipid) or \
                       (isinstance(ent, hlt.entity.Planet) and ent.id == sh.planetid):
                        logging.info("This ship is close to the SHIP/PLANET who needs help")
                        # HELP SHIP
                        ship_helping = sh.enemyid
                        break
                if count >= 3:
                    break



        # Check if the ship already has any plan
        plan_executed = -1
        if ship.id in my_ships_with_plans and ship_helping == -1:
            if my_ships_with_plans[ship.id].target_planet > -1:
                logging.info("This ship has plans to mine %s", my_ships_with_plans[ship.id].target_planet)

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
                    logging.info("This planet is owned! Let's attack to one docked ship: %s", ship_helping)
            else:
                logging.info("This ship has plans to attack %s", my_ships_with_plans[ship.id].target_ship)
                if should_mine_planet:
                    # We need to change plans
                    logging.info("We need to change plans from attack to mine.")
                    pass
                else:
                    if my_ships_with_plans[ship.id].target_ship in all_ships:
                        plan_executed = attack_ship(ship, all_ships[my_ships_with_plans[ship.id].target_ship], all_ships.keys(), game_map, my_ships_with_plans, command_queue)
                    else:
                        logging.info("Oh! The ship is gone!")
                        if ship.id in my_ships_with_plans:
                            my_ships_with_plans.pop(ship.id)

        if plan_executed == -1:  # NO PLAN. LET'S FIND ONE
            # Assign SHIP to COMANDO
            if ship.id not in assigned_comando:
                if len(comandos['explorers']) < (len(my_ships) * PCT_EXPLORERS) or should_mine_planet:
                    comandos['explorers'].append(ship.id)
                    assigned_comando.append(ship.id)
                    logging.info("This SHIP is EXPLORER")
                elif len(comandos['support']) < (len(my_ships) * PCT_SUPPORT):
                    comandos['support'].append(ship.id)
                    assigned_comando.append(ship.id)
                    logging.info("This SHIP is SUPPORT")
                elif len(comandos['lone_ranger']) < (len(my_ships) * PCT_LONE):
                    comandos['lone_ranger'].append(ship.id)
                    assigned_comando.append(ship.id)
                    logging.info("This SHIP is an LONE_RANGER")
                #elif len(comandos['suicide_squad']) < (len(my_ships) * .15): # The rest
                else:
                    comandos['suicide_squad'].append(ship.id)
                    assigned_comando.append(ship.id)
                    logging.info("This SHIP is SUICIDE_SQUAD")


            we_have_a_plan = False
            planet_already_targeted = False
            if len(closest_empty_planets) > 0 and ship_helping == -1:
                '''
                If there is at least one empty planet, let's check how it's going:
                    - If the ship is a explorer -> Mining
                    - If I have no planets -> Mining
                    - If I have "much" fewer planets -> Mining
                '''

                if (ship.id in comandos['explorers']) or should_mine_planet:
                    logging.info("New MINE plan!")

                    # Check if we have a big planet, let's try to get more from it
                    count = 0
                    logging.info("Let check if I should dock in my own planet")
                    pc = closest_planets[0]
                    if pc.owner is not None and pc.owner.id == player_id:
                        logging.info("Checking radius and MAX")
                        if pc.radius == big_planet and \
                           len(pc.all_docked_ships()) < NUM_MAX_SHIP_DOCKED_SAME_PLANET and \
                           not pc.is_full():
                            target_planet = pc
                            we_have_a_plan = True

                    if not we_have_a_plan:
                        count = 0
                        target_planet = closest_empty_planets[0]
                        for tp in closest_empty_planets:
                            count += 1
                            planet_already_targeted = False
                            logging.info('Checking planet: %s', tp)
                            for sid, plans in my_ships_with_plans.items():
                                if sid != ship.id and plans.target_planet == tp.id:
                                    logging.info('Someone going to this planet')
                                    if tp.radius == big_planet and len(tp.all_docked_ships()) + 1 < tp.num_docking_spots:
                                        logging.info('But is a big planet, worthy to go!')
                                    else:
                                        planet_already_targeted = True
                                    break
                            if not planet_already_targeted:
                                logging.info('No one is going to this planet')
                                if tp.radius > target_planet.radius:
                                    logging.info('This planet is better')
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



                if len(closest_enemy_ships) > 0:
                    if ship_helping != -1:
                        logging.info("Going to help")
                        target_ship = all_ships[ship_helping]
                    else:
                        logging.info("ATTACK plan!")
                        target_ship = closest_enemy_ships[0]
                    attack_ship(ship, target_ship, all_ships.keys(), game_map, my_ships_with_plans, command_queue)
                    for k, v in comandos.items():
                        if ship.id in v:
                            comandos[k].remove(ship.id)
                            break
                    comandos['support'].append(ship.id)

    game.send_command_queue(command_queue)
    time2 = time.time()
    logging.info("------------------------END TURN %0.3f ms", (time2-time1)*1000.0 )

    # TURN END
# GAME END