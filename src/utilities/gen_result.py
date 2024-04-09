import json, os, marvin


# * From imports
from datetime import datetime
from typing import List
from pprint import pprint
from extras.prompts import RESULT_PROMPT
from .call_llm import call_llm

from config import total_tokens_used


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
    cost_data = calc_cost(total_tokens_used)
    processed_data["cost"] = cost_data
    processed_data["chat_history"] = messages
    os.makedirs("results", exist_ok=True)
    with open(f"results/{now}.json", "w") as f:
        json.dump(processed_data, f, indent=4)
    os.makedirs("last_result", exist_ok=True)
    with open("last_result/last_result.json", "w") as f:
        json.dump(processed_data, f, indent=4)
