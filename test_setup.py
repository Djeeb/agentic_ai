import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=== Test Environnement Multi-Agents ===")
print(f"Python: {sys.version}")

# Test de votre clé OpenAI
openai_key = os.getenv("OPENAI_API_KEY")
print(
    f"OpenAI API: {'✅' if openai_key and openai_key.startswith('sk-proj-') else '❌'}"
)
print(f"Clé présente: {bool(openai_key)}")
