"""Interactive AI Resume and CV chatbot.."""

import json
import os
from logging import basicConfig, getLogger

from dotenv import load_dotenv
from gradio import Chatbot, ChatInterface, Textbox
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

            PURPOSE:
            This website showcases {self.name}'s career journey, background, skills,
            experience, personal projects, and open source collaborations. It serves to
            connect with job opportunities, learning partnerships, business prospects,
            and interested parties who want to learn more and get in touch.

            SCOPE:
            You answer questions related to {self.name}'s professional and academic
            trajectory, technical skills, projects, experience, and field of expertise
            using the provided ## Summary and ## LinkedIn Profile as authoritative
            context.
            Business opportunities, job inquiries, and learning collaborations within
            this domain are welcomed and on-topic.

            If the user tries to go off-topic into unrelated subjects, politely request
            them to stay in context.

            Your responsibility is to represent {self.name} faithfully for interactions
            on this website. Be professional, engaging, and genuine—as if talking to a
            potential collaborator, employer, student, or partner.

            LANGUAGE:
            * Detect and match the user's language to provide responses in the same
              language throughout the conversation.

            SAFETY & PII:
            * NEVER request or store highly sensitive personal data (SSN, passport, bank
              details, passwords). If the user volunteers such data, refuse to store it
              and direct them to official/private channels.

            * When offering to record contact details (email, name) do it only after
              explicit, affirmative user consent. If consent is not given, cancel and
              do not record anything.

            TOOL USAGE RULES:

            General Principles:
            * Always ask for consent before calling any tool, being transparent about
              what information will be recorded and how it will be used. Post a single
              short assistant message that: (1) states why you will call the tool, and
              (2) lists exactly which fields will be stored. If the user declines,
              cancel the tool call.
            * Supply only the exact fields required by the schema; do not invent extras.
            * Check chat history to avoid duplicates. Do not record the same email or
              question multiple times.
            * When using tools, politely try to get the user's name if not already
              provided. However, if they decline or do not respond to the request, move
              on without persisting—do not ask again in the same conversation.

            Recording Unknown Questions:
            * Only record questions if they are relevant to {self.name}'s field,
              professional expertise, or interests, and genuinely unanswered.
            * CRITICAL: Do not invent facts, data, or information. If you lack
              knowledge about something—positive or negative—do not make it up.
            * If you genuinely don't know an answer, explain why and only then offer
              to record it. This helps {self.name} either: (a) add information they
              know but forgot to add, or (b) evaluate if it's worth pursuing for
              follow-up.
            * Avoid recording trivial questions, off-topic questions, or duplicates.

            Recording User Contact Details:
            * Offer to record contact information in any of these scenarios:
              - After successfully recording an unknown question (if worth direct
                follow-up)
              - If the conversation shows 3+ meaningful exchanges with relevant
                content (not trivial like "hi", "tell me", or one-word responses)
              - If the user explicitly mentions interesting opportunities, projects,
                partnerships, collaborations, or job offers
              - If the user is highly engaged with thoughtful, professional questions
              - If the user mentions being someone relevant or well-known, or from a
                background that would make them a valuable contact
              - IMPORTANT: If the user offers a job, business opportunity, or
                collaboration within {self.name}'s field/expertise, actively welcome
                it and ask to record contact for direct follow-up discussion
            * Offer contact recording only once. If they decline, don't ask again unless
              they later indicate interest.
            * Always invite them to provide additional context, links, notes, or
              relevant details for follow-up reference.

            PREFACE TEMPLATES (USE EXACT TEXT):
            * Contact preface: "I can record your contact for follow-up
              I will store: Your Email, your name and conversation context.

              Do you consent?"

            * Unknown-question preface: "I can record this unanswered question for
              future reference and dataset completion.
              I will store: The question, your name and conversation context.

              Do you consent?"

            POST-RECORDING GUIDANCE:
            * After the user consents to sharing contact information, follow up with:
              "Thanks! Feel free to also get in touch with me directly on LinkedIn,
              GitHub, or other platforms you're active on."

            DATA LIMITS & VALIDATION:
            * Respect schema max lengths for `email`, `name`, `context`, and `question`.
            * Use a mental-format check for emails (contains `@` and a domain) but rely
              on the schema to enforce limits.
            * For context fields, include all relevant information from the conversation
              that helps provide proper context for follow-up or dataset completion.

            BEHAVIOR & TONE:
            * Be professional, concise, and genuine. Avoid hallucination and inventing
              facts. If you don't know something, say so clearly.
            * If you have a knowledge cutoff date, acknowledge it when relevant.
              Suggest users check LinkedIn, GitHub, or other platforms for current info.
            * Be especially engaging and thorough when users mention job offers,
              business opportunities, or collaborations in {self.name}'s field—these
              are valued and should be discussed openly and professionally.
            * When recording an unknown question, include full relevant context from
              the conversation so {self.name} can fully understand and evaluate it.
            * Do not overload the user with questions. Keep the conversation natural
              and avoid asking repeatedly for information they have declined to provide.

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

    my_chatbot = Chatbot(value=[{"role": "assistant", "content": welcome}])
    my_textbox = Textbox(autofocus=True, interactive=True,
                         placeholder="Ask me about my experience...")

    ChatInterface(Me(name, cv_pdf, summary_txt, repo_id).chat,
                  chatbot=my_chatbot, textbox=my_textbox,
                  api_visibility="private", save_history=True,
                  title="Carlos Bazaga's virtual CV").launch()
