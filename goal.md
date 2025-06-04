we are trying to make it easier to use minecraft-web-client using the console.
To do this assuming we are running a websocket server (see server.js and wsCommandClient.ts) on port 8081 and we will additionally accept websocket connections that would accept commands and store them in a queue and run them and sent them to the mineflayer bot.
specifically, we would focus on exposing the left and right (LeftTouchArea, RightTouchArea) controls via the wsCommandClient.ts interface.

see sample_client.py for how one can send messages to the bot

Our goal is to expose touch funtionality via cli.