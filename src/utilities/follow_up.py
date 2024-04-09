import streamlit as st

# From imports
from typing import List, Union
from extras.prompts import FOLLOWUP_QUESTION_PROMPT
from extras.classes import ConfidenceDetails, ConfidenceDates, ChatMessage
from .call_llm import call_llm


def format_followup_prompt(missing_key_attributes: List[str]) -> str:
    return FOLLOWUP_QUESTION_PROMPT.format(
        missing_key_attributes=", ".join(missing_key_attributes)
    )


def handle_no_confidence(
    messages: List,
    client,
    confidence: Union[ConfidenceDetails, ConfidenceDates],
) -> str:
    print("Handling no confidence")
    followup_prompt = format_followup_prompt(confidence.missing_key_attributes)
    st.sidebar.write("Follow up prompt  \n", followup_prompt)
    followup_question = call_llm(
        messages=messages,
        system_prompt=followup_prompt,
        client=client,
        response_model=ChatMessage,
        # model="claude-3-sonnet-20240229",
    )
    st.session_state.messages.append(
        {"role": "assistant", "content": followup_question.content}
    )
    return followup_question.content
