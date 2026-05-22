import gradio as gr
import os
import requests
import speech_recognition as sr
from gtts import gTTS
import pyttsx3
import tempfile
import traceback
import datetime

# ---------------------------------------------------------
# Configuration & Backend Webhook Routing
# ---------------------------------------------------------
# The n8n Webhook Endpoint hosted via zrok
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://sopranosn8n.share.zrok.io/webhook/triage")

# Default SMTP & Email Settings (Interviewers can swap directly in code here or via GUI)
DEFAULT_SMTP_SERVER = os.getenv("SMTP_SERVER", "")
DEFAULT_SMTP_PORT = os.getenv("SMTP_PORT", "587")
DEFAULT_SMTP_USER = os.getenv("SMTP_USER", "")
DEFAULT_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
DEFAULT_DOCTOR_EMAIL = os.getenv("DOCTOR_EMAIL", "doctor@example.com")

print(f"[Triage System] Initialized. Backend n8n Target: {N8N_WEBHOOK_URL}")

def log_interaction(input_text, category, severity, response_text, is_audio=False, case_summary=None):
    """
    Logs all patient triage interactions to a local file 'triage.log' directly inside the workspace directory.
    """
    try:
        # Save directly in the workspace directory (where Lumin.py resides)
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "triage.log")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        input_type = "Mic (Voice)" if is_audio else "Typed (Text)"
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"=== Patient Triage Interaction at {timestamp} ===\n")
            f.write(f"Input Method:  {input_type}\n")
            f.write(f"Patient Symptoms: {input_text}\n")
            f.write(f"Assessed Category: {category}\n")
            f.write(f"Assessed Severity: {severity}\n")
            
            if case_summary:
                f.write(f"--- Structured Case Summary ---\n")
                f.write(f"Symptoms Profile: {case_summary.get('symptoms', 'N/A')}\n")
                f.write(f"Timeline Duration: {case_summary.get('duration', 'N/A')}\n")
                f.write(f"Clinical Red Flags: {case_summary.get('red_flags', 'N/A')}\n")
                f.write(f"Recommended Next Step: {case_summary.get('recommended_next_step', 'N/A')}\n")
                f.write(f"--------------------------------\n")
                
            f.write(f"Agent Response: {response_text}\n")
            f.write("=" * 60 + "\n\n")
        print(f"[Logger] Interaction recorded successfully in: {log_path}")
    except Exception as e:
        print(f"[Logger] Error writing interaction log: {e}")

def send_email_alert(category, severity, case_summary, doctor_email="", smtp_server="", smtp_port="587", smtp_user="", smtp_password=""):
    """
    Sends a clinical alert through two parallel channels:
    1. Free zero-credential push alert via ntfy.sh (always fires — no setup required).
    2. Real SMTP email (only fires when valid SMTP credentials are provided via GUI or env vars).
    """
    # Dynamic GUI input takes priority, followed by environment variables, followed by global defaults
    smtp_server = smtp_server or os.getenv("SMTP_SERVER") or DEFAULT_SMTP_SERVER
    smtp_port = smtp_port or os.getenv("SMTP_PORT") or DEFAULT_SMTP_PORT
    smtp_user = smtp_user or os.getenv("SMTP_USER") or DEFAULT_SMTP_USER
    smtp_password = smtp_password or os.getenv("SMTP_PASSWORD") or DEFAULT_SMTP_PASSWORD
    doctor_email = doctor_email or os.getenv("DOCTOR_EMAIL") or DEFAULT_DOCTOR_EMAIL

    # ---------------------------------------------------------------
    # CHANNEL 1: Free Push Alert via ntfy.sh (zero credentials needed)
    # Open the live feed at: https://ntfy.sh/luminai-health-triage-alerts
    # ---------------------------------------------------------------
    try:
        ntfy_topic = "luminai-health-triage-alerts"
        ntfy_title = f"CLINICAL ALERT: Patient Triage Case - {category}"
        ntfy_body = (
            f"Status: SEVERE / EMERGENCY ESCALATION\n"
            f"Condition Category: {category}\n"
            f"Recipient Doctor: {doctor_email}\n"
            f"----------------------------------------\n"
            f"Symptom Profile: {case_summary.get('symptoms', 'N/A')}\n"
            f"Timeline Duration: {case_summary.get('duration', 'N/A')}\n"
            f"Clinical Red Flags: {case_summary.get('red_flags', 'N/A')}\n"
            f"Recommended Next Step: {case_summary.get('recommended_next_step', 'N/A')}"
        )
        requests.post(
            f"https://ntfy.sh/{ntfy_topic}",
            data=ntfy_body.encode("utf-8"),
            headers={
                "Title": ntfy_title,
                "Priority": "high",
                "Tags": "stethoscope,rotating_light"
            },
            timeout=5.0
        )
        print(f"[Alert] ntfy push notification sent to: https://ntfy.sh/{ntfy_topic}")
    except Exception as ntfy_err:
        print(f"[Alert] Warning: ntfy notification failed: {ntfy_err}")

    # ---------------------------------------------------------------
    # CHANNEL 2: Real SMTP Email (fires only when credentials provided)
    # ---------------------------------------------------------------
    subject = f"CLINICAL ALERT: Patient Triage Case - {category}"
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #d9534f; border-bottom: 2px solid #d9534f; padding-bottom: 8px;">🩺 Frontline Patient Triage Alert</h2>
        <p><strong>Status:</strong> <span style="color: #d9534f; font-weight: bold;">🚨 SEVERE / EMERGENCY ESCALATION</span></p>
        <p><strong>Condition Category:</strong> {category}</p>
        <p><strong>Assessed Severity:</strong> {severity}</p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <h3 style="color: #2e6da4;">📝 Patient Case Summary</h3>
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; width: 200px; background-color: #f9f9f9;">Symptoms Profile:</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{case_summary.get('symptoms', 'N/A')}</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background-color: #f9f9f9;">Timeline Duration:</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{case_summary.get('duration', 'N/A')}</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background-color: #f9f9f9;">Clinical Red Flags:</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #d9534f; font-weight: bold;">{case_summary.get('red_flags', 'N/A')}</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background-color: #f9f9f9;">Recommended Next Step:</td>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; color: #2e6da4;">{case_summary.get('recommended_next_step', 'N/A')}</td>
          </tr>
        </table>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <h3 style="color: #2e6da4;">💬 Generated Guidance</h3>
        <blockquote style="margin: 0; padding: 10px 20px; background-color: #f5f5f5; border-left: 5px solid #ccc; font-style: italic;">
          {case_summary.get('agent_response_text', 'No advice generated.')}
        </blockquote>
        <p style="font-size: 0.85em; color: #777; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 8px;">
          This is an automated priority clinical notification dispatched by the LuminAI Triage Frontline Triage Network.
        </p>
      </body>
    </html>
    """
    
    if smtp_server and smtp_user and smtp_password:
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            
            print(f"[Email Client] Preparing real SMTP email to {doctor_email} via {smtp_server}:{smtp_port}...")
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"LuminAI Triage <{smtp_user}>"
            msg["To"] = doctor_email
            
            # Simple text fallback
            text_fallback = (
                f"🩺 Frontline Patient Triage Alert\n"
                f"Status: SEVERE / EMERGENCY ESCALATION\n"
                f"Condition Category: {category}\n"
                f"Assessed Severity: {severity}\n\n"
                f"Patient Case Summary:\n"
                f"- Symptoms: {case_summary.get('symptoms', 'N/A')}\n"
                f"- Duration: {case_summary.get('duration', 'N/A')}\n"
                f"- Red Flags: {case_summary.get('red_flags', 'N/A')}\n"
                f"- Next Step: {case_summary.get('recommended_next_step', 'N/A')}\n"
            )
            
            msg.attach(MIMEText(text_fallback, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Establish secure session
            server = smtplib.SMTP(smtp_server, int(smtp_port), timeout=10)
            if smtp_port == "587":
                server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, doctor_email, msg.as_string())
            server.quit()
            print(f"[Email Client] Real SMTP email successfully sent to {doctor_email}!")
            return True, f"Real SMTP email successfully sent to {doctor_email}!"
        except Exception as e:
            err_msg = f"Failed to send real SMTP email: {e}"
            print(f"[Email Client] Error: {err_msg}")
            return False, err_msg
    else:
        print(f"[Email Client] SMTP Credentials not fully configured. Email dispatch simulated to {doctor_email}.")
        return True, "Simulated successfully."

def transcribe_audio(audio_path):
    """
    Translates spoken patient audio (.wav) into text using SpeechRecognition
    """
    if not audio_path or not os.path.exists(audio_path):
        return ""
    
    recognizer = sr.Recognizer()
    try:
        print(f"[STT] Transcribing audio file: {audio_path}")
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
        # Using Google Web Speech API (Free, zero-key, high accuracy)
        text = recognizer.recognize_google(audio_data)
        print(f"[STT] Transcribed text: '{text}'")
        return text
    except sr.UnknownValueError:
        print("STT Warning: Google Speech Recognition could not understand the audio.")
        return ""
    except sr.RequestError as e:
        print(f"STT Error: Could not request results from Google Speech Recognition; {e}")
        return ""
    except Exception as e:
        print(f"STT Exception: {e}")
        traceback.print_exc()
        return ""

def call_triage_backend(patient_text, chat_history):
    """
    Calls the zrok-hosted n8n webhook backend.
    """
    try:
        print(f"[Backend] Sending payload to n8n Webhook: {N8N_WEBHOOK_URL}")
        # Format payload matching our schema contract
        payload = {
            "patient_text": patient_text,
            "chat_history": chat_history
        }
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=30.0)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[Backend] Response received: {data}")
            return (
                data.get("agent_response_text", ""),
                data.get("condition_category", ""),
                data.get("severity_assessment", ""),
                data.get("case_summary", None)
            )
        else:
            print(f"[Backend] Warning: Non-200 status code returned: {response.status_code}")
            return (
                f"Error: The triage backend returned a server warning status ({response.status_code}). Please verify the n8n service.",
                "System Error",
                "N/A",
                None
            )
    except Exception as e:
        print(f"[Backend] Connection to n8n failed: {e}")
        return (
            "I am sorry, but the frontline triage backend is currently unreachable. Please verify that the n8n zrok webhook is active and try again.",
            "System Error",
            "N/A",
            None
        )

def synthesize_speech(text):
    """
    Converts agent response text into a playable spoken audio file (.mp3 / .wav)
    """
    if not text:
        return None
    
    temp_dir = tempfile.gettempdir()
    output_filepath_mp3 = os.path.join(temp_dir, f"agent_voice_{os.urandom(4).hex()}.mp3")
    
    # Tier 1: Cloud Google TTS (Premium, smooth natural flow)
    try:
        print("[TTS] Generating voice response via gTTS...")
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_filepath_mp3)
        print(f"[TTS] gTTS synthesis successful: {output_filepath_mp3}")
        return output_filepath_mp3
    except Exception as e:
        print(f"[TTS] gTTS warning: {e}. Falling back to offline OS voice synthesizer...")
        
    # Tier 2: Offline Windows Speech API (SAPI5)
    try:
        # Initialize COM library for the background thread to prevent deadlocks in Gradio worker threadpool
        try:
            import pythoncom
            pythoncom.CoInitialize()
            print("[TTS] COM initialized on background thread.")
        except Exception as com_err:
            print(f"[TTS] COM initialization warning (non-fatal): {com_err}")

        output_filepath_wav = os.path.join(temp_dir, f"agent_voice_{os.urandom(4).hex()}.wav")
        engine = pyttsx3.init()
        engine.setProperty('rate', 155)  # Professional, natural speech speed
        engine.setProperty('volume', 0.95)
        
        # Select English voice
        voices = engine.getProperty('voices')
        for voice in voices:
            if "EN" in voice.id.upper() or "ENGLISH" in voice.name.upper():
                engine.setProperty('voice', voice.id)
                break
                
        engine.save_to_file(text, output_filepath_wav)
        engine.runAndWait()
        print(f"[TTS] Offline pyttsx3 synthesis successful: {output_filepath_wav}")
        return output_filepath_wav
    except Exception as ex:
        print(f"[TTS] Error: Both gTTS and pyttsx3 synthesis engines failed; {ex}")
        return None

def transcribe_and_update_textbox(audio_path):
    """
    Called automatically when microphone voice recording is stopped or changed.
    Transcribes the audio immediately and populates the text box for user review and editing.
    """
    if not audio_path:
        # If recording is cleared or empty, do not change/clear the text box
        return gr.update()
    
    print(f"[Voice Capture] Recording detected at: {audio_path}")
    transcribed_text = transcribe_audio(audio_path)
    if not transcribed_text:
        # Graceful placeholder to inform the patient S2T failed
        transcribed_text = "[Speech not understood, please try speaking again or edit this text manually]"
        
    return gr.update(value=transcribed_text)

def triage_patient(patient_audio_filepath, patient_text, chat_history, doctor_email="", smtp_server="", smtp_port="587", smtp_user="", smtp_password=""):
    """
    The core routing function handling audio speech and keyboard text inputs.
    Option B (Textbox) is now the single source of truth since voice auto-populates
    it and allows the patient to review and edit what was captured before submission.
    """
    if chat_history is None:
        chat_history = []
        
    user_input = ""
    
    # Textbox is the single source of truth since it contains the edited version of speech or typed text
    if patient_text and patient_text.strip():
        user_input = patient_text.strip()
    elif patient_audio_filepath:
        # Fallback transcription in case the change event didn't complete
        user_input = transcribe_audio(patient_audio_filepath)
        if not user_input:
            user_input = "[Empty or Silent Audio Recording]"
    else:
        # No input provided
        return chat_history, gr.Audio(visible=False), "", None
 
    # STEP 2: The Agentic Brain (n8n API with Offline Local Fallback)
    agent_response_text, category, severity, case_summary = call_triage_backend(user_input, chat_history)
    
    # Log the interaction locally in the LuminAI Triage folder (triage.log)
    log_interaction(user_input, category, severity, agent_response_text, is_audio=bool(patient_audio_filepath), case_summary=case_summary)
    
    # Resolve the email routing info
    resolved_doctor_email = doctor_email or os.getenv("DOCTOR_EMAIL") or DEFAULT_DOCTOR_EMAIL
    
    # Try sending email alert (optional Real SMTP or simulated log)
    email_status = f"Priority SMTP alert simulated to doctor ({resolved_doctor_email})"
    if severity == "Severe" and case_summary:
        case_summary_copy = dict(case_summary)
        case_summary_copy['agent_response_text'] = agent_response_text
        success, msg = send_email_alert(
            category, 
            severity, 
            case_summary_copy,
            doctor_email=doctor_email,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password
        )
        if success and "Real SMTP" in msg:
            email_status = f"Real SMTP email successfully dispatched to physician ({resolved_doctor_email})"
    
    # STEP 3: Text-to-Speech synthesis
    agent_response_audio = synthesize_speech(agent_response_text)
    
    # Update UI transcription and response logs
    # Use gr.ChatMessage so Gradio renders HTML correctly in the transcript
    chat_history.append({"role": "user", "content": user_input})
    
    # Map severity to native emoji
    severity_emojis = {
        "Mild": "🟢",
        "Moderate": "🟡",
        "Severe": "🔴"
    }
    sev_emoji = severity_emojis.get(severity, "⚪")

    # Construct clean markdown presentation that clearly shows Classification Category and Severity Assessment
    md_content = f"### 🏷️ Category: **{category}** | {sev_emoji} Severity: **{severity}**\n\n"
    md_content += f"{agent_response_text}\n"

    if severity == "Severe" and case_summary:
        md_content += "\n---\n\n"
        md_content += "### 🩺 Structured Clinical Case Summary\n"
        md_content += f"* **🤒 Symptom Profile:** {case_summary.get('symptoms', 'N/A')}\n"
        md_content += f"* **⏱️ Timeline Duration:** {case_summary.get('duration', 'N/A')}\n"
        md_content += f"* **⚠️ Clinical Red Flags:** {case_summary.get('red_flags', 'N/A')}\n"
        md_content += f"* **📧 Alert Status:** {email_status}\n"
        md_content += f"* **➡️ Recommended Next Step:** {case_summary.get('recommended_next_step', 'N/A')}\n"

    chat_history.append({"role": "assistant", "content": md_content})

    # Determine audio player visibility based on synthesis success
    audio_update = gr.Audio(value=agent_response_audio, visible=bool(agent_response_audio))
    return chat_history, audio_update, "", None

# ---------------------------------------------------------
# Custom Modern Theme Setup (Healthcare Vibe)
# ---------------------------------------------------------
custom_theme = gr.themes.Soft(
    primary_hue="teal",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
).set(
    body_background_fill="*neutral_50",
    block_background_fill="white",
    block_border_width="1px",
    block_border_color="*neutral_200",
    block_radius="lg",
    button_primary_background_fill="*primary_500",
    button_primary_background_fill_hover="*primary_600",
)

# ---------------------------------------------------------
# The Gradio UI Foundation
# ---------------------------------------------------------
with gr.Blocks(title="LuminAI Triage") as interface:
    
    # Header Section - Now Centered
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown(
                """
                <div style="text-align: center;">
                    <h1>🩺 LuminAI Triage</h1>
                    <h3>Frontline Patient Triage Workflow</h3>
                    <p style="font-size: 1.1em; color: gray;">Speak or type your symptoms below. Our agentic system will assess your condition and provide guidance.</p>
                </div>
                """
            )
            
    gr.HTML("<hr style='border: 0; height: 1px; background: var(--border-color-primary, #e2e8f0); margin: 16px 0;'>")
    
    with gr.Row():
        # Left Column: The Input Controls (Moved from right to left)
        with gr.Column(scale=1):
            gr.Markdown("### 📝 Input Symptoms")
            
            # Using a Group to bind the inputs visually together like a modern form
            with gr.Group():
                patient_input_audio = gr.Audio(
                    sources=["microphone"], 
                    type="filepath", 
                    label="Option A: Use Microphone"
                )
                
                gr.Markdown("<center><i>— or —</i></center>")
                
                patient_input_text = gr.Textbox(
                    label="Option B: Type Symptoms", 
                    placeholder="E.g., I have had a high fever and a dry cough since yesterday...",
                    lines=3,
                    show_label=True
                )
            
            submit_button = gr.Button("Submit to Triage Agent", variant="primary", size="lg")
            
            gr.HTML("<br>")
            
            # Interactive Interviewer Dashboard for ultra-easy configuration swaps
            with gr.Accordion("⚙️ Interviewer Configuration Panel", open=False):
                gr.Markdown("### 📧 Dynamic Email Alert Routing\n*Swap configuration settings live on the fly without changing code or restarting servers!*")
                
                doctor_email_input = gr.Textbox(
                    label="📧 Doctor Recipient Email",
                    value=DEFAULT_DOCTOR_EMAIL,
                    placeholder="e.g., doctor@hospital.com",
                    show_label=True
                )
                
                with gr.Accordion("🔑 Advanced SMTP Server Credentials (Optional)", open=False):
                    gr.Markdown("Enter SMTP settings to test live email dispatches directly to the mailbox of your choice.")
                    with gr.Row():
                        smtp_server_input = gr.Textbox(
                            label="SMTP Server",
                            value=DEFAULT_SMTP_SERVER,
                            placeholder="e.g., smtp.gmail.com"
                        )
                        smtp_port_input = gr.Textbox(
                            label="SMTP Port",
                            value=DEFAULT_SMTP_PORT,
                            placeholder="587"
                        )
                    with gr.Row():
                        smtp_user_input = gr.Textbox(
                            label="SMTP Username",
                            value=DEFAULT_SMTP_USER,
                            placeholder="your.email@gmail.com"
                        )
                        smtp_password_input = gr.Textbox(
                            label="SMTP Password",
                            value=DEFAULT_SMTP_PASSWORD,
                            placeholder="Gmail App Password",
                            type="password"
                        )

        # Right Column: The Conversation (Moved from left to right)
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="📋 Triage Transcript",
                height=520,
                show_label=True,
                render_markdown=True,
                sanitize_html=False,
                layout="bubble",
                group_consecutive_messages=False,
                avatar_images=(None, "https://api.dicebear.com/7.x/thumbs/svg?seed=LuminAI&backgroundColor=0d9488"),
            )
            
            # The Audio Output (Mouth)
            agent_output_audio = gr.Audio(
                label="🔊 Agent Spoken Response", 
                autoplay=True,
                visible=False # Kept hidden until audio is generated for a cleaner UI
            )

    # Connect the UI elements to the Python function
    submit_button.click(
        fn=triage_patient, 
        inputs=[
            patient_input_audio, 
            patient_input_text, 
            chatbot,
            doctor_email_input,
            smtp_server_input,
            smtp_port_input,
            smtp_user_input,
            smtp_password_input
        ], 
        outputs=[chatbot, agent_output_audio, patient_input_text, patient_input_audio]
    )
    
    # Automatically transcribe microphone recording and put it into typing section for review/edit
    patient_input_audio.change(
        fn=transcribe_and_update_textbox,
        inputs=[patient_input_audio],
        outputs=[patient_input_text]
    )

CUSTOM_CSS = """
footer {visibility: hidden;}
"""

if __name__ == "__main__":
    interface.queue().launch(theme=custom_theme, css=CUSTOM_CSS)