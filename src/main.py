# Imports
import json
import streamlit as st
import marvin

# From imports
from enum import Enum

# My own imports
from utilities.init_session_state import init_session_state
from utilities.gen_result import generate_final_result
from utilities.checkers import check_accident_details, check_accident_dates
from utilities.gen_summary import gen_summary
from utilities.judge_case import process_result
from config import total_tokens_used


# * Classes
class clientType(Enum):
    OPENAI = 1
    ANTHROPIC = 2


# * Begin the Streamlit app
st.title("We want to learn more about your case")

# * Initialize the session state
init_session_state(st.session_state, clientType.OPENAI)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def process_user_input() -> str:
    client = st.session_state.client

    if st.session_state.accident_details_confirmed is False:
        followup_question = check_accident_details(
            st.session_state.messages,  #! Try without slicing
            client,
        )
        if followup_question:
            return followup_question

    if st.session_state.accident_dates_confirmed is False:
        followup_question = check_accident_dates(st.session_state.messages, client)
        if followup_question:
            return followup_question

    if st.session_state.summary_generated is False:
        confirmation = gen_summary(st.session_state.messages, st.session_state.client)
        st.session_state.summary_generated = True
        return confirmation

    if st.session_state.summary_confirmed is False:
        last_two_messages = st.session_state.messages[-2:]
        print("last_two_messages: ", last_two_messages)
        result = marvin.classify(
            " ".join([msg["content"] for msg in last_two_messages]),
            labels=["confirm", "deny"],
            instructions="Please classify the last two messages as either confirming or denying the summary.",
        )
        print("result: ", result)
        if result == "confirm":
            st.session_state.summary_confirmed = True
            result = generate_final_result(
                st.session_state.messages, st.session_state.client
            )
            #! Call this asychronously
            process_result(result)
            return (
                "Thank you for confirming the summary. We will come back to you in 1 to 3 days.",
            )

    summary = gen_summary(st.session_state.messages, st.session_state.client)
    return summary


# Get the user's input
if prompt := st.chat_input(
    "What happend?", disabled=st.session_state.summary_confirmed
):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.spinner("Processing..."):
        response = process_user_input()
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    if st.session_state.summary_confirmed:
        st.rerun()


#! For debugging
with st.sidebar:
    # Testing process_result function with json file from result folder
    uploaded_file = st.file_uploader("Upload a file", type=["json"])
    if uploaded_file is not None:
        if st.button("Process File"):
            data = json.load(uploaded_file)
            process_result(data)
    st.write("You can refresh the session by clicking the button below")
    if st.button("Clear"):
        st.session_state.clear()
        init_session_state(st.session_state, clientType.OPENAI)
        st.rerun()
    #! Remove when in production
    st.write("Token amount", total_tokens_used)
    st.write("summary_confirmed:  \n", st.session_state.summary_confirmed)
    st.write(
        "accident_details_confirmed:  \n", st.session_state.accident_details_confirmed
    )
    st.write("accident_dates_confirmed:  \n", st.session_state.accident_dates_confirmed)
    st.write("messages:  \n", st.session_state.messages)
