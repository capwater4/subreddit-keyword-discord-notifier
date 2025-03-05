import discord
import asyncio
import asyncpraw
import nest_asyncio
import os
from dotenv import load_dotenv
import time

# This is important... for something
nest_asyncio.apply()

# Checking to see if env is local or via docker
if os.getenv("ENVIRONMENT") == "local":
    load_dotenv()

# Getting variables from docker-compose.yml
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MONITOR_SUB = os.getenv("MONITOR_SUB").strip('"')
KEYWORDS = os.getenv("KEYWORDS").strip('"')
ENABLE_WELCOME_MESSAGE = (
    os.getenv("ENABLE_WELCOME_MESSAGE", "true").strip().lower() == "true"
)
NEW_POST_COUNT = int(os.getenv("NEW_POST_COUNT", 10))
CHECK_FREQUENCY = int(os.getenv("CHECK_FREQUENCY", 60))

# Split KEYWORDS string into a list, removing any whitespaces
keywords_list = [keyword.strip() for keyword in KEYWORDS.split(",")]

# Reddit API credentials and Async PRAW setup
reddit = asyncpraw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# Intents needed to start discord client
intents = discord.Intents.default()
intents.message_content = True  # Ensure the bot can read message content

# Create a client instance of the bot
client = discord.Client(intents=intents)

# Limit to the most recent posts (e.g., 100 posts)
MAX_HISTORY_SIZE = 100

# Dictionary to hold post IDs and their timestamp
sent_posts = {}

# Expiration time for posts in seconds (1 week in this case)
expiration_time = 604800  # 1 week in seconds


async def clean_expired_posts():
    """Periodically clean up expired posts from `sent_posts`."""
    while True:
        current_time = time.time()
        # Remove posts older than expiration_time (e.g., 1 week)
        for post_id, timestamp in list(sent_posts.items()):
            if current_time - timestamp > expiration_time:
                del sent_posts[post_id]
        print("Expired posts cleaned.")
        await asyncio.sleep(3600)  # Check expired posts every hour


async def check_keywords_notify():
    subreddit = await reddit.subreddit(MONITOR_SUB)
    while True:
        # Check the 10 most recent posts
        async for submission in subreddit.new(limit=NEW_POST_COUNT):
            # If the title contains any of the keywords and this post hasn't been sent yet
            if any(
                keyword.lower() in submission.title.lower() for keyword in keywords_list
            ):
                if submission.id not in sent_posts:
                    print("")
                    message = f"New post found: {submission.title}\n{submission.url}"
                    print(message)

                    # Send the post title to the Discord channel, print API usage
                    channel = client.get_channel(CHANNEL_ID)
                    if channel:
                        await channel.send(message)

                    # Add post to sent_posts with current timestamp
                    sent_posts[submission.id] = time.time()

                    print(f"Sent notification for: {submission.title}")
                    print(f"Rate limit: {reddit.auth.limits}")

                    # Check rate limits and wait if necessary
                    if reddit.auth.limits["remaining"] == 0:
                        reset_time = reddit.auth.limits["reset_timestamp"]
                        await asyncio.sleep(max(0, reset_time - time.time()))

        # Sleep for the check frequency (e.g., 60 seconds)
        await asyncio.sleep(CHECK_FREQUENCY)


@client.event
async def on_ready():
    # This function will be called when the bot has connected to Discord
    print(f"Logged in as {client.user}")

    # Start the Reddit post-checking task
    client.loop.create_task(
        check_keywords_notify()
    )  # Add the Reddit checking task to the event loop

    # Start the task to clean expired posts every hour
    client.loop.create_task(clean_expired_posts())

    # Send a welcome message to the Discord channel
    channel = client.get_channel(CHANNEL_ID)
    if channel and ENABLE_WELCOME_MESSAGE:
        await channel.send(
            f"Monitoring the r/{MONITOR_SUB} subreddit for {KEYWORDS} keywords"
        )


# Manually run the bot's event loop
async def main():
    await client.start(DISCORD_TOKEN)


# Use asyncio to run the main function
if __name__ == "__main__":
    asyncio.run(main())
