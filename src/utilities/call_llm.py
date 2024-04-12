import json
from typing import List, Type, Union, Literal
from openai import OpenAI
from anthropic import Anthropic
from extras.classes import ChatMessage, ConfidenceDetails, ConfidenceDates, Result
from fix_busted_json import repair_json
from config import total_tokens_used

# Constants
MODEL_OPENAI_NEWEST = "gpt-4-turbo"
MODEL_OPENAI_GPT4 = "gpt-4-1106-preview"
MODEL_OPENAI_GPT3 = "gpt-3.5-turbo"


def process_response(response, response_model):
    data = json.loads(repair_json(response))
    if response_model is None:
        return data
    else:
        model = response_model.model_validate(data)
        print("Model: ", model, "\n\n")
        return model


def call_llm_openai(
    messages: List,
    client: OpenAI,
    response_model: Union[
        Type[ChatMessage], Type[ConfidenceDetails], Type[ConfidenceDates], Type[Result]
    ],
    system_prompt: str,
) -> Union[ChatMessage, ConfidenceDetails, ConfidenceDates, dict]:
    # Chat history with system prompt
    chat_history = [{"role": "system", "content": system_prompt}]
    chat_history.extend(messages)
    #! For testing purposes only
    try:
        message = client.chat.completions.create(
            model=MODEL_OPENAI_NEWEST,
            response_format={"type": "json_object"},  # * JSON Mode
            messages=chat_history,
            temperature=0.5,
        )
    except Exception as e:
        print("Error: ", e)
        return None
    print("Response from LLM: ", message.choices[0].message.content, "\n\n")
    print("Token usage: ", message.usage.total_tokens, "\n\n")
    total_tokens_used["input_tok"] += message.usage.total_tokens
    total_tokens_used["output_tok"] += message.usage.completion_tokens
    return process_response(message.choices[0].message.content, response_model)


def call_llm_claude(
    messages: List,
    client: Anthropic,
    system_prompt: str,
    response_model: Union[
        Type[ChatMessage], Type[ConfidenceDetails], Type[ConfidenceDates], Type[Result]
    ],
    model: Literal["claude-3-sonnet-20240229", "claude-3-opus-20240229"],
) -> Union[ChatMessage, ConfidenceDetails, ConfidenceDates, Result]:
    print("Messages: ", messages, "\n\n")
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=messages,
        system=system_prompt,
    )
    print("Response from LLM: ", message.content[0].text, "\n\n")
    return process_response(message.content[0].text, response_model)


def call_llm(
    messages: List,
    client: Union[OpenAI, Anthropic],
    system_prompt: str,
    response_model: Union[
        Type[ChatMessage], Type[ConfidenceDetails], Type[ConfidenceDates], dict
    ],
    model: Literal["claude-3-sonnet-20240229", "claude-3-opus-20240229"] = None,
) -> Union[ChatMessage, ConfidenceDetails, ConfidenceDates, Result]:
    if isinstance(client, OpenAI):
        return call_llm_openai(messages, client, response_model, system_prompt)
    elif isinstance(client, Anthropic):
        return call_llm_claude(
            messages[1:],
            client,
            system_prompt,
            response_model,
            "claude-3-opus-20240229",
        )
    else:
        raise ValueError("Invalid client provided")
