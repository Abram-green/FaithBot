import sys
import os
import threading
import time
from config import *
from buttons import *

import asyncio
import datetime
import io
from optparse import Option
import re, time
import os
from fake_useragent import UserAgent

import discord
from discord import *
from discord import Embed
from discord import Emoji
from discord.commands import Option
from discord.commands import permissions as Perm
from discord.enums import ActivityType, Status
from discord.ext import commands
from discord.flags import Intents
from discord.partial_emoji import PartialEmoji

def start_bot():
    def start_bot(name):
        print(f"Start: {name}")
        os.system(f"nohup python3 {name} &")

    t = threading.Thread(target=start_bot, args=("bot.py", ))
    t.start()
    t.join()

def stop():
    os.system("pkill -f bot.py")
    print("Script stop")

def restart():
    stop()
    start_bot()

bot = commands.Bot(command_prefix=prefix, intents=Intents.all())

@bot.event
async def on_ready():
    t = threading.Thread(target=start_bot)
    t.start()
    t.join()


@bot.slash_command(name="panel", description="Управление ботом", guild_ids=[guild_id], default_permission=False)
@Perm.has_any_role("Разработчик", "Администратор")
async def _admin(inter):
    embed = Embed(title="Административная панель", description="Остоновка работы скрипта, рестарт и мб потом что-то ещё...")

    components = [
        AdminButton("Стоп", "stop", discord.enums.ButtonStyle.red, inter, bot),
        AdminButton("Рестарт", "restart", discord.enums.ButtonStyle.green, inter, bot)
    ]

    view = discord.ui.View(timeout=None)
    for i in components:
        view.add_item(i)

    await inter.respond(embed=embed, view=view)


if __name__ == "__main__":
    bot.run(token)