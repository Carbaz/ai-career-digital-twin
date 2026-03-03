"""Interactive AI Resume and CV chatbot.."""

import json
import os
from logging import basicConfig, getLogger

from dotenv import load_dotenv
from gradio import Chatbot, ChatInterface
from huggingface_hub import hf_hub_download
from openai import OpenAI
from pypdf import PdfReader
from requests import post


# Environment initialization.
load_dotenv(override=True)
HF_SELF_TOKEN = os.getenv("HF_SELF_TOKEN")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")


# Setup the global logger.
LOG_STYLE = '{'
LOG_LEVEL = 'INFO'
LOG_FORMAT = ('{asctime} {levelname:<8} {processName}({process}) '
              '{threadName} {name} {lineno} "{message}"')
basicConfig(level=LOG_LEVEL, style='{', format=LOG_FORMAT)
_logger = getLogger(__name__)
_logger.info('INITIALIZED LOGGER')


def read_pdf_from_hub(repo_id, filename) -> str:
    """Download a PDF from the Hugging Face Hub and return its extracted text."""
    try:
        path = hf_hub_download(repo_id=repo_id, repo_type="dataset", filename=filename,
                               token=HF_SELF_TOKEN)
    except Exception as ex:
        _logger.error(f"FAILED TO DOWNLOAD PDF FROM HUB: {repo_id}/{filename}: {ex}")
        return ""
    try:
        reader = PdfReader(path)
    except Exception as ex:
        _logger.error(f"FAILED TO OPEN PDF FILE AT {path}: {ex}")
        return ""
    text_out = ""
    for page in reader.pages:
        try:
            text = page.extract_text()
        except Exception as ex:
            _logger.error(f"FAILED TO EXTRACT TEXT FROM A PAGE IN {path}: {ex}")
            text = None
        if text:
            text_out += text
    return text_out


def read_text_from_hub(repo_id, filename) -> str:
    """Download a text file from the Hugging Face Hub and return its contents."""
    try:
        path = hf_hub_download(repo_id=repo_id, repo_type="dataset", filename=filename,
                               token=HF_SELF_TOKEN)
    except Exception as ex:
        _logger.error(f"FAILED TO DOWNLOAD TEXT FROM HUB: {repo_id}/{filename}: {ex}")
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as ex:
        _logger.error(f"FAILED TO READ TEXT FROM {path}: {ex}")
        return ""


def push_notification(title, message):
    """Send a push notification using Pushover."""
    post("https://api.pushover.net/1/messages.json",
         data={"sound": "gamelan",
               "title": title, "message": message,
               "user": os.getenv("PUSHOVER_USER"),
               "token": os.getenv("PUSHOVER_TOKEN")})


def record_user_details(email, name="No Name", context="No Context"):
    """Record user details via a push notification."""
    push_notification("Career Contact Request.",
                      f"From: {name} with email: {email}"
                      f"\n\nIn context:\n{context}")
    return {"recorded": "ok"}


def record_unknown_question(question, name="No Name", context="No Context"):
    """Record an unknown question via a push notification."""
    push_notification("Career Unknown Question.",
                      f"{name} asked: {question}"
                      f"\n\nIn context:\n{context}")
    return {"recorded": "ok"}


# Define tool JSON schema for the "record_user_details" tool.
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch"
                   " and provided an email address"
                   " along with any additional details provided such as their name or "
                   " context about the conversation",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "maxLength": 254,
                "format": "email",
                "description": "The email address of this user"},
            "name": {
                "type": "string",
                "maxLength": 100,
                "description": "The user's name if they provided it"},
            "context": {
                "type": "string",
                "maxLength": 550,
                "description": "Any additional contextual information about the"
                               " conversation that's worth recording for follow-up"}},
        "required": ["email"],
        "additionalProperties": False}}


# Define tool JSON schema for the 'record_unknown_question' tool.
record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Use this tool to record any question that couldn't be answered as "
                   " you didn't know the answer"
                   " along with any additional details provided such as their name or "
                   " context about the conversation",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "maxLength": 300,
                "description": "The question that couldn't be answered"},
            "name": {
                "type": "string",
                "maxLength": 100,
                "description": "The user's name if they provided it"},
            "context": {
                "type": "string",
                "maxLength": 550,
                "description": "Any additional contextual information about the"
                               " conversation that's worth recording for follow-up"}},
        "required": ["question"],
        "additionalProperties": False}}


# List of available tools.
tools = [{"type": "function", "function": record_user_details_json},
         {"type": "function", "function": record_unknown_question_json}]

tools_map = {"record_user_details": record_user_details,
             "record_unknown_question": record_unknown_question}


class Me:
    """Class representing myself for the chatbot."""
    def __init__(self, name, cv_pdf_filename, summary_filename, repo_id):
        """Initialize the Me class by loading profile and summary from Hugging Face."""
        self.openai = OpenAI()
        self.name = name
        # Download PDF CV from Hugging Face Hub and extract text.
        self.linkedin = read_pdf_from_hub(repo_id, cv_pdf_filename)
        # Download Summary from Hugging Face Hub and read text.
        self.summary = read_text_from_hub(repo_id, summary_filename)

    def handle_tool_call(self, tool_calls):
        """Handle tool calls made by the AI model."""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            _logger.info(f"TOOL CALLED: {tool_name}")
            tool = tools_map.get(tool_name)
            if not tool:
                _logger.error(f"TOOL NOT FOUND: {tool_name}")
                result = {}
            else:
                try:
                    result = tool(**arguments)
                except Exception as ex:
                    _logger.error(f"ERROR EXECUTING TOOL {tool_name}: {ex}")
                    result = {}
            results.append({"role": "tool",
                            "content": json.dumps(result),
                            "tool_call_id": tool_call.id})
        return results

    def system_prompt(self):
        """Generate the system prompt for the chatbot."""
        return f"""You are acting as {self.name}.

            You are answering questions on {self.name}'s website, particularly questions
            related to {self.name}'s career, background, skills and experience using the
            provided ## Summary and ## LinkedIn Profile as authoritative context.

            Stick conversation to those topics, if the user tries to go off there
            politely request him to stay in context.

            Your responsibility is to represent {self.name} for interactions on the
            website as faithfully as possible.

            You are given a summary of {self.name}'s background and LinkedIn profile
            which you can use to answer questions.

            Be professional and engaging, as if talking to a potential client or future
            employer who came across the website.

            SAFETY & PII:
            * NEVER request or store highly sensitive personal data (SSN, passport, bank
            details, passwords). If the user volunteers such data, refuse to store it and
            direct them to official/private channels.
            * Only record contact details (email, name) after explicit, affirmative user
            consent. If consent is not given, do not record anything.

            If you don't know the answer to any professional or academic related question
            use your 'record_unknown_question' tool to record the question that you
            couldn't answer, provide context about the conversation and history so later
            I can complete the source data with the appropriate information.

            Avoid recording questions about something trivial or unrelated to career
            and avoid recording repeated questions.

            If the user is engaging in discussion, or have unanswered relevant or
            important questions try to steer them towards getting in touch via email;
            ask for their email and a name to record using your 'record_user_details'
            tool. Do this only once to avoid annoying the user or spamming me with same
            email several times, if user insists remind him that you already have their
            email and you'll contact them.

            Offer them to provide any additional notes, links, etc. he feels relevant,
            as a position offer link or a relevant publication, whatever you or he sees
            related and relevant to the conversation so I can take into account when
            reaching back to him.

            Send the provided notes plus the context about the conversation and history
            together but mind the total size must respect limits.

            For both tools try politely always to get the user's name, ask if necessary,
            and provide context about the conversation context and history, but avoid
            asking for information that the user might not want to provide.

            TOOL USAGE RULES:
            * Call tools only when strictly necessary:
            * `record_user_details`: Only after explicit consent and when you have an
               email-like string.
            * `record_unknown_question`: Only when you cannot answer after consulting
              Summary and LinkedIn, and only on professional or academic related topics.
            * Before any tool call, post a single short assistant message that: (1)
              states why you will call the tool, and (2) lists exactly which fields will
              be stored (See below). If the user declines in reply, cancel the tool call.
            * Check chat history to avoid duplicates. Do not record the same email or
              question multiple times.
            * Supply only the exact fields required by the schema; do not invent extras.

            PREFACE TEMPLATES (USE EXACT TEXT):
            * Contact preface: "I can record your contact for follow-up
              I will store: Your Email, your name and conversation context.

              Do you consent?"

            * Unknown-question preface: "I can record this unanswered question for
              future reference and dataset completion.
              I will store: The question, your name and conversation context.

              Do you consent?"

            DATA LIMITS & SIMPLE VALIDATION:
            * Respect schema max lengths for `email`, `name`, `context`, and `question`.
              Use a mental-format check for emails (contains `@` and a domain) but rely
              on the schema to enforce limits.
            * Keep context minimal and non-verbatim where possible (summarize rather than
              copy long text, unless literal quoting proves useful as an exception).

            BEHAVIOR & TONE:
            * Be professional, concise, and avoid hallucination. If you do not know an
              answer, say you don't know and offer to record the question for dataset
              improvement and later updates.
            * Ask for name/email only once and only when consented; if already provided,
              acknowledge and do not re-ask.
            * When recording an unknown question, include at least one short reason
              (1 sentence) why it was recorded as a context, always try to make use
              of the context size provided on the schema if there is enough information.

            ## Summary:
            {self.summary}

            ## LinkedIn Profile:
            {self.linkedin}

            With this context, please chat with the user,
            always staying in character as {self.name}.
            """

    def chat(self, message, history):
        """Handle a chat message from the user."""
        messages = [{"role": "system", "content": self.system_prompt()}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        while True:  # Loop to handle tool calls until no more are needed.
            response = self.openai.chat.completions.create(
                model=CHAT_MODEL, messages=messages, tools=tools)
            # Check if the response includes tool calls.
            if response.choices[0].finish_reason != 'tool_calls':
                break
            message = response.choices[0].message
            results = self.handle_tool_call(message.tool_calls)
            messages.append(message)
            messages.extend(results)
        return response.choices[0].message.content


if __name__ == "__main__":
    name = "Carlos Bazaga"
    cv_pdf = "linkedin.pdf"
    summary_txt = "summary.txt"
    repo_id = "Carbaz/career_datastore"
    welcome = (f"Hello, I'm {name}'s career digital twin."
               "\nI can answer questions about my career, background and experience."
               "\nYou may write in any language and I will reply in the same language."
               "\nHow can I help you today?")
    chatbot = Chatbot(value=[{"role": "assistant", "content": welcome}])
    ChatInterface(Me(name, cv_pdf, summary_txt, repo_id).chat, chatbot=chatbot,
                  api_visibility="private", save_history=True,
                  title="Carlos Bazaga's virtual CV").launch()
