# Bitcoin News X Bot

## Overview
This is an automated Twitter/X bot that posts Bitcoin news updates on an hourly schedule. The bot scrapes recent Bitcoin news articles from Alpha Vantage's News Sentiment API, randomly selects an article, generates a tweet using a local LLM (via Ollama), and posts it to Twitter/X.

## Features
- Automatically posts once per hour from 8 AM to 10 PM US Central Time
- Randomly selects Bitcoin news articles for variety
- Uses local LLM models to generate tweet content based on article sentiment
- Detailed logging for monitoring and debugging
- Handles authentication with Twitter/X API v2 using Tweepy

## Requirements
- Python 3.7+
- Ollama server running locally (configured to use port 46007)
- Twitter/X Developer Account with API access
- Alpha Vantage API key

## Dependencies
```
requests
tweepy
schedule
pytz
```

## Installation
1. Clone this repository
2. Install required packages:
   ```
   pip install requests tweepy schedule pytz
   ```
3. Set up environment variables:
   ```
   export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"
   export X_CONSUMER_API_KEY="your_twitter_api_key"
   export X_CONSUMER_API_SECRET="your_twitter_api_secret"
   export X_ACCESS_TOKEN="your_twitter_access_token"
   export X_ACCESS_TOKEN_SECRET="your_twitter_access_token_secret"
   ```

## Configuration
The bot uses the following local LLM models via Ollama:
- deepseek-r1:1.5b (default)
- phi3:latest
- tinyllama:latest

You can adjust the model selection in the script based on your preferences.

## Usage
Simply run the script:
```
python x_bot.py
```

The bot will:
1. Start immediately with an initial post
2. Run every hour on the hour (only between 8 AM and 10 PM Central Time)
3. Print detailed logs of its operations

## How It Works
1. At the scheduled time, the bot fetches recent Bitcoin news from Alpha Vantage API
2. It randomly selects one article from the results
3. It sends the article title, summary, and sentiment to the local Ollama LLM to generate tweet content
4. It cleans the generated content by removing any `<think>` tags
5. It authenticates with the Twitter/X API
6. It posts the generated content as a tweet
7. It logs all steps and results

## Running as a Service
To run this bot continuously, you can set it up as a system service using systemd (Linux) or create a scheduled task (Windows).

### Example systemd service (Linux)
Create a file named `bitcoin-xbot.service` in `/etc/systemd/system/`:

```
[Unit]
Description=Bitcoin News X Bot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/x_bot.py
WorkingDirectory=/path/to/bot/directory
Environment="ALPHA_VANTAGE_API_KEY=your_key"
Environment="X_CONSUMER_API_KEY=your_key"
Environment="X_CONSUMER_API_SECRET=your_secret"
Environment="X_ACCESS_TOKEN=your_token"
Environment="X_ACCESS_TOKEN_SECRET=your_token_secret"
Restart=always
User=yourusername

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:
```
sudo systemctl enable bitcoin-xbot
sudo systemctl start bitcoin-xbot
```

## Logging
The bot includes extensive print statements to help debug and monitor its operation. For production use, you might want to modify the script to write to a log file instead.

## License
MIT

## Disclaimer
This bot is for educational and personal use. Be sure to comply with Twitter/X's Terms of Service and API usage guidelines. The content posted by this bot is generated automatically and may not always be accurate or appropriate - use at your own risk.
