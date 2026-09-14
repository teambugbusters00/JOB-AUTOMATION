from job_agent.models import Job, dedupe, india_eligible
from job_agent.matcher import score
from job_agent.applications.policy import requires_human_review


def test_india_eligibility():
    assert india_eligible(Job("AI Intern", "A", "India", "remote", "https://x", "test"))
    assert not india_eligible(Job("AI Intern", "A", "USA only", "", "https://x", "test"))


def test_dedupe():
    a = Job("Software Engineer Intern", "Acme", "India", "remote", "https://x", "a")
    b = Job("Software Engineer Intern", "Acme", "India", "remote", "https://x?ref=1", "b")
    assert len(dedupe([a, b])) == 1


def test_match_score_positive():
    job = Job("AI Engineer Intern", "Acme", "India", "remote", "https://x", "test", "Python React PyTorch LLM RAG FastAPI")
    assert score(job) >= 70


def test_sensitive_questions_stop_submission():
    assert requires_human_review("Do you require work authorization or sponsorship?")
    assert requires_human_review("Enter your OTP")
    assert not requires_human_review("What Python framework do you prefer?")
