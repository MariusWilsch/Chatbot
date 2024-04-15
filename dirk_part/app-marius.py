import json, datetime, logging
import streamlit as st

import anthropic
import openai

# * From imports
from openai import OpenAI, APIError
from anthropic import Anthropic, APIError

# * My own imports
from extras.prompts import OPENAI_PROMPT, CLAUDE_PROMPT

MODEL_OPENAI_GPT4 = "gpt-4-turbo"
MODEL_OPENAI_GPT3 = "gpt-3.5-turbo"

# Configure the logging system
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
)


def call_openai(user_prompt: str, system_prompt: str, client: OpenAI):
    messages = [{"role": "system", "content": system_prompt}]
    try:
        message = client.chat.completions.create(
            model=MODEL_OPENAI_GPT4,
            response_format={"type": "json_object"},  # * JSON Mode
            messages=messages.extend([{"role": "user", "content": user_prompt}]),
            temperature=0.2,
        )
        print("Response from LLM: ", message.choices[0].message.content, "\n\n")
        return message.choices[0].message.content
    except APIError as e:
        logging.error(f"API Error in call_llm_dirk: {str(e)}")
    except Exception as e:
        logging.error(f"General Error in call_llm_dirk: {str(e)}")


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
            messages=[{"role": "user", "content": user_prompt}],
        )
        print("Response from Claude: ", message.content[0].text, "\n\n")
        return message.content[0].text
    except APIError as e:
        logging.error(f"API Error in AI_letselschade: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"General Error in AI_letselschade: {str(e)}")
        return None


def go_to_judge(json_data_str):
    # API call to categorize letselschade, pass the complete JSON to the API
    type_letsel = AI_letselschade(json_data_str)
    if type_letsel is None:
        logging.error("Error in AI_letselschade")
        return None
    print(type_letsel)

    # Parse the JSON string into a JSON object
    json_data = json.loads(json_data_str)

    # Add the type_letselschade variable to the JSON object
    json_data["type_injury"] = type_letsel

    if type_letsel == "0" or type_letsel == "Medical liability":
        print("No letselschade")
        json_data["result"] = "not accepted"
        return json_data

    # If situation begin is more than 1 year ago from the current date, return case is closed
    if not json_data["situation_begin"][1]:
        json_data["result"] = "not accepted"
        return json_data

    situation_begin = datetime.strptime(json_data["situation_begin"][1], "%Y-%m-%d")
    if (datetime.now() - situation_begin).days > 365:
        if not json_data["case_started"][1]:
            json_data["result"] = "not accepted"
            return json_data

        case_started = datetime.strptime(json_data["case_started"][1], "%Y-%m-%d")
        json_data["result"] = (
            "not accepted" if (datetime.now() - case_started).days > 365 else "accepted"
        )
    else:
        json_data["result"] = "accepted"

    return json_data


def merge_json_objects(original_json, new_json):
    # Extract the desired variables from the original JSON
    situation_begin = original_json.get("situation_begin", [])
    case_started = original_json.get("case_started", [])

    # Add the extracted variables to the new JSON
    new_json["situation_begin"] = situation_begin
    new_json["case_started"] = case_started

    return new_json


def save_to_supabase(json_data):
    logging.info("Saving to supabase sql db")


def process_json_file(file_path):
    with open(file_path, "r") as file:
        json_data = json.load(file)
    # Concatenate all the text from chat_history
    chat_history_text = " ".join([msg["content"] for msg in json_data["chat_history"]])
    print(chat_history_text, "\n\n")

    # Pass the concatenated text to the extract_info_from_text function
    created_json_str = call_openai(
        user_prompt=chat_history_text,
        system_prompt=OPENAI_PROMPT,
        client=st.session_state.client,
    )
    # Bla Bla
    merged_json = merge_json_objects(json_data, json.loads(created_json_str))
    print(json.dumps(merged_json, indent=2))

    # create json string for merged json
    final_json = go_to_judge(json.dumps(merged_json))

    # Save the final JSON data to a CSV file
    save_to_supabase(final_json)
