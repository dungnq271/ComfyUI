from llama_index.core.prompts.base import PromptTemplate
from llama_index.core.prompts.prompt_type import PromptType

TOOL_QUERY_REWRITE_TMPL = (
    "Please rewrite the question to a shorter question "
    "which is then passed to the tool provided "
    "to get the information to answer the question.\n"
    "Try to include as many key details as possible.\n\n"
    "Tool description: {tool_description}\n"
    "Question: {question}\n"
    "New Question:\n"
)

DEFAULT_TOOL_QUERY_REWRITE_PROMPT = PromptTemplate(
    TOOL_QUERY_REWRITE_TMPL, prompt_type=PromptType.SUMMARY
)
