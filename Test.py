"""
Welcome to your first Halite-II bot!

This bot's name is Settler. It's purpose is simple (don't expect it to win complex games :) ):
1. Initialize game
2. If a ship is not docked and there are unowned planets
2.a. Try to Dock in the planet if close enough
2.b If not, go towards the planet

Note: Please do not place print statements here as they are used to communicate with the Halite engine. If you need
to log anything use the logging module.
"""
# Let's start by importing the Halite Starter Kit so we can interface with the Halite engine
import hlt
# Then let's import the logging module so we can print out information
import logging

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("TEST-BOT")
# Then we print our start message to the logs
logging.info("Starting my TEST bot!")
planned_planets = []
d_pos = {}
new_pos = hlt.entity.Position(-1, -1)
iturn = 0
while True:
    iturn += 1
    # TURN START
    # Update the map for the new turn and get the latest version
    logging.info("TURN: %s", iturn)
    game_map = game.update_map()
    max_x = int(game_map.width - 1)
    min_x = 1
    max_y = int(game_map.height - 1)
    min_y = 1


    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    # For every ship that I control
    for ship in game_map.get_me().all_ships():
        if ship.id not in d_pos:
            d_pos[ship.id] = [hlt.entity.Position(-1, -1), '0']

        new_pos = d_pos[ship.id][0]
        direction = d_pos[ship.id][1]
        # If the ship is docked
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            continue

        logging.info("Ship ID: %s", ship.id)
        logging.info("I'm at (%s,%s) int (%s, %s) and I should go to (%s,%s) with direction = %s", ship.x, ship.y, int(ship.x), int(ship.y), new_pos.x, new_pos.y, direction)


        navigating = False
        speed = int(hlt.constants.MAX_SPEED)
        if new_pos.x != -1:
            # If we have a position set, we need to know if we are there

            '''
            ship.x = 121
            ship.y = 19
            
            new.x = 120
            new.y = 0
            '''


            logging.info("ATLETI1 %s %s %s %s", new_pos.x, new_pos.y, ship.x, ship.y)




            if not (int(new_pos.x - 1) <= int(ship.x) <= int(new_pos.x + 1)) or \
               not (int(new_pos.y - 1) <= int(ship.y) <= int(new_pos.y + 1)):
                logging.info("ATLETI2: speed %s X- %s X+ %s Y- %s Y+ %s", speed, int(ship.x - speed), int(ship.x + speed), int(ship.y - speed), int(ship.y + speed))

                if direction == 'left' and (int(ship.x - speed) < min_x):
                    speed = int(ship.x - min_x)
                    logging.info("Too close to X = 0 so adjusting speed %s", speed)
                elif direction == 'right' and (int(ship.x + speed) > max_x):
                    speed = int(max_x - ship.x)
                    logging.info("Too close to X = MAX_X so adjusting speed %s", speed)
                elif direction == 'up' and (int(ship.y - speed) < min_y):
                    speed = int(ship.y - min_y)
                    logging.info("Too close to Y = 0 so adjusting speed %s", speed)
                elif direction == 'down' and (int(ship.y + speed) > max_y):
                    speed = int(max_y - ship.y)
                    logging.info("Too close to Y = MAX_Y so adjusting speed %s", speed)

                logging.info("STILL NAVIGATING")
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
        logging.info("I'm at (%s,%s) int INT (%s, %s) and WILL GO to (%s,%s) with direction = %s", ship.x, ship.y, int(ship.x), int(ship.y), new_pos.x, new_pos.y, direction)
        d_pos[ship.id] = [new_pos, direction]



        navigate_command = ship.navigate(
            new_pos,
            game_map,
            speed=speed,
            ignore_ships=False)
        # If the move is possible, add it to the command_queue (if there are too many obstacles on the way
        # or we are trapped (or we reached our destination!), navigate_command will return null;
        # don't fret though, we can run the command again the next turn)
        if navigate_command:
            command_queue.append(navigate_command)


    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
