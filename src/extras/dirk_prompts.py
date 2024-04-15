OPENAI_PROMPT = """Extract the following information from the given text. If a variable cannot be determined exactly from the given text, state this, NEVER make anything up!

For the variable 'personal injury' (personal injury damage), fill in 'Yes' or 'No' with a very brief and concise reason why and specifically what kind of damage/where. For extra clarity, here is the definition of personal injury damage:

Definition of personal injury damage: liability law (personal injury law) - physical or mental injury caused by another party that can lead to non-material damages or compensation for pain and suffering.

The JSON should contain the following variables filled in accordingly:
{
"personal_injury": "",
"claim": "",
"what_happened": "",
"how_happened": ""
}

Fill in each variable with as specific an explanation as possible, don't miss any details.

ONLY OUTPUT THE JSON OBJECT, NOTHING ELSE!"""

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
