# Application Runbook 🏃💻

This guide provides step-by-step instructions for running the application, utilizing observability tools, and troubleshooting common issues.

## 📋 Prerequisites

Before running the application, ensure your environment meets the following requirements:
1. **Python 3.11+** installed.
2. **Node.js (v18+)** and `npm` installed.
3. **Ollama:** Download and install [Ollama](https://ollama.com/).
   - Pull the required local model by running:
     ```bash
     ollama run gemma4:e4b
     ```

---

## 🚀 Starting the Application

The application requires both the FastAPI backend and the React frontend to be running simultaneously.

### 1. Start the Backend
The backend initializes the LangGraph application, connects to Ollama, builds the vector database, and starts the Phoenix observability server.

Open a terminal in the root directory and run:
```bash
./run_backend.sh
```
*Note: This script will activate the Python virtual environment and run the FastAPI server on `http://localhost:8000` with hot-reloading enabled.*

### 2. Start the Frontend
Open a **new** terminal in the root directory and run:
```bash
cd frontend
npm install  # (Only needed the first time)
../run_frontend.sh
```
*Note: This starts the Vite React server, typically on `http://localhost:5173`. Open this URL in your browser to interact with the UI.*

---

## 🔭 Monitoring & Observability

This project integrates with **Arize Phoenix** for real-time LLM tracing and observability.

When you start the backend, Phoenix is automatically launched.
- **Dashboard URL:** `http://localhost:6006`

**What can you do in Phoenix?**
- View the entire trace of a request through the LangGraph nodes.
- Inspect the inputs and outputs of the Query Rewriter and Router.
- See exactly which context chunks were retrieved by the Vector Store.
- Monitor token usage and latency for every LLM call.

---

## 🔧 Troubleshooting

### 1. Address Already In Use (`[::]:4317` or `6006`)
**Issue:** Phoenix fails to start, throwing an `Address already in use` or `Failed to bind to address` error.
**Cause:** You likely have a previous instance of the backend or Phoenix running in the background.
**Solution:**
Find and kill the zombie Python/Uvicorn process:
```bash
lsof -i :8000
lsof -i :6006
kill -9 <PID>
```

### 2. HuggingFace Warning: `sending unauthenticated requests`
**Issue:** `Warning: You are sending unauthenticated requests to the HF Hub.`
**Cause:** The backend is downloading the embedding model (`nomic-ai/nomic-embed-text-v1.5`) without a token.
**Solution:** This is a safe warning to ignore. However, to prevent rate limits, you can create a `.env` file in the root directory and add:
`HF_TOKEN=your_huggingface_token`

### 3. Missing `aioboto3` Warning
**Issue:** `boto3 is installed but aioboto3 is not.`
**Cause:** Phoenix checks for async AWS SDKs by default.
**Solution:** Safe to ignore, as we are using a local Ollama model, not AWS Bedrock.

### 4. Vector DB Stale Results
**Issue:** You modified a policy in `docs/*.txt`, but the LLM is still returning the old policy.
**Cause:** ChromaDB caches the embedded documents in the `chroma_db/` folder.
**Solution:** Delete the `chroma_db/` directory and restart the backend to force a re-embedding of the text files:
```bash
rm -rf chroma_db/
./run_backend.sh
```
