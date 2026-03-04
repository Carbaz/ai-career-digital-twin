"""Tool functions and definitions for the chatbot."""

import os
from logging import getLogger

from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
from pypdf import PdfReader
from requests import post


# Environment initialization.
load_dotenv(override=True)

# Required env vars. (KeyError raised if missing)
HF_SELF_TOKEN = os.environ["HF_SELF_TOKEN"]
PUSHOVER_USER = os.environ["PUSHOVER_USER"]
PUSHOVER_TOKEN = os.environ["PUSHOVER_TOKEN"]

# Instantiate logger.
_logger = getLogger(__name__)


# Function definitions.
def read_pdf_from_hub(repo_id, filename) -> str:
    """Download PDF from HF Hub and return extracted text."""
    try:
        path = hf_hub_download(repo_id=repo_id, repo_type="dataset",
                               filename=filename, token=HF_SELF_TOKEN)
    except Exception as ex:
        _logger.error(f"FAILED TO DOWNLOAD PDF FROM HUB: "
                      f"{repo_id}/{filename}: {ex}")
        return "NO DATA"
    try:
        reader = PdfReader(path)
    except Exception as ex:
        _logger.error(f"FAILED TO OPEN PDF FILE AT {path}: {ex}")
        return "NO DATA"
    text_out = ""
    for page in reader.pages:
        try:
            text = page.extract_text()
        except Exception as ex:
            _logger.error(f"FAILED TO EXTRACT TEXT FROM A PAGE IN {path}: {ex}")
            text = None
        if text:
            text_out += text
    return text_out if text_out else "NO DATA"


def read_text_from_hub(repo_id, filename) -> str:
    """Download text file from HF Hub and return its contents."""
    try:
        path = hf_hub_download(repo_id=repo_id, repo_type="dataset",
                               filename=filename, token=HF_SELF_TOKEN)
    except Exception as ex:
        _logger.error(f"FAILED TO DOWNLOAD TEXT FROM HUB: "
                      f"{repo_id}/{filename}: {ex}")
        return "NO DATA"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content if content else "NO DATA"
    except Exception as ex:
        _logger.error(f"FAILED TO READ TEXT FROM {path}: {ex}")
        return "NO DATA"


def push_notification(title, message):
    """Send a push notification using Pushover."""
    try:
        response = post("https://api.pushover.net/1/messages.json", timeout=3,
                        data={"sound": "gamelan", "title": title,
                              "message": message, "user": PUSHOVER_USER,
                              "token": PUSHOVER_TOKEN})
        if response.status_code != 200:
            _logger.error(f"PUSHOVER NOTIFICATION FAILED: "
                          f"{response.status_code} - {response.text}")
            raise RuntimeError(f"Pushover failed: {response.status_code}")
        _logger.info(f"PUSHOVER NOTIFICATION SENT: {title}")
    except RuntimeError:
        raise
    except Exception as ex:
        _logger.error(f"PUSHOVER NOTIFICATION ERROR: {ex}")
        raise RuntimeError(f"Pushover error: {ex}") from ex


def record_user_details(email, name="No Name", context="No Context"):
    """Record user details via a push notification."""
    push_notification("Career Contact Request.",
                      f"From: {name} with email: {email}"
                      f"\n\nIn context:\n{context}")
    return {"recorded": "ok"}


def record_unknown_question(question, name="No Name",
                            context="No Context"):
    """Record an unknown question via a push notification."""
    push_notification("Career Unknown Question.",
                      f"{name} asked: {question}"
                      f"\n\nIn context:\n{context}")
    return {"recorded": "ok"}


# Define "record_user_details" tool JSON schema.
record_user_details_json = {
    "name": "record_user_details",
    "description": ("Use this tool to record that a user is interested in being "
                    "in touch and provided an email address along with any "
                    "additional details such as their name or context about the "
                    "conversation"),
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "maxLength": 254,
                "format": "email",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "maxLength": 100,
                "description": "The user's name if they provided it"
            },
            "context": {
                "type": "string",
                "maxLength": 550,
                "description": ("Any additional contextual information about the "
                                "conversation that's worth recording for follow-up")
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

# Define "record_unknown_question" tool JSON schema.
record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": ("Use this tool to record any question that couldn't be "
                    "answered as you didn't know the answer along with any "
                    "additional details such as their name or context about the "
                    "conversation"),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "maxLength": 300,
                "description": "The question that couldn't be answered"
            },
            "name": {
                "type": "string",
                "maxLength": 100,
                "description": "The user's name if they provided it"
            },
            "context": {
                "type": "string",
                "maxLength": 550,
                "description": ("Any additional contextual information about the "
                                "conversation that's worth recording for follow-up")
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

# Instantiate logger.
_logger = getLogger(__name__)

# Define tools collections.
tools_def = [{"type": "function", "function": record_user_details_json},
             {"type": "function", "function": record_unknown_question_json}]

tools_map = {"record_user_details": record_user_details,
             "record_unknown_question": record_unknown_question}
