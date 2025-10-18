import discord
import asyncio
import asyncpraw
import nest_asyncio
import os
import logging
from dotenv import load_dotenv


if os.path.exists("/.dockerenv"):
    log_dir = "/app/logs"
else:
    log_dir = "./logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(f"{log_dir}/skdn.log"),
        logging.StreamHandler(),
    ],
)

nest_asyncio.apply()
load_dotenv()

try:
    token = os.getenv("DISCORD_TOKEN")
    channel_id = int(os.getenv("CHANNEL_ID"))
    subreddit = os.getenv("MONITOR_SUB")
    keywords = os.getenv("KEYWORDS")
    keywords = [k.strip() for k in keywords.split(",")]
    logging.info(f"Loaded keywords: {keywords}")
except Exception as e:
    logging.error(f"Error loading environment variables: {e}")

welcome_message = os.getenv("ENABLE_WELCOME_MESSAGE", "true")
new_post_limits = int(os.getenv("NEW_POST_LIMITS", 10))
check_frequency = int(os.getenv("CHECK_FREQUENCY", 60))

reddit = asyncpraw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


async def check_for_posts():
    sub = await reddit.subreddit(subreddit)
    logging.info(f"Monitoring subreddit: {subreddit}")
    seen_post_ids = set()
    while True:
        logging.info("--- Begin polling cycle ---")
        found = False
        async for submission in sub.new(limit=new_post_limits):
            if submission.id in seen_post_ids:
                continue
            title_lower = submission.title.lower()
            if any(kw.lower() in title_lower for kw in keywords):
                message = f"New post found: {submission.title}\n{submission.url}"
                logging.info(message)
                channel = client.get_channel(channel_id)
                if channel:
                    try:
                        await channel.send(message)
                        logging.info(f"Sent notification for: {submission.title}")
                    except Exception as e:
                        logging.error(f"Failed to send Discord message: {e}")
                else:
                    logging.warning(f"Discord channel {channel_id} not found.")
                found = True
            seen_post_ids.add(submission.id)
        if not found:
            logging.info("No matching posts found in this cycle.")
        await asyncio.sleep(check_frequency)


@client.event
async def on_ready():
    logging.info(f"Logged in as {client.user}")
    client.loop.create_task(check_for_posts())
    channel = client.get_channel(channel_id)
    if channel and welcome_message.lower() == "true":
        try:
            await channel.send(
                f"Monitoring {subreddit} for keywords: {', '.join(keywords)}"
            )
            logging.info("Sent welcome message.")
        except Exception as e:
            logging.error(f"Failed to send welcome message: {e}")


async def main():
    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())
