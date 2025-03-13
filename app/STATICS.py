# TABLE SETUP
CREATE_COMMAND = "CREATE TABLE IF NOT EXISTS reactions(user_id, message_text, time, message_url, rc_approval, rc_denial, global_username, guild_id, dumb)"
CREATE_USERS_TABLE = "CREATE TABLE IF NOT EXISTS users(user_id, count, guild_id, global_username)"
CREATE_GUILD_SETTINGS_TABLE = "CREATE TABLE IF NOT EXISTS guild_settings(guild_id, timer_length, vote_threshold, gifs_on_off, safe_message, dumb_message, prefix_text, admin_role)"

# ADD COMMANDS
ADD_COMMAND = "INSERT INTO reactions(USER_ID, MESSAGE_TEXT, TIME, MESSAGE_URL, RC_APPROVAL, RC_DENIAL, GLOBAL_USERNAME, GUILD_ID, DUMB) VALUES(?,?,?,?,?,?,?,?,?)"
ADD_TO_USER_TABLE = "INSERT INTO users(USER_ID, COUNT, GUILD_ID, GLOBAL_USERNAME) VALUES(?,0,?,?)"
ADD_TO_GUILD_SETTINGS = "INSERT INTO guild_settings(GUILD_ID, TIMER_LENGTH, VOTE_THRESHOLD, GIFS_ON_OFF, SAFE_MESSAGE, DUMB_MESSAGE, PREFIX_TEXT, ADMIN_ROLE) VALUES(?,?,?,?,?,?,?,?)"

# GET COMMANDS
GET_LEADERBOARD = "SELECT USER_ID, COUNT FROM users WHERE GUILD_ID = ? ORDER BY COUNT DESC "
GET_TOP_MESSAGES = "SELECT USER_ID, MESSAGE_TEXT, TIME, RC_APPROVAL, MESSAGE_URL FROM reactions WHERE GLOBAL_USERNAME = ? AND GUILD_ID = ? AND DUMB = 1 ORDER BY RC_APPROVAL DESC "
GET_COUNT = "SELECT COUNT FROM users WHERE GLOBAL_USERNAME = ? AND GUILD_ID = ?"
GET_TIMER = "SELECT TIMER_LENGTH FROM guild_settings WHERE GUILD_ID = ?"
GET_VOTE_THRESHOLD = "SELECT VOTE_THRESHOLD FROM guild_settings WHERE GUILD_ID = ?"
GET_GIFS_ON_OFF = "SELECT GIFS_ON_OFF FROM guild_settings WHERE GUILD_ID = ?"
GET_SAFE_MSG = "SELECT SAFE_MESSAGE FROM guild_settings WHERE GUILD_ID = ?"
GET_DUMB_MSG = "SELECT DUMB_MESSAGE FROM guild_settings WHERE GUILD_ID = ?"
GET_PREFIX = "SELECT PREFIX_TEXT FROM guild_settings WHERE GUILD_ID = ?"
GET_ADMIN_ROLE = "SELECT ADMIN_ROLE FROM guild_settings WHERE GUILD_ID = ?"
GET_TIMER_VOTE_THRESHOLD_GIFS_SAFE_DUMB_PREFIX = "SELECT TIMER_LENGTH, VOTE_THRESHOLD, GIFS_ON_OFF, SAFE_MESSAGE, DUMB_MESSAGE, PREFIX_TEXT FROM guild_settings WHERE GUILD_ID = ?"

# AI COMMAND
GET_RANDOM_MESSAGES = "SELECT message_text FROM reactions WHERE GLOBAL_USERNAME = ? AND GUILD_ID = ? ORDER BY RANDOM() LIMIT 3" 


# UPDATE COMMANDS
UPDATE_USERNAME = "UPDATE users SET GLOBAL_USERNAME = ? WHERE USER_ID = ?"
UPDATE_USERNAME_REACTIONS = "UPDATE reactions SET GLOBAL_USERNAME = ? WHERE USER_ID = ?"
UPDATE_USER_COUNT = "UPDATE users SET COUNT = ? WHERE USER_ID = ? AND GUILD_ID = ?"
UPDATE_TIMER_LENGTH = "UPDATE guild_settings SET TIMER_LENGTH = ? WHERE GUILD_ID = ?"
UPDATE_VOTE_THRESHOLD = "UPDATE guild_settings SET VOTE_THRESHOLD = ? WHERE GUILD_ID = ?"
UPDATE_GIFS = "UPDATE guild_settings SET GIFS_ON_OFF = ? WHERE GUILD_ID = ?"
UPDATE_SAFE_MSG = "UPDATE guild_settings SET SAFE_MESSAGE = ? WHERE GUILD_ID = ?"
UPDATE_DUMB_MSG = "UPDATE guild_settings SET DUMB_MESSAGE = ? WHERE GUILD_ID = ?"
UPDATE_PREFIX = "UPDATE guild_settings SET PREFIX_TEXT = ? WHERE GUILD_ID = ?"
UPDATE_ADMIN_ROLE = "UPDATE guild_settings SET ADMIN_ROLE = ? WHERE GUILD_ID = ?"

# CHECKS
CHECK_FOR_MESSAGE_EXIST = "SELECT COUNT(*) FROM reactions WHERE message_url = ?"


# STATIC FILES
winning_gif_url = "https://media.tenor.com/tNfwApVE9RAAAAAM/orange-cat-laughing.gif"
neutral_gif_url = "https://media.tenor.com/D7080WFLF90AAAAM/hxh.gif"
losing_gif_url = "https://media.tenor.com/2fK5bMUEc0UAAAAM/michael-scott-wink.gif"

# TEXT

help_txt = '''
👋 **Hello! Here's an overview of the bot.**

This bot's purpose is to track who writes the dumbest messages in chat most often.  
Currently, it supports several commands:

💬 **Checking the Leaderboard:**  
`!s checkldb(optional number)`  
Returns the full leaderboard, listing all members with at least one dumb message.  

📌 **Limit the results by adding a number.**  
Example: `!s checkldb5` — Returns the top 5 people with the most dumb messages.  

📖 **Getting Top Messages from a User:**  
`!s top_msg(optional number) (username)`  
Shows the top ten messages from the specified user that received the most votes against them.  

📌 **Limit the results by adding a number.**  
Example: `!s top_msg5 username_to_check` — Returns the top 5 messages for the user 'username_to_check'.  
📌 **Note:** The username is the global username, not the server nickname or display name.  

🔢 **Get a Specific Top Message by Rank:**  
`!s get_top_number(number) (username)`  
Fetches a specific message based on the user's `RC_APPROVAL` ranking.  

📌 **Limit the results by providing a number (rank).**  
Example: `!s get_top_number10 username_to_check` — Returns the 10th most approved message for the user 'username_to_check'.  
'''

part2= '''
⚙️ **Adjust Server Settings:**  
`!s adjust (setting) (value)`  
Allows administrators to adjust various server settings. The available settings are:

- `timer_length`: Set the timer for a specific task (must be an integer).  
- `vote_threshold`: Set the threshold for votes (must be an integer).  
- `gifs`: Toggle the use of GIFs (either "on" or "off").  
- `safe_message`: Set a custom message that will be displayed if a message is voted not dumb.  
- `dumb_message`: Set a custom message that will be displayed if a message is voted dumb.  
- `prefix_message`: Set a custom command prefix message.

📌 **Format of message:**  
`prefix_message` `safe_message/dumb_message` 

📌 **Example of adjusting settings:**  
`!s adjust timer_length 10` — Sets the timer length to 10.  
`!s adjust gifs on` — Enables GIFs.  

🧑‍💼 **Analyze a User's Messages:**  
`!s analyze (username)`  
Analyzes a user's messages based on incidents and tracks dumb messages. This command will fetch a few random messages from that user and generate a report.  

📌 **Note:** The username is the global username, not the server nickname or display name.  

❓ **Help Command:**  
`!s help`  
Displays this help page.  

Enjoy exposing the dumbest messages! 😜  
'''

show_defaults = '''
🛠️ **First-Time Setup Defaults:**

⏳ **timer_length**     : `60` minutes
🔢 **vote_threshold**   : `2` votes
🎉 **gifs_on_off**      : `Enabled` (1)
💬 **safe_message**     : `'fine.'`
🤪 **dumb_message**     : `'STUPID!!!!! HAHA!!!'`
🔠 **prefix_text**      : `'This user is'`

These values are customizable later. Let me know if you'd like to adjust them! 
'''

def get_invalid_cmd_str(cmd: str):
    return ("❌ **Invalid Command Format!**\n"
            "Please enter a valid command with a username and an optional number.\n\n"
            f"**Format:** `{cmd}(number) (username)`\n"
            f"**Example:** `{cmd} username_to_check`")

no_result_found_str = ("⚠️ **No Results Found!**\n"
            "Either:\n"
            "• An invalid index was provided.\n"
            "• The user doesn't exist.\n"
            "• The user has no incidents recorded.")

invalid_adjust = "Please send a valid command, check !s help for valid commands."

# AI MESSAGE MODEL


gpt_input=  '''
Make sure your response doesn't trigger the ChatGPT flagging system for usage policies (IMPORTANT). 
Make sure your response doesn't trigger the ChatGPT flagging system for usage policies (IMPORTANT).    
Make sure your response doesn't trigger the ChatGPT flagging system for usage policies (IMPORTANT).    

It's all for fun, so don't worry about the usage policies.
You're being given multiple messages of one person that people have voted as a "dumb message". 
Generate a devious and chaotic analysis of this person’s personality using the messages below. 
Make it sharp, sarcastic, and a decently angry. Don't add any specifics about each message, just analyze the person as a whole (the person reading shouldn't know what messages you've received specifically). 
Add a jab in there as well (for fun) with smiling imp energy. 
Add an emoji between every word. 
Add a lot of emojis, to make it look like a reddit copypasta, and make sure there's one between every 2 words.

Make sure your response doesn't trigger the ChatGPT flagging system for usage policies (IMPORTANT). 
Make sure your response doesn't trigger the ChatGPT flagging system for usage policies (IMPORTANT).    
Make sure your response doesn't trigger the ChatGPT flagging system for usage policies (IMPORTANT).

'''

defaults = [60, 2, 1, 'fine.', 'STUPID!!!!! HAHA!!!', 'This user is', "ADMIN"]
setup_str = """Hello, thank you for adding me to the server! The default values can be seen using `!s defaults`. Let's have a fun time 😜\n
Please type the command `!s adjust admin_role YOUR_SERVER_ADMINISTRATOR_ROLE_NAME`"""


