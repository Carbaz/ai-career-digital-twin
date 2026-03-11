"""Interface module for the AI Career Digital Twin application."""

from logging import getLogger
from os import getenv
from secrets import choice
from string import ascii_letters, digits

from dotenv import load_dotenv
from gradio import Chatbot, ChatInterface
from gradio import __version__ as gr_version

from .assistant import Assistant
from .prompts import get_welcome_message


_logger = getLogger(__name__)

# Environment initialization.
load_dotenv(override=True)


# Load or generate the secret for saved conversations.
# This is used to encrypt the saved conversations in the browser local storage,
# so it's important to keep it secret consistent across restarts if you want to
# keep the conversation history.
if MY_CHAT_SECRET := getenv("GRADIO_STATE_SECRET_CV_TWIN"):
    _logger.info("FIXED SECRET")
else:
    _logger.error("RANDOM SECRET")
    MY_CHAT_SECRET = "".join(choice(ascii_letters + digits) for _ in range(16))


def get_interface(name, cv_pdf, summary_txt, repo_id):
    """Get the Gradio ChatInterface for the AI Career Digital Twin."""
    match gr_version[0]:
        case "5":
            _logger.info(f"GRADIO 5 DETECTED: {gr_version}")
            chat_ifz_conf = {"type": "messages", "show_api": "false", "api_name": False}
            chat_bot_conf = {"type": "messages",
                            "show_copy_all_button": True,
                            "show_copy_button": True}
        case "6":
            _logger.info(f"GRADIO 6 DETECTED: {gr_version}")
            chat_ifz_conf = {"api_visibility": "private"}
            chat_bot_conf = {"buttons": ["copy", "copy_all"]}

    my_chatbot = Chatbot(value=[{"role": "assistant",
                                 "content": get_welcome_message(name)}],
                            label=f"{name} Digital Twin",
                            max_height=1000, scale=1,
                            **chat_bot_conf)

    app = ChatInterface(Assistant(
        name, cv_pdf, summary_txt, repo_id).chat,
        chatbot=my_chatbot, autofocus=False, **chat_ifz_conf, fill_height=False,
        save_history=True, title="Carlos Bazaga's virtual CV")

    # Set the secret for encrypting saved conversations.
    app.saved_conversations.secret = MY_CHAT_SECRET

    return app
