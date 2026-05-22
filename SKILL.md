# 🧠 LuminAI Triage — Skills & Technology Justification

This document explains the core technical skills, models, tools, libraries, and design choices used throughout the LuminAI Triage agentic triage system.

---

## 🤖 AI & Language Model

### medgemma:4b (via Ollama)
- **What it is:** Google's medically specialized 4-billion parameter language model, purpose-built for clinical understanding and health dialogue.
- **Why we chose it:** Unlike generic LLMs (e.g., Llama, Mistral), medgemma has been fine-tuned on medical datasets, providing more accurate condition recognition, appropriate clinical language, and safer triage responses.
- **How it runs:** Locally via [Ollama](https://ollama.com), zero cloud API calls, zero cost, and complete patient data privacy.

---

## 🔊 Voice Pipeline

### SpeechRecognition (STT)
- **Library:** `SpeechRecognition >= 3.10.0`
- **Backend used:** Google Web Speech API (free, zero API keys, high accuracy)
- **Why:** The assignment requires functional voice input. Google's backend provides state-of-the-art transcription for a wide range of accents and noise conditions at zero cost.
- **Fallback:** Gracefully handles `UnknownValueError` (silence or unclear speech) without crashing.

### gTTS — Google Text-to-Speech (TTS, Tier 1)
- **Library:** `gTTS >= 2.3.0`
- **Why:** Produces natural-sounding, cloud-synthesized MP3 audio. Outputs a file which Gradio streams back natively to the browser audio player.

### pyttsx3 — Offline SAPI5 TTS (TTS, Tier 2 Fallback)
- **Library:** `pyttsx3 >= 2.90`
- **Why:** If the user has no internet, the system gracefully degrades to Windows' built-in Speech API (SAPI5) voice synthesizer — ensuring the voice loop is always functional regardless of network conditions.

---

## 🖥️ Interface

### Gradio
- **Library:** `gradio >= 4.0.0`
- **Why:** Provides a professional, production-quality web UI that works out-of-the-box without any frontend (HTML/JS/CSS) development. Critical for keeping the system **runnable by any reviewer** with a single `python Lumin.py` command.
- **Key features used:**
  - `gr.Audio` (microphone source for voice input)
  - `gr.Chatbot` (structured multi-turn conversation view)
  - `gr.Accordion` (collapsible SMTP config panel)
  - `gr.themes.Soft` with custom Google Fonts for premium medical UI aesthetics

---

## ⚙️ Agentic Orchestration

### n8n (Workflow Automation)
- **Why n8n:** Provides a **visual, auditable canvas** where every agent decision step is visible as a connected node — ideal for demonstrating the agentic architecture requirement.
- **Nodes in the LuminAI Triage Workflow:**
  | Node | Role |
  |---|---|
  | Webhook Trigger | Receives patient payload from Gradio frontend |
  | AI Agent (medgemma:4b) | Classifies symptoms, assesses severity, generates response |
  | Ollama Chat Model | LLM backend subnode powering the agent |
  | JSON Parser | Cleans LLM output, applies clinical safety overrides |
  | Is-Severe IF Branch | Routes flow based on severity assessment |
  | Simulated SMTP Alert | Logs structured clinical HTML alert for severe cases |
  | Webhook Response | Returns JSON response to Gradio frontend |

### push_workflow.py (Developer Infrastructure Script)
- Programmatically built and deployed the entire n8n visual workflow via the n8n REST API to the hosted zrok instance.
- This script acts as Infrastructure-as-Code (IaC) to guarantee the workflow was deployed flawlessly to the backend, removing any need for manual GUI configuration.

---

## 🌐 Networking

### zrok (Secure Public Tunnel)
- **Why:** n8n runs locally on port `5678`. zrok exposes it securely to the internet via `https://sopranosn8n.share.zrok.io`, allowing the Gradio frontend (also local) and automated tests to reach the webhook from any network.
- **Alternative:** Similar in purpose to `ngrok`, but open-source.

### requests
- **Library:** `requests >= 2.31.0`
- Used for: frontend → n8n webhook calls, ntfy.sh push notifications.

---

## 📢 Alert System

### ntfy.sh (Zero-Credential Push Notifications)
- **Why:** The assignment requires physician notification for severe cases. Standard SMTP requires credentials that evaluators may not provide. ntfy.sh delivers real-time push alerts to any browser or mobile device with **zero accounts, zero passwords, zero setup**.
- **How:** A simple `requests.post()` to `https://ntfy.sh/luminai-health-triage-alerts` with the clinical summary in the body.

### smtplib (Real SMTP Email)
- **Library:** Python standard library (`smtplib`, `email.mime`)
- **Why:** Fulfills the assignment requirement for physician email dispatch when SMTP credentials are provided. Compatible with Gmail (App Passwords), Outlook, and any standard SMTP provider.

---

## 🧪 Testing

### unittest + requests
- **File:** `test_triage.py`
- **Coverage:** 4 end-to-end test cases covering all critical triage paths:
  1. Mild Upper Respiratory Issue
  2. Severe Fever Emergency
  3. Out-of-Scope Routing
  4. Clinical Safety Override (emergency keyword detection)
- Tests target the live zrok webhook, making them true integration tests of the full agentic pipeline.

---

## 📝 Logging

### triage.log
- A persistent, human-readable interaction log saved to the workspace directory.
- Records every patient interaction: input method, symptoms, category, severity, structured case summary, and agent response.
- Provides a full audit trail for evaluators to verify the system's decisions without needing to re-run every scenario.
