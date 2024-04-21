from anthropic import Anthropic

client = Anthropic(
    api_key="sk-xx",
)

# * Der User prompted die AI
message = [{"role": "system", "content": "<user_prompt>"}]

# * Der AI generierte die response
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    temperature=0.2,
    system="<system_prompt>",
    messages=message,
)

response_text = message.content[0].text

print("Response from Claude: ", message.content[0].text, "\n\n")

# * Wir fügen die Antwort der AI in das Array hinzu
message.append({"role": "assistant", "content": response_text})

print("Message: ", message)

# * Wir fügen die User Antwort in das Array hinzu
message.append({"role": "user", "content": "<user_prompt>"})

print("Message: ", message)

# * Wir prompten die AI mit dem Array
response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    temperature=0.2,
    system="<system_prompt>",
    messages=message,
)

print("Response from Claude: ", response.content[0].text, "\n\n")

# * Wir fügen die Antwort der AI in das Array hinzu
