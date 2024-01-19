import tweepy
import praw
import json
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import logging

logging.basicConfig(level=logging.INFO) # Set logging level to INFO

# Function to get secrets from Azure Key Vault
def get_key_vault_secret(secret_name):
    kv_url = "your-key-vault-url"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=kv_url, credential=credential)
    retrieved_secret = client.get_secret(secret_name)
    return retrieved_secret.value

# Initialize Blob Service Client
storage_connection_string = get_key_vault_secret('your-storage-connection-string')
blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)

# Twitter API initialisation
twitter_api_key = get_key_vault_secret('your-twitter-api-key')
twitter_api_key_secret = get_key_vault_secret('your-twitter-api-key-secret')
twitter_access_token = get_key_vault_secret('your-twitter-access-token')
twitter_access_token_secret = get_key_vault_secret('your-twitter-access-token-secret')

# Initialise Tweepy Client with OAuth 1.0a User Context
twitter_client = tweepy.Client(
    consumer_key=twitter_api_key,
    consumer_secret=twitter_api_key_secret,
    access_token=twitter_access_token,
    access_token_secret=twitter_access_token_secret
)

# Reddit API initialisation
reddit_client_id = get_key_vault_secret('reddit-client-id')
reddit_client_secret = get_key_vault_secret('reddit-client-secret')
logging.info('Retrieved reddit client secret from key vault')
reddit_user_agent = 'your-reddit-user-agent'

reddit = praw.Reddit(client_id=reddit_client_id,
                     client_secret=reddit_client_secret,
                     user_agent=reddit_user_agent)
logging.info('Initialized Reddit client')

# Functions to read and write blobs
def read_blob(container_name, blob_name):
    logging.info(f'Reading blob from container {container_name} with name {blob_name}')
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    return blob_client.download_blob().readall()

def write_blob(container_name, blob_name, data):
    logging.info(f'Writing blob to container {container_name} with name {blob_name}')
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(data, overwrite=True)

# Reading hashtags.json from Blob Storage
hashtags_blob = read_blob('tweeper-data', 'hashtags.json')
hashtags = json.loads(hashtags_blob)
logging.info('Loaded hashtags from blob storage')

# Reading and Writing tweet_history.json from Blob Storage
try:
    tweet_history_blob = read_blob('tweeper-data', 'tweet_history.json')
    tweet_history = json.loads(tweet_history_blob)
    logging.info('Loaded tweet history from blob storage')
except Exception as e:
    tweet_history = []
    logging.error(f'An error occurred while loading tweet history: {e}')


# Function to fetch top posts from Reddit
def get_top_posts(subreddit, flair, time_filter='day', limit=1):
    logging.info(f'Top posts retrived from Reddit for subreddit {subreddit} with flair {flair}')
    top_posts = []
    for submission in reddit.subreddit(subreddit).search(f'flair:"{flair}"', sort='top', time_filter=time_filter, limit=limit):
        top_posts.append((submission.title, submission.url, submission.selftext))
    return top_posts

def tweet_posts(posts, tweet_history):
    # Load tweet history
    logging.info('Starting to tweet posts')
    for post in posts:
        title, url, selftext = post
        logging.info(f'Processing post: {title}')
        # If the URL is a Reddit URL, replace it with the selftext
        if 'reddit.com' in url:
            url = selftext
            logging.info('Replaced Reddit URL with selftext')

        tweet = f"{title} {url}"

        # Hashtag collection
        tweet_hashtags = [hashtags[key] for key in hashtags if key in title.lower()]
        tweet_hashtags = tweet_hashtags[:3]  # Limit to max 3 hashtags
        logging.info(f'Collected hashtags for post: {tweet_hashtags}')

        if tweet_hashtags:
            tweet += " " + " ".join(tweet_hashtags)
        logging.info(f'Collected hashtags for post: {tweet_hashtags}') 
        
        if tweet not in tweet_history:
            # Post tweet
            logging.info(f"Attempting to post tweet: {tweet}")
            try:
                response = twitter_client.create_tweet(text=tweet)
                logging.info(f'Successfully posted tweet: {tweet}')
                # Add tweet to history after successful posting
                tweet_history.append(tweet)
            except tweepy.errors.Forbidden:
                logging.error(f'Failed to post tweet: {tweet}')
                continue

    # Write updated tweet history to blob storage
    if tweet_history:
        updated_tweet_history = json.dumps(tweet_history)
        write_blob('tweeper-data', 'tweet_history.json', updated_tweet_history)
        logging.info('Updated tweet history written to blob storage')

def main(mytimer: func.TimerRequest = None) -> None:
    logging.info('Tweep function started execution')
    try:
        # Fetching top posts
        logging.info('Fetching top posts')
        top_breaches = get_top_posts('cybersecurity', 'News - Breaches & Ransoms')
        top_general = get_top_posts('cybersecurity', 'News - General')

        # Tweeting posts
        logging.info('Tweeting posts')
        tweet_posts(top_breaches, tweet_history)
        tweet_posts(top_general, tweet_history)

    except Exception as e:
        logging.error(f'An error occurred: {e}')
        raise
    logging.info('Tweep function finished execution')

if __name__ == "__main__":
    main()
