import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load key from .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configure the SDK
genai.configure(api_key=api_key)

# Initialize Gemini Pro
model = genai.GenerativeModel('gemini-2.5-flash')

# Quick Test Call
def test_connection():
    try:
        response = model.generate_content("Hello! Are you ready to act as a clinical pharmacist?")
        print("API Response:", response.text)
    except Exception as e:
        print("Error connecting to Gemini:", e)

test_connection()