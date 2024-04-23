OPENAI_PROMPT = """Extract the following information from the given text. If a variable cannot be determined exactly from the given text, state this, NEVER make anything up!

For extra clarity, here is the definition of personal injury damage:

Definition of personal injury damage: liability law (personal injury law) - physical or mental injury caused by another party that can lead to non-material damages or compensation for pain and suffering.

<response_format>
The JSON must contain the following variables filled in accordingly:
{
"personal_injury": true/false,
"what_happened": string,
"how_happened": string
}

The "personal_injury" field must be a boolean value indicating whether the user is involved in a personal injury case or not.

The "what_happened" field must be a string containing a brief description of the events that led to the injury.

The "how_happened" field must be a string containing an explanation of how the injury occurred.

</response_format>

<notes>
- Fill in each variable with as specific an explanation as possible, don't miss any details.
</notes>
"""

CLAUDE_PROMPT = """You will receive a JSON with a description of what happened. Your task consists of 2 parts:
Check if there is any personal injury damage. If there is NO such damage, return immediately. In that case, ONLY output a '0'.
If there is personal injury damage, categorize the injury into one of the following categories:
Medical liability -> When you as a patient are dealing with a healthcare provider who makes a medical error causing you harm, the healthcare provider and/or the hospital is liable.
Traffic accidents
Occupational accidents
Accidents caused by animals
Accidents due to defective road surface
Other (if none of the above apply)
Choose 1 of the above without further explanation.
"""
