from llama_index.core.indices.vector_store.retrievers import VectorIndexRetriever
from llama_index.core.retrievers import BaseRetriever
from llama_index.retrievers.bm25 import BM25Retriever


class HybridRetriever(BaseRetriever):
    def __init__(self, vector_retriever: BaseRetriever, bm25_retriever: BM25Retriever):
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        super().__init__()

    def _retrieve(self, query, **kwargs):
        bm25_nodes = self.bm25_retriever.retrieve(query, **kwargs)
        vector_nodes = self.vector_retriever.retrieve(query, **kwargs)

        # combine the two lists of nodes
        all_nodes = []
        node_ids = set()
        for n in bm25_nodes + vector_nodes:
            if n.node.node_id not in node_ids:
                all_nodes.append(n)
                node_ids.add(n.node.node_id)
        return all_nodes


### Sample usage
if __name__ == "__main__":
    retriever = VectorIndexRetriever().retrieve
    bm25_retriever = BM25Retriever()
    hybrid_retriver = HybridRetriever(
        vector_retriever=retriever, bm25_retriever=bm25_retriever
    )
