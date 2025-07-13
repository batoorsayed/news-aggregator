import logging
import os
import re
from datetime import date, datetime, timedelta

import azure.functions as func
import requests
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient
from newsapi.newsapi_client import NewsApiClient
from requests.auth import HTTPBasicAuth

try:

    def enrich_articles(articles):
        """
        Add timestamp and create id using url to each article.
        Articles without a valid URL are skipped.
        """
        fetched_headlines = {}
        for article in articles:
            if (
                "url" not in article
                or article["url"] is None
                or article["url"].strip() == ""
            ):
                logging.debug("Missing url, article skipped.")
                continue
            else:
                url_id = re.sub(r"[^a-zA-Z0-9]", "", article.get("url"))
                fetched_headlines[url_id] = {
                    **article,
                    "id": url_id,
                    "fetched_datetime": datetime.now().isoformat(),
                }
        return fetched_headlines

    def azure_transformation(headlines):
        """
        Transform articles into Azure-compatible document format.

        Note: Each article is expected to have a 'language' field. If missing, 'en' will be used as default.
        """
        documents = []
        for article_id, article in headlines.items():
            document = {
                "id": article.get("id"),
                "language": article.get("language", "en"),
                "text": "Title: "
                + str(article.get("title"))
                + " | Description: "
                + str(article.get("description"))
                + " | Content: "
                + str(article.get("content")),
            }
            documents.append(document)
        return documents

    def save_fetched_articles_to_cosmos(container, fetched_articles):
        """
        Save or update fetched articles (after adding id and fetched_date) to Cosmos NoSQL DB

        For now individual upsert is good enough. I'm not sending thousands of articles per second. What am I, Jeff Bezos?
        """
        for article_id in fetched_articles:
            container.upsert_item(fetched_articles[article_id])

    def save_summary_output_to_cosmos(container, summary_output):
        """Store output from Azure Summary to Cosmos DB"""
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

    # Extract data from headlines
    def extract_data_from_headlines(headlines):
        """
        Extracts relevant data fields from a dictionary of headline articles.
        """
        merged_articles = []
        for article_id, article in headlines.items():
            article_data = {
                "id": article.get("id"),
                "source": article.get("source"),
                "author": article.get("author"),
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url"),
                "urlToImage": article.get("urlToImage"),
                "publishedAt": article.get("publishedAt"),
                "fetched_datetime": article.get("fetched_datetime"),
            }
            merged_articles.append(article_data)
        return merged_articles

    # Add summary data to matching articles
    def merge_summary_and_headlines(merged_articles, abstract_summary_results):
        """
        Merges abstract summary results into a list of articles by matching article IDs.

        For each result in abstract_summary_results, finds the corresponding article in merged_articles
        by matching the "id" field. If the result indicates an error, sets "is_error" to True and "summaries"
        to None for that article. Otherwise, sets "is_error" to False and populates "summaries" with the
        summary texts from the result.
        """
        for result in abstract_summary_results:
            # Find matching article by id
            for article in merged_articles:
                if article["id"] == result.id:
                    if result.is_error:
                        article["is_error"] = True
                        article["summaries"] = None
                    else:
                        article["is_error"] = False
                        article["summaries"] = [
                            summary.text for summary in result.summaries
                        ]
                    break
        return merged_articles


except Exception as e:
    import logging

    logging.error(f"Error in helper functions: {e}")


# Main function
app = func.FunctionApp()


# This function is triggered daily at 2 AM UTC
@app.timer_trigger(
    schedule="0 0 2 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
def daily_fetch_store(myTimer: func.TimerRequest) -> None:
    try:
        if myTimer.past_due:
            logging.info("The timer is past due!")

        # Keys
        api_key = os.environ["NEWSAPI_KEY"]
        key = os.environ["LANGUAGE_KEY"]
        endpoint = os.environ["LANGUAGE_ENDPOINT"]
        connection_string = os.environ["COSMOS_CONNECTION_STRING"]
        db_name = os.environ["COSMOS_DB_NAME"]
        fetched_headlines = os.environ["FETCHED_ARTICLE_CONTAINER_NAME"]
        summarized_articles = os.environ["SUMMARY_OUTPUT_CONTAINER_NAME"]
        api_url = os.environ["WP_API_URL"]
        api_username = os.environ["WP_API_USERNAME"]
        api_password = os.environ["WP_API_APP_PASSWORD"]

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
                api_url,
                api_username,
                api_password,
            ]
        ):
            logging.error("Missing API Key")
            raise RuntimeError(
                "One or more required API keys or config values are missing."
            )

        # NewsAPI Init
        newsapi = NewsApiClient(api_key)
        language = "en"  # Article language

        # Azure Cosmos DB Init
        client = CosmosClient.from_connection_string(connection_string)  # type: ignore
        database = client.get_database_client(db_name)  # type: ignore
        fetched_article_container = database.get_container_client(fetched_headlines)  # type: ignore
        summarized_article_container = database.get_container_client(
            summarized_articles
        )  # type: ignore

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
            raise RuntimeError("No documents to process")

        try:
            save_fetched_articles_to_cosmos(fetched_article_container, headlines)
            logging.info("Successfully saved fetched articles to DB")
        except Exception as e:
            logging.error(f"Unable to save fetched articles to DB: {e}")
            # TODO: Should I abort the process or not?

        # Generate summaries using Azure Text Analytics
        try:
            text_analytics_client = TextAnalyticsClient(
                endpoint, AzureKeyCredential(key)
            )  # type: ignore
            poller = text_analytics_client.begin_abstract_summary(
                documents, sentence_count=2
            )
            poller.wait()  # Waiting for the operation to complete
            abstract_summary_results = list(poller.result())
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

        logging.info(msg="Python timer trigger function executed.")

        # Merge summaries with fetched headlines
        try:
            headline_meta = extract_data_from_headlines(headlines)
            merged_articles = merge_summary_and_headlines(
                headline_meta, abstract_summary_results
            )
        except Exception as e:
            logging.error(f"Error merging headlines and summaries: {e}")
            raise

        # Only include articles where 'is_error' is False (i.e., successfully summarized).
        try:
            successful_articles = [
                article
                for article in merged_articles
                if not article.get("is_error", True)
            ]
            logging.info(
                f"Successfully merged {len(successful_articles)} fetched articles with summaries."
            )
        except Exception as e:
            logging.error(f"Error filtering successful articles: {e}")
            raise

        # If no successful articles, log and exit
        if not successful_articles:
            logging.warning("No successful articles to post.")
            return

        # Initialize WordPress API authentication
        auth = HTTPBasicAuth(api_username, api_password)  # type: ignore

        # Prepare the post title using yesterday's date
        title = "Headlines from: " + str(date.today() - timedelta(days=1))

        # Start building the HTML content for the WordPress post
        content = f'<h3 style="text-align: center;">{title}</h3>&nbsp;\n'

        # Add each successful article to the post content
        for i, article in enumerate(successful_articles, 1):
            content += f"""
            <div class="story-{i}">
            <h5>{article["title"]}</h5>
            <p><em>Source: <span style="text-decoration: underline;"><a href="{article["url"]}" target="_blank">{article["source"]["name"]}</a></span></em></p>
            <p>{article["summaries"][0]}</p>
            </div>
            <hr>
            """

        # Create the post payload for WordPress API
        post = {
            "title": title,
            "status": "draft",
            "content": content,
            "categories": 6,
        }

        # Send the post to WordPress using the REST API
        response = requests.post(api_url + "/posts", auth=auth, json=post)  # type: ignore

        # Log the result of the post creation
        if response.status_code == 201:
            post_data = response.json()
            logging.info(f"Post created successfully! ID: {post_data.get('id')}")
        else:
            logging.critical(
                f"Error creating post: {response.status_code}, : {response.text}"
            )

    except Exception as e:
        logging.critical(
            f"Unhandled exception in daily_fetch_store: {e}", exc_info=True
        )
