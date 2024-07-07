import json
from typing import Any, Dict, List

from llama_index.core.schema import ImageNode, MetadataMode, NodeWithScore

DEFAULT_CACHE_KEY = "tools"


def postprocess_nodes(nodes: List[NodeWithScore]):
    processed_nodes = []

    for node in nodes:
        if isinstance(node.node, ImageNode):
            processed_nodes.append(
                {"content": node.node.image, "score": str(node.score)}
            )
        else:
            processed_nodes.append(
                {
                    "content": node.node.get_content(metadata_mode=MetadataMode.ALL),
                    "score": str(node.score),
                }
            )

    return processed_nodes


async def push_to_cache(
    tool_name: str,
    cache_db: Any,
    query: str | None = None,
    key: str = DEFAULT_CACHE_KEY,
    value: List[Dict] = [],
):
    if value:
        value_dict = {"name": tool_name, "query": query, "output": value}
        # await cache_db.rpush(key, json.dumps(value_dict))
        await cache_db.publish(key, json.dumps(value_dict))
    else:
        # await cache_db.rpush(key, tool_name)
        await cache_db.publish(key, tool_name)
