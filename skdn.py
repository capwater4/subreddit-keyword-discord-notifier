import discord
import asyncio
import asyncpraw
import nest_asyncio
import os
import json
from dotenv import load_dotenv
import time
from datetime import datetime

# Apply nest_asyncio if needed
nest_asyncio.apply()

# Environment setup
if os.getenv("ENVIRONMENT") == "local":
    load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MONITOR_SUB = os.getenv("MONITOR_SUB").strip('"').lower()
KEYWORDS = os.getenv("KEYWORDS").strip('"')
ENABLE_WELCOME_MESSAGE = (
    os.getenv("ENABLE_WELCOME_MESSAGE", "true").strip().lower() == "true"
)
NEW_POST_COUNT = int(os.getenv("NEW_POST_LIMIT", 15))
CHECK_FREQUENCY = int(os.getenv("CHECK_FREQUENCY", 30))

# Process keywords
keywords_list = [keyword.strip().lower() for keyword in KEYWORDS.split(",")]

# Reddit client setup
reddit = asyncpraw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# Discord client setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Persistent storage setup
STORAGE_DIR = "/post/log"
STORAGE_FILE = os.path.join(STORAGE_DIR, "sent_posts.json")
SENT_POSTS = {}
EXPIRATION_DAYS = 7  # Keep posts for 1 week


def ensure_storage_dir():
    """Ensure the storage directory exists"""
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)
        print(f"Created storage directory: {STORAGE_DIR}")


def load_sent_posts():
    """Load sent posts from JSON file"""
    global SENT_POSTS
    try:
        ensure_storage_dir()
        if os.path.exists(STORAGE_FILE):
            with open(STORAGE_FILE, "r") as f:
                SENT_POSTS = json.load(f)
                # Convert string timestamps back to float
                SENT_POSTS = {k: float(v) for k, v in SENT_POSTS.items()}
        print(f"Loaded {len(SENT_POSTS)} sent posts from storage")
    except Exception as e:
        print(f"Error loading sent posts: {e}")
        SENT_POSTS = {}


def save_sent_posts():
    """Save sent posts to JSON file"""
    try:
        ensure_storage_dir()
        with open(STORAGE_FILE, "w") as f:
            json.dump(SENT_POSTS, f)
        print(f"Saved {len(SENT_POSTS)} sent posts to storage")
    except Exception as e:
        print(f"Error saving sent posts: {e}")


async def clean_expired_posts():
    """Periodically clean up expired posts"""
    while True:
        current_time = time.time()
        expired = [
            pid
            for pid, ts in SENT_POSTS.items()
            if current_time - ts > EXPIRATION_DAYS * 86400
        ]
        for pid in expired:
            del SENT_POSTS[pid]
        if expired:
            print(f"Cleaned {len(expired)} expired posts")
            save_sent_posts()
        await asyncio.sleep(3600)  # Clean every hour


async def check_keywords_notify():
    """Check for new posts and notify Discord"""
    subreddit = await reddit.subreddit(MONITOR_SUB)
    while True:
        try:
            # Check new posts
            async for submission in subreddit.new(limit=NEW_POST_COUNT):
                title_lower = submission.title.lower()

                # Skip if already sent or doesn't match keywords
                if submission.id in SENT_POSTS:
                    continue

                if not any(keyword in title_lower for keyword in keywords_list):
                    continue

                # Prepare and send message
                message = f"New post: {submission.title}\n{submission.url}"
                print(f"Processing: {message}")

                channel = client.get_channel(CHANNEL_ID)
                if channel:
                    try:
                        await channel.send(message)
                        SENT_POSTS[submission.id] = time.time()
                        print(f"Sent notification for: {submission.title}")
                        save_sent_posts()  # Save after each new post
                    except Exception as e:
                        print(f"Discord send error: {e}")

                # Small delay to avoid rate limits
                await asyncio.sleep(1)

            # Check rate limits
            try:
                limits = await reddit.auth.limits()
                if limits["remaining"] < 5:
                    sleep_time = max(0, limits["reset_timestamp"] - time.time()) + 2
                    print(f"Rate limit approaching, sleeping {sleep_time:.1f}s")
                    await asyncio.sleep(sleep_time)
            except Exception as e:
                print(f"Rate limit check error: {e}")

        except Exception as e:
            print(f"Main loop error: {e}")
            await asyncio.sleep(60)

        await asyncio.sleep(CHECK_FREQUENCY)


@client.event
async def on_ready():
    """Handle bot startup"""
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print(f"Monitoring r/{MONITOR_SUB} for: {', '.join(keywords_list)}")

    # Load previous sent posts
    load_sent_posts()

    # Start tasks
    client.loop.create_task(check_keywords_notify())
    client.loop.create_task(clean_expired_posts())

    # Send welcome message
    if ENABLE_WELCOME_MESSAGE:
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(
                f"Bot restarted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Monitoring r/{MONITOR_SUB} for: {', '.join(keywords_list)}\n"
                f"Loaded {len(SENT_POSTS)} previously sent posts"
            )


@client.event
async def on_disconnect():
    """Handle bot shutdown"""
    print("Bot disconnecting, saving sent posts...")
    save_sent_posts()


async def main():
    """Main entry point"""
    try:
        await client.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\nBot shutting down...")
        save_sent_posts()
    except Exception as e:
        print(f"Fatal error: {e}")
        save_sent_posts()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
