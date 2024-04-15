import json
import requests
from datetime import datetime
import anthropic
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import openai
import re
import time
import csv
import os

MODEL_OPENAI_GPT4 = "gpt-4-1106-preview"
MODEL_OPENAI_GPT3 = "gpt-3.5-turbo"


def extract_info_from_text(text):
    response_text = openai_first_call_2(text)
    print("response_text\n")
    print(response_text)
    # delete everything in response text before the first { and after the last }
    response_text = response_text[response_text.find("{") :]
    response_text = response_text[: response_text.rfind("}") + 1]

    return response_text


def openai_first_call(userprompt):
    system = f"""Extraheer de volgende informatie uit de gegeven tekst. Als een variabele niet exact kan worden bepaald uit de gegeven tekst, vermeld dit dan, NOOIT iets verzinnen! Voor het variabel 'letselschade' vul 'Ja' of 'Nee' in met een zeer korte en bondige reden waarom en specifiek wat voor een schade/waar. Voor extra duidelijkheid is hier de definitie van letselschade: defenitie letselschade: aansprakelijkheidsrecht (letselschaderecht) - lichamelijk of geestelijk letsel dat door een ander is veroorzaakt en kan leiden tot immateriële schadevergoeding of smartengeld. The json should contain the following variable filled in accordingly: "Letselschade": "", "Claim": "", "Wat is er gebeurd: "", "Hoe is het gebeurd": 
    
    ONlY OUTPUT THE JSON OBJECT NOTHING ELSE!!!
    \n"""
    try:
        response = openai.Completion.create(
            engine="gpt-4-0125-preview",
            prompt=system + userprompt,
            max_tokens=1000,
            temperature=0.2,
            api_key="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",
        )
        content_text = response.choices[0].text.strip()
        return content_text
    except Exception as e:
        print(f"Error in openai_json: {str(e)}")
        return None


def openai_first_call_2(userprompt):
    system = """Extract the following information from the given text. If a variable cannot be determined exactly from the given text, state this, NEVER make anything up!

For the variable 'personal injury' (personal injury damage), fill in 'Yes' or 'No' with a very brief and concise reason why and specifically what kind of damage/where. For extra clarity, here is the definition of personal injury damage:

Definition of personal injury damage: liability law (personal injury law) - physical or mental injury caused by another party that can lead to non-material damages or compensation for pain and suffering.

The JSON should contain the following variables filled in accordingly:
"personal injury": "",
"Claim": "",
"what happend": "",
"How it happend": ""

Fill in each variable with as specific an explanation as possible, don't miss any details.

ONLY OUTPUT THE JSON OBJECT, NOTHING ELSE!"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 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",
        }

        prompt = "information: " + userprompt
        data = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "model": "gpt-4-0125-preview",
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=data,
            headers=headers,
            timeout=25,
        )
        print(response.text)  # Temporarily log the complete response for debugging

        response_data = response.json()

        if "choices" in response_data and response_data["choices"]:
            print(response_data["choices"][0]["message"]["content"])
            return response_data["choices"][0]["message"]["content"]
        else:
            # Handle the case where the expected 'choices' key is not present in the response
            return ""
    except requests.exceptions.Timeout:
        # Handle the timeout exception
        print("The API request timed out after 10 seconds")
        return ""
    except Exception as e:
        # Handle any exception that occurs during the API call
        print(f"An error occurred: {e}")
        return ""


def AI_letselschade(userprompt):
    client = anthropic.Anthropic(
        api_key="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",
    )
    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.2,
            system="""You will receive a JSON with a description of what happened. Your task consists of 2 parts:
Check if there is any personal injury damage. If there is NO such damage, return immediately. In that case, ONLY output a '0'.
If there is personal injury damage, categorize the injury into one of the following categories:
Medical liability -> When you as a patient are dealing with a healthcare provider who makes a medical error causing you harm, the healthcare provider and/or the hospital is liable.
Traffic accidents
Occupational accidents
Accidents caused by animals
Accidents due to defective road surface
Other (if none of the above apply)
Choose 1 of the above without further explanation.
""",
            messages=[{"role": "user", "content": userprompt}],
        )

        content_text = ""
        for content in message.content:
            if hasattr(content, "text"):
                content_text += content.text
        print(content_text)
        return content_text
    except Exception as e:
        print(f"Error in claude_put_in_json: {str(e)}")
        return None


def go_to_judge(json_data_str):
    # API call to categorize letselschade, pass the complete JSON to the API
    type_letsel = AI_letselschade(json_data_str)
    print(type_letsel)

    # Parse the JSON string into a JSON object
    json_data = json.loads(json_data_str)

    # Add the type_letselschade variable to the JSON object
    json_data["type_injury"] = type_letsel

    if type_letsel == "0" or type_letsel == "Medical liability":
        print("No letselschade")
        json_data["result"] = "not accepted"
    else:
        # If situation begin is more than 1 year ago from the current date, return case is closed
        if json_data["situation_begin"][1]:
            situation_begin = json_data["situation_begin"][1]
            situation_begin = datetime.strptime(situation_begin, "%Y-%m-%d")
            if (datetime.now() - situation_begin).days > 365:
                # If case_started is null, then return
                if json_data["case_started"][1]:
                    case_started = json_data["case_started"][1]
                    case_started = datetime.strptime(case_started, "%Y-%m-%d")
                    if (datetime.now() - case_started).days > 365:
                        json_data["result"] = "not accepted"
                    else:
                        json_data["result"] = "accepted"
                else:
                    json_data["result"] = "not accepted"
            else:
                json_data["result"] = "accepted"
        else:
            json_data["result"] = "not accepted"
    return json_data


def merge_json_objects(original_json, new_json):
    # Extract the desired variables from the original JSON
    situation_begin = original_json.get("situation_begin", [])
    case_started = original_json.get("case_started", [])

    # Add the extracted variables to the new JSON
    new_json["situation_begin"] = situation_begin
    new_json["case_started"] = case_started

    return new_json


class JSONFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".json"):
            process_json_file(event.src_path)


def process_json_file(file_path):
    with open(file_path, "r") as file:
        json_data = json.load(file)
    # Concatenate all the text from chat_history
    chat_history_text = " ".join([msg["content"] for msg in json_data["chat_history"]])
    print(chat_history_text)
    print("\n\n")

    # Pass the concatenated text to the extract_info_from_text function
    created_json_str = extract_info_from_text(chat_history_text)
    # load into json
    created_json = json.loads(created_json_str)

    merged_json = merge_json_objects(json_data, created_json)
    print(json.dumps(merged_json, indent=2))

    # create json string for merged json
    merged_json_str = json.dumps(merged_json)
    final_json = go_to_judge(merged_json_str)

    # Save the final JSON data to a CSV file
    save_to_csv(final_json)


def save_to_csv(json_data):
    csv_file = "results.csv"

    # Define the headers in the desired order
    headers = [
        "result",
        "type_injury",
        "Claim",
        "what happend",
        "How it happend",
        "personal injury",
        "situation_begin",
        "case_started",
    ]

    # Check if the CSV file already exists
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, "a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)

        # Write the headers if the file doesn't exist
        if not file_exists:
            writer.writeheader()

        # Create a new dictionary with the desired order of variables
        ordered_data = {header: json_data.get(header, "") for header in headers}

        # Write the ordered data as a new row in the CSV file
        writer.writerow(ordered_data)


def main():
    observer = Observer()
    event_handler = JSONFileHandler()
    observer.schedule(event_handler, path="results", recursive=False)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
