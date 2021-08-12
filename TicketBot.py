#############################################################
#                                                           #
#                      Imports                              #
#                                                           #
#############################################################

from configparser import ConfigParser
from datetime import datetime

import discord
import pytz
from discord import MessageType
from discord.ext import commands
from discord_components import *

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.all()

#############################################################
#                                                           #
#                      Auto Var                             #
#                                                           #
#############################################################

file = "TicketBot.ini"
config = ConfigParser()
config.read(file)

#############################################################
#                                                           #
#                      Var Config                           #
#                                                           #
#############################################################

# General
BotToken = str(config['Config']['BotToken'])
Prefix = str(config['Config']['Prefix'])
GuildID = int(config['Config']['GuildID'])
MainLogID = int(config['Config']['MainLogID'])
TicketCategory = int(config['Config']['TicketCategory'])
ClosedTicketCategory = int(config['Config']['ClosedTicketCategory'])
SupRoleID = int(config['Config']['SupRoleID'])
TicketArchiv = int(config['Config']['TicketArchiv'])
BanRoles = list(map(int, config['Config']['BanRoles'].split(",")))

#############################################################
#                                                           #
#                      Defines                              #
#                                                           #
#############################################################

bot = commands.Bot(command_prefix=Prefix, intents=intents)
bot.remove_command('help')


def is_not_pinned(mess):
    return not mess.pinned


def is_pin_feedback(mess):
    return mess.type == MessageType.pins_add


def frapper(lines, chars=4000):
    size = 0
    mes = []
    for line in lines:
        if len(line) + size > chars:
            yield mes
            mes = []
            size = 0
        mes.append(line)
        size += len(line)
    yield mes


#############################################################
#                                                           #
#                      Bot Events                           #
#                                                           #
#############################################################

@bot.event
async def on_ready():
    print("---------------------------------")
    print(f"{bot.user.name} is online. \r\n"
          f"Running on current version: 1.0.0")
    print("---------------------------------")
    DiscordComponents(bot)


@bot.event
async def on_button_click(buttonclick: Interaction):
    guild = bot.get_guild(GuildID)
    suprole = guild.get_role(SupRoleID)
    user = buttonclick.user
    member = guild.get_member(user.id)
    if buttonclick.custom_id == "ticketsysopen":
        config.read(file)
        if not str(user.id) in config['TicketBans']:
            category = bot.get_channel(TicketCategory)
            overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False),
                          user: discord.PermissionOverwrite(read_messages=True),
                          suprole: discord.PermissionOverwrite(read_messages=True, send_messages=False)}
            channel = await guild.create_text_channel(f"{user.name}`s ticket", overwrites=overwrites, category=category)

            dateTimeObj = datetime.now(pytz.utc)
            buttons = [[Button(style=ButtonStyle.red, label="Delete ticket", id="ticketsysdel", emoji="🗑️"),
                        Button(style=ButtonStyle.blue, label="Close ticket", id="ticketsysclose", emoji="🔐")]]
            embed = discord.Embed(title=f"Welcome to the ticket support!",
                                  description=f"**Notes:** \r\n"
                                              f"Please explain your request in a message. The support team will deal with your problem as soon as possible.",
                                  color=0x00ffff, timestamp=dateTimeObj)
            mes = await channel.send(
                f"Hey {buttonclick.author.mention}, your request will be processed by {suprole.mention}. Please read the following notes!",
                embed=embed, components=buttons)
            config.set("TicketBans", f"{user.id}", f"{channel.id}")
            config.set("TicketChannels", f"{channel.id}", f"{user.id}")
            with open(file, "w") as configfile:
                config.write(configfile)
                config.read(file)

            embed = discord.Embed(
                title='Ticket created',
                description=f'Your ticket was created successfully. ({channel.mention})',
                color=0x22a7f0)

            if user.dm_channel:
                await user.dm_channel.send(embed=embed)
            else:
                await user.create_dm()
                await user.dm_channel.send(embed=embed)

            await mes.pin()

            await channel.purge(limit=10, check=is_pin_feedback)

            await buttonclick.respond(type=6)
        else:
            config.read(file)
            ticketchannelid = int(config['TicketBans'][f'{user.id}'])
            if not ticketchannelid == 0:
                ticketchannel = bot.get_channel(ticketchannelid)
                embed = discord.Embed(title=f"Ticket error",
                                      description=f"Hey {user.mention}, you currently already have a ticket! {ticketchannel.mention}",
                                      color=0x00ffff)
                if user.dm_channel:
                    await user.dm_channel.send(embed=embed)
                else:
                    await user.create_dm()
                    await user.dm_channel.send(embed=embed)
            else:
                embed = discord.Embed(title=f"Ticket error",
                                      description=f"Hey {user.mention}, you are Ticket-Banned and cannot open any more tickets.",
                                      color=0x00ffff)
                if user.dm_channel:
                    await user.dm_channel.send(embed=embed)
                else:
                    await user.create_dm()
                    await user.dm_channel.send(embed=embed)
    elif buttonclick.custom_id == "ticketsysdel":
        if member.permissions_in(buttonclick.channel).manage_channels:
            if str(buttonclick.channel.id) in config['TicketChannels']:
                config.read(file)
                ticketowner = int(config['TicketChannels'][f'{buttonclick.channel.id}'])
                config.remove_option('TicketChannels', f'{buttonclick.channel.id}')
                config.remove_option('TicketBans', f'{ticketowner}')
                with open(file, "w") as configfile:
                    config.write(configfile)
                    config.read(file)
            x = ""
            async for msg in buttonclick.channel.history(limit=100000, oldest_first=True):
                if not msg.author.bot:
                    x = f"{x}```{msg.author} [{datetime.strftime(msg.created_at, '%d.%m. %H:%M')}]:``` {msg.content} \r\n"
            chan = bot.get_channel(TicketArchiv)
            times = 1
            for mess in frapper(x):
                embed = discord.Embed(title=f"{buttonclick.channel.name} | Page: [{times}]",
                                      description="".join(mess),
                                      color=0x00ffff)
                await chan.send(embed=embed)
                times += 1
            await chan.send("``` ```")
            await buttonclick.channel.delete()
            await buttonclick.respond(type=6)
    elif buttonclick.custom_id == "ticketsysclose":
        if suprole in member.roles:
            if str(buttonclick.channel.id) in config['TicketChannels']:
                config.read(file)
                ticketowner = int(config['TicketChannels'][f'{buttonclick.channel.id}'])
                config.remove_option('TicketChannels', f'{buttonclick.channel.id}')
                config.remove_option('TicketBans', f'{ticketowner}')
                with open(file, "w") as configfile:
                    config.write(configfile)
                    config.read(file)
                category = bot.get_channel(ClosedTicketCategory)
                await buttonclick.channel.edit(category=category, sync_permissions=True)

            buttons = [[Button(style=ButtonStyle.red, label="Delete ticket", id="ticketsysdel", emoji="🗑️")]]

            await buttonclick.message.edit(components=buttons)
            await buttonclick.respond(type=6)


#############################################################
#                                                           #
#                      Bot Commands                         #
#                                                           #
#############################################################


@bot.command()
@commands.has_any_role(*BanRoles)
async def ticketban(ctx, user: discord.Member):
    userid = str(user.id)
    guild = bot.get_guild(GuildID)
    suprole = guild.get_role(SupRoleID)
    if suprole in ctx.author.roles:
        config.set("TicketBans", f"{userid}", f"0")
        with open(file, "w") as configfile:
            config.write(configfile)
            config.read(file)
        await ctx.message.delete()


@bot.command()
@commands.has_any_role(*BanRoles)
async def ticketunban(ctx, user: discord.Member):
    userid = str(user.id)
    guild = bot.get_guild(GuildID)
    suprole = guild.get_role(SupRoleID)
    if suprole in ctx.author.roles:
        if userid in config['TicketBans']:
            if int(config['TicketBans'][f'{userid}']) == 0:
                config.remove_option('TicketBans', f'{userid}')
                with open(file, "w") as configfile:
                    config.write(configfile)
                    config.read(file)
                await ctx.message.delete()


@bot.command()
@commands.has_guild_permissions(administrator=True)
async def ticket(ctx):
    buttons = [Button(style=ButtonStyle.gray, label="Create ticket", id="ticketsysopen", emoji="📩")]
    embed = discord.Embed(title="Ticket system", description="To create a ticket just click the button below.",
                          color=0x00ffff)
    await ctx.send(embed=embed, components=buttons)
    await ctx.message.delete()


bot.run(BotToken)
