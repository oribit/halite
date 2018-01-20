import hlt
import logging
from collections import OrderedDict
game = hlt.Game("Ganon-V2")
logging.info("Starting GanonBot-V2")

comandos = {'suicide_squad' : [], # 15%
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

def mine_planet(ship, target_planet, game_map, my_ships_with_plans, command_queue):
    logging.info("Let's MINE with ship %s to planet %s", ship.id, target_planet)

    if ship.can_dock(target_planet):
        command_queue.append(ship.dock(target_planet))
        my_ships_with_plans[ship.id] = ship_plan(ship.id, planet=target_planet.id)
        logging.info("SHIP PLANS1 %s %s", ship.id, my_ships_with_plans[ship.id])

    else:
        navigate_command = ship.navigate(
            ship.closest_point_to(target_planet),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            ignore_ships=False)

        if navigate_command:
            command_queue.append(navigate_command)
            my_ships_with_plans[ship.id] = ship_plan(ship.id, planet=target_planet.id)
            logging.info("SHIP PLANS2 %s %s", ship.id, my_ships_with_plans[ship.id])
    return True

def attack_ship(ship, target_ship, game_map, my_ships_with_plans, command_queue):
    logging.info("Let's ATTACK with ship %s to ship %s", ship.id, target_ship)

    if target_ship in all_ships:
        navigate_command = ship.navigate(
            ship.closest_point_to(target_ship),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            angular_step=5,
            ignore_ships=False)

        if navigate_command:
            command_queue.append(navigate_command)
            my_ships_with_plans[ship.id] = ship_plan(ship.id, ship=target_ship)
    else:
        logging.info("Oh! The ship is gone!")
        if ship.id in my_ships_with_plans:
            my_ships_with_plans.pop(ship.id)
        return False
    return True

while True:
    game_map = game.update_map()
    command_queue = []
    myself = game_map.my_id
    enemy_planets = []
    my_planets = []
    empty_planets = []
    targeted_planet = []


    for planet in game_map.all_planets():
        if planet.is_owned():
            logging.info("Planet.owner: %s", planet.owner.id)
            logging.info("myself: %s", myself)
            if planet.owner.id != myself:
                enemy_planets.append(planet.id)
            else:
                my_planets.append(planet.id)
        else:
            empty_planets.append(planet.id)

    my_ships = game_map.get_me().all_ships()
    all_ships = game_map._all_ships()

    for ship in assigned_comando:
        if ship not in my_ships:
            assigned_comando.remove(ship)
            for k,v in comandos.items():
                if ship.id in v:
                    v.remove(ship.id)
                    break

    logging.info("My planets: %s", my_planets)
    logging.info("Empty planets: %s", empty_planets)
    logging.info("Ememy planets: %s", enemy_planets)
    logging.info("Ship in comandos: %s", assigned_comando)
    logging.info("Comandos %s", comandos)

    for ship in my_ships:
        shipid = ship.id
        logging.info("Ship %s", shipid)
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            continue

        # Assign SHIP to COMANDO
        if shipid not in assigned_comando:
            # Matching EXPLORERS
            if len(comandos['explorers']) < len(my_ships) * .25:
                comandos['explorers'].append(shipid)
                assigned_comando.append(ship)
            elif len(comandos['support']) < len(my_ships) * .45:
                comandos['support'].append(shipid)
                assigned_comando.append(ship)
            elif len(comandos['lone_ranger']) < len(my_ships) * .15:
                comandos['lone_ranger'].append(shipid)
                assigned_comando.append(ship)
            elif len(comandos['suicide_squad']) < len(my_ships) * .15:
                comandos['suicide_squad'].append(shipid)
                assigned_comando.append(ship)


        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
        closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in my_ships]



        # Check if the ship already has any plan
        plan_executed = False
        if shipid in my_ships_with_plans:
            if my_ships_with_plans[shipid].target_planet > -1:
                logging.info("This ship has plans to mine %s", my_ships_with_plans[shipid].target_planet)
                plan_executed = mine_planet(ship, game_map.get_planet(my_ships_with_plans[shipid].target_planet), game_map, my_ships_with_plans, command_queue)
            else:
                logging.info("This ship has plans to attack %s", my_ships_with_plans[shipid].target_ship)
                plan_executed = attack_ship(ship, my_ships_with_plans[shipid].target_ship, game_map, my_ships_with_plans, command_queue)

        if not plan_executed: # NO PLAN. LET'S FIND ONE
             # If there are some empty planets and we are not "winning" planets, let's mine it
            if (len(closest_empty_planets) > 0 and len(my_planets) < len(enemy_planets) + 1) or \
               not (len(closest_enemy_ships) > 0):
                logging.info("New MINE plan!")
                planet_already_targeted = False
                for target_planet in closest_empty_planets:
                    planet_already_targeted = False
                    logging.info('Checking planet: %s', target_planet)
                    for sid, plans in my_ships_with_plans.items():
                        if sid != shipid and plans.target_planet == target_planet.id:
                            logging.info('Someone going to this planet')
                            planet_already_targeted = True
                            break
                    if not planet_already_targeted:
                        logging.info('No one is going to this planet')
                        break

                if not planet_already_targeted:
                    mine_planet(ship, target_planet, game_map, my_ships_with_plans, command_queue)

            # ATTACK!
            elif len(closest_enemy_ships) > 0:
                logging.info("New ATTACK plan!")
                target_ship = closest_enemy_ships[0]
                attack_ship(ship, target_ship, game_map, my_ships_with_plans, command_queue)


    game.send_command_queue(command_queue)
    # TURN END
# GAME END