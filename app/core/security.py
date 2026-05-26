"""
Security and Compliance Utilities
Agentic Clinical Intelligence Platform

Implements HIPAA-inspired PII redaction to sanitize medical
text before it is processed by the AI agents.
"""

import re
import logging

logger = logging.getLogger(__name__)

def redact_pii(text: str) -> str:
    """
    Fast regex-based PII redaction utility.
    Scrubs Names, SSNs, Phone Numbers, and MRNs to protect patient privacy
    before text is sent to the LLM.
    """
    if not text:
        return text

    # 1. Redact SSNs (Social Security Numbers)
    text = re.sub(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', '[REDACTED_SSN]', text)
    
    # 2. Redact Phone Numbers (US formats)
    text = re.sub(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[REDACTED_PHONE]', text)
    
    # 3. Redact Explicit Name Fields (e.g., "Patient Name: John Doe")
    text = re.sub(
        r'(?i)\b(Patient Name|Name|Patient)\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', 
        r'\1: [REDACTED_NAME]', 
        text
    )
    
    # 4. Redact MRNs (Medical Record Numbers)
    text = re.sub(
        r'(?i)\b(MRN|Medical Record Number)\s*[:\-#]*\s*([A-Z0-9\-]+)', 
        r'\1: [REDACTED_MRN]', 
        text
    )
    
    # 5. Redact Email Addresses
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
        '[REDACTED_EMAIL]', 
        text
    )

    return text
