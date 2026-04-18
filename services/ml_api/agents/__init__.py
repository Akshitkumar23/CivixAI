"""
CivixAI Modular Agent Pipeline
================================
Five-agent architecture for government scheme recommendations:
  1. InputAgent         — Validate & clean user profile data
  2. EligibilityEngine  — Hard rules + ML model ranking
  3. RetrievalAgent     — Keyword + embedding-based scheme retrieval
  4. ReasoningAgent     — GenAI-powered personalized explanations
  5. OutputAgent        — Format final JSON response for frontend
"""

from .input_agent import InputAgent
from .eligibility_engine import EligibilityEngine
from .retrieval_agent import RetrievalAgent
from .reasoning_agent import ReasoningAgent
from .output_agent import OutputAgent
from .pipeline import AgentPipeline

__all__ = [
    "InputAgent",
    "EligibilityEngine",
    "RetrievalAgent",
    "ReasoningAgent",
    "OutputAgent",
    "AgentPipeline",
]
