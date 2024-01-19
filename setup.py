import json
import os

# Setup script to generate data files
try:
    # Get the path to the Downloads folder
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")

    # Create the tweeter-data folder in the Downloads folder if it does not exist
    data_folder = os.path.join(downloads_folder, "tweeter-data")
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)
        print(f"\nCreated tweeter-data folder in {downloads_folder}")

    # Generate tweet_history.json with an empty array
    tweet_history_path = os.path.join(data_folder, "tweet_history.json")
    if not os.path.exists(tweet_history_path):
        tweet_history = []
        with open(tweet_history_path, "w") as file:
            json.dump(tweet_history, file)
            print(f"Created tweet_history.json in {data_folder}")

    # Generate hashtags.json with default hashtags
    hashtags_path = os.path.join(data_folder, "hashtags.json")
    if not os.path.exists(hashtags_path):
        hashtags = {
            "malware": "#Malware",
            "hacking": "#Hacking",
            "privacy": "#Privacy"
        }
        with open(hashtags_path, "w") as file:
            json.dump(hashtags, file)
            print(f"Created hashtags.json in {data_folder}")
    
    # Delete setup.py
    os.remove(__file__)
    print(f"\nFiles generated successfully in {data_folder}. Setup script has been deleted to prevent conflicts in Azure Functions.\n")

except Exception as e:
    print(f"An error occurred: {e}")
