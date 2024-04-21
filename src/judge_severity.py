import json
import streamlit as st


# * From Imports
from utilities.call_llm import call_llm
from extras.prompts import SEVERITY_PROMPT

# Hard coded list of compensation amount with name and money
compensation_amounts = [
    {"name": "Gering letsel", "money": "€100 - €2,000"},
    {"name": "Licht letsel", "money": "€2,000 - €3,500"},
    {"name": "Matig letsel", "money": "€3,500 - €9,000"},
    {"name": "Ernstig letsel", "money": "€9,000 - €21,000"},
    {"name": "Zwaar letsel", "money": "€21,000 - €43,000"},
    {"name": "Zeer zwaar letsel", "money": "€43,000 - €76,000"},
    {"name": "Uitzonderlijk zwaar letsel", "money": "€76,000 - €250,000"},
]


#! I'm not happy with how I'm currently doing this. I think the message should be generated by the LLM. Also the classfication system prompt is a bit abitrary. I think it should be more specific.
#! I want to build the system prompt chatbot first before I start building any other AI Project system prompt
def judge_severity(data: dict) -> str:
    keys_to_keep = [
        "type_injury",
        "short_summary",
        "annotations",
        "parties_involved",
        "consequences",
        "chat_history",
        "direct_cause",
        "what_happened",
        "how_happened",
    ]
    filtered_data = {key: data[key] for key in keys_to_keep if key in data}
    # TODO: Implement this function
    print("<input>\n" + str(filtered_data) + "\n</input>")
    classification = call_llm(
        messages=[{"role": "user", "content": str(filtered_data)}],
        client=st.session_state.client,
        system_prompt=SEVERITY_PROMPT,
        response_model=None,
    )
    print("Classification: ", classification)
    unique_severities = set(classification.values())
    unique_severities.discard(None)  # Remove None values if any

    severities_and_compensations = []
    for severity in unique_severities:
        for compensation in compensation_amounts:
            if compensation["name"] == severity:
                severities_and_compensations.append((severity, compensation["money"]))

    if len(severities_and_compensations) == 1:
        message = f"Your case could be classified as {severities_and_compensations[0][0]} with a compensation amount of {severities_and_compensations[0][1]}"
    else:
        message = "Your case could be classified as multiple severities: "
        for severity, compensation in severities_and_compensations:
            message += f"\n{severity} with a compensation amount of {compensation}\n"

    return (
        "Thank you for confirming the summary.  \n\n"
        + message
        + "  \n\n We will come back to you in 1 to 3 days."
    )
