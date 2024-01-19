# Tweeper-Azure

`Tweeper-Azure` is an automated version of the Tweeper program, deployed as an Azure Function. It's designed to scrape content from Reddit, specifically from the `/r/cybersecurity` subreddit, and share curated news on Twitter. This cloud-based setup allows for continuous, scheduled operation without manual intervention.

## Features

- **Automated Execution in Azure**: Runs as an Azure Function, leveraging serverless architecture for efficiency and scalability.
- **Scrape Top Content**: Automatically pulls top content from the `/r/cybersecurity` subreddit.
- **Twitter Integration**: Posts news updates to Twitter with relevant, context-aware hashtags.
- **Tweet History Tracking**: Maintains a record of tweeted posts to prevent duplication.

## Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/lewiswigmore/tweeper-azure.git
   ```
2. **Navigate to the Project Directory**:
   ```bash
   cd tweeper-azure
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Generate Data Files**
   ```bash
   python setup.py
   ```

## Azure Deployment and Configuration

To deploy and configure `Tweeper-Azure` for operation within the Azure environment, follow these steps:

### 1. Configure Azure Function App
- Set up an Azure Function App with a Python runtime in the Azure portal.

### 2. Deploy the Function
- Deploy the `Tweep` folder as an Azure Function. This can be done through source control integration or direct deployment methods like Azure CLI.

### 3. Configure API Credentials and Settings
- Add Twitter and Reddit API credentials to your Azure Function App configuration.
- Securely store sensitive information like API keys in Azure Key Vault.

### 4. Setup Azure Key Vault
- Navigate to your Azure Key Vault and configure the necessary secrets (API keys and tokens).
- Enable Managed Identity for your Azure Function App and grant it access to the Key Vault:
   - Go to the "Identity" section of your Function App and enable System Assigned Managed Identity.
   - In Key Vault, add a role assignment under "Access control (IAM)" and assign "Key Vault Secrets User" to your function's identity.

### 5. Configure Azure Blob Storage
- Ensure you have an Azure Storage Account with a `tweeper-data` blob container.
- If you have not already, run `setup.py` to generate required data files.
- Upload `hashtags.json` and `tweet_history.json` to this container for hashtag configurations and tweet history tracking.

### 6. Grant Blob Storage Access
- For Blob Storage access, add a role assignment to the managed identity of your Azure Function:
   - In the Azure Portal, navigate to your Storage Account.
   - Under "Access control (IAM)", assign the "Storage Blob Data Contributor" role to your function's identity.

### 7. Schedule Function Execution
- Configure the execution schedule in `function.json` based on your requirements (e.g., every 12 hours).

### 8. Deploy and Test
- After setting up the Azure Function, Key Vault, and Blob Storage, deploy your changes.
- Test the function to ensure it can access Key Vault secrets and read/write to Blob Storage.

Once deployed, `Tweeper-Azure` will automatically execute based on the defined schedule. It will scrape Reddit and post updates to Twitter, operating autonomously within the Azure cloud environment.

## Future Enhancements

- **Additional Content Sources**: Expand to include more sources for a broader range of content.
- **Tweet Formatting and Customisation**: Enhance the appearance and structure of tweets for better engagement.
- **Advanced Hashtag Logic**: Implement more sophisticated hashtag selection based on trending topics and analytics.

## License

This project is licensed under the [MIT License](LICENSE).
