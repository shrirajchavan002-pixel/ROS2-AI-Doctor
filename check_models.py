import os
from dotenv import load_dotenv
from google import genai

# .env मधून API Key लोड करा
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

try:
    client = genai.Client(api_key=api_key)
    print("\n✅ तुझ्या API Key साठी उपलब्ध असलेली मॉडेल्स:\n")
    
    # सर्व मॉडेल्सची लिस्ट काढा
    models = client.models.list()
    for m in models:
        # फक्त जी मॉडेल्स 'generateContent' सपोर्ट करतात तीच दाखवा
        print(f"- {m.name}")
        
except Exception as e:
    print(f"❌ Error: {e}")
print("\n")
