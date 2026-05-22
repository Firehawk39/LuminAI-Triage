# 🗺️ LuminAI Health — Engineering Plan

This document describes the full architectural design, engineering decisions, and phased implementation plan for the LuminAI Health Frontline Patient Triage Agent.

---

## 🎯 Objective

Build an agentic, voice-enabled, medically-informed triage workflow where a root agent:
1. Collects patient symptoms via spoken audio or typed text
2. Classifies the condition into one of three clinical categories
3. Assesses severity as **Mild** or **Severe**
4. For severe cases: generates a structured case summary and dispatches an alert to a partner physician

---

## 🏗️ System Architecture

The system uses a **hybrid distributed architecture** split into a local client layer and a server-side workflow orchestration layer:

```
+-------------------------------------------------------------+
|                    LOCAL MACHINE (Client)                   |
|                                                             |
|   +---------------------+    +-------------------------+   |
|   |   Gradio UI          |    |  Voice Pipeline         |   |
|   |   (Lumin.py)         |<-->|  - STT: SpeechRecog.    |   |
|   |   Port: 7860         |    |  - TTS: gTTS / pyttsx3  |   |
|   +----------+----------+    +-------------------------+   |
+--------------|----------------------------------------------+
               | HTTP POST JSON
               v
+-------------------------------------------------------------+
|                 n8n WORKFLOW BACKEND (zrok Tunnel)          |
|                                                             |
|   +------------------+       +------------------------+    |
|   |  Webhook Trigger | ----> |  AI Agent (medgemma:4b) |   |
|   +------------------+       +------------------------+    |
|                                        |                    |
|                              +---------v------------+       |
|                              |  JSON Parser Node    |       |
|                              |  + Safety Overrides  |       |
|                              +---------+------------+       |
|                                        |                    |
|                           +-----------v-----------+         |
|                           |  Is-Severe IF Branch  |         |
|                           +------+--------+-------+         |
|                                  |        |                  |
|                             Severe      Mild                |
|                                  |        |                  |
|                    +-------------v--+  +--v----------+      |
|                    | Simulated SMTP |  | Direct Resp |      |
|                    | Alert Node     |  | Node        |      |
|                    +----------------+  +-------------+      |
+-------------------------------------------------------------+
               | HTTP JSON Response
               v
+-------------------------------------------------------------+
|  Lumin.py: Post-Processing                                  |
|  - Real SMTP Email (if credentials provided)               |
|  - ntfy.sh Push Alert (zero-credential fallback)           |
|  - TTS Audio Synthesis                                      |
|  - triage.log Local Logging                                |
+-------------------------------------------------------------+
```

---

## ⚙️ Engineering Decisions

### 1. Local STT/TTS (Performance & Privacy)
- **SpeechRecognition** (Google Web Speech API) handles microphone audio → text transcription. Free, zero-key, high accuracy.
- **gTTS** (Google Text-to-Speech) generates natural MP3 audio responses locally.
- **pyttsx3** serves as an offline SAPI5 Windows fallback if internet is unavailable.
- Audio is processed locally to avoid sending heavy binary data across the network.

### 2. n8n + medgemma:4b as the Agentic Brain
- n8n provides a **visual, auditable workflow canvas** showing every agent decision step as a connected node.
- **medgemma:4b** via Ollama is a specialized medical language model ensuring clinically-appropriate triage responses.
- The workflow is deployed programmatically via `push_workflow.py` (n8n REST API), so reviewers don't need to manually drag and drop any nodes.

### 3. Programmatic Clinical Safety Overrides
- A **pre-scanner** in the `json-parser` n8n node checks patient text against a curated list of emergency keywords (`chest pain`, `difficulty breathing`, `unconscious`, etc.) and forces `Severe` severity if detected — bypassing any potential LLM hallucinations.
- Any `Other / Out-of-Scope` category is programmatically forced to `Severe` and routed directly to the doctor without providing home-care advice.

### 4. Dual-Channel Alert System
| Channel | Trigger Condition | Technology |
|---|---|---|
| **Real SMTP Email** | SMTP credentials provided via GUI/env vars | smtplib (stdlib) |
| **ntfy.sh Push** | Always fires on Severe, zero config needed | HTTP POST to ntfy.sh |
| **Console/Log Simulation** | Always fires as a permanent audit record | Python logging |

### 5. zrok Public Tunnel
- n8n runs locally on `192.168.1.13:5678`, exposed to the internet via a **zrok** tunnel at `https://sopranosn8n.share.zrok.io`.
- This allows the Gradio frontend and automated tests to reach the n8n webhook from any machine or network.

---

## 📋 Phased Implementation Plan

| Phase | Task | Status |
|---|---|---|
| 1 | Scaffold Gradio UI with voice+text input | ✅ Done |
| 2 | Implement STT (SpeechRecognition) | ✅ Done |
| 3 | Implement TTS (gTTS + pyttsx3 fallback) | ✅ Done |
| 4 | Build n8n 7-node triage workflow | ✅ Done |
| 5 | Deploy workflow via push_workflow.py | ✅ Done |
| 6 | Connect frontend to n8n via zrok webhook | ✅ Done |
| 7 | Add programmatic clinical safety overrides | ✅ Done |
| 8 | Implement SMTP email alert dispatch | ✅ Done |
| 9 | Add ntfy.sh push alert fallback | ✅ Done |
| 10 | Write automated test suite (test_triage.py) | ✅ Done |
| 11 | Write EXAMPLE_IO.md & README.md | ✅ Done |

---

## 🔒 Privacy & Safety Guarantees

- No patient email addresses are hardcoded in the codebase.
- Default `DOCTOR_EMAIL` is set to `doctor@example.com` as a neutral placeholder.
- All sensitive credentials (SMTP passwords) are sourced from environment variables or a collapsible Gradio panel — never committed to version control.
- ntfy topic names use a project-specific string (`luminai-health-triage-alerts`) rather than personal identifiers.
