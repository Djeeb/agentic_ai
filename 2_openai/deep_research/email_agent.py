import os
from typing import Dict

import resend
from agents import Agent, function_tool


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    resend.api_key = os.environ.get("RESEND_API_KEY")

    params = {
        "from": "actarus@djeeb.fr",  # Your verified sender domain
        "to": ["jibe75093@gmail.com"],  # Your recipient email
        "subject": subject,
        "html": html_body,
    }

    response = resend.Emails.send(params)
    print("Email response", response.get("id"))
    return {"status": "success", "id": response.get("id")}


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
