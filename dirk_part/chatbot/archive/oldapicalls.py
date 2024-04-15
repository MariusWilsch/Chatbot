# Old Code
def check_confidence(messages: str, client: Anthropic) -> bool:
    message = client.messages.create(
        model=MODEL, max_tokens=1024, messages=messages, system=CONFIDENCE_TYPE_PROMPT
    )
    print("Confidence Return val: ", message.content[0].text, "\n")
    return json.loads(message.content[0].text).get("confidence")


def choose_model(messages: List, return_val: bool, client: Anthropic):
    system_prompt = DATE_PROMPT if return_val else FOLLOW_UP_PROMPT
    print("Chat history before api call in choose_model: ", messages, "\n")
    messages = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=messages,
        system=f"Return all responses in english. {system_prompt}",
    )
    # print("Path return val:\n", messages.content[0].text, "\n")
    return json.loads(messages.content[0].text)
