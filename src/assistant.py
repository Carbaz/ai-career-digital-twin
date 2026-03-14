"""Assistant class for the AI Career Digital Twin application."""

from json import dumps, loads
from logging import getLogger
from os import getenv

from dotenv import load_dotenv
from openai import OpenAI

from .prompts import get_system_prompt
from .tools import read_pdf_from_hub, read_text_from_hub, tools_def, tools_map


# Environment initialization.
load_dotenv(override=True)

# Optional env vars. (with fallbacks)
CHAT_MODEL = getenv("CHAT_MODEL", "gpt-5-mini")


class Assistant:
    """Class representing myself for the chatbot."""

    def __init__(self, name, profile_pdf, summary_text, repo_id):
        """Initialize the Assistant class by loading profile and summary."""
        self.name = name
        self.openai = OpenAI()
        # Download PDF CV from Hugging Face Hub and extract text.
        self.linkedin = read_pdf_from_hub(repo_id, profile_pdf)
        # Download Summary from Hugging Face Hub and read text.
        self.summary = read_text_from_hub(repo_id, summary_text)

    def handle_tool_call(self, tool_calls):
        """Handle tool calls made by the AI model."""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = loads(tool_call.function.arguments)
            _logger.info(f"TOOL CALLED: {tool_name}")
            tool = tools_map.get(tool_name)
            if not tool:
                _logger.critical(f"TOOL NOT FOUND: {tool_name}")
                result = {"error": f"Internal error: Tool '{tool_name}' not defined"}
            else:
                try:
                    result = tool(**arguments)
                except Exception as ex:
                    _logger.error(f"ERROR EXECUTING TOOL {tool_name}: {ex}")
                    result = {"error": "Failed. Recording service unavailable"}
            results.append({"role": "tool",
                            "content": dumps(result),
                            "tool_call_id": tool_call.id})
        return results

    def chat(self, message, history):
        """Handle a chat message from the user."""
        messages = [{"role": "system",
                     "content": get_system_prompt(self.name, self.summary,
                                                  self.linkedin)}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        # Safety quota to prevent token waste from infinite tool call loops.
        max_tool_calls = len(tools_map)
        tool_calls_count = 0
        while True:  # Loop to handle tool calls until no more are needed.
            response = self.openai.chat.completions.create(
                model=CHAT_MODEL, messages=messages, tools=tools_def)
            # If the response doesn't include tool calls break the loop.
            if response.choices[0].finish_reason != 'tool_calls':
                break
            # If we've reached the max tool calls quota, log and exit the loop.
            if tool_calls_count >= max_tool_calls:
                _logger.warning(f"MAX TOOL CALLS REACHED ({max_tool_calls})")
                break
            # Handle tool calls.
            message = response.choices[0].message
            results = self.handle_tool_call(message.tool_calls)
            messages.append(message)
            messages.extend(results)
            # Increase count and loop.
            tool_calls_count += 1
        return response.choices[0].message.content


# Instantiate logger.
_logger = getLogger(__name__)
