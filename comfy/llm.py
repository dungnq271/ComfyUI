import os
from dotenv import find_dotenv, load_dotenv

from llama_index.core import Settings
from llama_index.core.utils import get_tokenizer
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.openai import OpenAI

_ = load_dotenv(find_dotenv())  # read local .env file

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")


def get_llm(model, **kwargs):
    if "gpt" in model:
        llm = OpenAI(model=model, **kwargs)
        Settings.tokenizer = get_tokenizer()
    elif "claude" in model:
        llm = Anthropic(model=model, **kwargs)
        Settings.tokenizer = Anthropic().tokenizer
    Settings.llm = llm
    return llm
