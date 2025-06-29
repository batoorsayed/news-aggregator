import logging
import os
import re
import sys
from datetime import datetime

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient
from dotenv import load_dotenv
from newsapi import NewsApiClient

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("azure").setLevel(logging.WARNING)

# Keys
load_dotenv()
api_key = os.getenv("NEWSAPI_KEY")
key = os.getenv("LANGUAGE_KEY")
endpoint = os.getenv("LANGUAGE_ENDPOINT")
connection_string = os.getenv("COSMOS_CONNECTION_STRING")

if not [x for x in (api_key, key, endpoint, connection_string) if x is None]:
    pass
else:
    logging.error("Missing API Key")
    sys.exit()

# NewsAPI Init
newsapi = NewsApiClient(api_key)
language = "en"  # Article language

# Azure Cosmos DB Init
client = CosmosClient.from_connection_string(connection_string)  # type: ignore
database = client.get_database_client("naive-gazeta")
container = database.get_container_client("fetched_headlines")  # Change location later


def fetched_headlines(articles):
    """Add timestamp to each article. Send a copy to Cosmos DB"""
    fetched_headlines = {}
    for article in articles:
        url_id = re.sub(r"[^a-zA-Z0-9]", "", article.get("url"))
        if (
            "url" not in article
            or article["url"] is None
            or article["url"].strip() == ""
        ):
            continue
        else:
            fetched_headlines[url_id] = {
                **article,
                "id": url_id,
                "fetched_datetime": datetime.now().isoformat(),
            }
            container.upsert_item(
                fetched_headlines[url_id]
            )  # Piggybacking off the function. Make it separate if needed.
    return fetched_headlines


def azure_transformation(headlines):
    """Transform articles into Azure-compatible document format."""
    documents = []
    for id, article in headlines.items():
        document = {
            "id": article.get("url"),
            "language": article.get("language"),
            "text": "Description: "
            + str(article.get("description"))
            + " | Content: "
            + str(article.get("content")),
        }
        documents.append(document)
    return documents


def main():
    # Fetch latest news headlines from NewsAPI
    try:
        top_headlines = newsapi.get_top_headlines(
            # q="bitcoin", # keywords
            # sources="bbc-news,the-verge",
            # category="business",
            language=language,
            country="us",
            page_size=5,  # Change after
        )
    except Exception as e:
        logging.error(f"NewsAPI call failed: {e}")
        sys.exit()

    # Process and enrich articles with metadata
    try:
        if top_headlines.get("status") != "ok":
            logging.error(
                f"{top_headlines.get('status')}- {top_headlines.get('code')}- {top_headlines.get('message')}"
            )
        else:
            logging.info(
                f"Successfully fetched {top_headlines.get('totalResults')} headlines."
            )
            headlines = fetched_headlines(top_headlines["articles"])
            documents = azure_transformation(headlines=headlines)
    except Exception as e:
        logging.error(f"Document creation failed: {e}")
        sys.exit()

    # Validate we have documents to process
    if len(documents) == 0:
        logging.warning("Document creation returned empty, aborting process.")
        sys.exit()

    # Generate summaries using Azure Text Analytics
    try:
        text_analytics_client = TextAnalyticsClient(endpoint, AzureKeyCredential(key))  # type: ignore
        poller = text_analytics_client.begin_abstract_summary(documents)
        abstract_summary_results = poller.result()
    except Exception as e:
        logging.error(f"Azure text analytics processing failed: {e}")
        sys.exit()

    # Display the generated summaries
    for result in abstract_summary_results:
        if result.kind == "AbstractiveSummarization":
            logging.info("Abstracted Summary:")
            [print(f"{summary.text}\n") for summary in result.summaries]
        elif result.is_error is True:
            logging.error(
                "...Is an error with code '{}' and message '{}'".format(
                    result.error.code, result.error.message
                )
            )


if __name__ == "__main__":
    main()