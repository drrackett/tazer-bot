import os
import random
import re

import discord
from dotenv import load_dotenv

# load_dotenv(os.path.join(os.getcwd(), '.env'))
load_dotenv()
client = discord.Client()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

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
    if re.search("^t! create-role ", message.content):
        await create_role(message)

    elif re.search("^t! delete-role ", message.content):
        await delete_role(message)

    elif re.search("^t! create-voice-channel ", message.content):
        channel_name = message.content.split("t! create-voice-channel ", 1)[1]
        voice_channel = await create_private_voice_channel(channel_name)
        if voice_channel:
            await message.channel.send(f'{channel_name} voice channel is created!')
        else:
            await message.channel.send(f'{channel_name} voice channel cannot be created!')

# HOST -- refers to the user that initiated the command to create a discussion-room
# Notes:
#  1. Which channels are created by default? Voice and/or Text?
#  2. Might need two roles for each discussion-room, eg. HOST AND MEMEBERS
#  3. HOST can later add MEMBERS, and MEMBERS can request to join a discussion-room with the approval of the HOST possible
#  4. Later combine create role and channels into ONE command
#  5. Implement a time tracker to countdown on each discussion-room

# create role -- to be implemented: create and assigned the role to the host 
async def create_role(message):
    guild = discord.utils.get(client.guilds, name=GUILD)
    role = message.content.split("t! create-role ", 1)[1]
    if discord.utils.get(guild.roles, name=role):
        await message.channel.send(f'{role} already exists!')
    else:
        await guild.create_role(name=role)
        await message.channel.send(f'{role} created!')

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
            guild.me: discord.PermissionOverwrite(read_messages=True),
            channel_admin: discord.PermissionOverwrite(read_messages=True)
        }
        channel = await guild.create_voice_channel(name=channel_name, overwrites=overwrites)


client.run(TOKEN)