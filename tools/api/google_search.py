"""Google Search tool spec."""

import os
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import requests  # type: ignore
from bs4 import BeautifulSoup
from llama_index.core.schema import Document
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from requests.exceptions import ConnectionError, ReadTimeout  # type: ignore

from ..utils.logger import setup_coloredlogs
from ..utils.text import remove_redundant_whitespaces

logger = setup_coloredlogs(__name__)

QUERY_URL_TMPL = (
    "https://www.googleapis.com/customsearch/v1?key={key}&cx={engine}&q={query}"
)


class CustomGoogleSearchToolSpec(BaseToolSpec):
    """Custom Google Search tool spec."""

    spec_functions = ["google_search"]

    def __init__(
        self,
        key: str,
        engine: str,
        num: int | None = None,
        log_dir: str = "tool_results",
    ) -> None:
        """Initialize with parameters."""
        self.key = key
        self.engine = engine
        self.num = num

        os.makedirs(log_dir, exist_ok=True)
        self.save_result_path = os.path.join(
            log_dir, self.spec_functions[0] + "_result.json"
        )

    @staticmethod
    def scrape_url(url: str):
        logger.info(f"Scraping {url}...")
        try:
            content = requests.get(url, timeout=10).content
        except (ReadTimeout, ConnectionError) as e:
            return url, f"Error: {e}"
        soup = BeautifulSoup(content, "html.parser")
        return url, soup.get_text()

    def google_search(self, query: str):
        """
        Make a query to the Google search engine to receive a list of results.
        Then scrape the text from link of each result.

        Args:
            query (str): The query to be passed to Google search.
            num (int, optional): The number of search results to return.
            Defaults to None.

        Raises:
            ValueError: If the 'num' is not an integer between 1 and 10.
        """
        # Query Google Search
        query_url = QUERY_URL_TMPL.format(
            key=self.key, engine=self.engine, query=urllib.parse.quote_plus(query)
        )

        if self.num is not None:
            if not 1 <= self.num <= 10:
                raise ValueError("num should be an integer between 1 and 10, inclusive")
            query_url += f"&num={self.num}"

        response = requests.get(query_url).json()

        # Scrape content of each url
        urls = [item["link"] for item in response["items"]]

        logger.info("URL results:")
        logger.info("\n".join(urls))

        result_text_nodes = []
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as exc:
            for url, text in exc.map(self.scrape_url, urls):
                text_node = Document(text=remove_redundant_whitespaces(text))
                text_node.metadata.update({"Link": url})
                text_node.excluded_llm_metadata_keys.append("Link")
                text_node.excluded_embed_metadata_keys.append("Link")
                result_text_nodes.append(text_node)

        return result_text_nodes
