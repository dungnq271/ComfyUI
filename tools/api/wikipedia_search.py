import wikipedia
from llama_index.core.schema import Document
from llama_index.core.tools.tool_spec.base import BaseToolSpec

from ..utils.logger import setup_coloredlogs

logger = setup_coloredlogs(__name__)


class WikipediaSearchToolSpec(BaseToolSpec):
    spec_functions = ["wikipedia_search"]

    def __init__(self, language="en", num_results: int = 1):
        self.language = language
        self.num_results = num_results
        wikipedia.set_lang(self.language)

    def wikipedia_search(self, query: str):
        results = wikipedia.search(query)
        logger.info("Search results:")
        logger.info(", ".join(results))
        result_text_nodes = []

        if self.num_results > len(results):
            num_results = len(results)
        else:
            num_results = self.num_results

        for idx in range(num_results):
            try:
                result = wikipedia.page(results[idx])
                url = result.url
                summary = result.summary

                text_node = Document(text=summary)
                text_node.metadata.update({"Link": url})
                text_node.excluded_llm_metadata_keys.append("Link")
                text_node.excluded_embed_metadata_keys.append("Link")

                result_text_nodes.append(text_node)
            except wikipedia.exceptions.PageError as e:
                print(e)

        return result_text_nodes


if __name__ == "__main__":
    search_query = "Who is Elon Musk?"
    num_results = 3
    summarizer = WikipediaSearchToolSpec(language="en", num_results=num_results)
    documents = summarizer.wikipedia_search(search_query)
    for i in range(num_results):
        print(documents[i])
        print("-" * 20)
