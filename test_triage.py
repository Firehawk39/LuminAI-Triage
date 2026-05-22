import requests
import unittest
import os
import json

class TestLuminAITriage(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.webhook_url = os.getenv("N8N_WEBHOOK_URL", "https://sopranosn8n.share.zrok.io/webhook/triage")
        print(f"\n[Test Setup] Testing targeting webhook: {cls.webhook_url}\n")
        
        # Verify endpoint is reachable before running tests
        try:
            r = requests.get(cls.webhook_url.replace("/webhook/", "/webhook-test/"), timeout=3)
            # The Webhook Trigger usually returns 405 Method Not Allowed on GET, but it means it is online!
            cls.online = True
        except requests.exceptions.RequestException:
            cls.online = False
            print("[Test Setup] WARNING: n8n webhook server is offline. Tests will be skipped.")

    def setUp(self):
        if not self.online:
            self.skipTest("n8n webhook is currently offline.")

    def test_mild_upper_respiratory(self):
        """Verifies mild upper respiratory issue flow"""
        payload = {
            "patient_text": "I have had a mild runny nose and slightly sore throat since yesterday.",
            "chat_history": []
        }
        r = requests.post(self.webhook_url, json=payload, timeout=12)
        self.assertEqual(r.status_code, 200)
        
        data = r.json()
        self.assertEqual(data.get("condition_category"), "Upper Respiratory Issue")
        self.assertEqual(data.get("severity_assessment"), "Mild")
        
        case_summary = data.get("case_summary", {})
        self.assertEqual(case_summary.get("severity"), "Mild")
        self.assertEqual(case_summary.get("red_flags"), "None")
        print("SUCCESS: Test Mild Upper Respiratory: PASSED")

    def test_severe_fever_emergency(self):
        """Verifies severe fever condition with emergency indicators"""
        payload = {
            "patient_text": "I have a high fever of 103F, chest pain, and severe difficulty breathing since this morning.",
            "chat_history": []
        }
        r = requests.post(self.webhook_url, json=payload, timeout=12)
        self.assertEqual(r.status_code, 200)
        
        data = r.json()
        self.assertEqual(data.get("condition_category"), "Fever-Related Condition")
        self.assertEqual(data.get("severity_assessment"), "Severe")
        
        case_summary = data.get("case_summary", {})
        self.assertEqual(case_summary.get("severity"), "Severe")
        self.assertTrue("Emergency red-flag override" in case_summary.get("red_flags", "") or "high fever" in case_summary.get("red_flags", "").lower())
        print("SUCCESS: Test Severe Fever Emergency: PASSED")

    def test_out_of_scope_routing(self):
        """Verifies out-of-scope injury category and severity forcing"""
        payload = {
            "patient_text": "I hurt my ankle playing football and it is very swollen.",
            "chat_history": []
        }
        r = requests.post(self.webhook_url, json=payload, timeout=12)
        self.assertEqual(r.status_code, 200)
        
        data = r.json()
        self.assertEqual(data.get("condition_category"), "Other / Out-of-Scope")
        self.assertEqual(data.get("severity_assessment"), "Severe")
        
        case_summary = data.get("case_summary", {})
        self.assertEqual(case_summary.get("severity"), "Severe")
        print("SUCCESS: Test Out of Scope Routing: PASSED")

    def test_clinical_safety_override(self):
        """Verifies the programmatic safety override when extreme keywords are present"""
        payload = {
            "patient_text": "I have had a runny nose but suddenly developed intense chest pain and shortness of breath.",
            "chat_history": []
        }
        r = requests.post(self.webhook_url, json=payload, timeout=12)
        self.assertEqual(r.status_code, 200)
        
        data = r.json()
        # Even if runny nose matches Upper Respiratory, chest pain forces Severe
        self.assertEqual(data.get("severity_assessment"), "Severe")
        
        case_summary = data.get("case_summary", {})
        self.assertEqual(case_summary.get("severity"), "Severe")
        self.assertTrue("Emergency red-flag override activated" in case_summary.get("red_flags"))
        print("SUCCESS: Test Clinical Safety Override: PASSED")

if __name__ == "__main__":
    unittest.main()
