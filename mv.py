from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from flask import Flask
import time
import os
import asyncio
import sqlite3
import logging
logging.basicConfig(level=logging.DEBUG)

# ------------------------ CONFIGURATION ------------------------
API_ID = os.getenv("API_ID")  # Name of the environment variable
API_HASH = os.getenv("API_HASH")  # Name of the environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Name of the environment variable
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))  # Get admin user ID from environment variables

# Force Join Configuration
CHANNEL_USERNAMES = ["@megahubbots", "@Freeinternetonly", "@Freenethubchannel", "@MunoFlix"]  # List of channel usernames
CHANNEL_LINKS = ["https://t.me/megahubbots", "https://t.me/Freeinternetonly", "https://t.me/Freenethubchannel", "https://t.me/MunoFlix"]  # List of channel links

# Movie Channel Configuration
MOVIE_CHANNEL_USERNAME = "@moviesdatabas"  # Replace with your movie channel's username

# File to store movie information
MOVIE_FILE = "movies.txt"

# Database Configuration
DATABASE_NAME = "movie_bot.db"

# Admin Configuration
ADMIN_USER_ID = 6211392720  # Replace with your admin user ID

# Signal verification animation
SIGNAL_FRAMES = [
    "📡 [▫▫▫▫▫] 𝑪𝒐𝒏𝒏𝒆𝒄𝒕𝒊𝒏𝒈...",
    "📡 [■▫▫▫▫] 𝑪𝒐𝒏𝒏𝒆𝒄𝒕𝒊𝒏𝒈...",
    "📡 [■■▫▫▫] 𝑪𝒐𝒏𝒏𝒆𝒄𝒕𝒊𝒏𝒈...",
    "📡 [■■■▫▫] 𝑪𝒐𝒏𝒏𝒆𝒄𝒕𝒊𝒏𝒈...",
    "📡 [■■■■▫] 𝑨𝒍𝒎𝒐𝒔𝒕 𝑫𝒐𝒏𝒆...",
    "📡 [■■■■■] ✅ 𝘾𝙊𝙉𝙉𝙀𝘾𝙏𝙀𝘿",
]

# Data syncing animation
SYNC_FRAMES = [
    "📊 𝑺𝒆𝒂𝒓𝒄𝒉𝒊𝒏𝒈 𝑫𝒂𝒕𝒂𝒃𝒂𝒔𝒆 [▓▓░░░░░░░░░░░] 15%",
    "📊 𝑺𝒆𝒂𝒓𝒄𝒉𝒊𝒏𝒈 𝑫𝒂𝒕𝒂𝒃𝒂𝒔𝒆 [▓▓▓░░░░░░░░░] 30%",
    "📊 𝑺𝒆𝒂𝒓𝒄𝒉𝒊𝒏𝒈 𝑫𝒂𝒕𝒂𝒃𝒂𝒔𝒆 [▓▓▓▓▓░░░░░░░] 45%",
    "📊 𝑺𝒆𝒂𝒓𝒄𝒉𝒊𝒏𝒈 𝑫𝒂𝒕𝒂𝒃𝒂𝒔𝒆 [▓▓▓▓▓▓▓░░░░░] 60%",
    "📊 𝑺𝒆𝒂𝒓𝒄𝒉𝒊𝒏𝒈 𝑫𝒂𝒕𝒂𝒃𝒂𝒔𝒆 [▓▓▓▓▓▓▓▓▓░░░] 80%",
    "📊 𝑺𝒆𝒂𝒓𝒄𝒉𝒊𝒏𝒈 𝑫𝒂𝒕𝒂𝒃𝒂𝒔𝒆 [▓▓▓▓▓▓▓▓▓▓▓] 100%",
]

# Rotating processing animation
PROCESSING_FRAMES = ["🔄", "🔃", "🔁", "🔂"]

# ---------------------- DATABASE SETUP ----------------------

def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Create tables for movies, users, and leaderboard
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            caption TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            search_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# ---------------------- BOT INITIALIZATION ----------------------

app = Client("MovieSearchBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------------- HELPER FUNCTIONS ----------------------

async def force_join(user_id):
    """Check if the user is a member of the required channels."""
    for username in CHANNEL_USERNAMES:
        try:
            chat_member = await app.get_chat_member(username, user_id)
            if chat_member.status not in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return False
        except Exception as e:
            print(f"Error checking membership: {e}")
            return False
    return True

async def show_animation(message, frames, delay=0.5):
    """Display an animation using editing messages."""
    msg = await message.reply(frames[0])
    for frame in frames[1:]:
        await asyncio.sleep(delay)
        await msg.edit(frame)
    return msg

def add_user(user_id, username):
    """Add a user to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def increment_search_count(user_id):
    """Increment the search count for a user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET search_count = search_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_top_users():
    """Get the top 10 users with the most searches."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, search_count FROM users ORDER BY search_count DESC LIMIT 10")
    top_users = cursor.fetchall()
    conn.close()
    return top_users

def add_movie(file_id, caption):
    """Add a movie to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO movies (file_id, caption) VALUES (?, ?)", (file_id, caption))
    conn.commit()
    conn.close()

def search_movies(query):
    """Search for movies in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, caption FROM movies WHERE caption LIKE ?", (f"%{query}%",))
    movies = cursor.fetchall()
    conn.close()
    return movies

# ---------------------- MOVIE STORAGE FUNCTIONS ----------------------

def add_movie_to_file(message_id, caption):
    """Add a movie's caption and ID to the .txt file."""
    with open(MOVIE_FILE, "a") as file:
        file.write(f"{message_id}: {caption}\n")

def search_movie_in_file(query):
    """Search for a movie in the .txt file."""
    if not os.path.exists(MOVIE_FILE):
        return None  # Return None if the file doesn't exist
    with open(MOVIE_FILE, "r") as file:
        for line in file:
            if query.lower() in line.lower():
                return line.split(":")[0]  # Return the message ID
    return None

# ---------------------- LISTEN FOR NEW MOVIE MESSAGES ----------------------

@app.on_message(filters.chat(MOVIE_CHANNEL_USERNAME))
def store_movie(client, message):
    """
    Listens for new messages in the movie channel and stores them in a file.
    """
    try:
        print(f"📥 New message received in the movie channel: {message.id}")
        # Check if the message contains a video or document
        if message.video or message.document:
            # Store the movie's ID and caption in the file
            caption = message.caption if message.caption else "No Caption"
            add_movie_to_file(message.id, caption)
            print(f"📥 New movie stored: {message.id}")
            print(f"Movie Details: {message}")
        else:
            print("❌ Message does not contain a video or document.")
    except Exception as e:
        print(f"❌ Error storing movie: {e}")

# ---------------------- START COMMAND ----------------------

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    """Handle the /start command with force join and animation."""
    user_id = message.from_user.id
    username = message.from_user.username
    add_user(user_id, username)  # Add user to the database
    # Show signal verification animation
    await show_animation(message, SIGNAL_FRAMES)
    # Check if the user is a member of the required channels
    if not await force_join(user_id):
        buttons = [[InlineKeyboardButton(f"Join {username}", url=link)] for username, link in zip(CHANNEL_USERNAMES, CHANNEL_LINKS)]
        await message.reply_text(
            "🪬 𝗩𝗲𝗿𝗶𝗳𝗶𝗰𝗮𝘁𝗶𝗼𝗻 𝗦𝘁𝗮𝘁𝘂𝘀: ⚠️ 𝐘𝐨𝐮 𝐦𝐮𝐬𝐭 𝐣𝐨𝐢𝐧 𝐭𝐡𝐞 𝐟𝐨𝐥𝐥𝐨𝐰𝐢𝐧𝐠 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐭𝐨 𝐮𝐬𝐞 𝐭𝐡𝐢𝐬 𝐛𝐨𝐭 𝐚𝐧𝐝 𝐕𝐞𝐫𝐢𝐟𝐲 𝐲𝐨𝐮'𝐫𝐞 𝐧𝐨𝐭 𝐚 𝐑𝐨𝐛𝐨𝐭",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    # Welcome message
    await message.reply_text(
        "🎬 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝘁𝗵𝗲 𝗠𝗼𝘃𝗶𝗲 𝗦𝗲𝗮𝗿𝗰𝗵 𝗕𝗼𝘁!\n\n"
        "🎥 𝗠𝗼𝘃𝗶𝗲𝘀 & 𝗦𝗲𝗿𝗶𝗼𝘂𝘀 𝗧𝘆𝗽𝗲𝘀:\n"
        "🍿 𝑇𝑟𝑎𝑛𝑠𝑙𝑎𝑡𝑒𝑑 & 𝐸𝑛𝑔𝑙𝑖𝑠ℎ 𝑀𝑜𝑣𝑖𝑒𝑠\n"
        "📽️ 𝑆𝑒𝑟𝑖𝑒𝑠 \n"
        "🎙️ 𝐷𝑢𝑏𝑏𝑒𝑑 𝑀𝑜𝑣𝑖𝑒𝑠 & 𝑆𝑒𝑟𝑖𝑒𝑠!\n"
        "🎭 𝐶𝑎𝑟𝑡𝑜𝑜𝑛 & 𝐴𝑛𝑖𝑚𝑒 \n\n"
        "🔍 Send me the movie or series name, and I'll find it for you!"
    )
@app.on_message(filters.text & filters.private & filters.command)
async def handle_search(client, message):
    """Handle movie search requests."""
    user_id = message.from_user.id
    if not await force_join(user_id):
        buttons = [[InlineKeyboardButton(f"Join {username}", url=link)] for username, link in zip(CHANNEL_USERNAMES, CHANNEL_LINKS)]
        await message.reply_text(
            "⚠️ 𝙔𝙤𝙪 𝙢𝙪𝙨𝙩 𝙟𝙤𝙞𝙣 𝙩𝙝𝙚 𝙛𝙤𝙡𝙡𝙤𝙬𝙞𝙣𝙜 𝙘𝙝𝙖𝙣𝙣𝙚𝙡𝙨 𝙩𝙤 𝙪𝙨𝙚 𝙩𝙝𝙞𝙨 𝙗𝙤𝙩:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    query = message.text.lower()
    message_id = search_movie_in_file(query)
    if message_id:
        print(f"✅ Movie found for query: {query}")
        # Show data syncing animation
        await show_animation(message, SYNC_FRAMES)
        await message.reply_text("✅ 𝙼𝚘𝚟𝚒𝚎 𝙵𝚘𝚞𝚗𝚍 𝚂𝚎𝚗𝚍𝚒𝚗𝚐...")
        time.sleep(2)  # Prevent rate limits
        # Forward the movie without the forward tag
        try:
            await client.copy_message(message.chat.id, MOVIE_CHANNEL_USERNAME, int(message_id))
            print(f"✅ Movie forwarded: {message_id}")
        except Exception as e:
            print(f"❌ Error forwarding movie: {e}")
            await message.reply_text("❌ Sorry, an error occurred while sending the movie.")
    else:
        print(f"❌ No movie found for query: {query}")
        await message.reply_text("❌ Sorry, no movie found with that name. Try another title.")

@app.on_message(filters.command("requestmovies") & filters.private)
async def request_movies(client, message):
    """Handle the /requestmovies command."""
    buttons = [[InlineKeyboardButton("𝙅𝙤𝙞𝙣 𝙍𝙚𝙦𝙪𝙚𝙨𝙩 𝘾𝙝𝙖𝙣𝙣𝙚𝙡", url="https://t.me/request_movies_today")]]
    await message.reply_text(
        "𝗛𝗲𝗿𝗲 𝗬𝗼𝘂 𝗖𝗮𝗻 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗠𝗼𝘃𝗶𝗲'𝘀, 𝗝𝘂𝘀𝘁 𝗦𝗲𝗻𝗱  𝗠𝗼𝘃𝗶𝗲 𝗼𝗿 𝗦𝗲𝗿𝗶𝗲  𝗡𝗮𝗺𝗲 𝗪𝗶𝘁𝗵 𝗣𝗿𝗼𝗽𝗲𝗿 𝗦𝗽𝗲𝗹𝗹𝗶𝗻𝗴 𝗶𝗻 𝘁𝗵𝗲 𝗚𝗿𝗼𝘂𝗽 𝗮𝗻𝗱 𝗶𝘁 𝘄𝗶𝗹𝗹 𝗯𝗲 𝗮𝗱𝗱𝗲𝗱 ..!!",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_message(filters.command("leaderboard") & filters.private)
async def leaderboard(client, message):
    """Handle the /leaderboard command."""
    # Show loading animation
    msg = await show_animation(message, PROCESSING_FRAMES)
    # Fetch top 10 users from the database
    top_users = get_top_users()
    # Format leaderboard message
    leaderboard_text = "🏆 𝗧𝗼𝗽 10 𝗨𝘀𝗲𝗿𝘀 🏆\n\n"
    for i, (username, count) in enumerate(top_users, start=1):
        leaderboard_text += f"{i}. {username} - {count} searches\n"
    await msg.edit(leaderboard_text)

@app.on_message(filters.command("profile") & filters.private)
async def profile(client, message):
    """Handle the /profile command."""
    user_id = message.from_user.id
    username = message.from_user.username
    await message.reply_text(f"👤 𝗬𝗼𝘂𝗿 𝗣𝗿𝗼𝗳𝗶𝗹𝗲:\n\n🆔 𝙐𝙨𝙚𝙧 𝙄𝘿: {user_id}\n👤 𝙐𝙨𝙚𝙧𝙣𝙖𝙢𝙚: {username}")

@app.on_message(filters.command("contactus") & filters.private)
async def contact_us(client, message):
    """Handle the /contactus command."""
    await message.reply_text(
        "📞 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗨𝘀  📞\n\n"
        "For any issues or inquiries, please reach out to our support team at:\n\n"
        "📨 𝗘𝗺𝗮𝗶𝗹 : freenethubbusiness@gmail.com\n"
        "👨‍💻 𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗺 : @SILANDO\n\n"
        "❗𝗢𝗡𝗟𝗬 𝗙𝗢𝗥 𝗕𝗨𝗦𝗜𝗡𝗘𝗦𝗦 𝗔𝗡𝗗 𝗛𝗘𝗟𝗣, 𝗗𝗢𝗡'𝗧 𝗦𝗣𝗔𝗠!"
    )

@app.on_message(filters.command("howtouse") & filters.private)
async def how_to_use(client, message):
    """Handle the /howtouse command."""
    await message.reply_text(
        "📘 𝗛𝗼𝘄 𝘁𝗼 𝗨𝘀𝗲 𝘁𝗵𝗲 𝗕𝗼𝘁 📘\n\n"
        "1. Send the movie or series name to search for it.\n"
        "2. Use /requestmovies to request new movies.\n"
        "3. Use /leaderboard to see the top users.\n"
        "4. Use /profile to view your profile.\n"
        "5. Use /contactus to contact the admin.\n"
        "6. Use /howtouse to see this guide again."
    )

@app.on_message(filters.command("stats") & filters.private)
async def stats(client, message):
    """Handle the /stats command (Admin only)."""
    user_id = message.from_user.id
    if user_id != ADMIN_USER_ID:
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    await message.reply_text(f"📊 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘀:\n\n👥 𝗧𝗼𝘁𝗮𝗹 𝗨𝘀𝗲𝗿𝘀: {total_users}")

@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast(client, message):
    """Handle the /broadcast command (Admin only)."""
    user_id = message.from_user.id
    if user_id != ADMIN_USER_ID:
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: /broadcast <message>")
        return
    broadcast_message = " ".join(message.command[1:])
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    for user in users:
        try:
            await app.send_message(user[0], broadcast_message)
        except Exception as e:
            print(f"Error sending broadcast to user {user[0]}: {e}")
    await message.reply_text("✅ Broadcast sent to all users.")

@app.on_message(filters.command("resetleaderboard") & filters.private)
async def reset_leaderboard(client, message):
    """Handle the /resetleaderboard command (Admin only)."""
    user_id = message.from_user.id
    if user_id != ADMIN_USER_ID:
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET search_count = 0")
    conn.commit()
    conn.close()
    await message.reply_text("✅ Leaderboard has been reset.")

# ---------------------- HANDLE SEARCH REQUESTS ----------------------

@app.on_message(filters.text & filters.private)
async def handle_search(client, message):
    """Handle movie search requests."""
    # Skip if the message is a command
    if message.text.startswith("/"):
        return

    user_id = message.from_user.id
    if not await force_join(user_id):
        buttons = [[InlineKeyboardButton(f"Join {username}", url=link)] for username, link in zip(CHANNEL_USERNAMES, CHANNEL_LINKS)]
        await message.reply_text(
            "⚠️ 𝙔𝙤𝙪 𝙢𝙪𝙨𝙩 𝙟𝙤𝙞𝙣 𝙩𝙝𝙚 𝙛𝙤𝙡𝙡𝙤𝙬𝙞𝙣𝙜 𝙘𝙝𝙖𝙣𝙣𝙚𝙡𝙨 𝙩𝙤 𝙪𝙨𝙚 𝙩𝙝𝙞𝙨 𝙗𝙤𝙩:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    query = message.text.lower()
    message_id = search_movie_in_file(query)
    if message_id:
        print(f"✅ Movie found for query: {query}")
        # Show data syncing animation
        await show_animation(message, SYNC_FRAMES)
        await message.reply_text("✅ 𝙼𝚘𝚟𝚒𝚎 𝙵𝚘𝚞𝚗𝚍 𝚂𝚎𝚗𝚍𝚒𝚗𝚐...")
        time.sleep(2)  # Prevent rate limits
        # Forward the movie without the forward tag
        try:
            forwarded_message = await client.copy_message(message.chat.id, MOVIE_CHANNEL_USERNAME, int(message_id))
            print(f"✅ Movie forwarded: {message_id}")

            # Notify the user about auto-deletion
            await message.reply_text(
                "⚠️ **Note:** This movie will be deleted in **5 minutes** to avoid copyright claims.\n"
                "Please forward it to your **Saved Messages** folder immediately to avoid losing it."
            )

            # Schedule deletion after 5 minutes
            await asyncio.sleep(300)  # 5 minutes = 300 seconds
            await forwarded_message.delete()
            await message.reply_text("🗑️ The movie has been deleted as part of our copyright protection policy.")
        except Exception as e:
            print(f"❌ Error forwarding movie: {e}")
            await message.reply_text("❌ Sorry, an error occurred while sending the movie.")
    else:
        print(f"❌ No movie found for query: {query}")
        await message.reply_text("❌ Sorry, no movie found with that name. Try another title.")

# ---------------------- RUN THE BOT ----------------------

# Create a Flask app
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running!"

# Start the bot
print("✅ Bot is running...")
app.start()

# Run the web server
if __name__ == "__main__":
    web_app.run(host="0.0.0.0", port=10000)

# Keep the process alive
while True:
    time.sleep(1)
