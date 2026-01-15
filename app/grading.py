import json
from app.llm import get_llm
from app.interview_prompts import GRADING_PROMPT

def grade_answer(question: str, answer: str) -> dict:
    """
    Grade the answer using LLM.
    Returns dict with score, feedback, strength, gap.
    """
    llm = get_llm(temperature=0, max_tokens=500)
    if not llm:
        return {"score": 0, "feedback": "LLM Error", "strength": "", "gap": ""}
        
    chain = GRADING_PROMPT | llm
    
    try:
        response = chain.invoke({
            "question": question,
            "answer": answer
        })
    except Exception as e:
        print(f"⚠️ Grading Error: {e}")
        # Return dummy response object
        response = type('obj', (object,), {'content': '{"score": 0.0, "feedback": "Service unavailable, unable to grade."}'})
    
    content = response.content.strip()
    
    # Cleaning JSON code blocks
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    try:
        data = json.loads(content)
        return {
            "score": float(data.get("score", 0)),
            "feedback": data.get("feedback", ""),
            "strength": data.get("strength", ""),
            "gap": data.get("gap", ""),
            "improvement": data.get("improvement", "")
        }
    except Exception as e:
        print(f"❌ Grading Parse Error: {e}")
        return {
            "score": 0,
            "feedback": "Could not parse grading.",
            "strength": "", 
            "gap": ""
        }
