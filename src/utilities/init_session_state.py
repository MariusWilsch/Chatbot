import streamlit as st
import marvin

# * From imports
from enum import Enum
from openai import OpenAI
from anthropic import Anthropic
from config import supabase_client


def init_session_state(state, clientType: Enum):
    if "client" not in state:
        state.client = (
            OpenAI(api_key=st.secrets["openai_api_key_dirk"])
            if clientType == clientType.OPENAI
            else Anthropic(api_key=st.secrets["anthropic_api_key"])
        )
    # if "client" not in state:
    #     state.client = (
    #         OpenAI(api_key=st.secrets["openai_api_key"])
    #         if clientType == clientType.OPENAI
    #         else Anthropic()
    #     )

    if "messages" not in state:
        state.messages = []
        state.messages.append(
            {
                "role": "assistant",
                "content": "Hello! I'm here to help you with your situation. Let's begin with:  \n**What can I help you with?** ",
            }
        )

    if "accident_details_confirmed" not in state:
        state.accident_details_confirmed = False

    if "accident_dates_confirmed" not in state:
        state.accident_dates_confirmed = False

    if "result" not in state:
        state.result = None

    if "summary_generated" not in state:
        state.summary_generated = False

    if "summary_confirmed" not in state:
        state.summary_confirmed = False

    if "marvin_api_key" not in state:
        marvin.settings.openai.api_key = st.secrets["openai_api_key"]

    if "supabase_user" not in state:
        state.supabase_user = supabase_client.auth.sign_in_with_password(
            {
                "email": st.secrets["connections"]["supabase"]["user_email"],
                "password": st.secrets["connections"]["supabase"]["user_password"],
            }
        )
        st.success("Logged in successfully!")

    if "result" not in state:
        state.result = None
