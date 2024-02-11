import tweepy
import praw
import json
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import logging

logging.basicConfig(level=logging.INFO) # Set general logging level to info
logging.getLogger('azure').setLevel(logging.WARNING) # Set logging level for azure sdk to warning

# Replace with your Key Vault URL
kv_url = "your-key-vault-url"

# Function to retrieve secret from Azure Key Vault
def get_key_vault_secret(secret_name):
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=kv_url, credential=credential)
    retrieved_secret = client.get_secret(secret_name)
    return retrieved_secret.value

# Function to initialise Blob Service Client
def initialise_blob_service_client():
    storage_connection_string = get_key_vault_secret('your-storage-connection-string')
    blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
    logging.info('Blob Service Client initialised')
    return blob_service_client

# Function to initialise Twitter Client
def initialise_twitter_client():
    twitter_api_key = get_key_vault_secret('your-twitter-api-key')
    twitter_api_key_secret = get_key_vault_secret('your-twitter-api-key-secret')
    twitter_access_token = get_key_vault_secret('your-twitter-access-token')
    twitter_access_token_secret = get_key_vault_secret('your-twitter-access-token-secret')
    twitter_client = tweepy.Client(
        consumer_key=twitter_api_key,
        consumer_secret=twitter_api_key_secret,
        access_token=twitter_access_token,
        access_token_secret=twitter_access_token_secret
    )
    logging.info('Twitter client initialised')
    return twitter_client

# Function to initialise Reddit Client
def initialise_reddit_client():
    reddit_client_id = get_key_vault_secret('your-reddit-client-id')
    reddit_client_secret = get_key_vault_secret('your-reddit-client-secret')
    reddit = praw.Reddit(client_id=reddit_client_id,
                         client_secret=reddit_client_secret,
                         user_agent='your-reddit-user-agent')
    logging.info('Reddit client initialised')
    return reddit

# Initialise clients
blob_service_client = initialise_blob_service_client()
twitter_client = initialise_twitter_client()
reddit = initialise_reddit_client()

# Function to read blob from Azure Storage
def read_blob(blob_client, container_name, blob_name):
    logging.info(f'Reading blob from container {container_name} with name {blob_name}')
    blob_client = blob_client.get_blob_client(container=container_name, blob=blob_name)
    return blob_client.download_blob().readall()

# Function to write blob to Azure Storage
def write_blob(blob_client, container_name, blob_name, data):
    logging.info(f'Writing blob to container {container_name} with name {blob_name}')
    blob_client = blob_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(data, overwrite=True)

# Function to retrieve top posts from Reddit
def get_top_posts(subreddit, flair, time_filter='year', limit=1):
    logging.info(f'Retrieving top posts from subreddit {subreddit} with flair {flair}')
    top_posts = []
    for submission in reddit.subreddit(subreddit).search(f'flair:"{flair}"', sort='top', time_filter=time_filter, limit=limit):
        top_posts.append((submission.title, submission.url, submission.selftext))
    return top_posts

# Function to tweet posts
def tweet_posts(twitter_client, posts, tweet_history, hashtags):
    logging.info('Preparing to tweet posts')
    for post in posts:
        if process_and_tweet_post(twitter_client, post, tweet_history, hashtags):
            # Update tweet history if tweet was successful
            tweet_history.append(post[0])

# Function to construct tweet content and append hashtags
def construct_tweet_content(title, url, hashtags):
    tweet_hashtags = [hashtags[key] for key in hashtags if key in title.lower()][:2]
    tweet_content = f"{title} {url}"
    if tweet_hashtags:
        tweet_content += " " + " ".join(tweet_hashtags)
    return tweet_content

# Function to process and tweet post
def process_and_tweet_post(twitter_client, post, tweet_history, hashtags):
    title, url, _ = post
    logging.info(f'Processing post: {title}')
    if 'reddit.com' in url:
        logging.info('Skipping Reddit URL post')
        return False
    # Construct tweet content
    tweet_content = construct_tweet_content(title, url, hashtags)
    if len(tweet_content) > 280:
        logging.warning(f'Tweet too long: {title}')
        return False
    # Check if post has already been tweeted
    if title not in tweet_history:
        logging.info(f'Attempting to tweet: {tweet_content}')
        try:
            response = twitter_client.create_tweet(text=tweet_content)
            logging.info(f'Successfully posted tweet: {tweet_content}')
            return True
        except tweepy.errors.TooManyRequests as e:
            handle_rate_limit(e)
        except tweepy.errors.BadRequest as e:
            logging.error(f'Error posting tweet: {e}')
    else:
        logging.info('Post already tweeted')
    return False

# Function to handle rate limit
def handle_rate_limit(exception):
    if 'Rate limit exceeded' in str(exception.reason):
        logging.warning('Rate limit exceeded, skipping this tweet...')
    else:
        logging.warning(f'Error due to rate limit: {exception}')

# Main function
def main(mytimer: func.TimerRequest = None) -> None:
    logging.info('Tweep function started execution')
    try:
        hashtags_blob = read_blob(blob_service_client, 'your-container-name', 'hashtags.json')
        hashtags = json.loads(hashtags_blob)
        tweet_history_blob = read_blob(blob_service_client, 'your-container-name', 'tweet_history.json')
        tweet_history = json.loads(tweet_history_blob)
        
        top_breaches = get_top_posts('cybersecurity', 'News - Breaches & Ransoms')
        top_general = get_top_posts('cybersecurity', 'News - General')

        tweet_posts(twitter_client, top_breaches, tweet_history, hashtags)
        tweet_posts(twitter_client, top_general, tweet_history, hashtags)

        updated_tweet_history = json.dumps(tweet_history)
        write_blob(blob_service_client, 'your-container-name', 'tweet_history.json', updated_tweet_history)
    except Exception as e:
        logging.error(f'An error occurred: {e}')
        raise
    logging.info('Tweep function finished execution')

if __name__ == "__main__":
    main()
