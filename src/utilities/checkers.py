import streamlit as st

# From imports
from typing import List
from extras.classes import ConfidenceDetails, ConfidenceDates
from extras.prompts import (
    CHECKER_DATE_PROMPT,
    CHECKER_DETAILS_PROMPT,
)

# Utilities imports
from .follow_up import handle_no_confidence
from .call_llm import call_llm


def check_accident_details(messages: List, client) -> str:
    print("Checking accident details")
    confidence_details = call_llm(
        messages=messages,
        client=client,
        system_prompt=CHECKER_DETAILS_PROMPT,
        response_model=ConfidenceDetails,
        # model="claude-3-opus-20240229",
    )
    if confidence_details.confidence:
        st.session_state.accident_details_confirmed = True
        return None
    else:
        return handle_no_confidence(messages, client, confidence_details)


def check_accident_dates(messages: List, client) -> str:
    print("Checking accident dates")
    confidence_dates = call_llm(
        messages=messages,
        client=client,
        system_prompt=CHECKER_DATE_PROMPT,
        response_model=ConfidenceDates,
        # model="claude-3-opus-20240229",
    )
    if confidence_dates.confidence:
        st.session_state.accident_dates_confirmed = True
        return None
    else:
        return handle_no_confidence(messages, client, confidence_dates)
