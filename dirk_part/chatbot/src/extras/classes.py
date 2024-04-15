from enum import Enum
from pydantic import BaseModel, Field
from typing import List


class AccidentType(str, Enum):
    VERKEERSONGEVALLEN = "verkeersongevallen"
    BEDRIJFSONGEVALLEN = "bedrijfsongevallen"
    ONGEVALLEN_DOOR_DIEREN = "ongevallen door dieren"
    ONGEVALLEN_DOOR_GEBREKKIG_WEGDEK = "ongevallen door gebrekkig wegdek"
    MEDISCHE_AANSPRAKELIJKHEID = "medische aansprakelijkheid"


# class ChatMessage(BaseModel):
#     """Chat Message Model that will be used to store the chat messages. Either user or assistant messages"""

#     content: str = Field(description="Just put the entire message in here")


class ChatMessage(BaseModel):
    """Chat Message Model that will be used to store the chat messages. Either user or assistant messages"""

    role: str = Field(
        description="The role of the chat message. Can be either 'user' or 'assistant'."
    )
    content: str = Field(
        description="The content of the chat message. Either the user or assistant message."
    )


class Result(BaseModel):
    """
    Result model that holds all information about the case.
    """

    accident_type: AccidentType = Field(
        default="",
        description="The classified type of accident. Can be one of the following: verkeersongevallen (traffic accidents), bedrijfsongevallen (occupational accidents), ongevallen door dieren (accidents caused by animals), ongevallen door gebrekkig wegdek (accidents due to poor road conditions), or medische aansprakelijkheid (medical liability). Choose from the predefined list of accident types.",
    )
    rationale: List[str] = Field(
        default="",
        description="A list of reasons providing a clear rationale for the classification of the accident type.",
    )
    annotation: List[str] = Field(
        default=[""],
        description="A list of key entities annotated in the user's description of the accident.",
    )
    accident_begin: str = Field(
        default="",
        description="The date the accident began, if mentioned in the user's description. If no date is mentioned, this field will be an empty string.",
    )
    case_started: str = Field(
        default="",
        description="The date the legal case started, if mentioned in the user's description. If no date is mentioned, this field will be an empty string.",
    )


class ConfidenceDetails(BaseModel):
    """This class will be used to store the output of the checker function for accident classification."""

    missing_key_attributes: List[str] = Field(
        default=[],
        description="A list of missing information or attributes needed to increase confidence in the accident classification. If no missing details are present, this field will be an empty list. ",
    )
    confidence: bool = Field(
        default=False,
        description="A boolean value indicating whether the AI is confident in the accident classification based on the available information.",
    )


class ConfidenceDates(BaseModel):
    """This class will be used to store the output of the checker function for date extraction."""

    # confidence_prompt: str = Field(
    #     description="The system prompt used to guide the AI in determining confidence and missing information for date extraction.",
    #     exclude=True,
    # )
    # question_prompt: str = Field(
    #     description="The user input or question that the AI is attempting to extract dates from.",
    #     exclude=True,
    # )
    missing_key_attributes: List[str] = Field(
        default=[],
        description="A list of missing key attributes needed to confidently extract all the required dates and determine the status of the legal case. If no missing details are present, this field will be an empty list.",
    )
    confidence: bool = Field(
        default=False,
        description="A boolean value indicating whether the AI is confident in its ability to extract all the important dates and determine the status of the legal case based on the available information.",
    )


# class Information(BaseModel):
#     accident_details: getDetails
#     accident_dates: getDates
