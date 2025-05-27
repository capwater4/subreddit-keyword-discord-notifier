import discord
import asyncio
import asyncpraw
import nest_asyncio
import os
from dotenv import load_dotenv

load_dotenv()
nest_asyncio.apply()

TOKEN = os.getenv('TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
SUBREDDIT = os.getenv('SUBREDDIT')

# Reddit API credentials and Async PRAW setup
reddit = asyncpraw.Reddit(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    user_agent=os.getenv('USER_AGENT')
)

# Create intents to specify what events your bot needs
intents = discord.Intents.default()
intents.message_content = True  # Ensure the bot can read message content
client = discord.Client(intents=intents)

async def check_for_posts():
    subreddit = await reddit.subreddit(subreddit)  # Move inside the async function
    while True:
        # Ensure subreddit.new() is awaited properly and the async generator is iterated over
        async for submission in subreddit.new(limit=10):  # Adjust the limit if needed
            if "[H]" in submission.title:
                message = f"New post found: {submission.title}\n{submission.url}"
                print(message)  # This will print the message to the console
                
                # Send a message to the Discord channel
                channel = client.get_channel(CHANNEL_ID)
                if channel:
                    await channel.send(message)
                    print(f"Sent notification for: {submission.title}")
            print(f"Rate limit: {reddit.auth.limits}")
        await asyncio.sleep(60)  # Check every 60 seconds

@client.event
async def on_ready():
    # This function will be called when the bot has connected to Discord
    print(f'Logged in as {client.user}')

    # Start the Reddit post-checking task
    client.loop.create_task(check_for_posts())  # Add the Reddit checking task to the event loop

    # Send a welcome message to the Discord channel (optional)
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("Hello, Discord! I'm now online and monitoring Reddit!")

# Manually run the bot's event loop
async def main():
    await client.start(TOKEN)

# Use asyncio to run the main function
if __name__ == '__main__':
    asyncio.run(main())