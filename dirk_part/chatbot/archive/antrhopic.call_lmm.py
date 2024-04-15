def call_llm(
    messages: List,
    client: Anthropic,
    system_prompt: str,
    response_model: Union[
        Type[ChatMessage], Type[ConfidenceDetails], Type[ConfidenceDates], Type[Result]
    ],
) -> Union[ChatMessage, ConfidenceDetails, ConfidenceDates, Result]:
    message = client.messages.create(
        model=MODEL_ANTHROPIC,
        max_tokens=1024,
        messages=messages,
        system=system_prompt,
        response_model=response_model,
        max_retries=1,
    )
    # print("Completion: ", completion)
    print("Message: ", message)
    return message
