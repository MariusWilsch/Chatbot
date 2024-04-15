import streamlit as st
import instructor as ins
import json, datetime

# From imports
from typing import List, Type, Union
from pydantic import BaseModel, Field
from anthropic import Anthropic, APIError
from dotenv import load_dotenv
from enum import Enum

# Load Environment Variables
load_dotenv()

# Constants
# MODEL = "claude-3-sonnet-20240229"
MODEL = "claude-3-opus-20240229"

CONFIDENCE_TYPE_PROMPT = """Based on the user's description of the accident and the chat history, do you have enough information to confidently classify it as one of the following types: verkeersongevallen, bedrijfsongevallen, ongevallen door dieren, ongevallen door gebrekkig wegdek, or medische aansprakelijkheid? Return a boolean value True if you are confident and False if you are not. Moreover return your rationale for your choice. The following attributes are important to identify to increase the confidence in the choice: Location, parties involved, direct cause Return response in english."""

CONFIDENCE_DATE_PROMPT = """Based on the user's latest chat message and the chat history do you have enough information to confidently determine the start date of the accident and if the case has started? Return a boolean value True if you are confident and False if you are not? The following The following attributes are important to identify to increase the confidence in the choice: Start date of the accident, date the case started or if the case has started. Return all responses in english."""

# Considering the user's provided information, determine the most probable accident type from the options: verkeersongevallen, bedrijfsongevallen, ongevallen door dieren, ongevallen door gebrekkig wegdek, or medische aansprakelijkheid

FOLLOW_UP_PROMPT = """
Current classification: {accident_type}.
Return language: {language}. 
Formulate a follow-up question to gather the missing key details needed to increase confidence in this classification. The question should be conversational and easily understandable to the user. The following attributes are important to identify to increase the confidence in the choice: Location, parties involved, direct cause.
"""

DATE_PROMPT = """Create a follow up message in a conversational and relatable tone. Your task is to figure out when the accident happened. Additionally, you should ask the user if the case has started. The following attributes are important to identify to increase the confidence in the choice: Start date of the accident, date the case started or if the case has started. Do not explain why you ask the question.
The entire response needs to be in english"""

# UI
st.title("We want to learn more about your case")

# Global Variables


class PromptType(Enum):
    CONFIDENCE = "confidence"
    CHAT_MESSAGE = "chat_message"


class StringEnum(Enum):
    UNKNOWN = "Unknown"
    NOTSTARTED = "Not Started"


# Pydantic Class
class ChatInput(BaseModel):
    """Chat Input Model that will be used to store the chat messages."""

    role: str
    content: str = Field(description="The content of the chat message")


class Information(BaseModel):
    """Information about the accident that was classified using the chat history and the user's description."""

    confidence: bool = Field(
        default=False,
        description="Confidence in the classification of the accident type",
    )
    accident_type: str = Field(
        default=[],
        description="The type of accident that was classified. Can be one of the following: verkeersongevallen, bedrijfsongevallen, ongevallen door dieren, ongevallen door gebrekkig wegdek, or medische aansprakelijkheid.",
    )
    rationale: List[str] = Field(
        default=[],
        description="The rationale for the classification of the accident type.",
    )
    # TODO: Imrpove this by using a enum for Unkown and datatime for data
    accident_begin: Union[str, bool] = Field(
        default=None,
        description="Return the date when the accident occurred as a string. If no date is mentioned return false.",
    )
    case_started: Union[str, bool] = Field(
        default=None,
        description="Return the date when the case has begun as a string. If no date is mentioned return false",
    )
    done: bool = Field(
        default=False,
        description="Whether we have all the information. We must have the accident type, start date of the accident, and if the case has started or when it started. Don't set this boolean to true until all the information is provided.",
    )
    # extra_information: str = Field(
    #     default="",
    #     description="Extra information that was provided by the user that can be useful to classify the accident type.",
    # )


# class AccidentDetails(BaseModel):
#     """Details about the accident that was classified using the chat history and the user's description."""

#     confidence: bool = Field(
#         default=False, description="Confidence in the classification"
#     )
#     accident_type: str = Field(
#         default=[],
#         description="The type of accident that was classified. Can be one of the following: verkeersongevallen, bedrijfsongevallen, ongevallen door dieren, ongevallen door gebrekkig wegdek, or medische aansprakelijkheid.",
#     )
#     rationale: List[str] = Field(
#         default=[],
#         description="The rationale for the classification of the accident type.",
#     )


# class AccidentDates(BaseModel):
#     """Dates related to the accident."""

#     accident_begin: Union[datetime.date, StringEnum] = Field(
#         default=None,
#         description="If the date the accident occurred is provided in datetime.date format or correctly assign one of the predefined enums.",
#     )
#     case_started: Union[datetime.date, StringEnum] = Field(
#         default=None,
#         description="If the date the case started is provided then return it datetime.date format else correctly assign one of the predefined enums.",
#     )
#     done: bool = Field(
#         default=False,
#         description="Whether we have all the information such as the accident type, start date of the accident, and if the case has started or when it started.",
#     )


# Session State
# if "AccidentDetails" not in st.session_state:
#     st.session_state.AccidentDetails = AccidentDetails()

# if "AccidentDates" not in st.session_state:
#     st.session_state.AccidentDates = AccidentDates()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        ChatInput(
            role="assistant",
            content="""Hello! The goal of this chat is to learn more about your case. Let us begin by answering this question:  \n**Can you briefly describe how the accident happened and where it took place?** """,
        ).model_dump()
    )
    # st.session_state.messages = []

if "client" not in st.session_state:
    st.session_state.client = ins.from_anthropic(
        client=Anthropic(),
        mode=ins.Mode.ANTHROPIC_JSON,
    )

if "Information" not in st.session_state:
    st.session_state.Information = Information()

if "Output" not in st.session_state:
    st.session_state.Output = []

if "confidence" not in st.session_state:
    st.session_state.confidence = False

for message in st.session_state.messages:
    message_model = ChatInput(**message)  # Provides Type Checking but do we need it?
    with st.chat_message(message_model.role):
        st.markdown(message_model.content)


def call_llm(
    messages: List,
    client: Anthropic,
    system_prompt: str,
    response_model: Union[Type[ChatInput], Type[Information]],
) -> Union[ChatInput, Information]:
    # try:
    message: response_model = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=messages,
        system=system_prompt,
        response_model=response_model,
        max_retries=1,
    )
    return message


# except APIError as e:
#     st.error(f"API Error in call_llm: {e}")
# except Exception as e:
#     st.error(f"Error in call_llm: {e}")


# except Exception as e:
#     st.error(f"Error in call_llm: {e}")


# TODO: Add a before validatior here to check if the messages are in relation to the goal of the chat
def choose_prompt(confidence: bool, type: PromptType):
    if type == PromptType.CONFIDENCE:
        if confidence:
            system_prompt = CONFIDENCE_DATE_PROMPT
        else:
            system_prompt = CONFIDENCE_TYPE_PROMPT
        return system_prompt
    system_prompt = (
        DATE_PROMPT
        if confidence
        else FOLLOW_UP_PROMPT.format(
            accident_type=st.session_state.Information.accident_type,
            language="English",
        )
    )
    return system_prompt


def saving_output(response: Information, confidence: bool):
    st.session_state.Information = response
    if confidence == False:
        st.session_state.Output.append(
            {
                "confidence": response.confidence,
                "accident_type": response.accident_type,
                "rationale": response.rationale,
            }
        )
        return
    st.session_state.Output.append(
        {
            "case_started": response.case_started,
            "accident_begin": response.accident_begin,
        }
    )


# HOW: When storing date how can I only update the case_started or accident_begin and not rest?
def process_prompt(client: Anthropic, messages: List):
    confidence = st.session_state.confidence
    with st.spinner("Processing..."):
        prompt = choose_prompt(
            confidence,
            PromptType.CONFIDENCE,
        )
        print(
            "Calling LLM",
            messages,
        )
        response = call_llm(
            messages=messages,
            client=client,
            system_prompt=prompt,
            response_model=Information,
        )
        # TODO: Instead of saving info into session state I think a class would be better
        saving_output(response, confidence)
        # If the confidcnce is set to to True once we don't want to change it again
        if st.session_state.confidence is False:
            st.session_state.confidence = response.confidence
        if response.done == True:
            return "Thank you for providing the information. We have all the information we need."
        print("Calling LLM 2")
        prompt = choose_prompt(response.confidence, PromptType.CHAT_MESSAGE)
        chat_message = call_llm(
            messages=messages,
            client=client,
            system_prompt=prompt,
            response_model=ChatInput,
        )
        return chat_message.content


if user_prompt := st.chat_input(
    "Add your answer here!", disabled=st.session_state.Information.done
):
    st.session_state.messages.append(
        ChatInput(role="user", content=user_prompt).model_dump()
    )
    with st.chat_message("user"):
        st.markdown(user_prompt, unsafe_allow_html=True)
    content = process_prompt(st.session_state.client, st.session_state.messages[1:])
    with st.chat_message("assistant"):
        st.markdown(content)
    st.session_state.messages.append(
        ChatInput(
            role="assistant",
            content=content,
        ).model_dump()
    )

with st.sidebar:
    st.write("Output: ", st.session_state.Output)
    st.write("Messages: ", st.session_state.messages)
    st.write("Information: ", st.session_state.Information)

# if __name__ == "__main__":
#     pass
