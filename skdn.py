import discord
import asyncio
import asyncpraw
import nest_asyncio
import os
from dotenv import load_dotenv

load_dotenv()
nest_asyncio.apply()

try:
    token = os.getenv("DISCORD_TOKEN")
    channel_id = int(os.getenv("CHANNEL_ID"))
    subreddit = os.getenv("MONITOR_SUB")
    keywords = os.getenv("KEYWORDS")
    keywords = [k.strip() for k in keywords.split(",")]
except Exception as e:
    print(f"Error loading environment variables: {e}")

welcome_message = os.getenv("ENABLE_WELCOME_MESSAGE", "true")
new_post_limits = int(os.getenv("NEW_POST_LIMITS",10))
check_frequency = int(os.getenv("CHECK_FREQUENCY",60))

reddit = asyncpraw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

# Need to create intents for bot to be able to message
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def check_for_posts():
    sub = await reddit.subreddit(subreddit)
    while True:
        async for submission in sub.new(limit=new_post_limits):
            # Find titles that contain your keywords
            if any(kw in submission.title for kw in keywords):
                message = f"New post found: {submission.title}\n{submission.url}"
                print(message)

                # Send a message to the Discord channel
                channel = client.get_channel(channel_id)
                if channel:
                    await channel.send(message)
                    print(f"Sent notification for: {submission.title}")
                print(f"Rate limit: {reddit.auth.limits}")
                print("")
        await asyncio.sleep(check_frequency)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(
        check_for_posts()
    )
    # Send a welcome message to the Discord channel (optional)
    channel = client.get_channel(channel_id)
    if channel and welcome_message:
        await channel.send("Hello, Discord! I'm now online and monitoring Reddit!")


async def main():
    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())