from enum import Enum
from typing import Dict, List
from pydantic import BaseModel
import streamlit as st
import marvin
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class checkingFor(Enum):
    AccidentDetails = 1
    AccidentDates = 2


class TypeOfAccident(Enum):
    NotSure = "Not sure"
    TrafficAccident = "verkeersongevallen"
    CompanyAccident = "bedrijfsongevallen"
    AnimalAccident = "ongevallen door dieren"
    RoadAccident = "ongevallen door gebrekkig wegdek"
    MedicalLiability = "medische aansprakelijkheid"


checker_instructions = [
    """Based on the chat_history can you confidently classify the type of accident? The possible options are verkeersongevallen, bedrijfsongevallen, ongevallen door dieren, ongevallen door gebrekkig wegdek, or medische aansprakelijkheid. Important attributes to check for are the Location, parties involved, and the direct cause of the accident. Only if you have all of them should you classify the accident."""
]


st.title("We want to know more about your case!")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": """Hello! The goal of this chat is to learn more about your case. Let us begin by answering this question:  \n\n**Can you briefly describe how the accident happened and where it took place?** """,
        }
    )

if "checker_state" not in st.session_state:
    st.session_state.checker_state = checkingFor.AccidentDetails

if "client" not in st.session_state:
    st.session_state.client = OpenAI()

for message in st.session_state.messages:
    if message["role"] == "step":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def confidence_checker(messages: List[Dict[str, str]]):
    chat_history = "\n".join([message["content"] for message in messages])
    confidence = marvin.classify(
        data=chat_history,
        labels=TypeOfAccident,
        instructions=checker_instructions[0],
    )
    print(confidence)


class AccidentDetails(BaseModel):
    type_of_accident: TypeOfAccident
    location: str
    parties_involved: str
    direct_cause: str


def extractor(messages: List[Dict[str, str]]):
    chat_history = "\n".join([message["content"] for message in messages])
    response = marvin.extract(
        data=chat_history,
        target=AccidentDetails,
        instructions="Based on the data extract the location, parties involved, and the direct cause of the accident. If you are not sure about any of them, please leave it empty.",
    )
    print(response)
    return response


system_prompt = "Test"


def ask_llm(messages: List[Dict[str, str]], client: OpenAI):
    messages = [{"role": "system", "content": system_prompt}].append(messages)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return completion.choices[0].message


if prompt := st.chat_input("Please answer the following question"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    res = extractor(st.session_state.messages[1:], st.session_state.client)
    st.session_state.messages.append(
        {
            "role": "step",
            "content": f"Extracted information is ${res}",
        }
    )
