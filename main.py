import discord
import logging
import json

debug = True

"""
Parse JSON
"""

with open('config.json') as cfg:
    settings = json.load(cfg)

"""
Set up logging
Currently does not preserve old logs, TODO: Set up log preservation
"""

logger = logging.getLogger('discord')

if debug == True:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

loghandler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
loghandler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(loghandler)

"""
Start Bot
"""

client = discord.Client()

#If the debug flag is enabled log messages to console to ensure the bot is connected properly
@client.event
async def on_message(message):
    if debug == True:
        print(message.content)


client.run(settings['bot-token'])