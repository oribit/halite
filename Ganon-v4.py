import hlt
import logging
import time
from collections import OrderedDict
game = hlt.Game("Ganon-V4")
logging.info("Starting GanonBot-V4")

NUM_MAX_SHIP_DOCKED_SAME_PLANET = 4

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


while True:
    time1 = time.time()
    game_map = game.update_map()
    command_queue = []
    myself = game_map.my_id
    enemy_planets = {}
    my_planets = []
    empty_planets = []
    targeted_planet = []
    big_planet = 0
    turn += 1

    # Planet Analysis
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


    my_ships = game_map.get_me().all_ships()
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

    logging.info("My planets: %s", my_planets)
    logging.info("Empty planets: %s", empty_planets)
    logging.info("Ememy planets: %s", enemy_planets)
    logging.info("Ship in comandos: %s", assigned_comando)
    logging.info("Comandos: %s", comandos)
    logging.info("All ships: %s", all_ships.keys())

    for ship in my_ships:
        logging.info("Ship %s", ship.id)
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            logging.info("Ship docked")
            continue

        # Check if the ship already has any plan
        plan_executed = -1
        if ship.id in my_ships_with_plans:
            if my_ships_with_plans[ship.id].target_planet > -1:
                logging.info("This ship has plans to mine %s", my_ships_with_plans[ship.id].target_planet)
                plan_executed = mine_planet(ship, game_map.get_planet(my_ships_with_plans[ship.id].target_planet), game_map, my_ships_with_plans, command_queue)
                for k, v in comandos.items():
                    if ship.id in v:
                        comandos[k].remove(ship.id)
                        break
                if plan_executed == 0:
                    comandos['mining'].append(ship.id)
                else:
                    comandos['explorers'].append(ship.id)
            else:
                logging.info("This ship has plans to attack %s", my_ships_with_plans[ship.id].target_ship)
                if my_ships_with_plans[ship.id].target_ship in all_ships:
                    plan_executed = attack_ship(ship, all_ships[my_ships_with_plans[ship.id].target_ship], all_ships.keys(), game_map, my_ships_with_plans, command_queue)
                else:
                    logging.info("Oh! The ship is gone!")
                    if ship.id in my_ships_with_plans:
                        my_ships_with_plans.pop(ship.id)

        if plan_executed == -1:  # NO PLAN. LET'S FIND ONE

            # Calculating distances
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
            closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]
            closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in my_ships]

            # Assign SHIP to COMANDO
            if ship.id not in assigned_comando:
                if len(comandos['explorers']) < (len(my_ships) * .25) and should_mine_planet:
                    comandos['explorers'].append(ship.id)
                    assigned_comando.append(ship.id)
                    logging.info("This SHIP is EXPLORER")
                elif len(comandos['support']) < (len(my_ships) * .45):
                    comandos['support'].append(ship.id)
                    assigned_comando.append(ship.id)
                    logging.info("This SHIP is SUPPORT")
                elif len(comandos['suicide_squad']) < (len(my_ships) * .15):
                    comandos['suicide_squad'].append(ship.id)
                    assigned_comando.append(ship.id)
                    logging.info("This SHIP is SUICIDE_SQUAD")
                else:
                    comandos['lone_ranger'].append(ship.id)
                    assigned_comando.append(ship.id)
                    logging.info("This SHIP is an LONE_RANGER")

            we_have_a_plan = False
            planet_already_targeted = False
            if len(closest_empty_planets) > 0:
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
                    for close_entities in entities_by_distance:
                        count += 1
                        if count >= 5:
                            break
                        if isinstance(close_entities, hlt.entity.Planet) and close_entities.is_owned():
                            if close_entities.radius == big_planet and len(
                                    close_entities.all_docked_ships()) < NUM_MAX_SHIP_DOCKED_SAME_PLANET:
                                target_planet = close_entities
                                we_have_a_plan = True
                                break

                    if not we_have_a_plan:
                        for target_planet in closest_empty_planets:
                            planet_already_targeted = False
                            logging.info('Checking planet: %s', target_planet)
                            for sid, plans in my_ships_with_plans.items():
                                if sid != ship.id and plans.target_planet == target_planet.id:
                                    logging.info('Someone going to this planet')
                                    planet_already_targeted = True
                                    break
                            if not planet_already_targeted:
                                logging.info('No one is going to this planet')
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
                    logging.info("ATTACK plan!")
                    target_ship = closest_enemy_ships[0]
                    attack_ship(ship, target_ship, all_ships.keys(), game_map, my_ships_with_plans, command_queue)

    game.send_command_queue(command_queue)
    time2 = time.time()
    logging.info("------------------------END TURN %0.3f ms", (time2-time1)*1000.0 )

    # TURN END
# GAME END