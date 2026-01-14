from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

def extract_skills(llm, resume_text: str, interview_data: list):
    interview_summary = ""
    for q in interview_data:
        interview_summary += f"Q: {q.question}\nA: {q.answer}\nScore: {q.score}\n\n"

    prompt = PromptTemplate.from_template("""
    Extract a clean list of technical skills ONLY.

    Resume:
    {resume}

    Interview Performance:
    {interview}

    RULES:
    - Return comma separated skills
    - No explanations
    - No soft skills
    """)

    chain = prompt | llm
    res = chain.invoke({
        "resume": resume_text[:2000],
        "interview": interview_summary[:2000]
    })

    return [s.strip() for s in res.content.split(",") if s.strip()]
