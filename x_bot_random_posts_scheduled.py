import requests
import json
import os
import random
import time
import schedule
from datetime import datetime, timezone, timedelta
import tweepy
from urllib.parse import parse_qs, urlparse
import pytz

def write_url():
    # Get current UTC time
    current_time = datetime.now(timezone.utc)
    print(f"Current UTC time: {current_time}")

    # Subtract 1 hour
    time_one_hour_ago = current_time - timedelta(hours=4)
    print(f"Looking for articles from the past hour (since {time_one_hour_ago})")

    # Format the time as required by Alpha Vantage API (YYYYMMDDTHHMM)
    time_from = time_one_hour_ago.strftime('%Y%m%dT%H%M')

    # Construct the URL with dynamic time_from
    api_url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=CRYPTO:BTC&time_from={time_from}&limit=10&apikey=key"
    print(f"API URL generated: {api_url}")
    return api_url

# Retrieve secrets
key = os.getenv("ALPHA_VANTAGE_API_KEY")
API_KEY = os.getenv("X_CONSUMER_API_KEY")
API_SECRET = os.getenv("X_CONSUMER_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")

# Current local models downloaded
models = {
    "deepseek": "deepseek-r1:1.5b",
    "phi": "phi3:latest",
    "tinyllama": "tinyllama:latest"
}

def get_random_article_info(feed):
    print(f"Processing feed with {len(feed)} articles")
    
    # Check if feed is empty
    if not feed:
        print("Warning: Feed is empty, no articles found")
        return None  # Return None if there are no articles
    
    # Select a random article from the feed
    random_article = random.choice(feed)
    print(f"Randomly selected article: '{random_article['title']}'")
    
    # Find the Bitcoin ticker sentiment, if available
    btc_sentiment = None
    for ts in random_article['ticker_sentiment']:
        if ts['ticker'] == 'CRYPTO:BTC':
            btc_sentiment = ts
            print(f"Found BTC sentiment: relevance={ts['relevance_score']}, sentiment={ts['ticker_sentiment_score']}")
            break
    
    # If no Bitcoin ticker sentiment is found, use the first ticker sentiment
    ticker_data = btc_sentiment if btc_sentiment else random_article['ticker_sentiment'][0]
    print(f"Using ticker: {ticker_data['ticker']}")
    
    # Return the required elements in a dictionary
    return {
        'title': random_article['title'],
        'summary': random_article['summary'],
        'overall_sentiment_label': random_article['overall_sentiment_label'],
        'ticker': ticker_data['ticker']
    }

def get_random_post(url):
    print("Fetching data from Alpha Vantage API...")
    r = requests.get(url)
    _data = r.json()
    
    if "feed" not in _data:
        print(f"Error: 'feed' not found in API response. Response: {_data}")
        return None
        
    feed = _data["feed"]
    return get_random_article_info(feed)

def extract_outside_think(text):
    """
    Extracts text outside of <think> and </think> tags.
    """
    print("Extracting content outside <think> tags")
    start_tag = "<think>"
    end_tag = "</think>"
    result = ""
    current_pos = 0
    
    while True:
        # Find the start of a <think> tag
        start_index = text.find(start_tag, current_pos)
        if start_index == -1:  # No more <think> tags found
            result += text[current_pos:]  # Add the remaining text
            break
        
        # Add text before the <think> tag
        result += text[current_pos:start_index]
        
        # Find the end of the <think> tag
        end_index = text.find(end_tag, start_index)
        if end_index == -1:  # No closing tag (malformed response)
            result += text[current_pos:]  # Add the rest and stop
            break
        
        # Move the current position past the </think> tag
        current_pos = end_index + len(end_tag)
    
    return result

def analyze_text_with_ollama(title, summary, ticker, sentiment, model=models['deepseek']):
    print(f"Analyzing text with Ollama model: {model}")
    url = "http://10.0.0.20:46007/api/generate"  # Default Ollama API endpoint
    payload = {
        "model": model,
        "prompt": f"""Write a tweet based on the following information and include hash tags:
        <title> {title}, <summary> {summary}, ticker: {ticker}.  Use a {sentiment} tone. Respond with only the tweet text, no extra commentary, 
        within 280 characters. """,
        "stream": False
    }
    print("Sending request to Ollama...")
    response = requests.post(url, json=payload)
        
    if response.status_code == 200:
        print("Successfully received response from Ollama")
        result = response.json()
        return result["response"]  # Adjust based on Ollama's response structure
    else:
        print(f"Error: Could not analyze text. Status code: {response.status_code}")
        return "Error: Could not analyze text"

def post_to_x(x_post):
    print("Authenticating with X API...")
    # Authenticate with the X API (v2)
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )

    # Test authentication
    try:
        user = client.get_me().data
        print(f"Authenticated as: {user['username']}")
    except tweepy.TweepyException as e:
        print(f"Authentication error: {str(e)}")
        return False

    # Post a tweet
    try:
        print("Posting tweet to X...")
        response = client.create_tweet(text=x_post)
        print(f"Tweet posted successfully! Tweet ID: {response.data['id']}")
        return True
    except tweepy.TweepyException as e:
        print(f"Error posting tweet: {str(e)}")
        return False

def job():
    print("\n" + "="*50)
    print(f"Job started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if current time is within operating hours
    central = pytz.timezone('US/Central')
    now = datetime.now(central)
    
    # Only run between 8 AM and 10 PM Central time
    if now.hour < 8 or now.hour >= 22:
        print(f"Outside operating hours (8 AM - 10 PM US Central). Current time: {now.strftime('%H:%M:%S')}. Skipping.")
        return
    
    print(f"Running job at {now.strftime('%H:%M:%S')} US Central Time")
    
    try:
        # Generate the URL with current time parameters
        url = write_url()
        
        # Get a random post from the feed
        random_post = get_random_post(url)
        
        if not random_post:
            print("No posts available. Skipping this run.")
            return
            
        print(f"Selected article: '{random_post['title']}'")
        print(f"Sentiment: {random_post['overall_sentiment_label']}")
        
        # Generate tweet content using LLM
        llm_result = analyze_text_with_ollama(
            random_post["title"], 
            random_post["summary"], 
            random_post["ticker"],
            random_post['overall_sentiment_label'], 
            model=models['deepseek']
        )
        
        x_post = extract_outside_think(llm_result).strip('\'"')
        
        print("="*20 + "> X Post <" + "="*20)
        print(x_post)
        print("="*50)
        
        # Post to X
        post_to_x(x_post)
        
    except Exception as e:
        print(f"Error in job: {str(e)}")
    
    print(f"Job completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")

def main():
    print("Starting X Bot with hourly schedule (8 AM - 10 PM US Central Time)")
    
    # Schedule the job to run every hour
    schedule.every().hour.at(":00").do(job)
    
    # Run the job once at startup
    print("Running initial job at startup...")
    job()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()