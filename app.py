"""Interactive AI Resume and CV chatbot.."""

import os
import secrets
import string
from logging import basicConfig, getLogger

from assistant import Assistant
from dotenv import load_dotenv
from gradio import Chatbot, ChatInterface


# Setup the global logger.
LOG_STYLE = '{'
LOG_LEVEL = 'INFO'
LOG_FORMAT = ('{asctime} {levelname:<8} {processName}({process}) '
              '{threadName} {name} {lineno} "{message}"')
basicConfig(level=LOG_LEVEL, style=LOG_STYLE, format=LOG_FORMAT)
_logger = getLogger(__name__)
_logger.info('INITIALIZED LOGGER')


# Environment initialization.
load_dotenv(override=True)

# Load or generate the secret for saved conversations.
# This is used to encrypt the saved conversations in the database,
# so it's important to keep it secret and consistent across restarts
# if you want to keep the conversation history.
if MY_CHAT_SECRET := os.getenv("GRADIO_STATE_SECRET_CV_TWIN"):
    _logger.info("FIXED SECRET")
else:
    _logger.error("RANDOM SECRET")
    MY_CHAT_SECRET = "".join(secrets.choice(
        string.ascii_letters + string.digits)
        for _ in range(16))

if __name__ == "__main__":
    name = "Carlos Bazaga"
    cv_pdf = "linkedin.pdf"
    summary_txt = "summary.txt"
    repo_id = "Carbaz/career_datastore"
    welcome = (f"Hello, I'm {name}'s career digital twin."
               "\nI can answer questions about my career, background and experience."
               "\nYou may write in any language and I will reply in the same language."
               "\nHow can I help you today?")

    # my_chatbot = Chatbot(value=[{"role": "assistant", "content": welcome}])  # Gradio 6

    my_chatbot = Chatbot(value=[{"role": "assistant", "content": welcome}],
                        label=f"{name} Digital Twin",
                        scale=1,
                        height=400,
                        type="messages",
                        autoscroll=True,
                        )  # Gradio 5

    chat = ChatInterface(Assistant(
        name, cv_pdf, summary_txt, repo_id).chat,
        chatbot=my_chatbot,
        # api_visibility="private",  # Gradio 6
        type="messages", show_api="false", api_name=False,  # Gradio 5
        save_history=True, title="Carlos Bazaga's virtual CV")
    chat.saved_conversations.secret = MY_CHAT_SECRET
    chat.launch()
