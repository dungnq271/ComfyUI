from typing import Any, Dict, List, Type

from llama_index.core import StorageContext
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.indices.base import BaseIndex
from llama_index.core.indices.service_context import ServiceContext
from llama_index.core.indices.vector_store import VectorStoreIndex
from llama_index.core.llms.llm import LLM
from llama_index.core.node_parser import (
    HierarchicalNodeParser,
    NodeParser,
    get_leaf_nodes,
)
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.schema import Document, NodeWithScore, QueryBundle
from llama_index.core.settings import (
    Settings,
    llm_from_settings_or_context,
)
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.tools import FunctionTool

from ...utils.cache import postprocess_nodes, push_to_cache

from .base_load_and_search_retriever import BaseLoadAndSearchRetriever


class LoadAndSearchAutoMergingRetriever(BaseLoadAndSearchRetriever):
    def __init__(
        self,
        tool: FunctionTool,
        llm: LLM,
        node_parser: Type[NodeParser],
        index_cls: Type[BaseIndex],
        index_kwargs: Dict,
        retriever_cls: Type[BaseRetriever],
        retriever_kwargs: Dict,
        cache_db: Any | None = None,
        index: BaseIndex | None = None,
    ):
        """Init params."""
        self._node_parser = node_parser
        self.retriever_cls = retriever_cls
        super().__init__(
            tool=tool,
            llm=llm,
            cache_db=cache_db,
            index_cls=index_cls,
            index_kwargs=index_kwargs,
            retriever_kwargs=retriever_kwargs,
        )

    @classmethod
    def from_defaults(
        cls,
        tool: FunctionTool,
        llm: LLM,
        index_cls: Type[BaseIndex] = VectorStoreIndex,
        cache_db: Any | None = None, 
        service_context: ServiceContext | None = None,
        node_parser: Type[NodeParser] | None = None,
        retriever_cls: Type[BaseRetriever] | None = None,
        index_kwargs: Dict | None = None,
        retriever_kwargs: Dict | None = None,
    ):
        """From defaults."""
        llm = llm or llm_from_settings_or_context(Settings, service_context)
        node_parser = node_parser or HierarchicalNodeParser.from_defaults()
        index_cls = index_cls
        index_kwargs = index_kwargs or {}
        retriever_kwargs = retriever_kwargs or {}
        retriever_cls = retriever_cls or AutoMergingRetriever
        return cls(
            tool=tool,
            llm=llm,
            cache_db=cache_db,
            node_parser=node_parser,
            index_cls=index_cls,
            index_kwargs=index_kwargs,
            retriever_cls=retriever_cls,
            retriever_kwargs=retriever_kwargs,
        )

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        rewrite_query = self._rewrite_question(str(query_bundle))
        docs = self._tool(rewrite_query).raw_output

        # convert to Document if necessary
        if isinstance(docs, list):
            for i, doc in enumerate(docs):
                if not isinstance(doc, Document):
                    docs[i] = Document(text=str(doc))
        elif isinstance(docs, str):
            docs = [Document(text=docs)]
        elif isinstance(docs, Document):
            docs = [docs]
        else:
            docs = [Document(text=str(docs))]

        nodes = self._node_parser.get_nodes_from_documents(docs)
        leaf_nodes = get_leaf_nodes(nodes)

        # insert nodes into docstore
        docstore = SimpleDocumentStore()
        docstore.add_documents(nodes)

        # define storage context (will include vector store by default too)
        storage_context = StorageContext.from_defaults(docstore=docstore)

        self._index = self._index_cls(
            leaf_nodes, storage_context=storage_context, **self._index_kwargs
        )

        base_retriever = self._index.as_retriever(**self._retriever_kwargs)
        retriever = AutoMergingRetriever(base_retriever, storage_context, verbose=True)
        nodes = retriever.retrieve(query_bundle)

        return nodes

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        if self._cache_db:
            await push_to_cache(tool_name=self._tool.metadata.name, cache_db=self._cache_db)

        rewrite_query = self._rewrite_question(str(query_bundle))
        docs = self._tool(rewrite_query).raw_output

        # convert to Document if necessary
        if isinstance(docs, list):
            for i, doc in enumerate(docs):
                if not isinstance(doc, Document):
                    docs[i] = Document(text=str(doc))
        elif isinstance(docs, str):
            docs = [Document(text=docs)]
        elif isinstance(docs, Document):
            docs = [docs]
        else:
            docs = [Document(text=str(docs))]

        nodes = self._node_parser.get_nodes_from_documents(docs)
        leaf_nodes = get_leaf_nodes(nodes)

        # insert nodes into docstore
        docstore = SimpleDocumentStore()
        docstore.add_documents(nodes)

        # define storage context (will include vector store by default too)
        storage_context = StorageContext.from_defaults(docstore=docstore)

        self._index = self._index_cls(
            leaf_nodes, storage_context=storage_context, **self._index_kwargs
        )

        base_retriever = self._index.as_retriever(**self._retriever_kwargs)
        retriever = AutoMergingRetriever(base_retriever, storage_context, verbose=True)
        nodes = retriever.retrieve(query_bundle)

        if self._cache_db:
            processed_nodes = postprocess_nodes(nodes)
            await push_to_cache(
                self._tool.metadata.name,
                cache_db=self._cache_db,
                query=rewrite_query,
                value=processed_nodes,
            )

        return nodes
