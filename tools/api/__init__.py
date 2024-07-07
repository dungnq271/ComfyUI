import os
from typing import Any, Dict, List

from dotenv import find_dotenv, load_dotenv
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from llama_index.core.tools.tool_spec.load_and_search.base import LoadAndSearchToolSpec

from .google_search import CustomGoogleSearchToolSpec
from .image_search import ImageSearchToolSpec
from .wikipedia_search import WikipediaSearchToolSpec

_ = load_dotenv(find_dotenv())  # read local .env file
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")  # type: ignore


DEFAULT_ALL_LOAD_AND_SEARCH_TOOL_SPECS: Dict[str, BaseToolSpec] = {
    "google_search": CustomGoogleSearchToolSpec(
        key=os.getenv("GOOGLE_SEARCH_API_KEY"),  # type: ignore
        engine=os.getenv("SEARCH_ENGINE_ID"),  # type: ignore
        num=5,
    ),
    "wikipedia_search": WikipediaSearchToolSpec(language="en", num_results=5),
    "image_search": ImageSearchToolSpec(
        search_params={
            "num": 7,
            "fileType": "jpg|gif|png|bmp|svg|webp|ico",
            "rights": "cc_publicdomain|cc_attribute|"
            "cc_sharealike|cc_noncommercial|cc_nonderived",
            "safe": "off",
        }
    ),
}


DEFAULT_ALL_LOAD_AND_SEARCH_TOOLS: Dict[str, List[Any]] = {
    tool_name: LoadAndSearchToolSpec.from_defaults(
        tool_spec.to_tool_list()[0],
    ).to_tool_list()
    for tool_name, tool_spec in DEFAULT_ALL_LOAD_AND_SEARCH_TOOL_SPECS.items()
}
