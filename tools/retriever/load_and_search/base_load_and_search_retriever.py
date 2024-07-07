from abc import abstractmethod
from typing import Any, Dict, List, Type

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.indices.base import BaseIndex
from llama_index.core.llms.llm import LLM
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.tools import FunctionTool

from ...prompt.query_rewrite import DEFAULT_TOOL_QUERY_REWRITE_PROMPT


class BaseLoadAndSearchRetriever(BaseRetriever):
    def __init__(
        self,
        tool: FunctionTool,
        llm: LLM,
        index_cls: Type[BaseIndex],
        cache_db: Any | None = None,
        rewrite_prompt: str | None = None,
        skip_rewrite: bool = False,
        index_kwargs: Dict | None = None,
        retriever_kwargs: Dict | None = None,
        index: BaseIndex | None = None,
    ):
        """Init params."""
        self._tool = tool
        self._llm = llm
        self._cache_db = cache_db
        self._index_cls = index_cls
        self._query_rewrite_prompt_template = (
            rewrite_prompt or DEFAULT_TOOL_QUERY_REWRITE_PROMPT
        )
        self._skip_rewrite = skip_rewrite
        self._index_kwargs = index_kwargs
        self._retriever_kwargs = retriever_kwargs
        self._index = index

    def _rewrite_question(self, latest_question: str) -> str:
        if self._skip_rewrite:
            return latest_question

        return self._llm.predict(
            self._query_rewrite_prompt_template,
            question=latest_question,
            tool_description=self._tool.metadata.description,
        )

    @abstractmethod
    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Use tool to load the index and then search from this index"""

    @abstractmethod
    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Use tool to load the index and then search from this index"""
