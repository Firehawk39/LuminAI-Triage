# 🩺 LuminAI Health - Take-Home Assignment Spec
## Role: AI & ML Scientist

---

## 📌 Context
Most rural households lack easy access to doctors. Many patients are more comfortable describing their health problems in local languages over phone calls than typing into apps. 

Your task is to build an agent that acts as the **first line of guidance** for patients — offering home-care advice for minor ailments while safely escalating serious cases to partner doctors. This assignment simulates that frontline triage workflow.

---

## 🎯 Objective
Build an agentic workflow where a **Root Agent** interacts with a patient to complete the following four tasks in sequence:

| # | Task | Description |
|---|---|---|
| **1** | **Collect Symptoms** | Engage the patient in a conversational voice interface to gather symptom information. |
| **2** | **Classify Condition** | Categorize the condition into one of three defined categories (see Classification below). |
| **3** | **Assess Severity** | Determine whether the condition is **Mild** or **Severe** and respond accordingly. |
| **4** | **Summarize & Route** | For severe/emergency cases only: generate a structured summary and send an email to the partner doctor. |

---

## 🗂️ Condition Classification
Classify every patient interaction into one of the following three categories:

| Category | Examples | Action |
|---|---|---|
| **Upper Respiratory Issue** | Cold, flu, sore throat, nasal congestion, bronchitis | Assess severity $\rightarrow$ advise or escalate |
| **Fever-Related Condition** | Viral fever, malaria, dengue, typhoid | Assess severity $\rightarrow$ advise or escalate |
| **Other / Out-of-Scope** | Symptoms that do not fit the above two categories | Route directly to doctor — **do not provide home advice** |

---

## ⚠️ Severity Assessment & Actions
* **Mild Cases**:
  * Provide empathetic, short spoken guidance.
  * Suggest simple, practical home care.
  * Reassure the patient appropriately.
* **Severe / Emergency Cases**:
  * Raise a red flag and strongly advise consulting a doctor.
  * Generate a structured case summary containing: **symptoms**, **duration**, **severity**, **red flags**, and **recommended next step**.
  * Route to partner doctor via email.

---

## 🛠️ Requirements & Grading Weights

### 1. Voice Interface (20%)
* The system must accept patient input as **speech** and respond in **spoken audio**.
* The voice loop must be functional end-to-end — not simulated with text.

### 2. Language Model Integration (15%)
* Use an LLM for patient conversation, condition classification, and response generation.
* The choice of model and provider is open (Ollama with local models is chosen).

### 3. Triage Logic & Safety (15%)
* Auto-classify condition type using the three categories.
* Auto-assess severity as Mild or Severe.
* Severity assessment must be reliable — consider what happens when the LLM is uncertain or wrong.
* Mild cases get concise spoken guidance; Severe cases get a structured summary.

### 4. Post-Session Email (10%)
* For severe/emergency cases only: automatically send an email summary to the partner doctor.
* For the purpose of this assignment, you are the partner doctor — send the email to yourself.
* The email must be structured and contain all fields from the case summary.

### 5. Interface & Runability (10%)
* Provide a working interface through which the triage flow can be demonstrated.
* The interface must be runnable locally by the interviewer without significant setup effort.

### 6. Agentic Architecture (25%)
* Root agent with clear separation of responsibilities and coherent orchestration logic.

### 7. Code Quality & README (5%)
* Readable, modular code; clear setup instructions; concise explanation of design choices.

---

## 📦 Deliverables
1. **Python Codebase**: Clean, runnable Python code for the complete triage workflow.
2. **README.md**: Setup instructions, environment variables, run instructions, and tool justifications.
3. **Example I/O**: Demonstrated triage flows showing full conversation, classification, response, and email output for at least one mild case and one severe case.
