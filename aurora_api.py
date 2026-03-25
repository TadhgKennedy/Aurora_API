import os
import sys
import json
import subprocess
from typing import List, Optional

# Notebook-friendly install if package missing
def _ensure_package(pkg):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

for pkg in ["fastapi", "uvicorn", "pandas", "google-genai", "nest-asyncio"]:
    _ensure_package(pkg)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
import pandas as pd
import uvicorn
import nest_asyncio

if "GOOGLE_API_KEY" not in os.environ:
    raise RuntimeError("Set GOOGLE_API_KEY environment variable before starting the API.")

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
app = FastAPI(title="Concierge Message Q&A API")

def find_messages_by_user_name(name_part: str) -> List[dict]:
    name_part = (name_part or "").strip().lower()
    if not name_part:
        raise HTTPException(status_code=400, detail="name_part is required")

    global df_messages
    if "df_messages" not in globals():
        if not os.path.exists("c:/Users/Kennedy/OneDrive/Documents/Aurora_Application/all_messages.csv"):
            raise HTTPException(status_code=500, detail="all_messages.csv not found; load your messages first.")
        df_messages = pd.read_csv("c:/Users/Kennedy/OneDrive/Documents/Aurora_Application/all_messages.csv")

    matches_df = df_messages[df_messages["user_name"].str.lower().str.contains(name_part, na=False)]
    return [{"id": row["id"], "message": row["message"]} for _, row in matches_df.iterrows()]


def generate_content(text: str):
    return client.models.generate_content(model="gemini-2.5-flash", contents=text)


def identify_person(question: str) -> str:
    prompt = f"""
You are an expert concierge and have received a question about a client. Identify the person the question is about and provide their name as output. 

Question:
{question}
"""
    response = generate_content(prompt)
    return response.text.strip()


def answer_with_sources(question: str, top_messages: List[dict]) -> str:
    context = "\n\n".join([f"[{m['id']}] {m['message']}" for m in top_messages])
    prompt = f"""
    You are an expert concierge and have received a request from a client. Use the snippets below.

    Question:
    {question}

    Context:
    {context}

    Structure your answer as a JSON object with the following format:
    {{
    "answer": "The final, concise answer.",
    "confidence": "score between 0 and 1 indicating confidence in the answer",
    "sources": ["msg_id_1", "msg_id_2"],
    "metadata": {{
        "reasoning": "A brief trace of how the system arrived at this conclusion."
    }}
    }}

    Output only the valid JSON object, without any additional explanation or text.
"""
    response = generate_content(prompt)
    return response.text


class IdentifyRequest(BaseModel):
    question: str


class SearchRequest(BaseModel):
    name_part: str
    limit: Optional[int] = 20


class AnswerRequest(BaseModel):
    question: str
    max_context: Optional[int] = 10


@app.get("/identify_person")
def api_identify_person(question: str):
    person = identify_person(question)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"person": person}


@app.post("/search_messages")
def api_search_messages(body: SearchRequest):
    matches = find_messages_by_user_name(body.name_part)
    return {"matched": len(matches), "messages": matches[: body.limit]}


@app.post("/answer")
def api_answer(body: AnswerRequest):
    person = identify_person(body.question)
    messages = find_messages_by_user_name(person)
    if not messages:
        return {
            "question": body.question,
            "person": person,
            "answer": None,
            "note": "No context messages found for person",
            "sources": [],
        }
    top_messages = messages[: body.max_context]
    raw = answer_with_sources(body.question, top_messages)
    try:
        parsed = json.loads(raw)
        return parsed
    except json.JSONDecodeError:
        return {"error": "invalid JSON from model", "raw_response": raw}


if __name__ == "__main__":
    nest_asyncio.apply()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
