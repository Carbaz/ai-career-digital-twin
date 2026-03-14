"""Main entrypoint module for the AI Career Digital Twin application."""

from logging import getLogger

from gradio import __version__ as gr_version

from .interface import get_interface


_logger = getLogger(__name__)


def main(name, profile_pdf, summary_text, repo_id):
    """Launch the AI Career Digital Twin application."""
    _logger.info('STARTING AI CAREER DIGITAL TWIN...')
    app = get_interface(name, profile_pdf, summary_text, repo_id)
    app.launch(footer_links=["gradio"])
    # We return the app instance for potential use in autoreload scenarios.
    return app


if __name__ == '__main__':
    name = "Carlos Bazaga"
    profile_pdf = "Profile.pdf"
    summary_text = "Summary.md"
    repo_id = "Carbaz/career_datastore"
    main(name, profile_pdf, summary_text, repo_id)
