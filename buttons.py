import asyncio
from cProfile import label

import discord
from discord import *
from discord import Embed
from discord.ext import commands

from bot import *
from sqldb import *
from config import *


async def on_vote_button(ctx, msg, x, bot):
    member = bot.get_guild(guild_id).get_member(ctx.author.id)
    rows = []
    for i in reactions_number.keys():
        if i < 16:
            rows.append(VoteChoiceTypeButton(style=discord.enums.ButtonStyle.green, label=f"{i}", custom_id=f"accept_{i}", row=(i%2) + 2, x=x, msg=msg, ctx=ctx, bot=bot))
    components = [
        VoteChoiceTypeButton(style=discord.enums.ButtonStyle.green, label="Лайк/Дизлайк", custom_id="accept_0", row=1, x=x, msg=msg, ctx=ctx, bot=bot),
        VoteChoiceTypeButton(style=discord.enums.ButtonStyle.red, label="Отменить", custom_id="cancel", row=4, x=x, msg=msg, ctx=ctx, bot=bot)
    ]

    view = discord.ui.View(timeout=None)
    view.add_item(components[0])
    for i in rows:
        view.add_item(i)
    view.add_item(components[1])

    await msg.edit(embed=Embed(title="Убедитесь, что сообщение соответствует требованиям для отправки. Если это не так, вам будет выдано наказание.", description="Данная функция существует для отправки голосования с одним вариантом ответ!\nУказывать за что какой голос обезательно!\nПеред отправкой выберете режим отправки!", color=discord.Color.from_rgb(238, 0, 255)).set_image(url=main_photo_url), view=view)
    

async def on_click_button(ctx, msg, x, bot):
    member = bot.get_guild(guild_id).get_member(ctx.author.id)
    components = [
        SendChoiceButton(style=discord.enums.ButtonStyle.green, label="Отправить", custom_id="accept", row=1, x=x, msg=msg, ctx=ctx, bot=bot),
        SendChoiceButton(style=discord.enums.ButtonStyle.red, label="Отменить", custom_id="cancel", row=1, x=x, msg=msg, ctx=ctx, bot=bot)
    ]
    desc = ""
    rows = [SendChoiceButton(style=discord.enums.ButtonStyle.green, label="Анонимно", custom_id=f"accept_anon", row=2,x=x, msg=msg, ctx=ctx, bot=bot)]
    for i in message_roles.keys():
        role = bot.get_guild(guild_id).get_role(i)
        if role in member.roles:
            desc += f'\nТак у вас есть роль "{role.name}", Вы можете отправить от имени {message_roles[i]}!'
            rows.append(SendChoiceButton(style=discord.enums.ButtonStyle.green, label=message_roles[i], custom_id=f"accept_{i}", row=2,x=x, msg=msg, ctx=ctx, bot=bot))
    
    view = discord.ui.View(timeout=None)
    for i in components + rows:
        view.add_item(i)
    
    await msg.edit(embed=Embed(title="Убедитесь, что сообщение соответствует требованиям для отправки. Если это не так, вам будет выдано наказание.", description=desc, color=discord.Color.from_rgb(238, 0, 255)).set_image(url=chl_photo[x]), view=view)

class MainMenuButton(discord.ui.Button):
    def __init__(self, label: str, custom_id: str, x: int, msg, ctx, bot, row: int=1):
        super().__init__(
            label=label,
            style=discord.enums.ButtonStyle.green,
            custom_id=custom_id,
            row = row
        )
        self.bot = bot
        self.x = x
        self.msg = msg
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        res = interaction.response
        res.is_done()
        if self.x == 5:
            await on_vote_button(self.ctx, self.msg, self.x, self.bot)
        else:
            await on_click_button(self.ctx, self.msg, self.x, self.bot)

class RemoveMessageButton(discord.ui.Button):
    def __init__(self, msg, t, bot):
        super().__init__(
            label="Удалить",
            style=discord.enums.ButtonStyle.red,
            custom_id="delete",
        )
        self.bot = bot
        self.msg = msg
        self.t = t

    async def callback(self, interaction: discord.Interaction):
        res = interaction.response
        res.is_done()
        await self.t.delete()
        await self.msg.edit(content="Удаленно")

class SendChoiceButton(discord.ui.Button):
    def __init__(self, style: discord.enums.ButtonStyle, label: str, custom_id: str, row: int, x: int, msg, ctx, bot, type='def', vote_type = 1):
        super().__init__(
            label=label,
            style=style,
            custom_id=custom_id,
            row = row
        )
        self.callback_type = type
        self.bot = bot
        self.x = x
        self.msg = msg
        self.ctx = ctx
        self.vote_type = vote_type

    async def callback(self, interaction: discord.Interaction):
        res = interaction.response
        res.is_done()
        if "accept" in self.custom_id:
            r = ""
            if self.label != "Отправить":
                r = self.label
            if self.callback_type == "def":
                t = await send_channel(self.ctx, chl_id[self.x], r, bot=self.bot)
            else:
                t = await send_channel_vote(self.ctx, chl_id[self.x], r, self.vote_type, self.bot)
                new_votes(t, self.vote_type)
            if t is not False:
                view = discord.ui.View(timeout=None)
                view.add_item(RemoveMessageButton(msg=self.msg, t=t, bot=self.bot))
                await self.msg.edit(content="Отправленно", embed=None, view=view)
                while users.get(self.ctx.author.id * self.x):
                    second = add_second_cooldown(self.ctx, self.x)
                    await self.msg.edit(embed=Embed(title=f"Осталось ждать {second} сек"), components=[])
                    if check_cooldown(self.ctx, self.x):
                        break
                    await asyncio.sleep(1)

class LinkButton(discord.ui.View):
    def __init__(self, label, url) -> None:
        super().__init__()
        self.add_item(discord.ui.Button(label=label, url=url))

class ActivityJoinButton(discord.ui.View):
    def __init__(self, url) -> None:
        super().__init__()
        self.add_item(discord.ui.Button(label="Присоединился", url=url))

class VoteChoiceTypeButton(discord.ui.Button):
    def __init__(self, style: discord.enums.ButtonStyle, label: str, custom_id: str, row: int, x: int, msg, ctx, bot):
        super().__init__(
            label=label,
            style=style,
            custom_id=custom_id,
            row = row
        )
        self.bot = bot
        self.x = x
        self.msg = msg
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        res = interaction.response
        res.is_done()
        if "accept" in self.custom_id:
            type = int(str(self.custom_id).replace("accept_", ""))
            member = self.bot.get_guild(guild_id).get_member(self.ctx.author.id)
            components = [
                SendChoiceButton(style=discord.enums.ButtonStyle.green, label="Отправить", custom_id="accept", row=1, x=self.x, msg=self.msg, ctx=self.ctx, bot=self.bot, type='vote', vote_type=type),
                SendChoiceButton(style=discord.enums.ButtonStyle.red, label="Отменить", custom_id="cancel", row=1, x=self.x, msg=self.msg, ctx=self.ctx, bot=self.bot, type='vote', vote_type=type)
            ]
            desc = ""
            rows = [SendChoiceButton(style=discord.enums.ButtonStyle.green, label="Анонимно", custom_id=f"accept_anon", row=2,x=self.x, msg=self.msg, ctx=self.ctx, bot=self.bot, type='vote', vote_type=type)]
            for i in message_roles.keys():
                role = self.bot.get_guild(guild_id).get_role(i)
                if role in member.roles:
                    desc += f'\nТак у вас есть роль "{role.name}", Вы можете отправить от имени {message_roles[i]}!'
                    rows.append(SendChoiceButton(style=discord.enums.ButtonStyle.green, label=message_roles[i], custom_id=f"accept_{i}", row=2,x=self.x, msg=self.msg, ctx=self.ctx, bot=self.bot, type='vote', vote_type=type))
                    view = discord.ui.View(timeout=None)
                    for i in components + rows:
                        view.add_item(i)
                    
                    await self.msg.edit(embed=Embed(title="Убедитесь, что сообщение соответствует требованиям для отправки. Если это не так, вам будет выдано наказание.", description=desc, color=discord.Color.from_rgb(238, 0, 255)).set_image(url=chl_photo[self.x]), view=view)

class ValentinButton(discord.ui.Button):
    def __init__(self, msg, ctx, x, bot, row: int=1) -> None:
        super().__init__(
            label="Валентинка",
            style=discord.enums.ButtonStyle.blurple,
            custom_id = "valentin",
            row = row
        )
        self.msg = msg
        self.ctx = ctx
        self.bot = bot
        self.x = x
    async def callback(self, interaction: discord.Interaction):
        res = interaction.response
        res.is_done()
        member = self.bot.get_guild(guild_id).get_member(self.ctx.author.id)
        components = [
            ValentinButtonAccept(style=discord.enums.ButtonStyle.green, label="Отправить", custom_id="accept", row=1, msg=self.msg, ctx=self.ctx, bot=self.bot, x=1),
            ValentinButtonAccept(style=discord.enums.ButtonStyle.red, label="Отменить", custom_id="cancel", row=1, msg=self.msg, ctx=self.ctx, bot=self.bot, x=1)
        ]
        desc = "Для отправки валентинки вам в начале своего сообщение нужно написать ник получателя!\nПросьба не оскорблять друг друга"
        rows = [ValentinButtonAccept(style=discord.enums.ButtonStyle.green, label="Анонимно", custom_id=f"accept_anon", row=2, msg=self.msg, ctx=self.ctx, bot=self.bot, x=1)]
        for i in message_roles.keys():
            role = self.bot.get_guild(guild_id).get_role(i)
            if role in member.roles:
                desc += f'\nТак у вас есть роль "{role.name}", Вы можете отправить от имени {message_roles[i]}!'
                rows.append(ValentinButtonAccept(style=discord.enums.ButtonStyle.green, label=message_roles[i], custom_id=f"accept_{i}", row=2, msg=self.msg, ctx=self.ctx, bot=self.bot, x=1))
        
        view = discord.ui.View(timeout=None)
        for i in components + rows:
            view.add_item(i)
        
        await self.msg.edit(embed=Embed(title="Убедитесь, что сообщение соответствует требованиям для отправки. Если это не так, вам будет выдано наказание.", description=desc, color=discord.Color.from_rgb(238, 0, 255)).set_image(url=chl_photo[self.x]), view=view)


class ValentinButtonAccept(discord.ui.Button):
    def __init__(self, label, custom_id, style, msg, x, ctx, bot, row: int=1) -> None:
        super().__init__(
            label=label,
            style=style,
            custom_id = custom_id,
            row = row
        )
        self.msg = msg
        self.ctx = ctx
        self.bot = bot
    async def callback(self, interaction: discord.Interaction):
        res = interaction.response
        res.is_done()
        if "accept" in self.custom_id:
            r = ""  
            if self.label != "Отправить":
                r = self.label  
            t = await send_channel_valentin(self.ctx, advert_channel_id, r, self.bot)
            if t is not False:
                view = discord.ui.View(timeout=None)
                view.add_item(RemoveMessageButton(msg=self.msg, t=t, bot=self.bot))
                await self.msg.edit(content="Отправленно", embed=None, view=view)
    
