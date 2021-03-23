import os
import random
from typing import Optional
import emojis
import asyncio
import typing

import discord
from dotenv import load_dotenv

from discord.ext import commands

RGB_MIN = 0
RGB_MAX = 255

# load_dotenv(os.path.join(os.getcwd(), '.env'))
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


GUILDS_CONNECTED = {}
DEFAULT_CATEGORY_NAME = 'Discussion Rooms'

VOICE_CHANNEL_STR = 'voice_channel'
ADMINS_STR = 'admins'
ROLE_STR = 'role'
TXT_CHANNEL_STR = 'text_channel'
CATEGORY_STR = 'catagory'
ROOMS_STR = 'rooms'


intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='t! ', intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    guilds = bot.guilds
    for guild in guilds:
        category = await guild.create_category_channel(DEFAULT_CATEGORY_NAME)
        GUILDS_CONNECTED[guild.id] = {}
        GUILDS_CONNECTED[guild.id][CATEGORY_STR] = category
        GUILDS_CONNECTED[guild.id][ROOMS_STR] = {}


# create role
async def create_role(guild, role_name):
    if discord.utils.get(guild.roles, name=role_name) is None:
        role_color = discord.Colour.from_rgb(random.randint(RGB_MIN, RGB_MAX), 
        random.randint(RGB_MIN, RGB_MAX), random.randint(RGB_MIN, RGB_MAX))
        role = await guild.create_role(name=role_name, color=role_color)
    else:
        print(f'Role {role_name} existed!') # for debugging purposes
        raise discord.DiscordException
    return role


# create a private voice channel
# current: voice_channel not created if already exists, and role needs to be 
#          created before creating corresponding voice_channel
async def create_private_text_channel(guild, channel_name, role_allowed):
    existing_channels = discord.utils.get(guild.text_channels, name=channel_name)
    if not existing_channels:
        assert role_allowed is not None
        category = GUILDS_CONNECTED[guild.id][CATEGORY_STR]
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True),
            role_allowed: discord.PermissionOverwrite(view_channel=True)
        }
        txt_channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
    else:
        print(f"Text channel {channel_name} existed!")
        raise discord.DiscordException
    return txt_channel


# create a private voice channel
# current: voice_channel not created if already exists, and role needs to be 
#          created before creating corresponding voice_channel
async def create_private_voice_channel(guild, channel_name, role_allowed):
    existing_channels = discord.utils.get(guild.voice_channels, name=channel_name)
    if not existing_channels:
        assert role_allowed is not None
        category = GUILDS_CONNECTED[guild.id][CATEGORY_STR]
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            role_allowed: discord.PermissionOverwrite(read_messages=True)
        }
        voice_channel = await category.create_voice_channel(name=channel_name, overwrites=overwrites)
    else:
        print(f"Voice channel {channel_name} existed!")
        raise discord.DiscordException
    return voice_channel


async def destruct_discussion_room(role, txt_channel, voice_channel):
    if role is not None:
        await role.delete()
    if txt_channel is not None:
        await txt_channel.delete()
    if voice_channel is not None:
        await voice_channel.delete()


@bot.command(name='start', help='Creates a discussion room')
async def create_discussion_room(ctx, room_name):
    try:
        await ctx.message.delete()

        role = None
        p_text_channel = None
        p_voice_channel = None

        guild = ctx.guild
        
        # create a role and both private text and voice channels
        role = await create_role(guild, room_name)
        p_text_channel = await create_private_text_channel(guild, room_name, role)
        p_voice_channel = await create_private_voice_channel(guild, room_name, role)

        # assign the specific role so that members are allowed to join both channels created
        await ctx.author.add_roles(role)

        members_to_be_added = ctx.message.mentions
        for member in members_to_be_added:
            await member.add_roles(role)
        
        GUILDS_CONNECTED[guild.id][ROOMS_STR][p_text_channel] = {
            ADMINS_STR: [ctx.author],
            ROLE_STR: role,
            TXT_CHANNEL_STR: p_text_channel,
            VOICE_CHANNEL_STR: p_voice_channel
        }

        # send a direct message to the host that the discussion room has been created
        await ctx.author.send(f'{room_name} is created!')
    except discord.DiscordException:
        p_text_channel = await destruct_discussion_room(role, p_text_channel, p_voice_channel)


async def destruct_by_room(room): # room is a dictionary
    await room[ROLE_STR].delete()
    await room[TXT_CHANNEL_STR].delete()
    await room[VOICE_CHANNEL_STR].delete()


@bot.command(name='remove', help='Removes users from the discussion room')
async def remove_members(ctx):
    guild = ctx.guild

    text_channel = ctx.channel
    all_rooms_created = GUILDS_CONNECTED[guild.id][ROOMS_STR]

    assert ctx.message.author in text_channel.members

    room_admins = all_rooms_created[text_channel][ADMINS_STR]

    assert ctx.author in room_admins, f'Only admins can remove people from this discussion room!'

    role = all_rooms_created[text_channel][ROLE_STR]

    for member in ctx.message.mentions:
        await member.remove_roles(role)


@bot.command(name='invite', help='Invites users to the discussion room')
async def invite_members_to_priv_channel(ctx):
    guild = ctx.guild
    txt_channel = ctx.channel
    all_rooms_created = GUILDS_CONNECTED[guild.id][ROOMS_STR]
    role_to_be_assigned = all_rooms_created[txt_channel][ROLE_STR]

    embedVar = discord.Embed(title=f"Invite people", 
    description=f"Here's a list of members not in {ctx.channel.name}", color=role_to_be_assigned.color)
    all_members = guild.members
    all_emojis = list(emojis.db.get_emoji_aliases().values())

    emojis_used = {}
    for member in all_members:
        if member not in txt_channel.members:
            emoji_unicode = random.choice(all_emojis)
            embedVar.add_field(name=f"{emoji_unicode}", value=f"{member.mention}", inline=True)
            emojis_used[emoji_unicode] = member
    bot_msg = await ctx.channel.send(embed=embedVar)

    for emoji in emojis_used.keys():
        await bot_msg.add_reaction(emoji)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in list(emojis_used.keys())

    try:
        while True:
            reaction, user = await bot.wait_for('reaction_add', timeout=7.0, check=check)
            member_to_be_added = emojis_used[str(reaction.emoji)]
            await member_to_be_added.add_roles(role_to_be_assigned)
            await ctx.channel.send(f'{member_to_be_added.name} has been added!')
    except asyncio.TimeoutError:
        await bot_msg.clear_reactions()


@bot.command(name='clear', help='Deletes messages')
async def clear_messages(ctx, limit=None):
    number_of_lines = int(limit) if limit else 1
    await ctx.channel.purge(limit=number_of_lines + 1)


@bot.command(name='poll', help='Create a poll')
async def create_poll(ctx, question, *options):
    guild = ctx.guild
    channel = ctx.channel

    embedVar = discord.Embed(title=f"{question.capitalize()}")
    all_emojis = list(emojis.db.get_emoji_aliases().values())

    emojis_used = []
    for option in options:
        emoji_unicode = random.choice(all_emojis)
        embedVar.add_field(name=f"{emoji_unicode}", value=f"{option.capitalize()}", inline=False)
        emojis_used.append(emoji_unicode)

    bot_msg = await channel.send(embed=embedVar)
    for emoji in emojis_used:
        await bot_msg.add_reaction(emoji)


@bot.command(name='assign', help='Assign @members admin of the discussion room')
async def assign_admin(ctx):
    await ctx.message.delete()

    guild = ctx.guild
    all_rooms_created = GUILDS_CONNECTED[guild.id][ROOMS_STR]
    room = ctx.channel

    # To make sure command can only be invoked in discussion_rooms created by the bot
    if room not in all_rooms_created:
        return
    
    room_properties = GUILDS_CONNECTED[guild.id][ROOMS_STR][room]
    room_admins = room_properties[ADMINS_STR]
    role_to_be_assigned = room_properties[ROLE_STR]

    if ctx.author in room_admins:
        for member_to_be_admin in ctx.message.mentions:
            # To avoid duplicates in room_admins list
            # assumed only members in the discussion_room can be mentioned
            if member_to_be_admin not in room_admins:
                room_admins.append(member_to_be_admin)
                await room.send(f'{member_to_be_admin.mention} is now an admin of {room.name}!')
    else:
        await room.send('Only admins of this discussion room can assign admins!')


''' ************************ TBD WHETHER TO ADD *******************************
@bot.command(name='admins', help='Assign @users admin of the discussion room')
async def admins_list(ctx):
    guild = ctx.guild
    room = ctx.channel
    room_properties = GUILDS_CONNECTED[guild.id][ROOMS_STR][room]

    room_admins = room_properties[ADMINS_STR]

    for admin in room_admins:
        await room.send(admin.mention)
'''


@bot.command(name='end', help='Deletes the discussion room')
async def delete_discussion_room(ctx):
    await ctx.message.delete()

    guild = ctx.guild
    text_channel = ctx.channel
    all_rooms_created = GUILDS_CONNECTED[guild.id][ROOMS_STR]

    assert ctx.message.author in text_channel.members

    # to make sure t! end is initiated in a room created by the bot
    assert text_channel in all_rooms_created

    room_admins = all_rooms_created[text_channel][ADMINS_STR]

    # assertations
    assert ctx.author in room_admins, f'Only admins can end this discussion room!'

    voice_channel = all_rooms_created[text_channel][VOICE_CHANNEL_STR]
    role = all_rooms_created[text_channel][ROLE_STR]

    all_rooms_created.pop(text_channel)

    # delete text and voice channels created and role created
    await voice_channel.delete()
    await text_channel.delete()
    await role.delete()


@bot.command(name='disconnect', help='Temporary command to kill the bot, equivalent to kicking the bot out of your server')
async def disconnect(ctx):
    await ctx.message.delete()
    guild_id = ctx.guild.id
    category_created = GUILDS_CONNECTED[guild_id][CATEGORY_STR]
    rooms_created = GUILDS_CONNECTED[guild_id][ROOMS_STR]
    for room, room_props in rooms_created.items():
        await destruct_by_room(room_props)
    await category_created.delete()
    GUILDS_CONNECTED.pop(guild_id)


# TEMPORARY COMMAND FOR THE DEVELOPERS ONLY PLEASE
@bot.command(name='logout', help='Temporary command to kill all bots')
async def disconnect_all(ctx):
    await ctx.message.delete()
    for guild, guild_props in GUILDS_CONNECTED.items():
        category_created = guild_props[CATEGORY_STR]
        rooms_created = guild_props[ROOMS_STR]
        for room, room_props in rooms_created.items():
            await destruct_by_room(room_props)
        await category_created.delete()
    await bot.logout()
    

# HOST -- refers to the user that initiated the command to create a discussion-room
# Notes:
#  1. Which channels are created by default? Voice and/or Text?
#  2. Might need two roles for each discussion-room, eg. HOST AND MEMEBERS
#  3. HOST can later add MEMBERS, and MEMBERS can request to join a discussion-room with the approval of the HOST possible
#  4. Later combine create role and channels into ONE command
#  5. Implement a time tracker to countdown on each discussion-room

''' ****************************** DEPRECATED *********************************

# delete role -- to be implemented (when channels can be created): only the host can delete its own role
async def delete_role(message):
    guild = discord.utils.get(client.guilds, name=GUILD)
    role_name = message.content.split("t! delete-role ", 1)[1]
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        await message.channel.send(f'{role} does not exist!')
    else:
        try:
            await role.delete()
            await message.channel.send(f'{role_name} deleted!')
        except discord.Forbidden:
            await message.channel.send(f'Forbidden to delete {role_name}!')


async def assign_role(member, role):
    await member.add_roles(role)


async def add_members(message):
    guild = discord.utils.get(client.guilds, name=GUILD)

    channel = message.channel
    assert message.author in channel.members

    # get role to be assigned to each member
    # Notes: 
    # 1. What if someone changes the channel's name? resolve: restrict user from changing the channel's name
    # 2. What if user add more roles to the private channel? resolve: restrict user from making changes to the channel
    # restriction: user will not change the channel's name, and the channel.name == role.name
    role = discord.utils.get(guild.roles, name=channel.name)

    # members <- get all members to add
    all_names = message.content.split("t! add ", 1)[1]
    all_names = map(lambda name: name.strip(), all_names.split(","))

    # assign the same role to each member in members
    # Notes: 
    # 1. member not found
    # 2. message to be printed? message to alert who's added?
    for name in all_names:
        member = discord.utils.get(guild.members, name=name)
        await assign_role(member, role)

''' 

bot.run(TOKEN)