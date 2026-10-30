import os
from dotenv import load_dotenv
import requests
load_dotenv()
# Fetch the live list directly from the Groq API
url = "https://api.groq.com/openai/v1/models"
headers = {"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    models = response.json().get("data", [])
    for model in models:
        print(f"Model ID: {model['id']}")
else:
    print(f"Failed to fetch models: {response.status_code} - {response.text}")
