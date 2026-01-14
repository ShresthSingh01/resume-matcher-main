from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import Any, List, Optional

class FallbackMockLLM(BaseChatModel):
    """
    Mock LLM that returns safe, static responses when the real API fails.
    """
    def _generate(self, messages: List[Any], stop: Optional[List[str]] = None, **kwargs) -> Any:
        # Check the last message to context-switch
        last_msg = messages[-1].content if messages else ""
        
        # Grading
        if "score" in last_msg.lower() and "feedback" in last_msg.lower():
            return "{\"score\": 7.0, \"feedback\": \"Good answer, but could be more specific.\", \"strength\": \"Clear communication\", \"gap\": \"Depth\", \"improvement\": \"Provide examples\"}"
        
        # Interview Question
        return "Can you describe a challenging technical problem you solved recently?"
        
    @property
    def _llm_type(self) -> str:
        return "mock"

def safe_invoke(llm, input_data):
    try:
        return llm.invoke(input_data)
    except Exception as e:
        print(f"⚠️ LLM Invoke Failed: {e}. Using Fallback.")
        mock = FallbackMockLLM()
        return mock.invoke(input_data)
