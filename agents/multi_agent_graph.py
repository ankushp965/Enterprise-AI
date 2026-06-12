import os
import json
from dotenv import load_dotenv

load_dotenv()
from typing import TypedDict, List, Dict, Any

from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from langgraph.graph import StateGraph, END
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from guardrails.policy_guard import validate_query
from evals.faithfulness_checker import check_faithfulness


ROUTE_TO_FILE = {
    "HR": "docs/hr_policy.txt",
    "EXPENSE": "docs/expense_policy.txt",
    "REMOTE_WORK": "docs/remote_work_policy.txt",
    "SECURITY": "docs/security_policy.txt",
    "IT_SUPPORT": "docs/it_support_policy.txt",
}

VALID_ROUTES = list(ROUTE_TO_FILE.keys())

CHUNK_SIZE = 120
CHUNK_OVERLAP = 0
VECTOR_K_PER_ROUTE = 2
KEYWORD_K_TOTAL = 2
FALLBACK_K = 4
RERANK_TOP_K = 3
MAX_HISTORY = 10

conversation_history = []


class AgentState(TypedDict):
    original_question: str
    rewritten_question: str
    blocked: bool
    guardrail_message: str
    routes: List[str]
    retrieved_docs: List[Any]
    context: str
    domain_outputs: Dict[str, str]
    answer: str
    faithfulness: str
    sources: List[str]


def load_components():
    docs_path = "docs"
    documents = []

    for file in os.listdir(docs_path):
        if file.endswith(".txt"):
            loader = TextLoader(os.path.join(docs_path, file))
            documents.extend(loader.load())

    from langchain_core.documents import Document
    splits = []
    for doc in documents:
        for p in doc.page_content.split("\n\n"):
            p = p.strip()
            if p:
                splits.append(Document(page_content=p, metadata=doc.metadata.copy()))

    tokenized_chunks = [
        doc.page_content.lower().split()
        for doc in splits
    ]

    bm25 = BM25Okapi(tokenized_chunks)

    embeddings = HuggingFaceEmbeddings(model_name="nomic-ai/nomic-embed-text-v1.5")

    if os.path.exists("./chroma_db") and os.listdir("./chroma_db"):
        vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings,
        )
    else:
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory="./chroma_db",
        )

    fallback_retriever = vectorstore.as_retriever(
        search_kwargs={"k": FALLBACK_K}
    )

    llm = ChatOllama(
        model="gemma4:e4b",
    )

    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    return vectorstore, fallback_retriever, llm, splits, bm25, reranker


vectorstore, fallback_retriever, llm, all_splits, bm25, reranker = load_components()


def keyword_search(query, target_files=None, top_k=KEYWORD_K_TOTAL):
    target_files = target_files or []

    query_tokens = query.lower().split()
    scores = bm25.get_scores(query_tokens)

    ranked_indexes = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True,
    )

    results = []

    for idx in ranked_indexes:
        doc = all_splits[idx]

        if target_files and doc.metadata.get("source") not in target_files:
            continue

        results.append(doc)

        if len(results) >= top_k:
            break

    return results


def deduplicate_docs(docs):
    unique_docs = []
    seen = set()

    for doc in docs:
        key = (
            doc.metadata.get("source", "Unknown"),
            doc.page_content,
        )

        if key not in seen:
            seen.add(key)
            unique_docs.append(doc)

    return unique_docs


def rerank_docs(query, docs, top_k=RERANK_TOP_K):
    if not docs:
        return []

    pairs = [[query, doc.page_content] for doc in docs]
    scores = reranker.predict(pairs)

    scored_docs = list(zip(scores, docs))

    scored_docs = sorted(
        scored_docs,
        key=lambda x: x[0],
        reverse=True,
    )

    if not scored_docs:
        return []

    best_score = scored_docs[0][0]

    filtered_docs = [
        doc for score, doc in scored_docs[:top_k]
        if score >= best_score - 2.0
    ]

    return filtered_docs


def rewrite_node(state: AgentState):
    question = state["original_question"].strip()

    history_text = "\n".join(conversation_history[-MAX_HISTORY:])

    if not history_text:
        rewritten = question

    else:
        prompt = f"""
You are a query rewriting agent for a company policy assistant.

Conversation History:
{history_text}

Current Question:
{question}

Task:
Rewrite the current question into a complete standalone question.

Rules:
- Use conversation history ONLY to resolve reference words like this, that, it, same, above, previous.
- Do NOT add unrelated topics from history.
- Preserve the user's current intent.
- Preserve all specific topics from the referenced previous answer.
- Output ONLY the rewritten question.

Examples:

Conversation History:
User: How much internet reimbursement is allowed?
Assistant: Remote employees may claim up to ₹1500/month.

Current Question:
Can interns get this?

Rewritten Question:
Can interns get internet reimbursement?

Conversation History:
User: How much internet reimbursement and VPN access?
Assistant: Internet reimbursement is ₹1500/month. VPN access is mandatory.

Current Question:
Can interns get this?

Rewritten Question:
Can interns get internet reimbursement and VPN access?

Conversation History:
User: How many sick leaves do employees get?
Assistant: Employees receive 12 sick leave days per year.

Current Question:
Is it paid?

Rewritten Question:
Is sick leave paid?

Rewritten Question:
"""

        rewritten = llm.invoke(prompt).content.strip()

    state["rewritten_question"] = rewritten
    return state


def guardrail_node(state: AgentState):
    message = validate_query(state["rewritten_question"])

    if message:
        state["blocked"] = True
        state["guardrail_message"] = message
        state["answer"] = message
        state["faithfulness"] = "N/A"
    else:
        state["blocked"] = False
        state["guardrail_message"] = ""

    return state


def keyword_fallback_router(question):
    q = question.lower()
    routes = []

    if any(word in q for word in ["leave", "sick", "maternity", "paternity", "work hours", "intern benefits", "benefits"]):
        routes.append("HR")

    if any(word in q for word in ["reimbursement", "travel", "meal", "claim", "expense", "internet", "wifi"]):
        routes.append("EXPENSE")

    if any(word in q for word in ["remote", "work from home", "outside india", "core hours", "dubai"]):
        routes.append("REMOTE_WORK")

    if any(word in q for word in ["password", "vpn", "mfa", "device", "usb", "security"]):
        routes.append("SECURITY")

    if any(word in q for word in ["support", "reset", "laptop", "incident", "network"]):
        routes.append("IT_SUPPORT")

    return routes


def router_node(state: AgentState):
    if state["blocked"]:
        return state

    question = state["rewritten_question"]

    prompt = f"""
You are an intent router for TechNova company policy assistant.

Available routes:
{VALID_ROUTES}

Question:
{question}

Return ONLY a JSON list of routes.

Examples:
Question: How much internet reimbursement is allowed?
Answer: ["EXPENSE"]

Question: How many sick leaves and is VPN required?
Answer: ["HR", "SECURITY"]

Question: Can interns get internet reimbursement, sick leave, and VPN access?
Answer: ["EXPENSE", "HR", "SECURITY"]

JSON Routes:
"""

    raw = llm.invoke(prompt).content.strip()

    try:
        routes = json.loads(raw)
        routes = [route for route in routes if route in VALID_ROUTES]
    except Exception:
        routes = []

    if not routes:
        routes = keyword_fallback_router(question)

    state["routes"] = routes
    return state


def extract_domain_question(route: str, question: str) -> str:
    prompt = f"""
You are a question splitter for a multi-agent RAG system.

Original Question:
{question}

Current Route:
{route}

Route meanings:
- HR: leave, sick leave, maternity, paternity, work hours, intern benefits
- EXPENSE: reimbursement, travel, meal, claim, internet reimbursement
- SECURITY: VPN, password, MFA, device, USB, security
- IT_SUPPORT: reset, laptop, incident, network support
- REMOTE_WORK: remote work, outside India, core hours

Task:
Extract ONLY the part of the question related to the current route.

Rules:
- Return only the domain-specific question.
- Do not include topics from other routes.
- If no part belongs to this route, return exactly:
NO_RELEVANT_QUESTION

Examples:

Original Question:
How much internet reimbursement, how many sick leaves, and is VPN required?

Route:
EXPENSE

Output:
How much internet reimbursement is allowed?

Original Question:
How much internet reimbursement, how many sick leaves, and is VPN required?

Route:
HR

Output:
How many sick leaves are allowed?

Original Question:
How much internet reimbursement, how many sick leaves, and is VPN required?

Route:
SECURITY

Output:
Is VPN required?

Domain-specific question:
"""

    return llm.invoke(prompt).content.strip()


def domain_agents_node(state: AgentState):
    if state["blocked"]:
        return state

    question = state["rewritten_question"]
    routes = state["routes"]

    all_retrieved_docs = []
    domain_outputs = {}

    for route in routes:
        if route not in ROUTE_TO_FILE:
            continue

        domain_question = extract_domain_question(route, question)

        if domain_question == "NO_RELEVANT_QUESTION":
            domain_outputs[route] = "No relevant information found for this domain."
            continue

        file_path = ROUTE_TO_FILE[route]

        filtered_retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": VECTOR_K_PER_ROUTE,
                "filter": {"source": file_path},
            }
        )

        vector_docs = filtered_retriever.invoke(domain_question)

        keyword_docs = keyword_search(
            query=domain_question,
            target_files=[file_path],
            top_k=KEYWORD_K_TOTAL,
        )

        route_docs = deduplicate_docs(vector_docs + keyword_docs)

        route_docs = rerank_docs(
            query=domain_question,
            docs=route_docs,
            top_k=RERANK_TOP_K,
        )

        route_context = "\n\n".join(
            [doc.page_content for doc in route_docs]
        )

        prompt = f"""
You are the {route} specialist agent for TechNova Solutions.

Your job:
- Answer ONLY the given domain-specific question.
- Use ONLY the provided context.
- If the context contains a general rule, apply it to the specific question.
- Do not answer topics outside your domain.
- Do not mention other domain names.
- Do not create sections for other domains.
- Do not make up information.
- Preserve numbers, dates, and currency symbols exactly as written in context.
- If your domain context truly does not contain the answer, say exactly:
  No relevant information found for this domain.

Examples:
- If context says "Interns are not eligible for any reimbursement", it applies to internet reimbursement, travel reimbursement, and meal reimbursement.
- If context says "Employees receive 12 sick leave days per year", it answers sick leave questions.
- If context says "VPN access is mandatory for external connections", it answers VPN requirement questions.

Context:
{route_context}

Question:
{domain_question}

{route} Agent Answer:
"""

        domain_answer = llm.invoke(prompt).content.strip()

        domain_outputs[route] = domain_answer
        all_retrieved_docs.extend(route_docs)

    if not all_retrieved_docs:
        vector_docs = fallback_retriever.invoke(question)

        keyword_docs = keyword_search(
            query=question,
            target_files=[],
            top_k=KEYWORD_K_TOTAL,
        )

        all_retrieved_docs = deduplicate_docs(vector_docs + keyword_docs)

        all_retrieved_docs = rerank_docs(
            query=question,
            docs=all_retrieved_docs,
            top_k=RERANK_TOP_K,
        )

        fallback_context = "\n\n".join(
            [doc.page_content for doc in all_retrieved_docs]
        )

        prompt = f"""
You are the GENERAL specialist agent for TechNova Solutions.

Use only this context to answer.

Context:
{fallback_context}

Question:
{question}

Answer:
"""

        domain_outputs["GENERAL"] = llm.invoke(prompt).content.strip()

    all_retrieved_docs = deduplicate_docs(all_retrieved_docs)

    state["retrieved_docs"] = all_retrieved_docs
    state["domain_outputs"] = domain_outputs
    state["context"] = "\n\n".join([doc.page_content for doc in all_retrieved_docs])
    state["sources"] = list(set([doc.metadata.get("source", "Unknown") for doc in all_retrieved_docs]))

    return state


def synthesizer_node(state: AgentState):
    if state["blocked"]:
        return state

    question = state["rewritten_question"]
    domain_outputs = state["domain_outputs"]

    prompt = f"""
You are the final answer synthesizer for TechNova Solutions.

User Question:
{question}

Domain Agent Outputs:
{json.dumps(domain_outputs, indent=2, ensure_ascii=False)}

Your job:
- Combine useful answers from domain agents into one final answer.
- If the question has multiple topics, answer each topic separately in bullet points.
- Keep topic names clearly.
- If a general rule answers a specific topic, explain the connection briefly.
- Remove duplicate or irrelevant information.
- Ignore "No relevant information found for this domain." if at least one domain has a useful answer.
- Do not add new facts beyond the domain agent outputs.
- Preserve numbers, dates, and currency symbols exactly as written.
- Do not change ₹ to ¥ or any other symbol.
- If all domains say "No relevant information found for this domain.", then say:
  I could not find this information in company policy.

Final Answer:
"""

    state["answer"] = llm.invoke(prompt).content.strip()
    return state


def evaluator_node(state: AgentState):
    if state["blocked"]:
        return state

    faithfulness = check_faithfulness(
        context=state["context"],
        answer=state["answer"],
    )

    state["faithfulness"] = faithfulness
    return state


def update_memory_node(state: AgentState):
    if not state["blocked"]:
        conversation_history.append(
            f"User: {state['original_question']}"
        )

        conversation_history.append(
            f"Assistant: {state['answer'][:300]}"
        )

    if len(conversation_history) > MAX_HISTORY:
        del conversation_history[:-MAX_HISTORY]

    return state


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("query_rewriter_agent", rewrite_node)
    graph.add_node("guardrail_agent", guardrail_node)
    graph.add_node("llm_router_agent", router_node)
    graph.add_node("domain_specialist_agents", domain_agents_node)
    graph.add_node("synthesizer_agent", synthesizer_node)
    graph.add_node("evaluator_agent", evaluator_node)
    graph.add_node("memory_update", update_memory_node)

    graph.set_entry_point("query_rewriter_agent")

    graph.add_edge("query_rewriter_agent", "guardrail_agent")
    graph.add_edge("guardrail_agent", "llm_router_agent")
    graph.add_edge("llm_router_agent", "domain_specialist_agents")
    graph.add_edge("domain_specialist_agents", "synthesizer_agent")
    graph.add_edge("synthesizer_agent", "evaluator_agent")
    graph.add_edge("evaluator_agent", "memory_update")
    graph.add_edge("memory_update", END)

    return graph.compile()


multi_agent_graph = build_graph()


def run_multi_agent_graph(question: str):
    initial_state = {
        "original_question": question,
        "rewritten_question": "",
        "blocked": False,
        "guardrail_message": "",
        "routes": [],
        "retrieved_docs": [],
        "context": "",
        "domain_outputs": {},
        "answer": "",
        "faithfulness": "",
        "sources": [],
    }

    result = multi_agent_graph.invoke(initial_state)
    return result