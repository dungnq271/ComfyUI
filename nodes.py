import os
from typing import Any, Dict, List, Optional, Tuple, ClassVar
import sys
import json
import hashlib
import traceback
import math
import time
import random
import logging

from llama_index.core.llms import ChatMessage, LLM
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.query_pipeline import InputComponent, CustomQueryComponent
from llama_index.core.schema import NodeWithScore
from llama_index.core.bridge.pydantic import Field
from tools.retriever import DEFAULT_ALL_RETRIEVERS

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "comfy"))

import comfy.llm
import comfy.utils

import comfy.model_management
from comfy.cli_args import args

import importlib

import folder_paths


def before_node_execution():
    comfy.model_management.throw_exception_if_processing_interrupted()


def interrupt_processing(value=True):
    comfy.model_management.interrupt_current_processing(value)


class Input(InputComponent):
    RETURN_TYPES: ClassVar[Tuple] = ("TEXT",)
    CATEGORY: ClassVar[str] = "input"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "user_message": ("STRING", {"multiline": True, "dynamicPrompts": True}),
            }
        }


class Search(CustomQueryComponent):
    tool: BaseRetriever = Field(..., description="Retriever Tool")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "tool_name": (["google_search", "wikipedia_search"],),
                "query": ("TEXT",),
            }
        }

    RETURN_TYPES: ClassVar[Tuple] = ("NODE",)
    CATEGORY: ClassVar[str] = "search"

    def __init__(self, tool_name: str, **kwargs):
        super().__init__(tool=DEFAULT_ALL_RETRIEVERS[tool_name]["retriever"], **kwargs)

    @property
    def _input_keys(self) -> set:
        """Input keys dict."""
        # NOTE: These are required inputs. If you have optional inputs please override
        # `optional_input_keys_dict`
        return {"query"}

    @property
    def _output_keys(self) -> set:
        return {"nodes"}

    def _run_component(self, **kwargs) -> Dict[str, Any]:
        nodes = self.tool.retrieve(kwargs["query"])
        return {"nodes": nodes}


DEFAULT_CONTEXT_PROMPT = (
    "Here is some context that may be relevant:\n"
    "-----\n"
    "{node_context}\n"
    "-----\n"
    "Please write a response to the following question, using the above context:\n"
    "{query_str}\n"
)


class ResponseWithChatHistory(CustomQueryComponent):
    llm: LLM = Field(..., description="LLM to use")
    system_prompt: Optional[str] = Field(
        default=None, description="System prompt to use for the LLM"
    )
    context_prompt: str = Field(
        default=DEFAULT_CONTEXT_PROMPT,
        description="Context prompt to use for the LLM",
    )

    OUTPUT_NODE: ClassVar[bool] = True
    RETURN_TYPES: ClassVar[Tuple] = ("TEXT",)
    CATEGORY: ClassVar[str] = "text"

    def __init__(
        self, model_name, system_prompt, context_prompt: str | Any = None, **kwargs
    ):
        super().__init__(
            llm=comfy.llm.get_llm(model_name),
            system_prompt=system_prompt,
            context_prompt=context_prompt or DEFAULT_CONTEXT_PROMPT,
            type="output",
        )
        # self.system_prompt = system_prompt
        # self.context_prompt = context_prompt or DEFAULT_CONTEXT_PROMPT
        # self.type = "output"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_name": (["gpt-3.5-turbo", "claude-3-haiku-20240307"],),
                "system_prompt": (
                    "STRING",
                    {"multiline": True, "dynamicPrompts": True},
                ),
            }
        }

    def _validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        # NOTE: this is OPTIONAL but we show you where to do validation as an example
        return input

    @property
    def _input_keys(self) -> set:
        """Input keys dict."""
        # NOTE: These are required inputs. If you have optional inputs please override
        # `optional_input_keys_dict`
        return {"nodes"}

    @property
    def _output_keys(self) -> set:
        return {"response"}

    def _prepare_context(
        self,
        chat_history: List[ChatMessage],
        nodes: List[NodeWithScore],
        query_str: str,
    ) -> List[ChatMessage]:
        node_context = ""
        for idx, node in enumerate(nodes):
            node_text = node.get_content(metadata_mode="llm")
            node_context += f"Context Chunk {idx}:\n{node_text}\n\n"

        formatted_context = self.context_prompt.format(
            node_context=node_context, query_str=query_str
        )
        user_message = ChatMessage(role="user", content=formatted_context)
        chat_history.append(user_message)

        if self.system_prompt is not None:
            chat_history = [
                ChatMessage(role="system", content=self.system_prompt)
            ] + chat_history

        return chat_history

    def _simple_prepare_context(
        self,
        nodes: List[NodeWithScore],
    ) -> List[ChatMessage]:
        node_context = ""
        for idx, node in enumerate(nodes):
            node_text = node.get_content(metadata_mode="llm")
            node_context += f"Context Chunk {idx}:\n{node_text}\n\n"

        user_message = ChatMessage(role="user", content=node_context)

        if self.system_prompt is not None:
            chat_history = [ChatMessage(role="system", content=self.system_prompt)] + [
                user_message
            ]

        return chat_history

    def _run_component(self, **kwargs) -> Dict[str, Any]:
        """Run the component."""
        nodes = kwargs["nodes"]
        # chat_history = kwargs["chat_history"]
        # query_str = kwargs["query_str"]

        # prepared_context = self._prepare_context(
        #     chat_history, nodes, query_str
        # )
        prepared_context = self._simple_prepare_context(nodes)

        response = self.llm.chat(prepared_context)

        return {"response": response}

    async def _arun_component(self, **kwargs: Any) -> Dict[str, Any]:
        """Run the component asynchronously."""
        # NOTE: Optional, but async LLM calls are easy to implement
        chat_history = kwargs["chat_history"]
        nodes = kwargs["nodes"]
        query_str = kwargs["query_str"]

        prepared_context = self._prepare_context(chat_history, nodes, query_str)

        response = await self.llm.achat(prepared_context)

        return {"response": response}


NODE_CLASS_MAPPINGS = {
    "Input": Input,
    "Search": Search,
    "Response": ResponseWithChatHistory,
}


NODE_DISPLAY_NAME_MAPPINGS = {
    "Input": "Input",
    "Search": "Search API",
    "Response": "Response",
}

EXTENSION_WEB_DIRS = {}


def load_custom_node(module_path, ignore=set()):
    module_name = os.path.basename(module_path)
    if os.path.isfile(module_path):
        sp = os.path.splitext(module_path)
        module_name = sp[0]
    try:
        logging.debug("Trying to load custom node {}".format(module_path))
        if os.path.isfile(module_path):
            module_spec = importlib.util.spec_from_file_location(
                module_name, module_path
            )
            module_dir = os.path.split(module_path)[0]
        else:
            module_spec = importlib.util.spec_from_file_location(
                module_name, os.path.join(module_path, "__init__.py")
            )
            module_dir = module_path

        module = importlib.util.module_from_spec(module_spec)
        sys.modules[module_name] = module
        module_spec.loader.exec_module(module)

        if (
            hasattr(module, "WEB_DIRECTORY")
            and getattr(module, "WEB_DIRECTORY") is not None
        ):
            web_dir = os.path.abspath(
                os.path.join(module_dir, getattr(module, "WEB_DIRECTORY"))
            )
            if os.path.isdir(web_dir):
                EXTENSION_WEB_DIRS[module_name] = web_dir

        if (
            hasattr(module, "NODE_CLASS_MAPPINGS")
            and getattr(module, "NODE_CLASS_MAPPINGS") is not None
        ):
            for name in module.NODE_CLASS_MAPPINGS:
                if name not in ignore:
                    NODE_CLASS_MAPPINGS[name] = module.NODE_CLASS_MAPPINGS[name]
            if (
                hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS")
                and getattr(module, "NODE_DISPLAY_NAME_MAPPINGS") is not None
            ):
                NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
            return True
        else:
            logging.warning(
                f"Skip {module_path} module for custom nodes due to the lack of NODE_CLASS_MAPPINGS."
            )
            return False
    except Exception as e:
        logging.warning(traceback.format_exc())
        logging.warning(f"Cannot import {module_path} module for custom nodes: {e}")
        return False


def load_custom_nodes():
    base_node_names = set(NODE_CLASS_MAPPINGS.keys())
    node_paths = folder_paths.get_folder_paths("custom_nodes")
    node_import_times = []
    for custom_node_path in node_paths:
        possible_modules = os.listdir(os.path.realpath(custom_node_path))
        if "__pycache__" in possible_modules:
            possible_modules.remove("__pycache__")

        for possible_module in possible_modules:
            module_path = os.path.join(custom_node_path, possible_module)
            if (
                os.path.isfile(module_path)
                and os.path.splitext(module_path)[1] != ".py"
            ):
                continue
            if module_path.endswith(".disabled"):
                continue
            time_before = time.perf_counter()
            success = load_custom_node(module_path, base_node_names)
            node_import_times.append(
                (time.perf_counter() - time_before, module_path, success)
            )

    if len(node_import_times) > 0:
        logging.info("\nImport times for custom nodes:")
        for n in sorted(node_import_times):
            if n[2]:
                import_message = ""
            else:
                import_message = " (IMPORT FAILED)"
            logging.info("{:6.1f} seconds{}: {}".format(n[0], import_message, n[1]))
        logging.info("")


def init_custom_nodes():
    extras_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "comfy_extras"
    )
    extras_files = [
        "nodes_latent.py",
        "nodes_hypernetwork.py",
        "nodes_upscale_model.py",
        "nodes_post_processing.py",
        "nodes_mask.py",
        "nodes_compositing.py",
        "nodes_rebatch.py",
        "nodes_model_merging.py",
        "nodes_tomesd.py",
        "nodes_clip_sdxl.py",
        "nodes_canny.py",
        "nodes_freelunch.py",
        "nodes_custom_sampler.py",
        "nodes_hypertile.py",
        "nodes_model_advanced.py",
        "nodes_model_downscale.py",
        "nodes_images.py",
        "nodes_video_model.py",
        "nodes_sag.py",
        "nodes_perpneg.py",
        "nodes_stable3d.py",
        "nodes_sdupscale.py",
        "nodes_photomaker.py",
        "nodes_cond.py",
        "nodes_morphology.py",
        "nodes_stable_cascade.py",
        "nodes_differential_diffusion.py",
        "nodes_ip2p.py",
        "nodes_model_merging_model_specific.py",
        "nodes_pag.py",
        "nodes_align_your_steps.py",
        "nodes_attention_multiply.py",
        "nodes_advanced_samplers.py",
        "nodes_webcam.py",
        "nodes_audio.py",
        "nodes_sd3.py",
        "nodes_gits.py",
    ]

    import_failed = []
    for node_file in extras_files:
        if not load_custom_node(os.path.join(extras_dir, node_file)):
            import_failed.append(node_file)

    load_custom_nodes()

    if len(import_failed) > 0:
        logging.warning(
            "WARNING: some comfy_extras/ nodes did not import correctly. This may be because they are missing some dependencies.\n"
        )
        for node in import_failed:
            logging.warning("IMPORT FAILED: {}".format(node))
        logging.warning(
            "\nThis issue might be caused by new missing dependencies added the last time you updated ComfyUI."
        )
        if args.windows_standalone_build:
            logging.warning("Please run the update script: update/update_comfyui.bat")
        else:
            logging.warning("Please do a: pip install -r requirements.txt")
        logging.warning("")
