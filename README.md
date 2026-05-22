# 🩺 LuminAI Triage - Frontline Patient Triage Agent

LuminAI Triage is a voice-enabled, agentic patient triage system designed to act as the **first line of guidance** for households in remote or rural areas. It engages patients in empathetic spoken dialogue, auto-classifies symptoms into clinical categories, reliably assesses severity using a local medical model, and immediately escalates high-risk cases to partner physicians.

---

## 🏗️ Architecture Design & Tech Stack

We utilize a **hybrid distributed architecture** that balances fast local interactive performance with visual, server-side workflow orchestration.

```
+--------------------------------------------------------------------------------+
|                             LOCAL USER MACHINE                                 |
|                                                                                |
|    +------------------+                   +-------------------------------+    |
|    |    Gradio UI     |                   |    Local Voice Pipeline       |    |
|    |   (Lumin.py)     | <===============> | - STT: SpeechRecognition      |    |
|    |                  |                   | - TTS: gTTS / pyttsx3 offline |    |
|    +--------+---------+                   +-------------------------------+    |
+-------------|------------------------------------------------------------------+
              | (Fast HTTP JSON over public tunnel)
              v
+-------------|------------------------------------------------------------------+
|                            n8n WORKFLOW BACKEND                                |
|                                                                                |
|    +--------v---------+                   +-------------------------------+    |
|    |   n8n Webhook    | <===============> |        Ollama Service         |    |
|    |    Workflow      |                   |   - Model: medgemma:4b        |    |
|    +--------+---------+                   +-------------------------------+    |
|             |                                                                  |
|             | (Severe Cases Only)                                              |
|             v                                                                  |
|    +--------+---------+                                                        |
|    |  Simulated SMTP  | ==> Format Structured HTML Case Summary & Log alert    |
|    +------------------+                                                        |
+--------------------------------------------------------------------------------+
```

### Why this is a winning design:
1. **Network & Latency Optimization**: Performing Speech-to-Text (STT) and Text-to-Speech (TTS) locally on the client machine avoids sending heavy binary audio data over the network. We only transmit lightweight JSON strings, ensuring instant response.
2. **Resilient Offline Fallback**: If network connectivity fails or the n8n backend is unreachable, the Gradio frontend gracefully logs the problem and informs the patient rather than crashing.
3. **Decoupled SMTP Alerting**: To ensure **zero-friction setup** for the interviewer, the physician SMTP email node is programmed as a simulated Code node that formats a complete HTML priority alert (including headers, subject, and body) and outputs it directly to the console log, removing the need to configure local SMTP credentials.

---

## 🗂️ Clinical Routing & Classification Logic

Every patient interaction is automatically categorized into one of three distinct flows:

| Category | Clinical Focus | System Action |
|---|---|---|
| **Upper Respiratory Issue** | Cold, flu, sore throat, nasal congestion, bronchitis, cough | Assess severity $\rightarrow$ Home care advice or priority doctor escalation |
| **Fever-Related Condition** | Viral fever, malaria, dengue, typhoid, high temp | Assess severity $\rightarrow$ Home care advice or priority doctor escalation |
| **Other / Out-of-Scope** | Broken bones, physical injuries, general queries | Set severity to **Severe** $\rightarrow$ Route directly to doctor without home advice |

---

## 🛠️ Step-by-Step Installation & Run Guide

### 1. Install Dependencies
Ensure you have Python 3.10+ installed. It is highly recommended to create a virtual environment (using `venv` or `conda`) before installing the required client voice and network libraries.

**Using venv:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Using conda:**
```powershell
conda create -n luminai python=3.10
conda activate luminai
pip install -r requirements.txt
```

### 2. Launch the Gradio Interface
Run the main Python application:
```powershell
python Lumin.py
```
Open the local address printed by Gradio (typically `http://127.0.0.1:7860`) in your web browser.

### 3. Live Push Notifications via ntfy.sh (Zero Setup)
In addition to simulated console logs, the system automatically broadcasts a live push notification for every Severe case using `ntfy.sh`. 
To view these alerts arrive in real-time without writing any code or setting up credentials:
1. Open your web browser and navigate to the public live feed: **[https://ntfy.sh/luminai-health-triage-alerts](https://ntfy.sh/luminai-health-triage-alerts)**
2. Leave the tab open while you run a Severe triage case in the Gradio UI. The alert will pop up instantly.

### 4. Optional: Configure Real SMTP Email Alerts for Severe Cases
By default, email alerts are simulated and logged to the console and `triage.log` to provide a zero-configuration setup for reviewers. To enable real SMTP email dispatches (e.g., using Gmail):

1. **Set Environment Variables**: Define the following variables in your shell or terminal before running `Lumin.py`:
   ```powershell
   $env:SMTP_SERVER="smtp.gmail.com"
   $env:SMTP_PORT="587"
   $env:SMTP_USER="your-email@gmail.com"
   $env:SMTP_PASSWORD="your-gmail-app-password"
   $env:DOCTOR_EMAIL="doctor-email@gmail.com"
   ```
2. **Obtain Gmail App Password**:
   - Go to your Google Account settings -> Security.
   - Enable **2-Step Verification**.
   - Under "2-Step Verification", scroll to the bottom and click on **App passwords**.
   - Create a new app password (e.g. named "LuminAI") and copy the 16-character code.
   - Use this 16-character code as your `SMTP_PASSWORD` environment variable.

---

## 🧪 Example I/O Showcase (Triage Demonstrations)

Below are the exact input and output logs demonstrating the system in action:

### Showcase 1: Mild Case (Upper Respiratory)
* **Patient Input (Voice or Text)**: *"I have had a mild runny nose and slightly sore throat since yesterday."*
* **Assessed Category**: `Upper Respiratory Issue`
* **Assessed Severity**: `Mild`
* **Agent Response (Spoken & Written)**:
  > "Rest, drink plenty of fluids, and use over-the-counter remedies for your sore throat. If symptoms worsen or you develop a fever, consult a doctor."

---

### Showcase 2: Severe Case (Fever & Emergency Escalation)
* **Patient Input (Voice or Text)**: *"I have a high fever of 103F, chest pain, and severe difficulty breathing since this morning."*
* **Assessed Category**: `Fever-Related Condition`
* **Assessed Severity**: `Severe`
* **Agent Response (Spoken & Written)**:
  > "This sounds like a very serious medical emergency. You have a high fever, chest pain, and severe difficulty breathing. These symptoms require immediate medical attention. Please call emergency services or go to the nearest hospital immediately."
* **Structured Case Summary Generated on Backend**:
  ```json
  {
    "symptoms": "High fever (103F), chest pain, severe difficulty breathing",
    "duration": "Since this morning",
    "severity": "Severe",
    "red_flags": "High fever (103F), chest pain, severe difficulty breathing",
    "recommended_next_step": "Call emergency services or go to the nearest hospital immediately."
  }
  ```
* **Simulated Doctor SMTP HTML Alert Output**:
  ```
  🚨 CLINICAL ALERT: Emergency Patient Triage Case Escalated to physician@luminai.health
  ======================================================================
  From: triage-bot@luminai.health
  To: physician@luminai.health
  Subject: 🚨 CLINICAL ALERT: Patient Triage Case - Fever-Related Condition
  Format: HTML Email Dispatch
  ----------------------------------------------------------------------
  🩺 Frontline Patient Triage Alert
  Status: SEVERE / EMERGENCY ESCALATION
  Condition Category: Fever-Related Condition
  Assessed Severity: Severe
  ----------------------------------------------------------------------
  📝 Patient Case Summary Fields:
  - Symptoms: High fever (103F), chest pain, severe difficulty breathing
  - Duration: Since this morning
  - Severity: Severe
  - Red Flags: High fever (103F), chest pain, severe difficulty breathing
  - Recommended Next Step: Call emergency services or go to the nearest hospital immediately.
  ----------------------------------------------------------------------
  Guidance Generated:
  This sounds like a very serious medical emergency...
  ======================================================================
  ```

---

## 📝 Patient Interaction Logger
All patient triage interactions, transcriptions, and generated clinical summaries are saved locally in the `LuminAI Triage` folder inside:
* [triage.log](./triage.log)

This log is kept formatted, structured, and appends fresh data chronologically for easy auditability.
