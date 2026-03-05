---
title: Carlos Bazaga's Career Conversation Digital Twin.
app_file: app.py
sdk: gradio
sdk_version: 6.8.0
license: mit
emoji: 📚
colorFrom: gray
colorTo: yellow
short_description: Owner's Career Conversation Digital Twin.
pinned: true
thumbnail: >-
  https://cdn-uploads.huggingface.co/production/uploads/67caf50af30e4fe450042ac4/yKmJhrBhO66PULG4SZQ0F.png
---

## Career conversation digital twin

This project is an interactive chatbot that answers questions about the owner's
professional career and projects. It uses an LLM model for natural language
understanding and a simple web interface powered by [Gradio](https://www.gradio.app/).

It is designed to be deployed as a Space on
[Hugging Face](https://huggingface.co/spaces).

It can also record unanswered questions and user contact details (email),
sending notifications via [Pushover](https://pushover.net/).

> [!NOTE]
>
> * The chatbot does not store sensitive data or answer questions outside the
>   owner's professional profile.
> * If you have issues with the interface, use Gradio version 5.x for best
>   compatibility. (For HuggingFace Spaces deployment change it up on this file)

## Project's Structure & Architecture

**Structure:**

* `app.py`: Entry point. Delegates to the main function in `src/__main__.py`.
* `Pipfile`: Dependency and environment management for local development.
* `src/`
  * `__main__.py`: Launches the app and exposes the `main()` function.
  * `interface.py`: Configures the Gradio chat interface.
  * `assistant.py`: Assistant logic and tool orchestration.
  * `prompts.py`: System messages and templates.
  * `tools.py`: Functions for reading data and sending notifications.

**Architecture:**

* The project is modular and organized for clarity and maintainability.
* The entrypoint (`app.py`) delegates to the main logic in `src/__main__.py`.
* The assistant logic, prompts, and tools are separated into their own modules.
* The interface is managed in `interface.py`, which adapts to Gradio 5.x or 6.x.
* All environment variables are loaded in each module as needed, making them
  autonomous and easy to reuse.

## Quick Deployment

* Install dependencies and create a virtual environment using pipenv:

  > [!TIP]
  > It is recommended to use the provided `Pipfile` and `pipenv` to create your
  > virtual environment for local development.
  >
  > The `requirements.txt` is mainly for Hugging Face Spaces deployment,
  > but can be used locally if needed.

  ```bash
  pipenv install
  pipenv shell
  ```

* Create a `.env` file in the root directory with the required variables.\
  *(see below)*

* Run the app with gradio to enable auto-reload:

  ```bash
  gradio app.py
  ```

* Open your browser at the URL shown by Gradio.\
  *(default is <http://localhost:7860>)*

## Required Environment Variables

You must define these variables in a `.env` file:

* `OPENAI_API_KEY`: OpenAI API key for LLM access.
* `HF_SELF_TOKEN`: Hugging Face token to download private files.
* `PUSHOVER_USER`: Pushover user key for notifications.
* `PUSHOVER_TOKEN`: Pushover API token.
* `CHAT_MODEL`: (optional) OpenAI model to use (default: `gpt-4o-mini`).
* `GRADIO_STATE_SECRET_CV_TWIN`: A random secret key to make sure sessions recorded
  are kept between service restarts.

Example `.env`:

```env
HF_SELF_TOKEN="your_hf_token"
PUSHOVER_USER="your_user_key"
PUSHOVER_TOKEN="your_api_token"
CHAT_MODEL="gpt-4o-mini"
GRADIO_STATE_SECRET_CV_TWIN="your_generated_secret_key"
```

## TODO

* [ ] **Message timestamps for time-aware behavior**: Add timestamps to all
  messages so the model can react to time gaps (e.g., "good morning, long
  time no see"). Enable time-window-based decisions like "5 errors within
  1 hour voids that error record" or graceful timeout behaviors. Useful for
  natural conversation and smart error recovery strategies.

* [ ] **Time-window error tracking**: Implement error rate tracking with time
  windows to inform when to gracefully degrade service or reset error
  counters (e.g., 24-hour window for error count reset).

* [ ] **Finish parametrizing personal information**: Move all personal/profile
  data (name, CV, summary, etc.) to environment variables or configuration files
  for easier reuse and deployment.
