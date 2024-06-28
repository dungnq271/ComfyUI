import os
import sys
import json
import hashlib
import traceback
import math
import time
import random
import logging

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "comfy"))

import comfy.llm
import comfy.utils

import comfy.model_management
from comfy.cli_args import args

import importlib

import folder_paths
import wikipedia


def before_node_execution():
    comfy.model_management.throw_exception_if_processing_interrupted()


def interrupt_processing(value=True):
    comfy.model_management.interrupt_current_processing(value)


class Input:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "dynamicPrompts": True}),
            }
        }

    RETURN_TYPES = ("TEXT",)
    FUNCTION = "generate"

    CATEGORY = "prompt"

    def generate(self, text):
        return (text,)    


class LLM:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_name": (["gpt-3.5-turbo", "claude-3-haiku-20240307"],),
                "system_prompt": ("STRING", {"multiline": True, "dynamicPrompts": True}), 
                "prompt": ("TEXT", ), 
            }
        }

    RETURN_TYPES = ("TEXT",)
    FUNCTION = "generate"

    CATEGORY = "LLM"

    def generate(self, model_name, system_prompt, prompt):
        llm = comfy.llm.get_llm(model_name, system_prompt=system_prompt)
        return (llm.complete(prompt).text,)


class WikipediaSearch:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "language": (["en", "vi"], ),
                "num_results": ("INT", {"dynamicPrompts": True}),
                "query": ("TEXT", ),
            }
        }

    RETURN_TYPES = ("TEXT",)
    FUNCTION = "search"

    CATEGORY = "SEARCH"

    def search(self, language, num_results, query):
        summaries = []
        wikipedia.set_lang(language)
        results = wikipedia.search(query)

        if num_results > len(results):
            num_results = len(results)

        for idx in range(num_results):
            try:
                result = wikipedia.page(results[idx])
                summary = result.summary
                summaries.append(summary)
            except wikipedia.exceptions.PageError as e:
                print(e)                

        return ("\n".join(summaries), )


class End:
    def __init__(self):
        self.type = "output"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("TEXT",),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "print_text"

    OUTPUT_NODE = True

    CATEGORY = "text"

    def print_text(self, text):
        print(text)
        return {"ui": {"text": [{"text": text, "type": self.type}]}}


NODE_CLASS_MAPPINGS = {
    "Input": Input,
    "LLM": LLM,
    "WikipediaSearch": WikipediaSearch,
    "End": End,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Input": "Input (Prompt)",
    "LLM": "LLM (System Prompt)",
    "WikipediaSearch": "Wikipedia Search",
    "End": "End",
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
