from pprint import pprint
import streamlit as st
import json, uuid, os, marvin, datetime

# From imports
from typing import List, Type, Union
from openai import OpenAI
from fix_busted_json import repair_json
from datetime import datetime

# My own imports
from prompts import (
    CHECKER_DETAILS_PROMPT,
    CHECKER_DATE_PROMPT,
    FOLLOWUP_QUESTION_PROMPT,
    RESULT_PROMPT,
)
from classes import ConfidenceDetails, ConfidenceDates, Result, ChatMessage

MODEL_OPENAI_GPT4 = "gpt-4-1106-preview"
MODEL_OPENAI_GPT3 = "gpt-3.5-turbo"

# * Begin the Streamlit app
st.title("We want to learn more about your case")

# * Initialize the session state
if "client" not in st.session_state:
    st.session_state.client = OpenAI()

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

if "chat_flow_done" not in st.session_state:
    st.session_state.chat_flow_done = False

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def convert_json(json_str: str) -> dict:
    json_str = repair_json(json_str)
    return json.loads(json_str)


def call_llm(
    messages: List,
    client: OpenAI,
    response_model: Union[
        Type[ChatMessage], Type[ConfidenceDetails], Type[ConfidenceDates], Type[Result]
    ],
    system_prompt: str,
) -> Union[ChatMessage, ConfidenceDetails, ConfidenceDates, dict]:
    # Chat history with system prompt
    chat_history = [{"role": "system", "content": system_prompt}]
    chat_history.extend(messages)
    #! For testing purposes only
    message = client.chat.completions.create(
        model=MODEL_OPENAI_GPT4,
        response_format={"type": "json_object"},  # * JSON Mode
        messages=chat_history,
        temperature=0.5,
    )
    print("Response from LLM: ", message.choices[0].message.content, "\n\n")
    json = convert_json(message.choices[0].message.content)
    if response_model is None:
        return json
    else:
        model = response_model.model_validate(json)
        print("Model: ", model, "\n\n")
        return model


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


def use_marvin(res_dict: dict, now: datetime) -> dict:
    res_keys = [
        key
        for key in ["accident_begin", "case_started"]
        if key in res_dict and res_dict[key] is not None
    ]
    res_str = ", ".join([str(res_dict[key]) for key in res_keys])
    print("Result string: ", res_str)
    res = marvin.extract(
        data=res_str,
        target=str,
        instructions=f"Please format the data as datetime.date format but as str. For relative values compare to {now}. Only return YYYY-MM-DD formatted dates.",
    )
    for i, key in enumerate(res_keys):
        if i < len(res):
            res_dict[key].append(str(res[i]))
    print("Result from Marvin: ", res, "\n\n")
    pprint(res_dict, indent=2)
    return res_dict


def generate_final_result(messages: List, client) -> bool:
    print("Generating final result")
    data = call_llm(
        messages=messages,
        client=client,
        system_prompt=RESULT_PROMPT,
        response_model=None,
    )
    #! For debugging purposes only - Remove this later. Save the model dump to a file
    now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    processed_data = use_marvin(data, now)
    os.makedirs("results", exist_ok=True)
    with open(f"results/{now}.json", "w") as f:
        json.dump(processed_data, f, indent=4)
    return True


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
        followup_question = check_accident_dates(st.session_state.messages[1:], client)
        if followup_question:
            return followup_question

    st.session_state.chat_flow_done = generate_final_result(
        # st.session_state.messages[1:],
        st.session_state.messages,  #! Try without slicing - Doesn't work for Anthropic
        client,
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
    if st.session_state.chat_flow_done:
        st.rerun()
        # st.session_state.messages.clear()

with st.sidebar:
    st.write("chat_flow_done:  \n", st.session_state.chat_flow_done)
    st.write("result:  \n", st.session_state.result)
    st.write("messages:  \n", st.session_state.messages)
    st.write(
        "accident_details_confirmed:  \n", st.session_state.accident_details_confirmed
    )
    st.write("accident_dates_confirmed:  \n", st.session_state.accident_dates_confirmed)
    if btn := st.button("Try marvin"):
        with open("results/2024-04-08-09-03-49.json", "r") as f:
            result_dict = json.load(f)
        use_marvin(res_dict=result_dict, now=datetime.now())
