---
title: Carlos Bazaga's Career Conversation Digital Twin.
app_file: app.py
sdk: gradio
sdk_version: 6.8.0
license: mit
emoji: 📚
colorFrom: gray
colorTo: yellow
short_description: Carlos Bazaga's background, experience, and key projects.
pinned: true
thumbnail: >-
  https://cdn-uploads.huggingface.co/production/uploads/67caf50af30e4fe450042ac4/yKmJhrBhO66PULG4SZQ0F.png
---

## Career conversation digital twin

AI-powered interactive chatbot about my own academic and professional career.

## TODO

* [ ] **Message timestamps for time-aware behavior**: Add timestamps to all
  messages so the model can react to time gaps (e.g., "good morning, long
  time no see"). Enable time-window-based decisions like "5 errors within
  1 hour voids that error record" or graceful timeout behaviors. Useful for
  natural conversation and smart error recovery strategies.

* [ ] **Time-window error tracking**: Implement error rate tracking with time
  windows to inform when to gracefully degrade service or reset error
  counters (e.g., 24-hour window for error count reset).
