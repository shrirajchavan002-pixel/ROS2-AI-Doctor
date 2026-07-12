import os
from dotenv import load_dotenv
from google import genai

# 1. Open our digital safe (.env) and load the secret key
load_dotenv()
my_key = os.getenv("GEMINI_API_KEY")

# 2. Give the key to the new Gemini Client
client = genai.Client(api_key=my_key)

# 3. Send a simple message to the AI using the universal model name
print("Sending message to AI...")
response = client.models.generate_content(
    model='gemini-flash-latest',
    contents='Say a short, encouraging hello to a robotics student!'
)

# 4. Print the AI's reply to the screen
print("AI says:", response.text)
