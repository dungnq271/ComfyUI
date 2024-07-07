import os

from dotenv import find_dotenv, load_dotenv
from llama_index.embeddings.openai import OpenAIEmbedding

from ..api import DEFAULT_ALL_LOAD_AND_SEARCH_TOOL_SPECS
from comfy.llm import get_llm

from .hybrid_retriever import HybridRetriever
from .load_and_search import (
    LoadAndSearchAutoMergingRetriever,
    LoadAndSearchRetriever,
    SimpleSearchRetriever,
)
from .multi_retriever import MultiRetriever

_ = load_dotenv(find_dotenv())  # read local .env file

DEFAULT_EMBED_MODEL = OpenAIEmbedding(
    model="text-embedding-3-small", timeout=60, max_tries=3
)

DEFAULT_MODEL_NAME = "claude-3-haiku-20240307"
DEFAULT_LLM = get_llm(DEFAULT_MODEL_NAME)

DEFAULT_ALL_RETRIEVERS = {
    "google_search": {
        "name": "google_search_retriever",
        "description": "Use this tool to search information "
        "from Google to answer questions",
        "retriever": LoadAndSearchAutoMergingRetriever.from_defaults(
            tool=DEFAULT_ALL_LOAD_AND_SEARCH_TOOL_SPECS["google_search"].to_tool_list()[
                0
            ],
            llm=DEFAULT_LLM,
            index_kwargs={"embed_model": DEFAULT_EMBED_MODEL},
            retriever_kwargs={"similarity_top_k": 5},
        ),
    },
    "wikipedia_search": {
        "name": "wikipedia_search_retriever",
        "description": "Use this tool to search information "
        "from Wikipedia to answer questions",
        "retriever": LoadAndSearchAutoMergingRetriever.from_defaults(
            tool=DEFAULT_ALL_LOAD_AND_SEARCH_TOOL_SPECS[
                "wikipedia_search"
            ].to_tool_list()[0],
            llm=DEFAULT_LLM,
            index_kwargs={"embed_model": DEFAULT_EMBED_MODEL},
            retriever_kwargs={"similarity_top_k": 5},
        ),
    },
    "image_search": {
        "name": "google_image_search_retriever",
        "description": "Use this tool to search images "
        "related to user's query from Google",
        # "retriever": LoadAndSearchRetriever.from_defaults(
        #     tool=DEFAULT_ALL_LOAD_AND_SEARCH_TOOL_SPECS[
        #         "image_search"
        #     ].to_tool_list()[0],
        #     index_kwargs={"embed_model": DEFAULT_EMBED_MODEL},
        #     retriever_kwargs={"image_similarity_top_k": 3},
        # ),
        "retriever": SimpleSearchRetriever(
            tool=DEFAULT_ALL_LOAD_AND_SEARCH_TOOL_SPECS["image_search"].to_tool_list()[
                0
            ],
            llm=DEFAULT_LLM,
        ),
    },
}

__all__ = [
    "HybridRetriever",
    "MultiRetriever",
    "LoadAndSearchRetriever",
    "DEFAULT_ALL_RETRIEVERS",
]
