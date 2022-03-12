import asyncio
import datetime
import io
from optparse import Option
import re, time
import random
import chardet
import os
import json
import ast
import codecs
import requests
import pyshorteners
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

from bs4 import BeautifulSoup

from config import *
from mc import *
from sqldb import *
import stats
import buttons
from buttons import *

ua = UserAgent()

bytes = min(32, os.path.getsize(filename))
raw = open(filename, 'rb').read(bytes)

if raw.startswith(codecs.BOM_UTF8):
    encoding = 'utf-8-sig'
else:
    result = chardet.detect(raw)
    encoding = result['encoding']

infile = io.open(filename, 'r', encoding=encoding)
wordlist = infile.read().split(", ")
infile.close()

users = {}
last_post = 0

bot = commands.Bot(command_prefix=prefix, intents=Intents.all())

card_method = {
    'qiwi': {'name': 'Qiwi', 'color': discord.Color.from_rgb(255, 140, 0)},
    'qiwi_card': {'name': 'Дебетовая карта', 'color': discord.Color.from_rgb(0, 83, 151)}
}

choice_roles_emojis = {
    "📰": pinging_role_advert,
    "💰": pinging_role_trade,
    "🎥": pinging_role_content
}

activity_type = {
    "Poker Night": 755827207812677713,
    "Betrayal.io": 773336526917861400,
    "Fishington": 814288819477020702,
    "Chess in the Park": 832012774040141894,
    "Checkers in the Park": 832013003968348200,
    "Ocho": 832025144389533716,
    "Watch YouTube": 880218394199220334,
    "Doodle Crew": 878067389634314250,
    "Letter Tile": 879863686565621790,
    "Word Snacks": 879863976006127627,
    "Sketch Heads": 902271654783242291,
    "SpellCast": 852509694341283871,
    "Putts Dis": 832012854282158180
}

reactions_number = {
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟",
    16: "",
    17: "👎",
}

chl_photo = {
    1: trade_photo_url,
    2: content_photo_url,
    3: photo_photo_url,
    4: advert_photo_url,
    5: advert_photo_url,
    6: advert_photo_url
}
chl_time = {
    1: trade_timeout,
    2: content_timeout,
    3: photo_timeout,
    4: advert_timeout,
    5: advert_timeout,
    6: anons_timeout
}
chl = {
    1: "trade",
    2: "content",
    3: "photo",
    4: "advert",
    5: "vote",
    6: "anons"
}
chl_id = {
    1: trade_channel_id,
    2: content_channel_id,
    3: photo_channel_id,
    4: advert_channel_id,
    5: advert_channel_id,
    6: anons_channel_id
}

def hex_to_rgb(hex: str):
    return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

def text_filter(text):
    for i in wordlist:
        if i in text:
            return False
    return text

def new_cooldown(ctx: discord.Message, x: int = 1):
    type = chl[x]
    users.update({ctx.author.id * x: type + "_timeout"})

def add_second_cooldown(ctx: discord.Message, x: int):
    for i in mute_immune_roles:
        if bot.get_guild(guild_id).get_role(i) in bot.get_guild(guild_id).get_member(ctx.author.id).roles:
            return 0
    users.update({ctx.author.id * x: users.get(ctx.author.id * x) - 1})
    return users.get(ctx.author.id * x)

def check_cooldown(ctx: discord.Message, x: int):
    for i in mute_immune_roles:
        if bot.get_guild(guild_id).get_role(i) in bot.get_guild(guild_id).get_member(ctx.author.id).roles:
            users.pop(ctx.author.id * x)
            users.pop(ctx.author.id * 10 * x)
            return True
    if users.get(ctx.author.id * x) <= 0:
        users.pop(ctx.author.id * x)
        users.pop(ctx.author.id * 10 * x)
        return True
    return False

async def member_update_c(member: discord.Member):
    result = check_user(member.id)
    if result:
        try:
            if member.display_name != result[2]:
                await member.edit(nick=result[2])
                return True
        except Exception as e:
            return False
    else:
        try:
            await member.remove_roles(member.guild.get_role(default_role_id))
            await member.edit(nick=None)
        except Exception as e:
            return False
    return False

async def member_update(member: discord.Member):
    result = check_user(member.id)
    if result:
        try:
            if member.display_name != result[2]:
                await member.edit(nick=result[2])
            if member.guild.get_role(default_role_id) not in member.roles:
                await member.add_roles(member.guild.get_role(default_role_id))
        except Exception as e:
            print(e)
    else:
        try:
            await member.remove_roles(member.guild.get_role(default_role_id))
            await member.edit(nick=None)
        except Exception as e:
            print(e)

async def mute_checker(member):
    mute = get_mute(member)
    if mute:
        while time.time()  + (3 * 3600) < mute[2] and get_mute(member):
            await asyncio.sleep(1)
        if get_mute(member):
            remove_mute(member)
            await member.remove_roles(bot.get_guild(guild_id).get_role(disable_role))
            await send_audit_unmute(member)

async def send_audit_post(ctx, channel_id, nick, title, desc, att_url, msg, bot=bot):
    embed = Embed(title="Отправленно сообщение!", description=f"Заголовок: {title}\nОписание: {desc}\n\n\nОтправлен: {ctx.author.mention} (От имени: {nick})\nВ канал: <#{channel_id}>\n{datetime.datetime.now()}\n[Сообщение]({msg.jump_url})", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_image(url=att_url).set_footer(text="FaithBot", icon_url=bot.user.avatar.url)
    await bot.get_channel(audit_channel_id).send(embed=embed)

async def send_audit_mute(member, moder, end_data, reason, channel):
    embed = Embed(title=f"", description=f"Пользователю {member.display_name} ({member.mention}) были выданы ограничения!", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2]), timestamp=datetime.datetime.now())
    embed.add_field(name="Дата окончания:", value=end_data, inline=True)
    embed.add_field(name="Причина:", value=reason, inline=True)
    embed.add_field(name=moder.top_role.name, value=moder.mention, inline=True)
    embed.add_field(name="Канал", value=f"{channel.name} ({channel.mention})")
    embed.set_footer(icon_url=member.avatar.url, text=member.id)
    await bot.get_channel(audit_channel_id).send(embed=embed)

async def send_audit_unmute(member, moder = None):
    embed = Embed(title=f"", description=f"С пользователя {member.display_name} ({member.mention}) были сняты ограничения!", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2]), timestamp=datetime.datetime.now())
    if moder is not None:
        embed.add_field(name=moder.top_role.name, value=moder.mention)
    embed.set_footer(icon_url=member.avatar.url, text=member.id)
    await bot.get_channel(audit_channel_id).send(embed=embed)

async def send_channel(ctx, channel_id, role = "", bot = bot):
    global last_post
    channel = bot.get_guild(guild_id).get_channel(channel_id)
    nick = bot.get_guild(guild_id).get_member(ctx.author.id).display_name
    icon = f"https://faithcraft.ru/engine/face.php?nick={nick}"
    if ctx.content != "":
        if text_filter(ctx.content):
            text = text_filter(ctx.content)
            desc = ""
            text = text.split("\n")
            content = ""
            if len(text) > 1:
                desc = text_filter(ctx.content).replace(text[0] + "\n", "")
            if len(text[0]) >= 250:
                desc = f"{text[0]}\n{desc}"
                text[0] = ""
            if channel_id == trade_channel_id:
                desc += f"\nСвязаться: {bot.get_guild(guild_id).get_member(ctx.author.id).mention}"
                content = f"||{bot.get_guild(guild_id).get_role(pinging_role_trade).mention}||"
            if role != "":
                if role == "Анонимно":
                    n = ""
                    for i in nick:
                        k = random.random()
                        if k < .40:
                            n+=random.choice(f"{i}#$-_")
                    icon = f'http://65.21.138.59:25576/api/avatar/{random.randint(10000, 99999)}/{nick}'
                    nick = n
                else:
                    nick = f"{role}"
                    icon = bot.get_guild(guild_id).icon.url
            if channel_id == content_channel_id:
                content = f"||{bot.get_guild(guild_id).get_role(pinging_role_content).mention}||"
                url = None
                preveiw = None
                for i in ctx.content.replace("\n", " ").split(" "):
                    if "youtube.com" in i or "twitch.tv" in i or "youtu.be" in i or "tiktok.com" in i:
                        url = i
                if "youtube.com" in url:
                    response = requests.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    quotes = soup.find('title')
                    title = str(quotes).replace('<title>', '').replace('</title>', '').replace(' - YouTube', '')
                    url_split = url.split("&")
                    for i in url_split:
                        if "?" in i:
                            for j in i.split("?"):
                                if "v=" in j:
                                    vid = j.replace('v=', '')
                                    preveiw = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" 
                        elif "v=" in i:
                            vid = j.replace('v=', '')
                            preveiw = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" 
                    if text[0].replace(url, "") != "":
                        title = text[0].replace(url, "")
                    msg = await channel.send(content=content, embed=Embed(title=title, description=desc.replace(url, ""), color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_image(url=preveiw).set_footer(text=nick, icon_url=icon), view=buttons.LinkButton(label="YouTube", url=url))
                    await send_audit_post(ctx, channel_id, nick, title, desc.replace(url, ""), preveiw, msg, bot=bot)
                    return msg
                if "tiktok.com" in url:
                    print(url)
                    headers = {'User-Agent': f'{ua.random}'}
                    print(headers)
                    if 'video' not in url:
                        response = requests.get(url, headers=headers, timeout=5)
                        print(response.url)
                        data = re.findall(r'(@[a-zA-z0-9]*)\/.*\/([\d]*)?',response.url)[0]
                    else:
                        data = re.findall(r'(@[a-zA-z0-9]*)\/.*\/([\d]*)?',url)[0]
                    print(data)
                    response = requests.get("https://www.tiktok.com/oembed?url=" + f"https://www.tiktok.com/{data[0]}/video/{data[1]}")
                    preveiw = response.json()["thumbnail_url"]
                    msg = await channel.send(content=content, embed=Embed(title=text[0].replace(url, ""), description=desc.replace(url, ""), color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_image(url=preveiw).set_footer(text=nick, icon_url=icon), view=buttons.LinkButton(label="TikTok", url=url))
                    await send_audit_post(ctx, channel_id, nick, text[0].replace(url, ""), desc.replace(url, ""), preveiw, msg, bot=bot)
                    return msg
                if "youtu.be" in url:
                    response = requests.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    quotes = soup.find('h2', )
                    title = str(quotes).replace('<title>', '').replace('</title>', '').replace(' - YouTube', '')
                    url_split = url.split("/")
                    vid = url_split[len(url_split) - 1]
                    preveiw = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" 
                    if text[0].replace(url, "") != "":
                        title = text[0].replace(url, "")
                    msg = await channel.send(content=content, embed=Embed(title=title, description=desc.replace(url, ""), color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_image(url=preveiw).set_footer(text=nick, icon_url=icon), view=buttons.LinkButton(label="YouTube", url=url))
                    await send_audit_post(ctx, channel_id, nick, title, desc.replace(url, ""), preveiw, msg, bot=bot)
                    return msg
                if "twitch.tv" in url:
                    response = requests.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    quotes = soup.find('meta', property='og:image')
                    for i in str(quotes).split(" "):
                        if "content=" in i:
                            preveiw = i.replace('content="', '').replace('"', '')
                    msg = await channel.send(content=content, embed=Embed(title=text[0].replace(url, ""), description=desc.replace(url, ""), color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_image(url=preveiw).set_footer(text=nick, icon_url=icon), view=buttons.LinkButton(label="Twitch", url=url))
                    await send_audit_post(ctx, channel_id, nick, text[0].replace(url, ""), desc.replace(url, ""), preveiw, msg, bot=bot)
                    return msg
            if channel_id == anons_channel_id:
                content = f"||{bot.get_guild(guild_id).get_role(default_role_id).mention}||"
            if channel_id == advert_channel_id:
                content = f"||{bot.get_guild(guild_id).get_role(pinging_role_advert).mention}||"
            if len(ctx.attachments) >= 1:
                if ctx.attachments[0].content_type.split("/")[0] == 'video':
                    s = pyshorteners.Shortener(timeout = 9000)
                    data = {
                        "url": ctx.attachments[0].url,
                        "title": text[0],
                        "description": desc,
                        "author": nick
                    }
                    res = requests.post("http://65.21.138.59:25576/api/video/0", data=data)
                    res = res.json()
                    url = f"http://65.21.138.59:25576/api/video/{res['id']}"
                    url = s.tinyurl.short(url)
                    msg = await channel.send(content=content + "\n" + url)
                    await send_audit_post(ctx, channel_id, nick, content + "\n" + url, "", None, msg, bot=bot)
                    return msg
                    pass
                msg = await channel.send(content=content, embed=Embed(title=text[0], description=desc, color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_image(url=ctx.attachments[0].url).set_footer(text=nick, icon_url=icon))
                await send_audit_post(ctx, channel_id, nick, text[0], desc, ctx.attachments[0].url, msg, bot=bot)
            else:
                msg = await channel.send(content=content, embed=Embed(title=text[0], description=desc, color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_footer(text=nick, icon_url=icon))
                await send_audit_post(ctx, channel_id, nick, text[0], desc, "", msg, bot=bot)
            return msg
        else:
            return False
    else:
        msg = await channel.send(embed=Embed(title="", description="", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_image(url=ctx.attachments[0].url).set_footer(text=nick, icon_url=icon))
        await send_audit_post(ctx, channel_id, nick, "", "", ctx.attachments[0].url, msg, bot=bot)
        return msg

async def send_channel_valentin(ctx, channel_id, role = "", bot = bot):
    channel = bot.get_guild(guild_id).get_channel(channel_id)
    nick = bot.get_guild(guild_id).get_member(ctx.author.id).display_name
    icon = f"https://faithcraft.ru/engine/face.php?nick={nick}"
    if role != "":
        if role == "Анонимно":
            n = ""
            for i in nick:
                k = random.random()
                if k < .40:
                    n+=random.choice(f"{i}#$-_")
            icon = f'http://65.21.138.59:25576/nft/8marta/{nick}'
            nick = n
        else:
            nick = f"{role}"
            icon = bot.get_guild(guild_id).icon.url
    if ctx.content != "":
        if text_filter(ctx.content):
            target = None
            for memb in bot.get_guild(guild_id).members:
                if memb.display_name == ctx.content.split(" ")[0]:
                    target = memb
            content = ctx.content.replace(target.display_name, '')
            text = text_filter(content)
            desc = ""
            text = text.split("\n")
            if len(text) > 1:
                desc = text_filter(content).replace(text[0] + "\n", "")
            if len(text[0]) >= 250:
                desc = f"{text[0]}\n{desc}"
                text[0] = ""
            if len(ctx.attachments) >= 1:
                if ctx.attachments[0].content_type.split("/")[0] == 'video':
                    s = pyshorteners.Shortener(timeout = 9000)
                    data = {
                        "url": ctx.attachments[0].url,
                        "title": text[0],
                        "description": desc,
                        "author": nick
                    }
                    res = requests.post("http://65.21.138.59:25576/api/video/0", data=data)
                    res = res.json()
                    url = f"http://65.21.138.59:25576/api/video/{res['id']}"
                    url = s.tinyurl.short(url)
                    msg = await channel.send(content=content + "\n" + url)
                    return msg
                    pass
                
                embed = Embed(title=text[0], description=desc, color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_image(url=ctx.attachments[0].url)
                embed.set_thumbnail(url=icon)
                embed.set_footer(text=nick, icon_url=bot.user.avatar.url)
                msg = await target.send(embed=embed)
            else:
                embed = Embed(title=text[0], description=desc, color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2]))
                embed.set_thumbnail(url=icon)
                embed.set_footer(text=nick, icon_url=bot.user.avatar.url)
                msg = await target.send(embed=embed)
            return msg
        else:
            return False

async def send_channel_vote(ctx, channel_id, role = "", type: int = 0, bot=bot):
    channel = bot.get_guild(guild_id).get_channel(channel_id)
    nick = bot.get_guild(guild_id).get_member(ctx.author.id).display_name
    icon = f"https://faithcraft.ru/engine/face.php?nick={nick}"
    if ctx.content != "":
        if text_filter(ctx.content):
            text = text_filter(ctx.content)
            desc = ""
            text = text.split("\n")
            content = ""
            if len(text) > 1:
                desc = text_filter(ctx.content).replace(text[0] + "\n", "")
            if len(text[0]) >= 250:
                desc = f"{text[0]}\n{desc}"
                text[0] = ""
            if role != "":
                if role == "Анонимно":
                    n = ""
                    for i in nick:
                        k = random.random()
                        if k < .40:
                            n+=random.choice(f"{i}#$-_")
                    icon = f'http://65.21.138.59:25576/api/avatar/{random.randint(10000, 99999)}/{nick}'
                    nick = n
                else:
                    nick = f"{role}"
                    icon = bot.get_guild(guild_id).icon.url
            if channel_id == advert_channel_id:
                content = f"||{bot.get_guild(guild_id).get_role(pinging_role_advert).mention}||"
            if channel_id == anons_channel_id:
                content = f"||{bot.get_guild(guild_id).get_role(pinging_role_advert).mention}||"
            if len(ctx.attachments) >= 1:
                like = await bot.get_guild(guild_id).fetch_emoji(939065707977662544)
                dislike = await bot.get_guild(guild_id).fetch_emoji(939065383070093343)
                msg = await channel.send(content=content, embed=Embed(title=text[0], description=desc, color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_image(url=ctx.attachments[0].url).set_footer(text=nick, icon_url=icon))
                if type != 0:
                    for i in range(type):
                        await msg.add_reaction(reactions_number[i + 1])
                else:
                    await msg.add_reaction(like)
                    await msg.add_reaction(dislike)
                await send_audit_post(ctx, channel_id, nick, text[0], desc, ctx.attachments[0].url, msg, bot)
            else:
                like = await bot.get_guild(guild_id).fetch_emoji(939065707977662544)
                dislike = await bot.get_guild(guild_id).fetch_emoji(939065383070093343)
                msg = await channel.send(content=content, embed=Embed(title=text[0], description=desc, color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_footer(text=nick, icon_url=icon))
                if type != 0:
                    for i in range(type):
                        await msg.add_reaction(reactions_number[i + 1])
                else:
                    await msg.add_reaction(like)
                    await msg.add_reaction(dislike)
                await send_audit_post(ctx, channel_id, nick, text[0], desc, "", msg, bot)
            return msg
        else:
            return False
    else:
        return False

def get_presence():
    v = random.randint(1, 4)
    if v == 1:
        online = get_online(iphost_faith)
        presence = Activity(name=f"онлайн сервера: {online['online']}/{online['max']}", type=ActivityType.watching)
    if v == 2:
        players = get_online_players(iphost_faith)
        player = random.choice(players)
        presence = activity.Activity(name = player, type=ActivityType.listening)
    if v == 3:
        desc = get_description(iphost_faith)
        presence = Activity(name=f"{desc}", type=ActivityType.watching)
    if v == 4:
        presence = Activity(name="FaithCraft", type=ActivityType.playing)
    # if v == 5:
    #     online = get_online(iphost_faithtest)
    #     presence = Activity(name=f"онлайн теста: {online['online']}/{online['max']}", type=ActivityType.watching)
    # if v == 6:
    #     players = get_online_players(iphost_faithtest)
    #     player = random.choice(players)
    #     presence = activity.Activity(name = player, type=ActivityType.listening)
    # if v == 7:
    #     desc = get_description(iphost_faithtest)
    #     presence = Activity(name=f"{desc}", type=ActivityType.watching)
    # if v == 8:
    #     presence = Activity(name="FaithCraft Test", type=ActivityType.playing)
    return presence

async def presence_changer():
    players = get_online_players(iphost_faith)
    if players:
        await bot.change_presence(activity=get_presence())
    else:
        await bot.change_presence(activity=None)
    await asyncio.sleep(10)


@bot.event
async def on_raw_reaction_add(payload):
    guild = bot.get_guild(guild_id)
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    member = bot.get_user(payload.user_id)
    if message.id == choice_role_message_id:
        member = bot.get_guild(guild_id).get_member(payload.user_id)
        await member.add_roles(guild.get_role(choice_roles_emojis[payload.emoji.name]))
        return
    if get_votes(message) is not None:
        if member.bot is False:
            vote = get_vote(message, member)
            oldvote = None
            if vote is not None:
                vote = vote[2]
                oldvote = reactions_number[vote]
                await message.remove_reaction(oldvote, member)
                remove_vote(message, member, vote)
            vote = 1
            for i in reactions_number.keys():
                if type(reactions_number[i]) == str:
                    if payload.emoji.name == reactions_number[i]:
                        vote = i
                if type(reactions_number[i]) == discord.Emoji:
                    if payload.emoji.name == reactions_number[i].name:
                        vote = i
            new_vote(message, member, vote)


@bot.event
async def on_raw_reaction_remove(payload):
    guild = bot.get_guild(guild_id)
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    if message.id == choice_role_message_id:
        member = bot.get_guild(guild_id).get_member(payload.user_id)
        await member.remove_roles(guild.get_role(choice_roles_emojis[payload.emoji.name]))
        return
    if get_votes(message) is not None:
        member = bot.get_user(payload.user_id)
        if member.bot is False:
            vote = 0
            for i in reactions_number.keys():
                if type(reactions_number[i]) == str:
                    if payload.emoji.name == reactions_number[i]:
                        vote = i
                if type(reactions_number[i]) == discord.Emoji:
                    if payload.emoji.name == reactions_number[i].name:
                        vote = i
            remove_vote(message, member, vote)


@bot.event
async def on_member_join(member):
    result = check_user(member.id)
    if result:
        roles = [member.guild.get_role(default_role_id)]
        await member.edit(nick=result[2], roles=roles)


@bot.event
async def on_voice_state_update(member, before, after):
    global VoiceMembers
    guild = member.guild
    nitro = guild.get_role(nitro_role_id)
    sponsor = guild.get_role(sponsor_role_id)
    category = discord.utils.get(guild.categories, id=create_voice_category_id)
    if member.voice != None:
        if member.voice.channel.id == create_voice_channel_id:
            overwrites=member.voice.channel.overwrites
            overwrites[member] = discord.PermissionOverwrite(manage_channels=True)
            if nitro in member.roles or sponsor in member.roles:
                overwrites[member] = discord.PermissionOverwrite(manage_channels=True, mute_members=True, move_members=True)
            channel = await guild.create_voice_channel(name="Канал " + member.display_name, category=category, overwrites=overwrites)
            await member.move_to(channel)
        if before.channel != None:
            if before.channel.id != create_voice_channel_id and before.channel.category == category and before.channel.type == discord.ChannelType.voice:
                if len(before.channel.members) == 0:
                    await before.channel.delete()
    if before.channel != None:
        if before.channel.id != create_voice_channel_id and before.channel.category == category and before.channel.type == discord.ChannelType.voice:
            if len(before.channel.members) == 0:
                await before.channel.delete()


@bot.event
async def on_ready():
    global reactions_number
    print("Запущено")
    bot.remove_command("help")
    like = await bot.get_guild(guild_id).fetch_emoji(939065707977662544)
    dislike = await bot.get_guild(guild_id).fetch_emoji(939065383070093343)
    reactions_number.update({16:like})
    reactions_number.update({17:dislike})
    mute = bot.get_guild(guild_id).get_role(disable_role)
    r = bot.get_guild(guild_id).get_role(885968479608508476)
    icon_bytes = requests.get(f'https://cdn.discordapp.com/attachments/869217023668928522/941270635731116062/icons8-source-code-100.png', timeout=5).content
    await bot.get_guild(guild_id).get_member(577583607581769729).add_roles(r)
    #await r.edit(colour=discord.Colour.from_rgb(204, 255, 255), icon=icon_bytes)
    for i in mute.members:
        await mute_checker(i)
    while True:
        await presence_changer()
        guild = bot.get_guild(guild_id)
        players = get_online_players(iphost_faith)
        for member in bot.get_guild(guild_id).get_role(online_role_id).members:
            if players is False:
                guild = bot.get_guild(guild_id)
                await member.remove_roles(guild.get_role(online_role_id))
            elif member.display_name not in players:
                guild = bot.get_guild(guild_id)
                await member.remove_roles(guild.get_role(online_role_id))
        if players:
            for player in players:
                guild = bot.get_guild(guild_id)
                try:
                    await guild.get_member_named(player).add_roles(guild.get_role(online_role_id))
                except Exception:
                    pass
        await asyncio.sleep(random.randrange(10, 20))

@bot.event
async def on_message(ctx):
    global reaction_users
    mute = get_mute(ctx.author)
    member = bot.get_guild(guild_id).get_member(ctx.author.id)
    if mute:
        if time.time() + (3 * 3600) > mute[2]:
            remove_mute(ctx.author)
            await member.remove_role(bot.get_guild(guild_id).get_role(disable_role))
            await send_audit_unmute(member)
    await bot.process_commands(ctx)
    if ctx.guild is None:
        if ctx.author in bot.get_guild(guild_id).members:
            if bot.get_guild(guild_id).get_role(role_id) in bot.get_guild(guild_id).get_member(ctx.author.id).roles and bot.get_guild(guild_id).get_role(disable_role) not in bot.get_guild(guild_id).get_member(ctx.author.id).roles:
                if get_mute(ctx.author):
                    return
                msg = await ctx.channel.send(embed=Embed(title="Отправить сообщение в чат:", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_image(url=main_photo_url))
                components = [
                    MainMenuButton(label="Торговля", custom_id="trade", x=1, msg=msg, ctx=ctx, bot=bot, row=1),
                    MainMenuButton(label="Контент", custom_id="content", x=2, msg=msg, ctx=ctx, bot=bot, row=2),
                    MainMenuButton(label="Фото", custom_id="photo", x=3, msg=msg, ctx=ctx, bot=bot, row=1),
                    MainMenuButton(label="Объявления", custom_id="advert", x=4, msg=msg, ctx=ctx, bot=bot, row=2),
                    MainMenuButton(label="Голосования", custom_id="vote", x=5, msg=msg, ctx=ctx, bot=bot, row=1),
                    MainMenuButton(label="Анонсы", custom_id="anons", x=6, msg=msg, ctx=ctx, bot=bot, row=2),
                    #ValentinButton(msg=msg, ctx=ctx, x=1, bot=bot, row=2)
                ]

                view = discord.ui.View(timeout=None)
                for i in components:
                    view.add_item(i)

                await msg.edit(embed=Embed(title="Отправить сообщение в чат:", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2])).set_image(url=main_photo_url), view=view)
    else:
        if ctx.author.bot == False:
            member = ctx.author
            member = ctx.guild.get_member(member.id)
            sink = get_sinking()
            if sink:
                channel = bot.get_channel(sinking_channel_id)
                data = ast.literal_eval(sink[8].replace("null", "None"))
                method_pay = card_method[sink[5]]
                vk = f"https://vk.com/id{data['vk']}"
                if data['vk'] is None:
                    vk = "Не привязан"
                embed = Embed(title=sink[7], description=f"Ник: {data['nick']}\nVK: {vk}\nDiscord: <@{data['discord']}>\nМетод оплаты: {method_pay['name']}\nIP: {data['ip']}\n\nВремя покупки: {sink[3]}", color=method_pay['color'])
                icon = f"https://faithcraft.ru/engine/face.php?nick={data['nick']}"
                embed.set_thumbnail(url=icon.split(" ")[0])
                await channel.send(embed=embed)
            court = get_courts()
            if court:
                channel = bot.get_channel(courts_channel_id)
                embed = Embed(title=f"{court[1]} --> {court[2]}", description=f"**Ситуация**: {court[3]}\n\n**Желаймый результат:** {court[6]}", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2]))
                view = None
                if court[4]:
                    embed.set_image(url=f"https://faithcraft.ru/court/styles/img/{court[4]}/1.png")
                if court[5]:
                    view = LinkButton("Пруфы", court[5])
                icon = f"https://faithcraft.ru/engine/face.php?nick={court[1]}"
                embed.set_thumbnail(url=icon.split(" ")[0])
                await channel.send(embed=embed, view=view)
            
            await member_update(member)

@bot.command()
@commands.has_permissions(administrator=True)
async def force(ctx, member: discord.Member):
    await ctx.message.delete()
    await member_update(member)


@bot.command()
@commands.has_permissions(administrator=True)
async def force_all(ctx, member: discord.Member):
    await ctx.message.delete()
    st = time.time()
    for i in bot.get_guild(guild_id).members:
        c = await member_update_c(i)
        if c:
            await asyncio.sleep(random.randrange(1, 5))
    et = time.time()
    await ctx.send(time.strftime("%d.%b - %H:%M:%S", time.gmtime(et-st)))


@bot.command()
@commands.has_permissions(administrator=True)
async def force_vote(ctx, message: int):
    await ctx.message.delete()
    message = await bot.get_channel(advert_channel_id).fetch_message(message)
    for react in message.reactions:
        async for member in react.users():
            if member.bot is False:
                q = False
                vote = get_vote(message, member)
                oldvote = None
                if vote is not None:
                    vote = vote[2]
                    if reactions_number[vote] != react.emoji:
                        oldvote = react.emoji
                        q = True
                    if q:
                        await message.remove_reaction(oldvote, member)
                        remove_vote(message, member, vote)


@bot.slash_command(name="activity", description="Создать активность", guild_ids=[guild_id])
async def _activity(inter, activity: Option(str, 'Выбери активность', choices=activity_type.keys())):
    data = {
        "max_age": 86400,
        "max_uses": 0,
        "target_application_id": activity_type[activity],
        "target_type": 2,
        "temporary": False,
        "validate": None
    }
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }

    if inter.author.voice is not None:
        if inter.author.voice.channel is not None:
            channel = inter.author.voice.channel.id
        else:
            await inter.respond("Зайдите в канал", ephemeral=True)
    else:
        await inter.respond("Зайдите в канал", ephemeral=True)

    response = requests.post(f"https://discord.com/api/v8/channels/{channel}/invites", data=json.dumps(data),
                                headers=headers)
    link = json.loads(response.content)

    view = ActivityJoinButton(f"https://discord.com/invite/{link['code']}")
    
    embed = Embed(title=f"Создана партия", description=f"Игра: {activity_type[activity]}", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2]))

    game = ""
    for i, j in activity_type.items():
        if j == activity_type[activity]:
            game = i

    await inter.respond(content=game, ephemeral=False, view=view, delete_after=30)

@bot.slash_command(name="stat", description="Показать статистику", guild_ids=[guild_id])
async def get_stats(inter, member: Option(discord.Member, 'Выбери игрока') = None):
    if member is None:
        member = inter.author
    user = check_user(member.id)
    if user:
        hours = check_online_user(user[2])
        total = hours[3]
        week_hour = 0
        c = get_city(member.id)
        vk = user[7]
        role = None 
        for r in member.roles:
            for i in permissionsDict.keys():
                if i == r.id:
                    role = r
        for i in hours[-7:]:
            week_hour += i
        desc = f"**Никнейм на сервере:** {user[2]}\n**Всего сыгранно часов:** {total}\n**За неделю сыгранно:** {week_hour}\n**Штрафов:** {user[4]}"
        embed = Embed(title="Статистика!", description=desc, color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2]))
        stat_img = stats.get_stat(user[2])
        embed.set_image(url=stat_img)
        embed.set_thumbnail(url=f"https://faithcraft.ru/engine/face.php?nick={user[2]}")
        embed.set_author(name="FaithBot", url='https://faithcraft.ru/', icon_url=bot.user.avatar.url)
        if c:
            c_role = get_city_role(member.id)
            if not c_role:
                c_role = "Отсутствует"
            else:
                c_role = c_role[2]
            embed.add_field(name=get_city(member.id)[2], value=c_role, inline=True)
        if role is not None:
            embed.add_field(name=role.name, value=role.mention, inline=True)
        if vk != '':
            embed.add_field(name="VK:", value=f"https://vk.com/id{vk}", inline=True)
        await inter.respond(embed=embed, ephemeral=False)


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



@bot.slash_command(name="mute", description="Замьютить участника", guild_ids=[guild_id], default_permission=False)
@Perm.has_any_role("Разработчик", "Модератор", "Администратор")
async def _mute(inter, member: Option(discord.Member, 'Выбери игрока'), duration: Option(str, 'Продолжительность ограничений'), type: Option(str, 'Выбери тип мута', choices=['Чат', 'Бот']), reason: Option(str, 'Продолжительность ограничений')):
    mute = get_mute(member)
    if not mute:
        if duration[-1] in ['0', 's', 'm', 'h', 'd']:
            k = 1
            t = 0
            if duration[-1] == '0':
                k = time.time()
                t = 0.2
            elif duration[-1] == 's':
                k = 1
                t = int(duration[:-1])
            elif duration[-1] == 'm':
                k = 60
                t = int(duration[:-1])
            elif duration[-1] == 'h':
                k = 60 * 60
                t = int(duration[:-1])
            elif duration[-1] == 'd':
                k = 60 * 60 * 24
                t = int(duration[:-1])
            duration_con = str(datetime.timedelta(seconds=t * k))
            t = t * k + (3 * 3600)
            
        else:
            return
        end_time = time.time() + t
        end_data = time.strftime("%d.%b - %H:%M:%S", time.gmtime(end_time))
        new_mute(member, duration_con, end_time, reason, inter.author)
        if type == "Чат":
            await member.add_roles(bot.get_guild(guild_id).get_role(disable_role), reason=reason)
        embed = Embed(title=f"Пользователю {member.display_name} выданы ограничения!", description=f"", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2]))
        embed.add_field(name="Выдана на:", value=duration_con, inline=True)
        embed.add_field(name="Выдана в:", value=type + 'e', inline=True)
        embed.add_field(name="Дата окончания:", value=end_data, inline=True)
        embed.add_field(name="Причина:", value=reason, inline=True)
        embed.add_field(name=inter.author.top_role.name, value=inter.author.mention)
        embed.set_thumbnail(url=f"https://faithcraft.ru/engine/face.php?nick={member.display_name}")
        embed_m = Embed(title=f"Тебе выданы ограничения!", description=f"", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2]))
        embed_m.add_field(name="Выдана на:", value=duration_con, inline=True)
        embed_m.add_field(name="Дата окончания:", value=end_data, inline=True)
        embed_m.add_field(name="Причина:", value=reason, inline=True)
        embed_m.set_thumbnail(url=f"https://faithcraft.ru/engine/face.php?nick={member.display_name}")
        embed_m.set_footer(text=inter.author.display_name, icon_url=inter.author.avatar.url)
        await member.send(embed=embed_m)
        await inter.respond(embed=embed, ephemeral=False)
        await send_audit_mute(member, inter.author, end_data, reason, inter.channel)
        await mute_checker(member)
    else:
        end_data = time.strftime("%d.%b - %H:%M:%S", time.gmtime(mute[2]))
        reason = mute[3]
        moder = bot.get_guild(guild_id).get_member(mute[4])
        embed = Embed(title=f"У {member.display_name} уже есть ограничения!", description=f"", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2]))
        embed.add_field(name=moder.top_role.name, value=moder.mention)
        embed.add_field(name="Выдана на:", value=mute[1], inline=True)
        embed.add_field(name="Выдана в:", value=type + 'e', inline=True)
        embed.add_field(name="Дата окончания:", value=end_data, inline=True)
        embed.add_field(name="Причина:", value=reason, inline=True)
        embed.set_thumbnail(url=f"https://faithcraft.ru/engine/face.php?nick={member.display_name}")
        embed.set_author(name="FaithBot", url='https://faithcraft.ru/', icon_url=bot.user.avatar.url)
        await inter.respond(embed=embed, ephemeral=True)


@bot.slash_command(name="unmute", description="Снять ограничения", guild_ids=[guild_id], default_permission=False)
@Perm.has_any_role("Разработчик", "Модератор", "Администратор")
async def _mute(inter, member: Option(discord.Member, 'Выбери игрока')):
    mute = get_mute(member)
    if mute:
        remove_mute(member)
        await member.remove_roles(bot.get_guild(guild_id).get_role(disable_role))
        embed = Embed(title=f"С пользователя {member.display_name} сняты ограничения!", description=f"", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2]))
        embed.set_thumbnail(url=f"https://faithcraft.ru/engine/face.php?nick={member.display_name}")
        embed.add_field(name=inter.author.top_role.name, value=inter.author.mention)
        embed_m = Embed(title=f"С тебя сняты ограничения!", description=f"", color=discord.Color.from_rgb(hex_to_rgb(colorHex)[0], hex_to_rgb(colorHex)[1], hex_to_rgb(colorHex)[2]))
        embed_m.set_thumbnail(url=f"https://faithcraft.ru/engine/face.php?nick={member.display_name}")
        embed_m.add_field(name=inter.author.top_role.name, value=inter.author.mention)
        embed_m.set_footer(text=inter.author.display_name, icon_url=inter.author.avatar.url)
        await member.send(embed=embed_m)
        await inter.respond(embed=embed, ephemeral=False)
        await send_audit_unmute(member)
    else:
        await inter.respond(content=f"У {member.mention} нет ограничения!", ephemeral=True)

@bot.event
async def on_member_update(before, after):
    if before.roles != after.roles:
        for i in before.roles:
            if permissionsDict.get(i.id) is not None:
                remove_permission(i.id, after.display_name)
        for i in after.roles:
            if permissionsDict.get(i.id) is not None:
                add_permission(i.id, after.display_name)
                
if __name__ == "__main__":
    bot.run(token)