import os
import random
import re
from typing import Optional
import emojis
import asyncio

import discord
from dotenv import load_dotenv

RGB_MIN = 0
RGB_MAX = 255

# load_dotenv(os.path.join(os.getcwd(), '.env'))
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

# store voice_channel as key and user created as key
DISCUSSION_ROOMS = {}
CATEGORY_NAME = 'Discussion Rooms'

VOICE_CHANNEL = 'voice_channel'
CATEGORY = None


@client.event
async def on_ready():
    # discord.utils.find(lambda g: g.name == GUILD, client.guilds)
    guild = discord.utils.get(client.guilds, name=GUILD)
    
    # DO NOT DELETE THIS FOR NOW SO THAT WE KNOW THE BOT HAS SUCCESSFULLY CONNECTED
    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})\n'
    )

    global CATEGORY
    CATEGORY = await guild.create_category_channel(CATEGORY_NAME)


@client.event
async def on_member_join(member):
    # create a direct message channel and use that channel to .send() a direct message
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to my Discord server!'
    )


async def destruct_by_room(room):
    await room['role'].delete()
    await room['text_channel'].delete()
    await room[VOICE_CHANNEL].delete()


async def cleanup():
    for room, room_props in DISCUSSION_ROOMS.items():
        await destruct_by_room(room_props)
    await CATEGORY.delete()
    await client.close()

@client.event
async def on_message(message):

    # DO NOT DELETE THIS
    if message.author == client.user:
        return

    # List of commands here - will switch to discord commands later
    if message.content.startswith("t! start"):
        await message.delete()
        room_name = message.content.split("t! start ", 1)[1].split(" ", 1)[0]
        members = message.mentions
        room = await create_discussion_room(message.author, room_name, members)
        assert room is not None
        # notify host (created) and members (invited)
        await message.author.send(f'{room_name} is created!')

    elif message.content.startswith("t! add"):
        await add_members(message)

    elif message.content.startswith("t! remove"):
        await remove_members(message)

    elif message.content.startswith("t! end"):
        await delete_discussion_room(message)

    # elif re.search("^t! config category ", message.content):
    
    elif message.content.startswith("t! clear"):
        lines = int(message.content.split("t! clear ", 1)[1])
        await clear_messages(message, lines)

    elif message.content.startswith("t! invite"):
        await invite_members_to_priv_channel(message)

    elif message.content.startswith("t! disconnect"):
        await message.delete()
        await cleanup()

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


async def invite_members_to_priv_channel(message):
    guild = discord.utils.get(client.guilds, name=GUILD)
    embedVar = discord.Embed(title=f"Invite people", 
    description=f"Here's a list of members not in {message.channel.name}", color=0x00ff00)
    all_members = guild.members
    all_emojis = list(emojis.db.get_emoji_aliases().values())

    emojis_used = {}
    for member in all_members:
        if member not in message.channel.members:
            emoji_unicode = random.choice(all_emojis)
            embedVar.add_field(name=f"{emoji_unicode}", value=f"{member.mention}", inline=True)
            emojis_used[emoji_unicode] = member
    bot_msg = await message.channel.send(embed=embedVar)

    for emoji in emojis_used.keys():
        await bot_msg.add_reaction(emoji)

    def check(reaction, user):
        return str(reaction.emoji) in list(emojis_used.keys()) and user == message.author

    try:
        while True:
            reaction, user = await client.wait_for('reaction_add', timeout=7.0, check=check)
            await emojis_used[str(reaction.emoji)].add_roles(DISCUSSION_ROOMS[message.channel]['role'])
            await message.channel.send(f'{emojis_used[str(reaction.emoji)].name} has been added!')
    except asyncio.TimeoutError:
        await bot_msg.clear_reactions()


# create role
async def create_role(role_name):
    guild = discord.utils.get(client.guilds, name=GUILD)
    if discord.utils.get(guild.roles, name=role_name) is None:
        role_color = discord.Colour.from_rgb(random.randint(RGB_MIN, RGB_MAX), 
        random.randint(RGB_MIN, RGB_MAX), random.randint(RGB_MIN, RGB_MAX))
        role = await guild.create_role(name=role_name, color=role_color)
    else:
        print(f'Role {role_name} existed!') # for debugging purposes
        raise
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
async def create_private_voice_channel(channel_name, role_allowed):
    guild = discord.utils.get(client.guilds, name=GUILD)
    if discord.utils.get(guild.voice_channels, name=channel_name):
        print(f"Voice channel {channel_name} existed!")
        raise
    else:
        assert role_allowed is not None
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            role_allowed: discord.PermissionOverwrite(read_messages=True)
        }
        voice_channel = await CATEGORY.create_voice_channel(name=channel_name, overwrites=overwrites)
    return voice_channel


# create a private voice channel
# current: voice_channel not created if already exists, and role needs to be 
#          created before creating corresponding voice_channel
async def create_private_text_channel(channel_name, role_allowed):
    guild = discord.utils.get(client.guilds, name=GUILD)
    if discord.utils.get(guild.text_channels, name=channel_name):
        print(f"Text channel {channel_name} existed!")
        raise
    else:
        assert role_allowed is not None
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True),
            role_allowed: discord.PermissionOverwrite(view_channel=True)
        }
        txt_channel = await CATEGORY.create_text_channel(name=channel_name, overwrites=overwrites)
    return txt_channel


async def assign_role(member, role):
    await member.add_roles(role)


async def create_discussion_room(host, room_name, members):
    role = None
    p_text_channel = None
    p_voice_channel = None
    try:
        # create a role and both private text and voice channels
        role = await create_role(room_name)
        p_text_channel = await create_private_text_channel(room_name, role)
        p_voice_channel = await create_private_voice_channel(room_name, role)

        # assign the specific role so that members are allowed to join both channels created
        await host.add_roles(role)
        for member in members:
            if not member == client.user:
                await member.add_roles(role)
        
        DISCUSSION_ROOMS[p_text_channel] = {
            'host': host,
            'role': role,
            'text_channel': p_text_channel,
            VOICE_CHANNEL: p_voice_channel
        }
    except:
        await destruct_discussion_room(role, p_text_channel, p_voice_channel)
    return p_text_channel


async def destruct_discussion_room(role, txt_channel, voice_channel):
    if role is not None:
        await role.delete()
    if txt_channel is not None:
        await txt_channel.delete()
    if voice_channel is not None:
        await voice_channel.delete()


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

    if not message.author == DISCUSSION_ROOMS[text_channel]['host']:
        await message.channel.send(f'Only the host, {DISCUSSION_ROOMS[text_channel]} can remove people from this discussion room!')
        return

    role = discord.utils.get(guild.roles, name=text_channel.name)

    for member in message.mentions:
        if not member == client.user:
            await member.remove_roles(role)


async def delete_discussion_room(message):
    text_channel = message.channel
    assert message.author in text_channel.members

    if not message.author == DISCUSSION_ROOMS[text_channel]['host']:
        await message.channel.send(f'Only the host, {DISCUSSION_ROOMS[text_channel]} can end this discussion room!')
        return

    voice_channel = DISCUSSION_ROOMS[text_channel][VOICE_CHANNEL]
    role = DISCUSSION_ROOMS[text_channel]['role']

    DISCUSSION_ROOMS.pop(text_channel)

    # delete text and voice channels created and role created
    await voice_channel.delete()
    await text_channel.delete()
    await role.delete()

#clear text messages in discussion room or text channel
@client.event
async def clear_messages(ctx, limit= 1):
    await ctx.channel.purge(limit=limit+1)
    

client.run(TOKEN)