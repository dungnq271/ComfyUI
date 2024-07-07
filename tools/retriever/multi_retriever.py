from typing import Any, List

from llama_index.core.indices.vector_store.retrievers import VectorIndexRetriever
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.retrievers.bm25 import BM25Retriever

from ..utils.cache import postprocess_nodes, push_to_cache
from ..utils.logger import setup_coloredlogs

logger = setup_coloredlogs(__name__)


class MultiRetriever(BaseRetriever):
    def __init__(
        self, vector_retriever_list: List[BaseRetriever], cache_db: Any | None = None
    ):
        self.vector_retriever_list = vector_retriever_list
        self._cache_db = cache_db
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        all_nodes = []
        for retriever in self.vector_retriever_list:
            retriever_name = type(retriever).__name__
            logger.info(f"Using {retriever_name}")
            nodes = retriever.retrieve(query_bundle)
            all_nodes.extend(nodes)
        return all_nodes

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        all_nodes = []
        for retriever in self.vector_retriever_list:
            retriever_name = type(retriever).__name__
            logger.info(f"Using {retriever_name}")

            if self._cache_db and retriever_name == "MultiRetriever":
                await push_to_cache(
                    tool_name="knowledge_search",
                    cache_db=self._cache_db,
                )

            nodes = await retriever.aretrieve(query_bundle)
            if self._cache_db and retriever_name == "MultiRetriever":
                processed_nodes = postprocess_nodes(nodes)
                await push_to_cache(
                    tool_name="knowledge_search",
                    cache_db=self._cache_db,
                    query=str(query_bundle),
                    value=processed_nodes,
                )

            all_nodes.extend(nodes)
        return all_nodes


### Sample usage
if __name__ == "__main__":
    retriever = VectorIndexRetriever()
    bm25_retriever = BM25Retriever()
    hybrid_retriver = MultiRetriever(vector_retriever_list=[retriever, bm25_retriever])
