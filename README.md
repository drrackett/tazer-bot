# Tazer Bot :robot:
Tazer is a discord meeting creation bot where it will help you in create and delete meeting related commands to provide you a streamlined meeting in discord.

## How does it work?
Still a work in progress
<br/>
### **The features of Tazer Bot**
- create/delete roles
- create & delete voice & text channel
- add/remove list of members to the discussion-channel with one simple command
- set of time (eg. 1hr then it will delete itself - voice & chat channel)

## Installation
### Prerequisites
Docker
1. Create a discord bot on Discord Developer Portal
2. Clone this repository
<br/>```git clone https://github.com/ywbtan/tazer-bot.git```
3. Create a .env file in the cloned repository with your bot token
<br/>```DISCORD_TOKEN=YOUR_BOT_TOKEN```
4. Start terminal from the cloned repository
<br/>```cd path/to/cloned/repository```
5. Build an image with Docker
<br/>```docker build -t imageName .```
6. Run the image as a container
<br/>```docker run --env-file .env imageName```

## Commands
1. Create a discussion room with both text and voice channels
<br/>```t! start discussion-room-name```
<br/>OR
<br/>```t! start discussion-room-name @user```

2. Invite users to discussion-room created
<br/>```t! invite```

3. Delete the discussion room created
<br/>```t! end```

## License
[MIT](https://choosealicense.com/licenses/mit/)
