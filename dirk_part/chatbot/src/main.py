# Imports
import streamlit as st

# From imports
from enum import Enum

# My own imports
from utilities.session_state import init_session_state
from utilities.gen_result import generate_final_result
from utilities.checkers import check_accident_details, check_accident_dates

# * Constats
TOKEN_AMOUNT = 0


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
            # st.session_state.messages[1:],
            st.session_state.messages,  #! Try without slicing
            client,
        )
        if followup_question:
            return followup_question

    if st.session_state.accident_dates_confirmed is False:
        followup_question = check_accident_dates(st.session_state.messages, client)
        if followup_question:
            return followup_question

    st.session_state.chat_flow_done = True
    end_prompt = "Thank you for sharing your story. We will now generate a comprehensive result based on the information provided."
    st.session_state.messages.append({"role": "assistant", "content": end_prompt})
    return end_prompt


# Get the user's input
if prompt := st.chat_input("What happend?", disabled=st.session_state.chat_flow_done):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.spinner("Processing..."):
        response = process_user_input()
    with st.chat_message("assistant"):
        st.markdown(response)
    if st.session_state.chat_flow_done:
        generate_final_result(st.session_state.messages, st.session_state.client)
        st.rerun()
        # st.session_state.messages.clear()

with st.sidebar:
    st.write("chat_flow_done:  \n", st.session_state.chat_flow_done)
    st.write("messages:  \n", st.session_state.messages)
    st.write(
        "accident_details_confirmed:  \n", st.session_state.accident_details_confirmed
    )
    st.write("accident_dates_confirmed:  \n", st.session_state.accident_dates_confirmed)
