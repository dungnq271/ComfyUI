from typing import List

from llama_index.core.schema import Document, ImageDocument, NodeWithScore, QueryBundle

from .base_load_and_search_retriever import BaseLoadAndSearchRetriever


class LoadAndSearchRetriever(BaseLoadAndSearchRetriever):
    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        docs = self._tool(str(query_bundle)).raw_output

        # convert to Document if necessary
        if isinstance(docs, list):
            for i, doc in enumerate(docs):
                if isinstance(doc, ImageDocument):
                    pass
                elif not isinstance(doc, Document):
                    docs[i] = Document(text=str(doc))
        elif isinstance(docs, str):
            docs = [Document(text=docs)]
        elif isinstance(docs, Document):
            docs = [docs]
        else:
            docs = [Document(text=str(docs))]

        if self._index:
            for doc in docs:
                self._index.insert(doc, **self._index_kwargs)
        else:
            self._index = self._index_cls.from_documents(docs, **self._index_kwargs)

        retriever = self._index.as_retriever(**self._retriever_kwargs)
        nodes = retriever.retrieve(query_bundle)
        return nodes
