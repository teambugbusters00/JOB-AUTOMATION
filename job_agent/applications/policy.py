SENSITIVE_PATTERNS = [
    "captcha", "otp", "one-time password", "work authorization",
    "sponsorship", "legal declaration", "disability", "veteran", "passport",
    "national id", "aadhaar", "pan number", "salary expectation",
]


def requires_human_review(question: str) -> bool:
    q = question.lower()
    return any(pattern in q for pattern in SENSITIVE_PATTERNS)


def submission_policy() -> dict:
    return {
        "auto_prepare": True,
        "auto_submit": False,
        "human_approval_required": True,
        "captcha_bypass": False,
        "credential_collection": False,
        "false_answer_generation": False,
    }
