from typing import List
from extras.prompts import GEN_SUMMARY_PROMPT
from .call_llm import call_llm


def check_summary(messages: List, result: dict, client) -> str:
    print("Checking Generating")
    # GEN_SUMMARY_PROMPT.format(result_json_placeholder=str(result))
    user_message = {
        "role": "user",
        "content": f"Here's the output json for you to reference: {str(result)}",
    }
    summary = call_llm(
        messages=messages,
        client=client,
        system_prompt=GEN_SUMMARY_PROMPT,
        response_model=None,
    )
    return summary
