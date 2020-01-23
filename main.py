import discord
import json

"""
Parse JSON
"""

with open('config.json') as cfg:
    settings = json.load(cfg)
print(settings)
"""
Start Bot
"""

#client = discord.Client()
#client.run()
