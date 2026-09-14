# JOB-AUTOMATION

Remote internship/job discovery and application assistant.

## Pipeline
GitHub Actions -> collectors -> normalize -> deduplicate -> eligibility -> CV matcher -> ranking -> storage -> notifications -> approval queue.

Approval-first by design: the system prepares applications but does not bypass CAPTCHAs, authentication, robots rules, or submit legal/work-authorisation declarations without approval.

## Profile
Vijay Ramdev | Jodhpur, Rajasthan, India | B.Tech CSE (AI & ML), JIET | Graduation June 2028 | CGPA 7.18

Target roles: Software Engineering, Full Stack, AI/ML, AI Engineering, ML, Backend, Frontend, GenAI/LLM, AI Agents, Research.

## Run
```bash
pip install -r requirements.txt
python -m job_agent
```
