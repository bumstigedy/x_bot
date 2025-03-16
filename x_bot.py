import requests
import json
import os
from datetime import datetime, timezone, timedelta
import tweepy
from urllib.parse import parse_qs, urlparse
#
def write_url():

    # Get current UTC time
    current_time = datetime.now(timezone.utc)

    # Subtract 1 hour
    time_one_hour_ago = current_time - timedelta(hours=1)

    # Format the time as required by Alpha Vantage API (YYYYMMDDTHHMM)
    time_from = time_one_hour_ago.strftime('%Y%m%dT%H%M')

    # Construct the URL with dynamic time_from
    return f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=CRYPTO:BTC&time_from={time_from}&limit=10&apikey=key"
url=write_url()

#retrieve secrets
key=os.getenv("ALPHA_VANTAGE_API_KEY")
API_KEY = os.getenv("X_CONSUMER_API_KEY")
API_SECRET = os.getenv("X_CONSUMER_API_SECRET")
ACCESS_TOKEN=os.getenv("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET=os.getenv("X_ACCESS_TOKEN_SECRET")

# current local models downloaded
models = {
"deepseek":"deepseek-r1:1.5b",
"phi":"phi3:latest",
"tinyllama":"tinyllama:latest" 
}
#focused on bitcoin
url="https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=CRYPTO:BTC&time_from=20250314T0130&limit=10&apikey=key"
#
def get_top_article_info(feed):
    # Helper function to compute Bitcoin score for an article
    def get_btc_score(article):
        for ts in article['ticker_sentiment']:
            if ts['ticker'] == 'CRYPTO:BTC':
                return (ts['relevance_score'], ts['ticker_sentiment_score'])
        return (0, 0)  # Default score if Bitcoin is not mentioned
    
    # Check if feed is empty
    if not feed:
        return None  # Return None if there are no articles
    
    # Select the top article based on Bitcoin score
    top_article = max(feed, key=get_btc_score)
    
    # Return the required elements in a dictionary
    return {
        'title': top_article['title'],
        'summary': top_article['summary'],
        'overall_sentiment_label': top_article['overall_sentiment_label'],
        'ticker':top_article['ticker_sentiment'][0]['ticker']
    }
#
def get_top_post(url):
    r = requests.get(url)
    _data = r.json()
    feed = _data["feed"]
    return get_top_article_info(feed)
#
def extract_outside_think(text):
    """
    Extracts text outside of <think> and </think> tags.
    """
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
#
def analyze_text_with_ollama(title, summary, ticker, sentiment, model=models['deepseek']):
    url = "http://10.0.0.20:46007/api/generate"  # Default Ollama API endpoint
    payload = {
        "model": model,
        "prompt": f"""Write a tweet based on the following information and include hash tags:
        <title> {title}, <summary> {summary}, ticker: {ticker}.  Use a {sentiment} tone.  """,
        "stream": False
    }
    response = requests.post(url, json=payload)
        
    if response.status_code == 200:
        result = response.json()
        return result["response"]  # Adjust based on Ollama's response structure
    else:
        return "Error: Could not analyze text"
    #
top_post=get_top_post(url)
#
llm_result=analyze_text_with_ollama(top_post["title"], top_post["summary"], top_post["ticker"],top_post['overall_sentiment_label'], model=models['deepseek'])
x_post = extract_outside_think(llm_result).strip('\'"')
#
print("----------------->X Post <-------------")
print(x_post)

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
    print("Authenticated as:", user["username"])
except tweepy.TweepyException as e:
    print("Authentication error:", str(e))
    exit()

# Post a tweet
try:
    response = client.create_tweet(text=x_post)
    print("Tweet posted successfully! Tweet ID:", response.data["id"])
except tweepy.TweepyException as e:
    print("Error posting tweet:", str(e))     