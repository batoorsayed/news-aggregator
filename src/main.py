import datetime
import logging
import os
import sys
import uuid

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
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

# NewsAPI Init
newsapi = NewsApiClient(api_key)
language = "en"


def fetched_headlines(articles):
    """Add unique ID and timestamp to each article."""
    fetched_articles = {}
    for article in articles:
        id = uuid.uuid1()
        fetched_articles[id] = {
            **article,
            "id": id,
            "datetime": datetime.datetime.now(),
        }
    return fetched_articles


def azure_transformation(headlines):
    """Transform articles into Azure-compatible document format."""
    documents = []
    for id, article in headlines.items():
        document = {
            "id": id,
            "language": article.get("language"),
            "text": "Description: "
            + str(article.get("description"))
            + " | Content: "
            + str(article.get("content")),
        }
        documents.append(document)
    return documents


if __name__ == "__main__":
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