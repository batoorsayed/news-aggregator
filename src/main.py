import logging
import os
import re
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


def enrich_articles(articles):
    """Add timestamp and create id using url to each article."""
    fetched_headlines = {}
    for article in articles:
        url_id = re.sub(r"[^a-zA-Z0-9]", "", article.get("url"))
        if (
            "url" not in article
            or article["url"] is None
            or article["url"].strip() == ""
        ):
            logging.debug("Missing url, article skipped.")
            continue
        else:
            fetched_headlines[url_id] = {
                **article,
                "id": url_id,
                "fetched_datetime": datetime.now().isoformat(),
            }
    return fetched_headlines


def azure_transformation(headlines):
    """Transform articles into Azure-compatible document format."""
    documents = []
    for article_id, article in headlines.items():
        document = {
            "id": article.get("id"),
            "language": article.get("language"),
            "text": "Description: "
            + str(article.get("description"))
            + " | Content: "
            + str(article.get("content")),
        }
        documents.append(document)
    return documents


# For now individual upsert is good enough. I'm not sending thousands of articles per second. What am I, Jeff Bezos?
def save_fetched_articles_to_cosmos(container, fetched_articles):
    """Save or update fetched articles (after adding id and fetched_date) to Cosmos NoSQL DB"""
    for article_id in fetched_articles:
        container.upsert_item(fetched_articles[article_id])

# Store output from Azure Summary to DB
def save_summary_output_to_cosmos(container, summary_output):
    for result in summary_output:
        if result.is_error:
            summary_data = {
                "id": result.id,
                "is_error": result.is_error,
                "kind": result.kind,
                "error_code": result.error.code,
                "error_message": result.error.message,
            }
        else:
            summary_data = {
                "id": result.id,
                "is_error": result.is_error,
                "kind": result.kind,
                "summaries": [summary.text for summary in result.summaries],
                "warnings": [
                    {"code": warning.code, "message": warning.message}
                    for warning in result.warnings
                ],
            }
        container.upsert_item(summary_data)

def main():
    # Keys
    # Only load .env file if running locally
    if os.getenv("AZURE_FUNCTIONS_ENVIRONMENT") is None:
        load_dotenv()
    api_key = os.getenv("NEWSAPI_KEY")
    key = os.getenv("LANGUAGE_KEY")
    endpoint = os.getenv("LANGUAGE_ENDPOINT")
    connection_string = os.getenv("COSMOS_CONNECTION_STRING")
    db_name = os.getenv("COSMOS_DB_NAME")
    fetched_headlines = os.getenv("FETCHED_ARTICLE_CONTAINER_NAME")
    summarized_articles = os.getenv("SUMMARY_OUTPUT_CONTAINER_NAME")

    # Check for missing API Keys
    if not all(
        [
            api_key,
            key,
            endpoint,
            connection_string,
            db_name,
            fetched_headlines,
            summarized_articles,
        ]
    ):
        logging.error("Missing API Key")
        raise

    # NewsAPI Init
    newsapi = NewsApiClient(api_key)
    language = "en"  # Article language

    # Azure Cosmos DB Init
    client = CosmosClient.from_connection_string(connection_string)  # type: ignore
    database = client.get_database_client(db_name)  # type: ignore
    fetched_article_container = database.get_container_client(fetched_headlines)  # type: ignore
    summarized_article_container = database.get_container_client(summarized_articles)  # type: ignore

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
        raise

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
            headlines = enrich_articles(top_headlines["articles"])
            documents = azure_transformation(headlines=headlines)
    except Exception as e:
        logging.error(f"Document creation failed: {e}")
        raise

    # Validate we have documents to process
    if len(documents) == 0:
        logging.warning("Document creation returned empty, aborting process.")
        raise

    try:
        save_fetched_articles_to_cosmos(fetched_article_container, headlines)
        logging.info("Successfully saved fetched articles to DB")
    except Exception as e:
        logging.error(f"Unable to save fetched articles to DB: {e}")
        # TODO: Should I abort the process or not?

    # Generate summaries using Azure Text Analytics
    try:
        text_analytics_client = TextAnalyticsClient(endpoint, AzureKeyCredential(key))  # type: ignore
        poller = text_analytics_client.begin_abstract_summary(documents)
        abstract_summary_results = poller.result()
    except Exception as e:
        logging.critical(f"Azure text analytics processing failed: {e}")
        raise

    # Store output from Azure Summary to DB
    try:
        save_summary_output_to_cosmos(
            container=summarized_article_container,
            summary_output=abstract_summary_results,
        )
        logging.info("Successfully saved summarized articles to DB")
    except Exception as e:
        logging.critical(f"Unable to save summarized articles to DB {e}")
        raise


if __name__ == "__main__":
    main()
