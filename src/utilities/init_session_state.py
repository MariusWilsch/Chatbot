from enum import Enum
from openai import OpenAI
from anthropic import Anthropic


def init_session_state(state, clientType: Enum):
    if "client" not in state:
        state.client = OpenAI() if clientType == clientType.OPENAI else Anthropic()

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

    if "chat_flow_done" not in state:
        state.chat_flow_done = False

    if "summary_generated" not in state:
        state.summary_generated = False

    if "summary_confirmed" not in state:
        state.summary_confirmed = False