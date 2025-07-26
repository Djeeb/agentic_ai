# =============================================================================
# IMPORTS ET CONFIGURATION
# =============================================================================
from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

# Chargement des variables d'environnement (.env)
load_dotenv(override=True)

# =============================================================================
# FONCTIONS UTILITAIRES - ACTIONS DANS LE MONDE RÉEL
# =============================================================================


def push(text):
    """Envoie une notification Pushover sur le téléphone"""
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        },
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    """Enregistre les détails d'un utilisateur intéressé"""
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    """Enregistre une question à laquelle on n'a pas pu répondre"""
    push(f"Recording {question}")
    return {"recorded": "ok"}


# =============================================================================
# DÉFINITION DES OUTILS (TOOLS) POUR L'IA
# =============================================================================

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user",
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it",
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered",
            },
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

# Liste des outils disponibles pour l'IA
tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]

# =============================================================================
# CLASSE PRINCIPALE - AGENT IA PROFESSIONNEL
# =============================================================================


class Me:
    """Agent IA qui représente une personne professionnellement"""

    def __init__(self):
        """Initialise l'agent avec les données personnelles"""
        self.openai = OpenAI()
        self.name = "Olivier JEAN-BAPTISTE"  # TODO: Remplacer par votre nom

        # Lecture du profil LinkedIn (PDF)
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text

        # Lecture du résumé personnel (texte)
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    def handle_tool_call(self, tool_calls):
        """Gère l'exécution des outils appelés par l'IA"""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)

            # Exécution dynamique de la fonction (évite les gros IF/ELIF)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}

            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id,
                }
            )
        return results

    def system_prompt(self):
        """Génère le prompt système qui définit le comportement de l'IA"""
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        # Injection des données personnelles dans le contexte
        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def chat(self, message, history):
        """Fonction principale de chat avec gestion des outils"""
        # Construction de la conversation complète
        messages = (
            [{"role": "system", "content": self.system_prompt()}]
            + history
            + [{"role": "user", "content": message}]
        )

        done = False
        while not done:
            # Appel à l'IA avec les outils disponibles
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini", messages=messages, tools=tools
            )

            # Si l'IA veut utiliser un outil
            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls

                # Exécution des outils et ajout des résultats à la conversation
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                # Conversation terminée
                done = True

        return response.choices[0].message.content


# =============================================================================
# LANCEMENT DE L'APPLICATION
# =============================================================================

if __name__ == "__main__":
    # Création de l'instance et lancement de l'interface Gradio
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
