import discord
import logging
import json
import requests

from sys import exit
from pathlib import Path
from datetime import datetime
from discord.ext import commands

def switch_platform(arg):
    switch = {
        'br': 'br1',
        'eun': 'eun1',
        'euw': 'euw1',
        'jp': 'jp1',
        'kr': 'kr',
        'lan': 'la1',
        'las': 'la2',
        'na': 'na1',
        'oce': 'oc1',
        'tr': 'tr1',
        'ru': 'ru'
    }
    return switch.get(arg, '-1')

# TODO: Change debug to be a launch option instead of program variable
debug = True

"""
Parse JSON
"""

with open('config.json') as cfg:
    settings = json.load(cfg)
    cfg.close()

rgkey = settings['riot-api-key']

#Get region from config and set host
host = switch_platform(settings['region'].lower())
if host == '-1':
    print("ERROR: Region in config is invald, must be one of the folowing: ['br', 'eun', 'euw', 'jp', 'kr', 'lan', 'las', 'na', 'oce', 'tr', 'ru']")
    exit(1)
host = 'https://' + host + '.api.riotgames.com/lol/'

#Check current DDragon files against live Riot ones to see if there's an update
#TODO: Look into replacing this call with one to the realms cdn file instead
rg_ver = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]

try:
    local_ver = json.loads(sorted(Path('.').rglob('manifest.json'))[0].read_text())['v']
except:
    print(f"ERROR: No Data Dragon files were detected, download them at https://ddragon.leagueoflegends.com/cdn/dragontail-{rg_ver}.tgz")
    exit(1)

if rg_ver > local_ver:
    print(f"ERROR: New Data Dragon files are available, download at https://ddragon.leagueoflegends.com/cdn/dragontail-{rg_ver}.tgz (local version: {local_ver})")
    exit(2)
elif local_ver > rg_ver:
    print(f"ERROR: You must have used Chronobreak because your local Data Dragon files are newer than Riot's! (Riot: {rg_ver}, local: {local_ver})")
    exit(2)

#Get language from config and set path
#TODO: I just found the languages.json file! Replace this hacked together method with that; currently id_ID not available so add check for that
langs = set()
data_folders = list(Path('.').rglob('data/*'))

for i in range(0, len(data_folders)):
    langs.add(data_folders[i].name)

if settings['language'] in langs:
    data_files = sorted(Path('.').rglob(settings['language']))[0]
else:
    print(f"ERROR: Language in config is invalid, must be one of the following: {sorted(langs)}")
    exit(1)

#Get champion keys, names, and ids from current language for later reference
champs_file = data_files/'champion.json'
champs_file_contents = json.loads(champs_file.read_text())
champs = {}
champids ={}

for (k, info) in champs_file_contents['data'].items():
    champs[int(info['key'])] = info['name']
    champids[info['name']] = info['id']

del champs_file_contents

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
    await ctx.send(f":ping_pong: Pong! `{round(bot.latency*1000, 2)} ms`")

#A test command to make sure the bot is handling arguments properly in the current context
@bot.command()
async def echo(ctx, *, args):
    await ctx.send(args)

#Lookup basic summoner info
@bot.command()
async def summoner(ctx, *, args):
    #TODO: Sanitize user input
    parsed_summoner = requests.utils.quote(args)

    query = host + 'summoner/v4/summoners/by-name/' + parsed_summoner
    payload = {'api_key': rgkey}
    response = requests.get(query, params=payload)
    summoner = response.json()

    if response.status_code == 200:
        embedURL = 'https://' + settings['region'].lower() + '.op.gg/summoner/userName=' + parsed_summoner
        embedIMG = str(sorted(Path('.').rglob('profileicon'))[0].resolve()) + '/' + str(summoner['profileIconId']) + '.png'
        file = discord.File(embedIMG, filename='icon.png')

        embed = discord.Embed(title=summoner['name'], url=embedURL, color=0xddc679)
        embed.set_thumbnail(url='attachment://icon.png')

        #Summoner level
        embed.add_field(name='Level', value=summoner['summonerLevel'], inline=False)

        #Ranking information
        rquery = host + 'league/v4/entries/by-summoner/' + summoner['id']
        rresponse = requests.get(rquery, params=payload)
        ranks = rresponse.json()

        if len(ranks) > 0:
            rank = ''

            for i in range(0, len(ranks)):
                queue = ranks[i]['queueType'].split('_')
                rank = rank + queue[1] + ' - ' + ranks[i]['tier'] + ' ' + ranks[i]['rank'] + ' (' + str(ranks[i]['leaguePoints']) + ' LP)\n'

            embed.add_field(name='Rank', value=rank, inline=False)
        else:
            embed.add_field(name='Rank', value='Unranked', inline=False)

        #Champion mastery
        mquery = host + 'champion-mastery/v4/champion-masteries/by-summoner/' + summoner['id']
        mresponse = requests.get(mquery, params=payload)
        masteries = mresponse.json()

        if len(masteries) > 0:
            mastery = ''

            for i in range(0, min(len(masteries), 3)):
                mastery = mastery + champs.get(masteries[i]['championId'], '') + ' - ' + "{:,}".format(masteries[i]['championPoints']) + ' points\n'

            embed.add_field(name='Top 3 Champions', value=mastery, inline=False)

        await ctx.send(file=file, embed=embed)

    elif response.status_code == 404:
        await ctx.send(f"No information was found for the summoner \"{args}\" on the {settings['region'].upper()} server.")

    else:
        try:
            await ctx.send(f"ERROR {summoner['status']['status_code']}: {summoner['status']['message']}")
        except:
            await ctx.send(f"ERROR {response.status_code}, no other information is available.")

#Retrieve ranked match history
#TODO: Unranked match history too?
@bot.command()
async def history(ctx, *, args):
    parsed_summoner = requests.utils.quote(args)

    query = host + 'summoner/v4/summoners/by-name/' + parsed_summoner
    payload = {'api_key': rgkey}
    response = requests.get(query, params=payload)
    summoner = response.json()

    if response.status_code == 200:
        await ctx.send("Not yet implemented.")
    elif response.status_code == 404:
        await ctx.send(f"No information was found for the summoner \"{args}\" on the {settings['region'].upper()} server.")

    else:
        try:
            await ctx.send(f"ERROR {summoner['status']['status_code']}: {summoner['status']['message']}")
        except:
            await ctx.send(f"ERROR {response.status_code}, no other information is available.")

#Displays information about a champion using localized Data Dragon information
@bot.command()
async def champion(ctx, *, args):
    found = False
    
    for (name, champid) in champids.items():
        if name == args:
            found = True
            champ = champid
            break
        elif champid == args:
            found = True
            champ = champid
            break

    if found:
        champ_file = data_files/'champion'/(champ+'.json')
        champ_file_contents = json.loads(champ_file.read_text())
    else:
        await ctx.send(f"I couldn't find any information on the champion \"{args}\", did you type it in correctly?")

#If the debug flag is enabled log messages to console to ensure the bot is connected properly
@bot.event
async def on_message(message):
    if debug == True:
        print(f"{message.guild} - #{message.channel} - {message.author}({message.author.id}): {message.content}")
    await bot.process_commands(message)

bot.run(settings['bot-token'])
