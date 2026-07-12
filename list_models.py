import os
import requests
from dotenv import load_dotenv

# 1. Load the secret key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 2. Ask Google for the list of models
print("Asking Google for available models...")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
response = requests.get(url)

# 3. Print out the names of the models we can use
data = response.json()
print("\nHere are the models you can use:")
for model in data.get('models', []):
    if 'generateContent' in model.get('supportedGenerationMethods', []):
        # We remove "models/" from the start of the name to make it clean
        print(model['name'].replace('models/', ''))
