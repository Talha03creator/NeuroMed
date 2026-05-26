"""
Agents Package — 4-Agent System
Agentic Clinical Intelligence Platform

Agent 1: Orchestrator — Master pipeline controller
Agent 2: Context Agent — Fivetran MCP historical data retrieval
Agent 3: Critic Agent — Arize Phoenix self-healing validation
Agent 4: DevSecOps Agent — GitLab MCP incident management
"""

from app.agents.orchestrator import orchestrator_agent, OrchestratorAgent
from app.agents.context_agent import context_agent, ContextAgent
from app.agents.critic_agent import critic_agent, CriticAgent, phoenix_client
from app.agents.devsecops_agent import devsecops_agent, DevSecOpsAgent, gitlab_client

__all__ = [
    "orchestrator_agent",
    "context_agent",
    "critic_agent",
    "devsecops_agent",
    "phoenix_client",
    "gitlab_client",
    "OrchestratorAgent",
    "ContextAgent",
    "CriticAgent",
    "DevSecOpsAgent",
]
