"""Entrypoint wrapper for Hugging Face Spaces. Delegates to src/__main__.py."""

from src.__main__ import main


name = "Carlos Bazaga"
cv_pdf = "linkedin.pdf"
summary_txt = "summary.txt"
repo_id = "Carbaz/career_datastore"

# HBD: We assign the 'app' to 'demo' to allow watch autoreload:
# 'demo' is required to be defined at the global scope for reload to work in Gradio.
# Initial warnings may appear at launch with 'gradio app.py' because 'demo' will not
# exists until the app service ends inside main, but it will do when reload requires it,
# once the service has been stopped.
demo = main(name, cv_pdf, summary_txt, repo_id)
