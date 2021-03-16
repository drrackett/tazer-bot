import os
import random
import re

import discord
from dotenv import load_dotenv

# load_dotenv(os.path.join(os.getcwd(), '.env'))
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

# store voice_channel as key and user created as key
DISCUSSION_ROOMS = {}


@client.event
async def on_ready():
    # discord.utils.find(lambda g: g.name == GUILD, client.guilds)
    guild = discord.utils.get(client.guilds, name=GUILD)
    
    # DO NOT DELETE THIS FOR NOW SO THAT WE KNOW THE BOT HAS SUCCESSFULLY CONNECTED
    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})\n'
    )

@client.event
async def on_member_join(member):
    # create a direct message channel and use that channel to .send() a direct message
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to my Discord server!'
    )

@client.event
async def on_message(message):

    # DO NOT DELETE THIS
    if message.author == client.user:
        return

    # List of commands here - will switch to discord commands later
    if re.search("^t! start ", message.content):
        room_name = message.content.split("t! start ", 1)[1].split(" ", 1)[0]
        members = message.mentions
        room = await create_discussion_room(message.author, room_name, members)
        DISCUSSION_ROOMS[room] = message.author
        await message.channel.send(f'{room_name} is created!')

    elif re.search("^t! add ", message.content):
        await add_members(message)

    elif re.search("^t! remove ", message.content):
        await remove_members(message)

    elif re.search("^t! end", message.content):
        await delete_discussion_room(message)

    elif re.search("^t! clear", message.content):
        await clear(message)

    '''elif message.content.startswith('$greet'):
        channel = message.channel
        await channel.send('Say hello!')

        verifymsg2 = await client.send_message(channel, "React with 👍 to gain access to Hard Chats.")
        await client.add_reaction(verifymsg2, "👍")

        def check(reaction, user):
            return user == message.author and str(reaction.emoji) == '👍'

        try:
            reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await channel.send('👎')
        else:
            await channel.send('👍')'''

    # elif re.search("^t! create-role ", message.content):
        # await create_role(message)

    '''elif re.search("^t! delete-role ", message.content):
        await delete_role(message)

    elif re.search("^t! create-voice-channel ", message.content):
        channel_name = message.content.split("t! create-voice-channel ", 1)[1]
        voice_channel = await create_private_voice_channel(channel_name)
        if voice_channel:
            await message.channel.send(f'{channel_name} voice channel is created!')
        else:
            await message.channel.send(f'{channel_name} voice channel cannot be created!')'''

# HOST -- refers to the user that initiated the command to create a discussion-room
# Notes:
#  1. Which channels are created by default? Voice and/or Text?
#  2. Might need two roles for each discussion-room, eg. HOST AND MEMEBERS
#  3. HOST can later add MEMBERS, and MEMBERS can request to join a discussion-room with the approval of the HOST possible
#  4. Later combine create role and channels into ONE command
#  5. Implement a time tracker to countdown on each discussion-room

# create role -- to be implemented: create and assigned the role to the host 
async def create_role(role_name):
    guild = discord.utils.get(client.guilds, name=GUILD)
    if discord.utils.get(guild.roles, name=role_name) is None:
        role = await guild.create_role(name=role_name)
    else:
        pass # name has to be unique
    return role

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

# create a private voice channel
# current: voice_channel not created if already exists, and role needs to be 
#          created before creating corresponding voice_channel
async def create_private_voice_channel(channel_name):
    guild = discord.utils.get(client.guilds, name=GUILD)
    if discord.utils.get(guild.voice_channels, name=channel_name):
        # raise exception
        pass
    else:
        # role = await create_role(channel_name)
        channel_admin = discord.utils.get(guild.roles, name=channel_name)
        if channel_admin is None:
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True), # necessary?
            channel_admin: discord.PermissionOverwrite(read_messages=True)
        }
        channel = await guild.create_voice_channel(name=channel_name, overwrites=overwrites)
    return channel

# create a private voice channel
# current: voice_channel not created if already exists, and role needs to be 
#          created before creating corresponding voice_channel
async def create_private_text_channel(channel_name):
    guild = discord.utils.get(client.guilds, name=GUILD)
    if discord.utils.get(guild.text_channels, name=channel_name):
        # raise exception
        pass
    else:
        # role = await create_role(channel_name)
        channel_admin = discord.utils.get(guild.roles, name=channel_name)
        if channel_admin is None:
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True), # necessary?
            channel_admin: discord.PermissionOverwrite(read_messages=True)
        }
        channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
    return channel

async def assign_role(member, role):
    await member.add_roles(role)

async def create_discussion_room(host, room_name, members):
    role = await create_role(room_name)

    await assign_role(host, role)
    for member in members:
        if not member == client.user:
            await member.add_roles(role)

    p_voice_channel = await create_private_voice_channel(room_name)
    p_text_channel = await create_private_text_channel(room_name)
    return p_text_channel

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

async def remove_members(message):
    guild = discord.utils.get(client.guilds, name=GUILD)

    text_channel = message.channel
    assert message.author in text_channel.members

    if not message.author == DISCUSSION_ROOMS[text_channel]:
        await message.channel.send(f'Only the host, {DISCUSSION_ROOMS[text_channel]} can remove people from this discussion room!')
        return

    role = discord.utils.get(guild.roles, name=text_channel.name)

    for member in message.mentions:
        if not member == client.user:
            await member.remove_roles(role)


async def delete_discussion_room(message):
    guild = discord.utils.get(client.guilds, name=GUILD)

    text_channel = message.channel
    assert message.author in text_channel.members

    if not message.author == DISCUSSION_ROOMS[text_channel]:
        await message.channel.send(f'Only the host, {DISCUSSION_ROOMS[text_channel]} can end this discussion room!')
        return

    voice_channel = discord.utils.get(guild.voice_channels, name=text_channel.name)
    role = discord.utils.get(guild.roles, name=text_channel.name)

    DISCUSSION_ROOMS.pop(text_channel)

    # delete text and voice channels created and role created
    await voice_channel.delete()
    await text_channel.delete()
    await role.delete()

async def clear(ctx, amount):
    await ctx.channel.purge(limit=amount)

client.run(TOKEN)