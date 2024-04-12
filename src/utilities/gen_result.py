import json, os, marvin
import streamlit as st


# * From imports
from datetime import datetime
from typing import List
from pprint import pprint
from extras.prompts import RESULT_PROMPT
from .call_llm import call_llm
from st_supabase_connection import SupabaseConnection

from config import total_tokens_used

st_supabase_client = st.connection(
    name="supabase_prod_connection",
    type=SupabaseConnection,
)


def use_marvin(res_dict: dict, now: datetime) -> dict:
    marvin.settings.openai.api_key = st.secrets["openai_api_key"]
    res_keys = [
        key
        for key in ["situation_begin", "case_started"]
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


def calc_cost(total_tokens_used):
    input_tokens = total_tokens_used["input_tok"]
    output_tokens = total_tokens_used["output_tok"]

    input_cost = input_tokens * (10.00 / 1000000)
    output_cost = output_tokens * (30.00 / 1000000)

    total_cost = input_cost + output_cost

    total_tokens_used["input_tok"] = 0
    total_tokens_used["output_tok"] = 0

    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
    }


def save_result_to_disk(processed_data: dict):
    now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    os.makedirs("results", exist_ok=True)
    with open(f"results/{now}.json", "w") as f:
        json.dump(processed_data, f, indent=4)
    os.makedirs("last_result", exist_ok=True)
    with open("last_result/last_result.json", "w") as f:
        json.dump(processed_data, f, indent=4)


def save_result_to_supabase(processed_data: dict):
    now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    file_name = f"{now}.json"
    try:
        file_content = json.dumps(processed_data).encode("utf-8")
        try:
            st_supabase_client.create_signed_upload_url(
                "chatbot_results",
                f"results/{file_name}",
                file_content,
                content_type="application/json",
            )
        except Exception as e:
            print(f"Error uploading result file: {e}")
            # Handle the exception or log the error

        try:
            st_supabase_client.create_signed_upload_url(
                "chatbot_results",
                "last_result/last_result.json",
                file_content,
                content_type="application/json",
            )
        except Exception as e:
            print(f"Error uploading last result file: {e}")
            # Handle the exception or log the error

    except Exception as e:
        print(f"Error in save_result_to_supabase: {e}")
        # Handle the exception or log the error


def generate_final_result(messages: List, client):
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
    processed_data["cost"] = calc_cost(total_tokens_used)
    processed_data["chat_history"] = messages
    # * in dev mode, save the result to disk
    # save_result_to_disk(processed_data)
    # * in prod mode, save the result to Supabase
    save_result_to_supabase(processed_data)
