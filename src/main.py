import logging
import os
import sys

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from newsapi import NewsApiClient

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Keys
load_dotenv()
api_key = os.getenv("NEWSAPI_KEY")
key = os.getenv("LANGUAGE_KEY")
endpoint = os.getenv("LANGUAGE_ENDPOINT")

# NewsAPI Init
newsapi = NewsApiClient(api_key)
language = "en"

# /v2/top-headlines
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

# Document Creation
try:
    if top_headlines.get("status") != "ok":
        logging.error(
            f"{top_headlines.get('status')}- {top_headlines.get('code')}- {top_headlines.get('message')}"
        )
    else:
        logging.info(
            f"Successfully fetched {top_headlines.get('totalResults')} headlines."
        )
        documents = []
        for idx, article in enumerate(top_headlines["articles"]):
            document = {
                "id": idx,
                "language": language,
                "text": "Description: "
                + article.get("description")
                + " | Content: "
                + article.get("content"),
            }
            documents.append(document)
except Exception as e:
    logging.error(f"Document creation failed: {e}")
    sys.exit()

# In case Document creation fails
if len(documents) == 0:
    logging.warning("Document creation returned empty, aborting process.")
    sys.exit()

# Authenticate the client using your key and endpoint
try:
    text_analytics_client = TextAnalyticsClient(endpoint, AzureKeyCredential(key))  # type: ignore
    poller = text_analytics_client.begin_abstract_summary(documents)
    abstract_summary_results = poller.result()
except Exception as e:
    logging.error(f"Azure text analytics processing failed: {e}")
    sys.exit()

for result in abstract_summary_results:
    if result.kind == "AbstractiveSummarization":
        logging.info(f"Summaries abstracted: {len(result.summaries)}")
        [print(f"{summary.text}\n") for summary in result.summaries]
    elif result.is_error is True:
        logging.error(
            "...Is an error with code '{}' and message '{}'".format(
                result.error.code, result.error.message
            )
        )