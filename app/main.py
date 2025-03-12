from typing import Final, List
import os, aiosqlite
from dotenv import load_dotenv
from discord import Intents, Client, Message, Reaction, User, Guild, Member
from time import sleep
from collections import Counter
import asyncio 
import STATICS
import re
from datetime import datetime
from openai import OpenAI

# loading token
load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
GPT_TOKEN: Final[str] = os.getenv('GPT_KEY')

# activating intents (permissions)
intents: Intents = Intents.default()
intents.guild_reactions = True 
intents.message_content = True
intents.guilds = True
intents.members = True
client: Client = Client(intents=intents)

# DB Connections
database_client = None
cursor = None

# current state
current_guild = None
# ################## CLIENT EVENTS ################## #
active_timers = {}
# bot startup
@client.event
async def on_ready() -> None:
    # connecting to db
    global database_client
    global cursor

    os.makedirs("../database_storage", exist_ok=True) # makes directory, if doesn't exist

    database_client = await aiosqlite.connect((os.path.join("../database_storage/main.db")), timeout=20)
    cursor = await database_client.cursor()
    await cursor.execute(STATICS.CREATE_COMMAND)
    await cursor.execute(STATICS.CREATE_USERS_TABLE)
    await cursor.execute(STATICS.CREATE_GUILD_SETTINGS_TABLE)
    await database_client.commit()


# on guild join, add all members to DB
@client.event
async def on_guild_join(guild: Guild):
    await cursor.execute(STATICS.ADD_TO_GUILD_SETTINGS, (guild.id, STATICS.defaults[0], STATICS.defaults[1], STATICS.defaults[2], STATICS.defaults[3], STATICS.defaults[4], STATICS.defaults[5], STATICS.defaults[6],))
    await database_client.commit()
    print(guild.text_channels[0])
    await guild.text_channels[0].send(STATICS.setup_str)
    for member in guild.members:
        await cursor.execute(STATICS.ADD_TO_USER_TABLE, (member.id, guild.id, member.name, ))
        
        await database_client.commit()

# om memebr joining, add them to db
@client.event
async def on_member_join(member: Member):
    await cursor.execute(STATICS.ADD_TO_USER_TABLE, (member.id, member.guild.id, member.name, ))
    await database_client.commit()
    
# updates database to have the most updated global username
@client.event
async def on_user_update(before: User, after: User):
    await cursor.execute(STATICS.UPDATE_USERNAME, (after.name, after.id,))
    await cursor.execute(STATICS.UPDATE_USERNAME_REACTIONS, (after.name, after.id,))
    await database_client.commit()

# handle incoming message
@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return
    await get_help(message)
    await get_leaderboard(message)
    await get_top_messages_per_person(message)
    await get_specific_index(message)
    await adjust_server_information(message)
    await check_no_message(message)
    await run_user_analysis(message)
    await defaults(message)

# handle reaction logic
@client.event
async def on_reaction_add(reaction: Reaction, user: User):
    global active_timers
    channel_to_send = reaction.message.channel
    message: Message = reaction.message
    guild_id = message.guild.id

    if message.author.name == client.user.name:
        return

    # If reaction wasn't one of these, don't do anything
    if reaction.emoji not in ("✅", "🚫"):
        return

    # Check if message already exists in the database (not needed in the new check, but kept for context)
    message_exists_query = await cursor.execute(STATICS.CHECK_FOR_MESSAGE_EXIST, (reaction.message.jump_url,))
    result = await message_exists_query.fetchone()
    if result and result[0] != 0:
        return

    # If the timer has already been triggered for this message, exit
    if reaction.message.id in active_timers:
        return  # Timer already started for this message, so exit.

    

    # retrieve the guild information on what to send
    result_execute = await cursor.execute(STATICS.GET_TIMER_VOTE_THRESHOLD_GIFS_SAFE_DUMB_PREFIX, (guild_id, ))
    (timer, vote, gifs_on, safe_msg, dumb_message, prefix_text) = await result_execute.fetchone()
    print()

    # Check if any reaction for "🚫" has count >= 2 (the condition for starting the timer)
    if any(r.emoji == "🚫" and r.count >= vote for r in message.reactions):
        print(f"timer: {timer} vote: {vote}")

        active_timers[reaction.message.id] = True  # Add it to active timers
        print("Starting timer!")
        
        # Only send the "Timer has started!" message once
        await channel_to_send.send(f"Voting has started on message {message.jump_url}, get your votes in!")

        # Prevent further reactions from triggering the timer by setting a delay for 10 seconds
        await asyncio.sleep(timer)

        # Fetch updated message and count reactions
        updated_message = await message.fetch()
        reactions: List[Reaction] = updated_message.reactions
        reaction_check_ct = 0
        reaction_deny_ct = 0

        # Count reactions for each emoji
        for reaction in reactions:
            if reaction.emoji == "🚫":
                reaction_check_ct = reaction.count
            elif reaction.emoji == "✅":
                reaction_deny_ct = reaction.count

        print(reaction_check_ct)
        print(reaction_deny_ct)
        await channel_to_send.send(f"{prefix_text} {dumb_message if reaction_check_ct > reaction_deny_ct else safe_msg}")

        # Add message to the database
        await add_message(reaction.message.author.id, message.content, message.created_at, message.jump_url, reaction_check_ct, reaction_deny_ct, reaction.message.author.name, guild_id, 1 if reaction_check_ct > reaction_deny_ct else 0)

        # Send GIF depending on the result
        if gifs_on == 1:
            if reaction_check_ct > reaction_deny_ct:
                await channel_to_send.send(STATICS.winning_gif_url)
            elif reaction_check_ct == reaction_deny_ct:
                await channel_to_send.send(STATICS.neutral_gif_url)
            else:
                await channel_to_send.send(STATICS.losing_gif_url)

        # Remove from active timers to avoid triggering again
        del active_timers[reaction.message.id]
                

# ################## DB MANAGEMENT ################## #

async def add_message(user_id, msg_txt, time, msg_url, rc_approve, rc_denial, username, guild_id, dumb):
    cursor = await database_client.cursor()
    if dumb == 1:
        count = 0
        count_fetch = await cursor.execute(STATICS.GET_COUNT, (username, guild_id, ))
        result = await count_fetch.fetchone()
        
        # If a result is found, increment the count
        if result:
            count = result[0] + 1  # Increment the count
        await cursor.execute(STATICS.UPDATE_USER_COUNT, (count, user_id, guild_id, ))
        
    
    await cursor.execute(STATICS.ADD_COMMAND, (user_id, msg_txt, time, msg_url, rc_approve, rc_denial, username, guild_id, dumb, ))
    await database_client.commit()

async def get_leaderboard(msg: Message):
    # Retrieves the full leaderboard or a limited version based on the user's input
    if not msg.content.startswith("!s checkldb"):
        return
    
    leaderboard = None
    if msg.content == "!s checkldb":
        leaderboard = await cursor.execute(STATICS.GET_LEADERBOARD, (msg.guild.id,))
    elif msg.content.startswith("!s checkldb"):
        top_amnt = msg.content[11:].strip()
        leaderboard = await cursor.execute(STATICS.GET_LEADERBOARD + f" LIMIT {top_amnt}", (msg.guild.id,))
    
    # Prepare leaderboard message
    str_to_print = "📊 **Leaderboard of Dumbest Messages** 📊\n\n"
    idx = 1

    for (id, count) in await leaderboard.fetchall():
        if id != client.user.id:
            str_to_print += f"**{idx}.** <@{id}> — **{count} incidents** 💀\n"
            idx += 1

    if idx == 1:  # No entries found
        str_to_print += "No dumb messages recorded yet. Everyone's a genius... for now. 🧐"

    # Send placeholder then edit to make it not mention users
    msg_placeholder = await msg.channel.send('Loading...')
    await msg_placeholder.edit(content=str_to_print)
  
  
# message should be the users globalname
async def get_top_messages_per_person(msg: Message):
    if not msg.content.startswith("!s top_msg"):
        return
    
    msg_placeholder = await msg.channel.send('Loading...')
    leaderboard = None
    msg_txt = msg.content.strip().lower()
    match = re.search(r"!s top_msg(\d*)\s*(.*)", msg_txt)

    top_amount = match.group(1).strip().lower()  # The number
    username = match.group(2).strip().lower()  # The username
    # if we're provided a specific number, get that many, otherwise get the top 10
    if top_amount and username:
        leaderboard = await cursor.execute(STATICS.GET_TOP_MESSAGES+f"LIMIT {top_amount} ", (username, msg.guild.id, ))
    elif username:
        leaderboard = await cursor.execute(STATICS.GET_TOP_MESSAGES+"LIMIT 10 ", (username, msg.guild.id, ))
    else: 
        await msg_placeholder.edit(content=STATICS.get_invalid_cmd_str("!s top_msg"))
        return

    new_str = ''
    idx = 1
    user_id = None
    

    for (id, txt, time, rc_approval, msg_url) in await leaderboard.fetchall():
        user_id = id
        formatted_time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f%z").strftime("%B %d, %Y, %I:%M %p (UTC)")
        new_str+= f"**{idx}.** \"{txt}\" at {formatted_time} with **{rc_approval} approvals!** 🔗 {msg_url}\n"
        idx+=1

    count_call = await cursor.execute(STATICS.GET_COUNT, (username.lower().strip(), msg.guild.id,))
    result = await count_call.fetchone()
    count = 0
    # If a result is found, extract the count
    if result:
        count = result[0]
    
    if count == 0:
        await msg_placeholder.edit(content=STATICS.no_result_found_str)
        return

    # logic for printing them into a string for execution
    str_to_print = f'<@{user_id}> has {count} incidents!\n'


    if (new_str == ''):
        await msg_placeholder.edit(content=(STATICS.no_result_found_str))
    else:
        await msg_placeholder.edit(content=str_to_print+new_str)

async def get_help(message: Message):
    print(f"message: {message.content}")
    if message.content != "!s help":
        return
    await message.channel.send(STATICS.help_txt)
    await message.channel.send(STATICS.part2)

async def get_specific_index(message: Message):
    if not message.content.startswith("!s get_top_number"):
        return
    
    msg_placeholder = await message.channel.send('Loading...')
    msg_txt = message.content.strip().lower()
    match = re.search(r"!s get_top_number(\d*)\s*(.*)", msg_txt)
    top_amount = match.group(1).strip().lower()  # The number
    username = match.group(2).strip().lower()  # The username   

    if top_amount and username:
        print(f"top amount {top_amount} username {username}")
        leaderboard = await cursor.execute(STATICS.GET_TOP_MESSAGES+f"LIMIT 1 OFFSET {int(top_amount)-1} ", (username, message.guild.id, ))
    else: 
        await msg_placeholder.edit(content=STATICS.get_invalid_cmd_str("!s get_top_number"))
        return
    
    result = await leaderboard.fetchone()

    if result:
        (id, txt, time, rc_approval, msg_url) = result
        print(f"loop: {id} {txt} {time} {rc_approval} {msg_url}")
        
        await msg_placeholder.edit(content=f"<@{id}> sent \"{txt}\" at {time} with {rc_approval} approving! {msg_url}")
    else:
        await msg_placeholder.edit(content=(STATICS.no_result_found_str))
        return
    
async def adjust_server_information(message: Message):
    # command must start with "!s adjust"
    message_content = message.content
    current_channel = message.channel
    guild_id = message.guild.id
    if not message_content.startswith("!s adjust"):
        return 
    result = await cursor.execute(STATICS.GET_ADMIN_ROLE, (guild_id,))

    # if not an admin, can't adjust

    print(message.author.roles)

    # retrieveing the admin role for the server
    admin_role = await result.fetchone()
    print(admin_role)
    admin_role = admin_role[0]
    permission_granted = False
    for role in message.author.roles:
        if role.name == admin_role:
            permission_granted = True
    
    if not message.author.guild_permissions.administrator and not permission_granted:
        return 
    
    message_placeholder = await current_channel.send("Loading...")
    match = re.search(r"!s adjust\s*(\S+)\s*(.*)", message_content)
    
    what_to_adjust = None
    value = None
    
    if match:
        what_to_adjust = match.group(1).strip().lower()    
        value = match.group(2).strip()
    else:
        message_placeholder.edit(content = STATICS.invalid_adjust)

    print(f"value: {value} what_to_adjust: {what_to_adjust}")

    if what_to_adjust == "timer_length":
        # must pass in int for value
        try:
            int(value)
            await cursor.execute(STATICS.UPDATE_TIMER_LENGTH, (int(value), guild_id,))
            await database_client.commit()
        except ValueError:
            print("timer")
            await message_placeholder.edit(content=STATICS.invalid_adjust)
            return
    elif what_to_adjust == "vote_threshold":
        # must pass in int for value
        try:
            int(value)
            await cursor.execute(STATICS.UPDATE_VOTE_THRESHOLD, (int(value), guild_id,))
            await database_client.commit()
        except ValueError:
            print("vote")
            await message_placeholder.edit(content=STATICS.invalid_adjust)
            return
    elif what_to_adjust == "gifs":
        if (value.lower() != "on" and value.lower() != "off"): # only acceptable values are on and off
            await message_placeholder.edit(content=STATICS.invalid_adjust)
            return
        else:
            print("gifs")
            await cursor.execute(STATICS.UPDATE_GIFS, (1 if value.lower() == "on" else 0, guild_id,))
            await database_client.commit()
    elif what_to_adjust == "safe_message":
        print("safe_msg")
        await cursor.execute(STATICS.UPDATE_SAFE_MSG, (value, guild_id,))
        await database_client.commit()
    elif what_to_adjust == "dumb_message":
        print("dumb_msg")
        await cursor.execute(STATICS.UPDATE_DUMB_MSG, (value, guild_id,))
        await database_client.commit()
    elif what_to_adjust == "prefix_message":
        print("prefix")
        await cursor.execute(STATICS.UPDATE_PREFIX, (value, guild_id, ))
        await database_client.commit()
    elif what_to_adjust == "admin_role":
        await cursor.execute(STATICS.UPDATE_ADMIN_ROLE, (value.lower(), guild_id))
        await database_client.commit()
    else:
        await message_placeholder.edit(content=STATICS.invalid_adjust)
        return
    await message_placeholder.edit(content="Adjusted!")
    return
    
async def defaults(message: Message):
    if message.content != "!s defaults":
        return
    else:
        await message.channel.send(STATICS.show_defaults)


async def check_no_message(message: Message):
    pattern = r"!s(.*)"
    match = re.search(pattern, message.content)

    if not match:
        return

    match = match.group(1).lower().strip()
    if not match.startswith(("adjust", "get_top_number", "top_msg", "checkldb", "analyze", "defaults")):
        await message.channel.send("Did you mean to send a command? Type `!s help` for a list of commands.")



## AI FUNCTIONALITY ##

async def run_user_analysis(message: Message):
    if not message.content.startswith("!s analyze"):
        return
    message_placeholder = await message.channel.send("Loading...")

    message_content = message.content
    match = re.search(r"!s analyze(.*)", message_content).group(1).lower().strip()
    
    input_str = ""
    result = await cursor.execute(STATICS.GET_RANDOM_MESSAGES, (match, message.guild.id, ))
    idx = 1
    if result:
        for msg_txt in await result.fetchall():
            print(f"msg_txt: {msg_txt[0]}")
            input_str+=f"{idx}){msg_txt}\n"
            idx+=1
        if input_str == "":
            await message_placeholder.edit(content="Either invalid user provided or user has no incidents!")
            return
        
    else:
        await message_placeholder.edit(content="Either invalid user provided or user has no incidents!")
        return
    
    client = OpenAI(
        api_key=GPT_TOKEN
    )
    response = client.responses.create(
        model="gpt-3.5-turbo",
        instructions=STATICS.gpt_input,
        input=input_str
    )

    await message_placeholder.edit(content=response.output_text)


def main() -> None:
    # checking if environment variables are not null
    if not DISCORD_TOKEN or not GPT_TOKEN:
        print("One or both of tokens are missing. Program terminating...")
        return 

    client.run(token=DISCORD_TOKEN)

if __name__ == '__main__':
    main()

