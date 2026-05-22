# 🩺 LuminAI Triage - Frontline Triage Example I/O Showcase

This document provides detailed, end-to-end clinical input and output flows demonstrating how the **LuminAI Triage** agentic triage network handles patient symptoms. These examples showcase the full conversation, automated condition classification, severity assessment, custom home-care or emergency guidance, structured case summaries, and Doctor SMTP dispatch alerts.

All tests below are verified against the zrok-hosted **n8n workflow backend** powered by the **local `medgemma:4b` medical model**.

---

## 🗂️ Triage Case Scenario Index

1. [Showcase 1: Mild Upper Respiratory Issue (Home Care Advice)](#showcase-1-mild-upper-respiratory-issue-home-care-advice)
2. [Showcase 2: Severe Fever Emergency (Physician Escalation)](#showcase-2-severe-fever-emergency-physician-escalation)
3. [Showcase 3: Out-of-Scope Physical Injury (Forced Escalation)](#showcase-3-out-of-scope-physical-injury-forced-escalation)
4. [Showcase 4: Clinical Safety Override (Chest Pain Emergency Protection)](#showcase-4-clinical-safety-override-chest-pain-emergency-protection)

---

### Showcase 1: Mild Upper Respiratory Issue (Home Care Advice)

This flow demonstrates a low-risk, common cold symptom. The system reassures the patient, auto-classifies the condition, assesses severity as **Mild**, and generates supportive home-care instructions to play back as spoken audio.

#### 📥 Patient Input
* **Input Mode**: Voice (Transcribed to Text) or Typed TextBox
* **Patient Symptoms**: *"I have had a mild runny nose and slightly sore throat since yesterday."*

#### 📤 Triage Output (n8n Backend Response)
* **Condition Category**: `Upper Respiratory Issue`
* **Severity Assessment**: `Mild`
* **Agent Response (Spoken via TTS & Displayed in UI Card)**:
  > "Rest, drink plenty of fluids, and use over-the-counter remedies for your sore throat. If symptoms worsen or you develop a fever, please consult a doctor."

#### 📋 Structured UI Bubble Card
```html
<div style="font-family:'Inter',sans-serif;line-height:1.6;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
    <span style="background:#d1fae5;color:#065f46;border:1.5px solid #6ee7b7;border-radius:999px;padding:4px 14px;font-size:0.82em;font-weight:700;letter-spacing:0.05em;">
      🟢 MILD
    </span>
    <span style="background:#f0f9ff;color:#0369a1;border:1px solid #bae6fd;border-radius:999px;padding:4px 14px;font-size:0.82em;font-weight:600;">
      🏷️ Upper Respiratory Issue
    </span>
  </div>
  <p style="margin:0;color:#1e293b;font-size:0.97em;line-height:1.7;">Rest, drink plenty of fluids, and use over-the-counter remedies for your sore throat. If symptoms worsen or you develop a fever, please consult a doctor.</p>
</div>
```

#### 💾 Local Interaction Log Record (`triage.log`)
```
=== Patient Triage Interaction at 2026-05-22 16:45:12 ===
Input Method:  Mic (Voice)
Patient Symptoms: I have had a mild runny nose and slightly sore throat since yesterday.
Assessed Category: Upper Respiratory Issue
Assessed Severity: Mild
Agent Response: Rest, drink plenty of fluids, and use over-the-counter remedies for your sore throat. If symptoms worsen or you develop a fever, please consult a doctor.
============================================================
```

---

### Showcase 2: Severe Fever Emergency (Physician Escalation)

This flow highlights high-risk symptoms (extreme high fever, breathing difficulties). The system immediately flags the severity as **Severe**, constructs a structured clinical case summary, triggers the SMTP alert system, and advises the patient to seek urgent medical attention.

#### 📥 Patient Input
* **Input Mode**: Voice or Typed TextBox
* **Patient Symptoms**: *"I have a high fever of 103F, chest pain, and severe difficulty breathing since this morning."*

#### 📤 Triage Output (n8n Backend Response)
* **Condition Category**: `Fever-Related Condition`
* **Severity Assessment**: `Severe`
* **Agent Response (Spoken & UI Card)**:
  > "This sounds like a very serious medical emergency. You have a high fever, chest pain, and severe difficulty breathing. These symptoms require immediate medical attention. Please call emergency services or go to the nearest hospital immediately."

#### 📋 Structured Case Summary (JSON Contract)
```json
{
  "symptoms": "High fever (103F), chest pain, severe difficulty breathing",
  "duration": "Since this morning",
  "severity": "Severe",
  "red_flags": "High fever of 103F, chest pain, severe difficulty breathing present",
  "recommended_next_step": "Call emergency services or go to the nearest hospital immediately."
}
```

#### 📧 Physician SMTP HTML Email Alert
```html
Subject: 🚨 CLINICAL ALERT: Patient Triage Case - Fever-Related Condition
From: LuminAI Triage <triage-bot@luminai.health>
To: doctor@luminai.health

🩺 Frontline Patient Triage Alert
Status: 🚨 SEVERE / EMERGENCY ESCALATION
Condition Category: Fever-Related Condition
Assessed Severity: Severe

📝 Patient Case Summary
--------------------------------------------------------------------------------
Symptoms Profile:     High fever (103F), chest pain, severe difficulty breathing
Timeline Duration:    Since this morning
Clinical Red Flags:   High fever of 103F, chest pain, severe difficulty breathing present
Recommended Next Step: Call emergency services or go to the nearest hospital immediately.
--------------------------------------------------------------------------------

💬 Generated Guidance
"This sounds like a very serious medical emergency. You have a high fever, chest pain, and severe difficulty breathing. These symptoms require immediate medical attention. Please call emergency services or go to the nearest hospital immediately."
```

#### 💾 Local Interaction Log Record (`triage.log`)
```
=== Patient Triage Interaction at 2026-05-22 16:47:04 ===
Input Method:  Typed (Text)
Patient Symptoms: I have a high fever of 103F, chest pain, and severe difficulty breathing since this morning.
Assessed Category: Fever-Related Condition
Assessed Severity: Severe
--- Structured Case Summary ---
Symptoms Profile: High fever (103F), chest pain, severe difficulty breathing
Timeline Duration: Since this morning
Clinical Red Flags: High fever of 103F, chest pain, severe difficulty breathing present
Recommended Next Step: Call emergency services or go to the nearest hospital immediately.
--------------------------------
Agent Response: This sounds like a very serious medical emergency. You have a high fever, chest pain, and severe difficulty breathing. These symptoms require immediate medical attention. Please call emergency services or go to the nearest hospital immediately.
============================================================
```

---

### Showcase 3: Out-of-Scope Physical Injury (Forced Escalation)

To protect patient safety, queries or physical injuries that do not match our standard categories are automatically routed directly to a doctor as **Severe**, bypassing home-care advice.

#### 📥 Patient Input
* **Input Mode**: Voice
* **Patient Symptoms**: *"I hurt my ankle playing football and it is very swollen."*

#### 📤 Triage Output (n8n Backend Response)
* **Condition Category**: `Other / Out-of-Scope`
* **Severity Assessment**: `Severe` (Forced)
* **Agent Response (Spoken & UI Card)**:
  > "Since your condition does not match our standard frontline triage scope, I cannot provide home care advice. I have automatically summarized your case and escalated it to our partner physician for review. Please contact a professional doctor directly."

#### 📋 Structured Case Summary (JSON Contract)
```json
{
  "symptoms": "Hurt ankle playing football, very swollen",
  "duration": "Just now",
  "severity": "Severe",
  "red_flags": "Out-of-scope physical trauma / structural injury",
  "recommended_next_step": "Escalate directly to partner physician for diagnostic consultation."
}
```

---

### Showcase 4: Clinical Safety Override (Chest Pain Emergency Protection)

To guarantee patient safety, the triage system includes a programmatic safeguard. If the patient mentions an extreme clinical emergency keyword (e.g., "chest pain"), the backend immediately overrides any other symptom matches, sets the severity to **Severe**, formats a red-flag warning, and dispatches the doctor alert.

#### 📥 Patient Input
* **Input Mode**: Voice or Typed TextBox
* **Patient Symptoms**: *"I have had a mild runny nose but suddenly developed intense chest pain and shortness of breath."*

#### 📤 Triage Output (n8n Backend Response)
* **Condition Category**: `Upper Respiratory Issue` (Based on runny nose)
* **Severity Assessment**: `Severe` (Overridden programmatically from Mild due to Chest Pain)
* **Agent Response (Spoken & UI Card)**:
  > "You have mentioned chest pain and shortness of breath. This is a potential critical emergency requiring immediate medical intervention. Please call emergency services or seek medical help immediately."

#### 📋 Structured Case Summary (JSON Contract)
```json
{
  "symptoms": "Mild runny nose, sudden intense chest pain and shortness of breath",
  "duration": "Sudden onset",
  "severity": "Severe",
  "red_flags": "Emergency red-flag override activated: Chest pain or extreme breathing difficulty detected.",
  "recommended_next_step": "Seek emergency medical help or consult a cardiologist immediately."
}
```
