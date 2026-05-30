# NeuroMed: Agentic Clinical Intelligence Platform by Growthstack.dev

![NeuroMed Dashboard](https://img.shields.io/badge/Status-Hackathon_Ready-success?style=for-the-badge) ![Gemini 1.5 Pro](https://img.shields.io/badge/Powered_by-Gemini_1.5_Pro-blue?style=for-the-badge)

NeuroMed is an autonomous Agentic Reasoning Engine designed to fundamentally transform how clinicians interact with unstructured medical data. Built for the Google Cloud Rapid Agent Hackathon, this platform ensures clinical safety, automated tool execution, and transparent observability.



## 🩺 The Problem & Solution

**The Problem:** 
Modern healthcare systems generate massive volumes of unstructured clinical text. Manual chart review is prone to human error, cognitive overload, and delayed diagnosis, especially when reconciling real-time pathology reports with deeply buried historical Electronic Health Records (EHR).

**The Solution:** 
NeuroMed is not a simple chatbot. It is a deterministic, multi-agent orchestration platform. It ingests complex clinical reports, natively interfaces with Model Context Protocol (MCP) tools to dynamically pull historical EHR data, identifies critical contradictions, and automates downstream actions—such as escalating critical risks directly to clinical review boards. It prioritizes zero-hallucination structured outputs, clinical safety, and absolute observability.

## 🧠 Agentic Architecture (Powered by Gemini 1.5 Pro & Vertex AI)

Our architecture abandons legacy linear RAG pipelines in favor of a robust, self-correcting multi-agent framework:

- **Context Agent:** Dynamically parses unstructured medical text to extract core entity identifiers (e.g., Patient IDs, Biomarkers).
- **Orchestrator Agent:** The central intelligence powered by **Gemini 1.5 Pro**. It evaluates extracted data, autonomously decides when to invoke external tools, and synthesizes a deeply explainable structured clinical summary.
- **Critic Agent (Self-Healing Loop):** A supervisory AI that critiques the Orchestrator's logic before the response reaches the user. If logic gaps or missing data are detected, the system autonomously executes a self-healing retry loop to correct itself.

## 🔗 MCP Integrations (Fivetran EHR & GitLab Escalations)

NeuroMed natively integrates with Model Context Protocol (MCP) standard tools for real-world enterprise impact:

- **Fivetran EHR Integration:** The Agent autonomously fetches a patient's historical records when a new report is uploaded, actively comparing new diagnoses with historical medications to prevent dangerous contradictions.
- **GitLab Incident Escalation:** When critical neurological or cardiovascular risks are identified, the Agent autonomously opens a GitLab incident ticket for immediate "human-in-the-loop" clinical review.

## 📊 Observability & Self-Healing (Arize Phoenix)

- **Deterministic Structured Output:** We guarantee pristine JSON responses using strict Pydantic model validation and native Python parsing, eliminating fragile LLM markdown rendering.
- **Agentic Telemetry:** Deep integration with Arize Phoenix tracks every reasoning step, token usage, tool invocation, and confidence score. This provides hospital administrators with a transparent "glass-box" view into the AI's decision-making process.

## 💻 Local Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Talha03creator/NeuroMed.git
   cd NeuroMed
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup:**
   Create a `.env` file in the root directory (use `.env.example` as a template) and add your API keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   AI_MODEL=gemini-1.5-pro
   ```

4. **Run the Backend (FastAPI):**
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

5. **Run the Frontend:**
   Open a new terminal and start a local HTTP server for the dashboard:
   ```bash
   python -m http.server 3000 -d frontend
   ```

6. **Access the Dashboard:**
   Open your browser and navigate to `http://localhost:3000`. Upload a clinical report to see the Agent in action!
