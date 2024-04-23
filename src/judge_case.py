from enum import Enum
import json, logging
from pprint import pprint
import streamlit as st

# * From imports
from openai import OpenAI, APIError
from anthropic import Anthropic, APIError
from datetime import datetime

# * My own imports
from extras.dirk_prompts import OPENAI_PROMPT, CLAUDE_PROMPT
from config import supabase_client, total_tokens_used

MODEL_OPENAI_GPT4 = "gpt-4-turbo"

# Configure the logging system
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
)


# * ENUM
class Result(str, Enum):
    NOT_ACCEPTED = "not accepted"
    SYSTEM_ERROR = "system_error"
    REQUIRES_HUMAN_ATTENTION = "requires_human_attention"
    ACCEPTED = "accepted"


def call_openai(user_prompt: str, system_prompt: str, client: OpenAI):
    messages = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": user_prompt})
    try:
        message = client.chat.completions.create(
            model=MODEL_OPENAI_GPT4,
            response_format={"type": "json_object"},  # * JSON Mode
            messages=messages,
            temperature=0.2,
        )
        print("Response from LLM: ", message.choices[0].message.content, "\n\n")
        return json.loads(message.choices[0].message.content)
    except APIError as e:
        logging.error(f"API Error in call_openai: {str(e)}")
    except Exception as e:
        logging.error(f"General Error in call_openai: {str(e)}")


def AI_letselschade(user_prompt: str):
    client = Anthropic(
        api_key=st.secrets["anthropic_api_key"],
    )
    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.2,
            system=CLAUDE_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt}
            ],  # ensure this is a list of dictionaries
        )
        print("Response from Claude: ", message.content[0].text, "\n\n")
        return message.content[0].text
    except APIError as e:
        logging.error(f"API Error in AI_letselschade: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"General Error in AI_letselschade: {str(e)}")
        return None


def go_to_judge(data: dict):
    # API call to categorize letselschade, pass the complete JSON to the API
    type_letsel = AI_letselschade(json.dumps(data))
    if type_letsel is None:
        logging.error("Error in AI_letselschade")
        data["result"] = Result.SYSTEM_ERROR
        return data
    print(type_letsel)

    # Add the type_letselschade variable to the JSON object
    data["type_injury"] = type_letsel

    if type_letsel == "0" or type_letsel == "Medical liability":
        print("No letselschade")
        data["result"] = Result.NOT_ACCEPTED
        data["personal_injury"] = False
        data["result_reason"] = (
            "No letselschade" if type_letsel == "0" else "Medical liability"
        )
        return data

    # If situation begin is missing, return system error
    if not data["situation_begin"][1]:
        data["result"] = Result.SYSTEM_ERROR
        data["result_reason"] = "Missing situation date"
        return data

    situation_begin = datetime.strptime(data["situation_begin"][1], "%Y-%m-%d")
    # If situation begin is within 365 days from now, return accepted
    if (datetime.now() - situation_begin).days < 365:
        data["result"] = Result.ACCEPTED
        data["result_reason"] = "Recent situation"
        return data

    if not isinstance(data["case_started"], list):
        data["case_started"] = [data["case_started"]]
    # If case started is unknown, return requires human attention
    if data["case_started"][-1] == "unknown":
        data["result"] = Result.REQUIRES_HUMAN_ATTENTION
        data["result_reason"] = "Unknown case date"
        return data

    # If case started is a date, check if it is within 365 days from now
    if data["case_started"][-1]:
        case_started = datetime.strptime(data["case_started"][-1], "%Y-%m-%d")
        if (datetime.now() - case_started).days < 365:
            data["result"] = Result.ACCEPTED
            data["result_reason"] = "Recent case date"
            return data
        # If case started is more than 365 days ago and situation begin is after case started, return system error
        if situation_begin > case_started:
            data["result"] = Result.SYSTEM_ERROR
            data["result_reason"] = "Case > situation date"
            return data

    data["result"] = Result.NOT_ACCEPTED
    data["result_reason"] = (
        "Situation too old" if data["case_started"][-1] is None else "Case too old"
    )
    return data


def save_to_supabase(data: dict):
    try:
        supabase_client.table("chatbot_results").insert(
            {
                "case_started": (data.get("case_started") or [None])[-1],
                "parties_involved": data.get("parties_involved", None),
                "direct_cause": data.get("direct_cause", None),
                "consequences": data.get("consequences", None),
                "situation_begin": data["situation_begin"][-1],
                "personal_injury": data["personal_injury"],
                "result": data["result"],
                "result_reason": data["result_reason"],
                "type_injury": data["type_injury"],
                "what_happened": data["what_happened"],
                "how_happened": data["how_happened"],
                "short_summary": data["short_summary"],
                "annotations": data["annotation"],
                "cost": data["cost"]["total_cost"],
                "chat_history": data["chat_history"],
            }
        ).execute()
        logging.info("Saved to supabase sql db")
    except Exception as e:
        logging.error(f"Error in save_to_supabase: {e}")


def process_result(chatbot_dict: dict):
    # Concatenate all the text from chat_history
    print("Judging case\n\n")
    chat_history_text = (
        "<chat_history>"
        + "\n".join([msg["content"] for msg in chatbot_dict["chat_history"]])
        + "</chat_history>"
    )

    # Pass the concatenated text to the extract_info_from_text function
    new_dict: dict = call_openai(
        user_prompt=chat_history_text,
        system_prompt=OPENAI_PROMPT,
        client=st.session_state.client,
    )

    # * Merge the extracted info with the original chatbot_dict
    new_dict["situation_begin"] = chatbot_dict.get("situation_begin", [])
    new_dict["case_started"] = chatbot_dict.get("case_started", [])
    # *  Pass the merged dictionary directly to go_to_judge
    final_result = go_to_judge(new_dict)
    final_result.update(chatbot_dict)
    # save_to_supabase(final_result)

    return final_result
