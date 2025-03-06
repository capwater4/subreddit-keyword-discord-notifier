# Subreddit Scanner Discord Bot

A discord bot that monitors a subreddit of your choosing and messages a discord channel whenever a new post with your keywords is found. Uses free OAUTH Reddit API token and asyncio with your own discord bot.

## Setup

1. Create an app -> script at https://old.reddit.com/prefs/apps to get your API Key and Client
   * ```Client_ID``` is under "personal use script", ```Client_Secret``` = secret
2. Register for the reddit api at https://support.reddithelp.com/hc/en-us/requests/new?ticket_form_id=14868593862164
   * Choose "I'm a developer" and "I want to register to use the free tier of the Reddit API"
3. Create a discord channel and right click it to copy the ```Channel_ID```
   * If you don't see the copy channel id option, you need to enable dev mode in discord
4. Create a discord bot and add to your channel with message privileges and message content intentions
   * https://discord.com/developers/applications > new application
   * Copy your token ```discord_token``` or generate/copy a new one in the bot menu
   * Navigate to bot > priveleged gateway intents and check Message Content Intent
   * Then go to OAuth2 > URL generator select bot scope > bot permissions send messages > guild install
   * Paste your generated URL and add your bot to your server. Make sure it can access your designated channel
  
_Steps 1 and 2 are done together- you need the Oauth2 from step 1 to register for API usage in step 2_
## Environment
These are the variables you will need to run the script:
```yml
    environment:
      - DISCORD_TOKEN=yourtoken
      - REDDIT_CLIENT_ID=yourid
      - REDDIT_CLIENT_SECRET=yoursecret
      - REDDIT_USER_AGENT="User-Agent:subreddit keyword scanner by u/your_username"
      - CHANNEL_ID=yourid
      - MONITOR_SUB="subreddit" #no r/, just the name
      - KEYWORDS="list, of, keywords"
      - ENABLE_WELCOME_MESSAGE=true #Sends a monitoring description to Discord on start
      - NEW_POST_LIMIT=10 #specifies the # of new posts that are 
      - CHECK_FREQUENCY=60 #controls how often the script checks your subreddit
```
Welcome message, post limit and check frequency are optional and will default to the values shown above. You may need to adjust these based on how active the subreddit is. Either use .env or fill these out in docker compose, not both. 

## Installation
Clone the repo or download the zip. There are 3 ways of running the script:
- Using docker compose (recommended)
- Building docker locally
- Running the python script locally

### Docker Compose
Run the above compose file and fill in the environment variables. That's it!

### Building Docker Locally
Download all files above into 1 directory and build locally after filling out .env. 

### Python Script
Uses python 3.9, probably compatible with other versions. Fill out .env within the same directory.

## Usage
* By deafult, every 60 seconds the script will check the 10 most recent posts from your subreddit for keywords
* When it finds a matching post, your discord bot will post the title + URL for the post
* Create a new instance/container of the script for every additional subreddit you want to monitor

The script stays well below Reddit's 100 calls per minute free tier and you can see your usage within the container logs. It continuously checks your remaining calls limit and will timeout if you hit the limit. 

Posts sent to discord will be stored and "expired" every week so that duplicates are not sent if the same post is scanned twice.

If you have any questions/suggestions or just need some help using the bot, you can raise an issue or message me on reddit at u/Resolute_Pecan.
