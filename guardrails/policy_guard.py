from typing import Optional


def validate_query(query: str) -> Optional[str]:
    q = query.lower().strip()

    if not q:
        return "Please enter a valid question."

    blocked_patterns = [
        "ignore company policy",
        "ignore previous instructions",
        "ignore all instructions",
        "reveal system prompt",
        "show system prompt",
        "developer message",
        "hidden prompt",
        "jailbreak",
        "bypass",
        "admin password",
        "tell admin password",
        "steal password",
        "hack",
        "disable security"
    ]

    if any(pattern in q for pattern in blocked_patterns):
        return "This query was blocked by security guardrails."

    company_terms = [
        "company",
        "policy",
        "employee",
        "employees",
        "intern",
        "interns",
        "benefit",
        "benefits",
        "leave",
        "sick",
        "maternity",
        "paternity",
        "work hours",
        "remote",
        "reimbursement",
        "travel",
        "meal",
        "claim",
        "expense",
        "internet",
        "wifi",
        "vpn",
        "password",
        "mfa",
        "security",
        "support",
        "laptop",
        "device",
        "usb",
        "approval",
        "gym"
    ]

    if not any(term in q for term in company_terms):
        return "I can only answer TechNova company policy questions."

    return None