import os
import sys
import json
from datetime import datetime
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from observability.phoenix_setup import setup_phoenix
from agents.multi_agent_graph import run_multi_agent_graph


setup_phoenix()

app = FastAPI(title="Enterprise AI Evals API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


class FeedbackRequest(BaseModel):
    question: str
    answer: str
    feedback: str


def log_interaction(result):
    os.makedirs("logs", exist_ok=True)

    log_record = {
        "timestamp": datetime.now().isoformat(),
        "question": result["original_question"],
        "rewritten_question": result["rewritten_question"],
        "routes": result["routes"],
        "retrieved_sources": result["sources"],
        "answer": result["answer"],
        "faithfulness": result["faithfulness"],
        "domain_outputs": result["domain_outputs"],
    }

    with open("logs/interactions.jsonl", "a") as f:
        f.write(json.dumps(log_record) + "\n")


@app.get("/")
def health_check():
    return {"status": "API is running"}


@app.post("/ask")
def ask_question(request: AskRequest):
    question = request.question.strip()

    result = run_multi_agent_graph(question)

    log_interaction(result)

    return {
        "blocked": result["blocked"],
        "answer": result["answer"],
        "routes": result["routes"],
        "sources": result["sources"],
        "context": result["context"],
        "faithfulness": result["faithfulness"],
        "rewritten_question": result["rewritten_question"],
        "domain_outputs": result["domain_outputs"],
    }


@app.get("/logs")
def get_logs():
    log_file = "logs/interactions.jsonl"

    if not os.path.exists(log_file):
        return {"logs": []}

    logs = []

    with open(log_file, "r") as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))

    return {"logs": logs[-20:]}


@app.get("/metrics")
def get_metrics():
    log_file = "logs/interactions.jsonl"

    route_counts = {}
    source_counts = {}
    blocked_queries = 0
    faithful_count = 0
    not_faithful_count = 0
    positive_feedback = 0
    negative_feedback = 0

    logs = []

    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))

    for log in logs:
        routes = log.get("routes", [])
        sources = log.get("retrieved_sources", [])
        faithfulness = log.get("faithfulness")

        if len(routes) == 0:
            blocked_queries += 1

        if faithfulness == "FAITHFUL":
            faithful_count += 1
        elif faithfulness == "NOT_FAITHFUL":
            not_faithful_count += 1

        for route in routes:
            route_counts[route] = route_counts.get(route, 0) + 1

        for source in sources:
            source_counts[source] = source_counts.get(source, 0) + 1

    feedback_file = "logs/feedback.jsonl"

    if os.path.exists(feedback_file):
        with open(feedback_file, "r") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    feedback = record.get("feedback", "").lower()

                    if feedback == "positive":
                        positive_feedback += 1
                    elif feedback == "negative":
                        negative_feedback += 1

    return {
        "total_questions": len(logs),
        "blocked_queries": blocked_queries,
        "route_counts": route_counts,
        "source_counts": source_counts,
        "faithful_count": faithful_count,
        "not_faithful_count": not_faithful_count,
        "positive_feedback": positive_feedback,
        "negative_feedback": negative_feedback,
    }


@app.post("/feedback")
def save_feedback(request: FeedbackRequest):
    os.makedirs("logs", exist_ok=True)

    feedback_record = {
        "timestamp": datetime.now().isoformat(),
        "question": request.question,
        "answer": request.answer,
        "feedback": request.feedback,
    }

    with open("logs/feedback.jsonl", "a") as f:
        f.write(json.dumps(feedback_record) + "\n")

    return {"status": "feedback_saved"}