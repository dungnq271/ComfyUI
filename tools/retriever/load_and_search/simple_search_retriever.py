from typing import Any, List

from llama_index.core.llms.llm import LLM
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.tools import FunctionTool

from ...utils.cache import postprocess_nodes, push_to_cache

from .base_load_and_search_retriever import BaseLoadAndSearchRetriever


class SimpleSearchRetriever(BaseLoadAndSearchRetriever):
    def __init__(
        self,
        tool: FunctionTool,
        llm: LLM,
        cache_db: Any | None = None,
    ):
        """Init params."""
        self.tool = tool
        self.llm = llm
        self.cache_db = cache_db

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        rewrite_query = self._rewrite_question(str(query_bundle))
        nodes = self._tool(rewrite_query).raw_output
        score_nodes = [NodeWithScore(node=node) for node in nodes]
        return score_nodes

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        if self._cache_db:
            await push_to_cache(tool_name=self._tool.metadata.name, cache_db=self._cache_db)

        rewrite_query = self._rewrite_question(str(query_bundle))
        nodes = self._tool(rewrite_query).raw_output
        score_nodes = [NodeWithScore(node=node) for node in nodes]

        if self._cache_db:
            processed_nodes = postprocess_nodes(score_nodes)
            await push_to_cache(
                self._tool.metadata.name,
                cache_db=self._cache_db,
                query=rewrite_query,
                value=processed_nodes,
            )

        return score_nodes
