import discord
import logging
import json

from pathlib import Path
from datetime import datetime
from discord.ext import commands

# TODO: Change debug to be a launch option instead of program variable
debug = True

"""
Parse JSON
"""

with open('config.json') as cfg:
    settings = json.load(cfg)

"""
Set up logging
"""

Path('logs').mkdir(parents=True, exist_ok=True)
logfile = 'logs/' + datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + '.log'

logger = logging.getLogger('discord')

if debug == True:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

loghandler = logging.FileHandler(filename=logfile, encoding='utf-8', mode='w')
loghandler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(loghandler)

"""
Start Bot
"""

bot = commands.Bot(command_prefix=settings['prefix'])

#TODO: Put champ quotes in a file and random pull
@bot.event
async def on_ready():
    print("Ready to set the world on fire? hehehe... -Brand")

#A test command to make sure that the bot is hooking into the Discord API properly
@bot.command()
async def ping(ctx):
    await ctx.send(f':ping_pong: Pong! `{round(bot.latency*1000, 2)} ms`')

#A test command to make sure the bot is handling arguments properly in the current context
@bot.command()
async def echo(ctx, arg):
    await ctx.send(arg)

#If the debug flag is enabled log messages to console to ensure the bot is connected properly
@bot.event
async def on_message(message):
    if debug == True:
        print(f"{message.channel} - {message.author}/{message.author.name}: {message.content}")
    await bot.process_commands(message)

bot.run(settings['bot-token'])