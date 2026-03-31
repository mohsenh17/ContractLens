"""
prompts.py
----------
Compliance question definitions and prompt templates.

Each question has:
- id: int
- title: short display name
- requirement: the full compliance requirement text from the assignment
- retrieval_query: what to search for in the vectorstore (can differ from the
  requirement text — tuned to find the most relevant contract clauses)
"""

COMPLIANCE_QUESTIONS = [
    {
        "id": 1,
        "title": "Password Management",
        "requirement": (
            "The contract must require a documented password standard covering: "
            "password length/strength, prohibition of default and known-compromised passwords, "
            "secure storage (no plaintext; salted hashing if stored), brute-force protections "
            "(lockout/rate limiting), prohibition on password sharing, vaulting of privileged "
            "credentials/recovery codes, and time-based rotation for break-glass credentials."
        ),
        "retrieval_query": (
            "password policy length strength complexity default credentials storage "
            "hashing brute force lockout rotation privileged vault"
        ),
    },
    {
        "id": 2,
        "title": "IT Asset Management",
        "requirement": (
            "The contract must require an in-scope asset inventory (including cloud accounts/"
            "subscriptions, workloads, databases, security tooling), define minimum inventory "
            "fields, require at least quarterly reconciliation/review, and require secure "
            "configuration baselines with drift remediation and prohibition of insecure defaults."
        ),
        "retrieval_query": (
            "asset inventory cloud accounts workloads databases configuration baseline "
            "reconciliation quarterly drift remediation insecure defaults"
        ),
    },
    {
        "id": 3,
        "title": "Security Training & Background Checks",
        "requirement": (
            "The contract must require security awareness training on hire and at least annually, "
            "and background screening for personnel with access to Company Data to the extent "
            "permitted by law, including maintaining a screening policy and attestation/evidence."
        ),
        "retrieval_query": (
            "security awareness training annual background check screening personnel "
            "employees access company data attestation policy"
        ),
    },
    {
        "id": 4,
        "title": "Data in Transit Encryption",
        "requirement": (
            "The contract must require encryption of Company Data in transit using TLS 1.2+ "
            "(preferably TLS 1.3 where feasible) for Company-to-Service traffic, administrative "
            "access pathways, and applicable Service-to-Subprocessor transfers, with certificate "
            "management and avoidance of insecure cipher suites."
        ),
        "retrieval_query": (
            "encryption in transit TLS 1.2 1.3 data transfer HTTPS cipher suite "
            "certificate subprocessor administrative access"
        ),
    },
    {
        "id": 5,
        "title": "Network Authentication & Authorization Protocols",
        "requirement": (
            "The contract must specify authentication mechanisms (e.g., SAML SSO for users, "
            "OAuth/token-based for APIs), require MFA for privileged/production access, require "
            "secure admin pathways (bastion/secure gateway) with session logging, and require "
            "RBAC authorization."
        ),
        "retrieval_query": (
            "authentication MFA multi-factor SAML SSO OAuth RBAC role-based access control "
            "privileged production admin bastion session logging authorization"
        ),
    },
]


ANALYSIS_PROMPT_TEMPLATE = """You are a strict compliance analyst reviewing a third-party contract.

Your task: assess whether the contract satisfies the compliance requirement below.

=== COMPLIANCE REQUIREMENT ===
{requirement}

=== RELEVANT CONTRACT EXCERPTS ===
{context}

=== INSTRUCTIONS ===
1. Read the excerpts carefully and decide on the compliance state:
   - "Fully Compliant": all aspects of the requirement are explicitly addressed.
   - "Partially Compliant": some aspects are addressed but others are missing or unclear.
   - "Non-Compliant": the requirement is not addressed or contradicted.
2. Extract direct quotes from the excerpts that are most relevant. Use the exact wording from the excerpts.
3. Write a concise rationale explaining your assessment.
4. Estimate your confidence as an integer 0-100.

Respond ONLY with a valid JSON object. No markdown, no explanation outside the JSON.

{{
  "compliance_state": "Fully Compliant" | "Partially Compliant" | "Non-Compliant",
  "confidence": <integer 0-100>,
  "relevant_quotes": ["<exact quote from excerpts>", ...],
  "rationale": "<your reasoning>"
}}
"""
