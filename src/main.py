import os

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from newsapi import NewsApiClient

# Keys
load_dotenv()
api_key = os.getenv("NEWSAPI_KEY")
key = os.getenv("LANGUAGE_KEY")
endpoint = os.getenv("LANGUAGE_ENDPOINT")

# NewsAPI Init
newsapi = NewsApiClient(api_key)
language = "en"

# /v2/top-headlines
top_headlines = newsapi.get_top_headlines(
    # q="bitcoin", # keywords
    # sources="bbc-news,the-verge",
    # category="business",
    language=language,
    country="us",
    page_size=5,  # Change after
)
# TODO: Add error handling fpr NewsAPI

if top_headlines.get("status") != "ok":
    print(f"Status: {top_headlines.get('status')}")
    print(f"Eror Code: {top_headlines.get('code')}")
    print(f"Error Message: {top_headlines.get('message')}")
else:
    print(f"Successfully fetched {top_headlines.get('totalResults')} headlines.")
    documents = []
    for idx, article in enumerate(top_headlines["articles"]):
        document = {"id": idx, "language": language, "text": article.get("content")}
        documents.append(document)


# Authenticate the client using your key and endpoint
text_analytics_client = TextAnalyticsClient(endpoint, AzureKeyCredential(key))  # type: ignore

poller = text_analytics_client.begin_abstract_summary(documents)
abstract_summary_results = poller.result()
for result in abstract_summary_results:
    # print(vars(result)) # Discard after
    if result.kind == "AbstractiveSummarization":
        print("Summaries abstracted:")
        [print(f"{summary.text}\n") for summary in result.summaries]
    elif result.is_error is True:
        print(
            "...Is an error with code '{}' and message '{}'".format(
                result.error.code, result.error.message
            )
        )
# TODO: Add error handling for summarization