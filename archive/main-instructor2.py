from pprint import pprint
import json, os, uuid
import streamlit as st
import instructor as ins

# From imports
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from typing import List, Literal, Type, Union


# My own imports
from extras.classes import (
    Result,
    ChatMessage,
    ConfidenceDetails,
    ConfidenceDates,
)
from extras.prompts import (
    CHECKER_DETAILS_PROMPT,
    CHECKER_DATE_PROMPT,
    FOLLOWUP_QUESTION_PROMPT,
    RESULT_PROMPT,
)

# Load environment variables
load_dotenv()

# Constants
MODEL_OPENAI = "gpt-4-1106-preview"
# MODEL_ANTHROPIC_SONNET = "claude-3-sonnet-20240229"
# MODEL_ANTHROPIC = "claude-3-opus-20240229"

# Patch the OpenAI client
if "client" not in st.session_state:
    st.session_state.client = ins.from_openai(OpenAI(), mode=ins.Mode.JSON)

st.title("We want to learn more about your case")

# if "client" not in st.session_state:
#     st.session_state.client = ins.from_anthropic(
#         client=Anthropic(),
#         # mode=ins.Mode.ANTHROPIC_JSON,
#     )

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "Hello! I'm here to help you with your case. Let's begin with:  \n**Can you briefly describe how the accident happened and where it took place?** ",
        }
    )

if "accident_details_confirmed" not in st.session_state:
    st.session_state.accident_details_confirmed = False

if "accident_dates_confirmed" not in st.session_state:
    st.session_state.accident_dates_confirmed = False

if "result" not in st.session_state:
    st.session_state.result = None


# Display the chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def call_llm(
    messages: List,
    client,
    system_prompt: str,
    response_model: Union[
        Type[ChatMessage], Type[ConfidenceDetails], Type[ConfidenceDates], Type[Result]
    ],
) -> Union[ChatMessage, ConfidenceDetails, ConfidenceDates, Result]:
    # Chat history with system prompt
    chat_history = [{"role": "assistant", "content": system_prompt}]
    chat_history.extend(messages)
    if response_model is None:
        #! For testing purposes only
        client = OpenAI()
        message = client.chat.completions.create(
            model=MODEL_OPENAI,
            messages=chat_history,
            temperature=1,
        )
        print("Response from LLM: ", message)
        return message.choices[0].message
    else:
        test = client.chat.messages.create(
            model=MODEL_OPENAI,
            messages=chat_history,
            response_model=response_model,
            max_retries=1,
        )
        print("Response from LLM: ", test)
        # print("test: ", test)
        return test


# def call_llm(
#     messages: List,
#     client: Anthropic,
#     system_prompt: str,
#     response_model: Union[
#         Type[ChatMessage], Type[ConfidenceDetails], Type[ConfidenceDates], Type[Result]
#     ],
#     model: Literal["claude-3-sonnet-20240229", "claude-3-opus-20240229"],
# ) -> Union[ChatMessage, ConfidenceDetails, ConfidenceDates, Result]:
#     print("Chat history: ")
#     pprint(messages)
#     print("\n\n")
#     message = client.messages.create(
#         model=model,
#         max_tokens=1024,
#         messages=messages,
#         system=system_prompt,
#         response_model=response_model,
#         max_retries=1,
#     )
#     # print("Completion: ", completion)
#     print("Message: ", message)
#     return message


def format_followup_prompt(missing_key_attributes: List[str]) -> str:
    return FOLLOWUP_QUESTION_PROMPT.format(
        missing_key_attributes=", ".join(missing_key_attributes)
    )


def handle_no_confidence(
    messages: List,
    client: OpenAI,
    confidence: Union[ConfidenceDetails, ConfidenceDates],
) -> str:
    print("Handling no confidence")
    followup_prompt = format_followup_prompt(confidence.missing_to_increase_confidence)
    st.sidebar.write("Follow up prompt  \n", followup_prompt)
    followup_question = call_llm(
        messages=messages,
        system_prompt=followup_prompt,
        response_model=confidence,
        client=client,
        # model="claude-3-sonnet-20240229",
    )
    # print("Completion: ", completion)
    st.session_state.messages.append(
        {"role": "assistant", "content": followup_question.content}
    )
    return followup_question.content


def check_accident_details(messages: List, client: Anthropic) -> str:
    print("Checking accident details")
    confidence_details: ConfidenceDetails = call_llm(
        messages,
        client,
        CHECKER_DETAILS_PROMPT,
        ConfidenceDetails,
        # model="claude-3-opus-20240229",
    )
    if confidence_details.confidence:
        st.session_state.accident_details_confirmed = True
        return None
    else:
        return handle_no_confidence(messages, client, confidence_details)


def check_accident_dates(messages: List, client: Anthropic) -> str:
    print("Checking accident dates")
    confidence_dates: ConfidenceDates = call_llm(
        messages,
        client,
        CHECKER_DATE_PROMPT,
        ConfidenceDates,
        # model="claude-3-opus-20240229",
    )
    if confidence_dates.confidence:
        st.session_state.accident_dates_confirmed = True
        return None
    else:
        return handle_no_confidence(messages, client, confidence_dates)


def generate_final_result(messages: List, client: Anthropic) -> bool:
    print("Generating final result")
    st.session_state.result = call_llm(messages, client, RESULT_PROMPT, Result)
    #! For debugging purposes only - Remove this later. Save the model dump to a file
    os.makedirs("results", exist_ok=True)
    with open(f"results/{uuid.uuid4()}.json", "w") as f:
        json.dump(st.session_state.result.model_dump(), f, indent=2)
    st.session_state.messages.clear()
    return True


def process_user_input() -> str:
    client = st.session_state.client

    if st.session_state.accident_details_confirmed is False:
        followup_question = check_accident_details(
            st.session_state.messages[1:], client
        )
        if followup_question:
            return followup_question

    if st.session_state.accident_dates_confirmed is False:
        followup_question = check_accident_dates(st.session_state.messages[1:], client)
        if followup_question:
            return followup_question

    st.session_state.chat_flow_done = generate_final_result(
        st.session_state.messages[1:], client
    )
    return "Thank you for providing the necessary information. We will reach out back to you."


# Get the user's input
if prompt := st.chat_input("What happend?", disabled=st.session_state.chat_flow_done):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.spinner("Processing..."):
        response = process_user_input()
    with st.chat_message("assistant"):
        st.markdown(response)

with st.sidebar:
    st.write("chat_flow_done:  \n", st.session_state.chat_flow_done)
    st.write("result:  \n", st.session_state.result)
    st.write("messages:  \n", st.session_state.messages)
    st.write(
        "accident_details_confirmed:  \n", st.session_state.accident_details_confirmed
    )
    st.write("accident_dates_confirmed:  \n", st.session_state.accident_dates_confirmed)
    # st.write(st.session_state.client)

# I was walking on the sidewalk in the city center when I accidentally stepped into a large pothole. The pothole was quite deep, and I couldn't see it because it was filled with water from the recent rain. As a result, I lost my balance and fell forward, landing on my right arm. I felt a sharp pain in my wrist and couldn't move it properly. The sidewalk was in poor condition, with several cracks and uneven surfaces around the pothole. I had to go to the hospital for an X-ray, and it turns out I had a fractured wrist.

# Yes the accident happend last year in Feburary. I didn't start and legal proceddings as of now
