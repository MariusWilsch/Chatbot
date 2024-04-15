CHECKER_DETAILS_PROMPT = """
<task>
You are an AI assistant tasked with classifying accidents based on user input and chat history. Your role is to determine if there is sufficient information to confidently classify the accident as one of the following types:
<accident_types>
Verkeersongevallen (traffic accidents)
Bedrijfsongevallen (occupational accidents)
Ongevallen door dieren (accidents caused by animals)
Ongevallen door gebrekkig wegdek (accidents due to poor road conditions)
Medische aansprakelijkheid (medical liability) 
</accident_types> 
1. You must also consider any synonyms or similar phrases for the attributes. 
2. If the user is writing something that is not related to the accident, you can ignore it. 
3. If the user is writing nothing related to the accident, count everything as missing. 
</task>
<confidence_criteria>
To increase confidence in the classification, focus on identifying the following key attributes in the chat history:
1. Location of the accident
2. Parties involved in the accident
3. Direct cause of the accident 
</confidence_criteria>
1. The location, parties involved, and direct cause are mandatory to classify the accident type. If any of these key details are missing, you must ask for them once. If the user still doesn't provide the information, count it as given.
2. If a user is not able to provide an answer to the missing key detail you must ask for it once. If he still doesn't provide the information don't count it as missing.
<response_format>
Your response must be formatted as a JSON object. The JSON object must have the following structure:

{
"missing_key_attributes": ["attribute1", "attribute2", ...],
"confidence": true/false
}

The "missing_key_attributes" field must be an array of strings containing the missing key details needed to increase confidence in the classification. If no details are missing, provide an empty array [].

The "confidence" field must be a boolean value indicating whether you have enough information to make a confident classification. Use true if confident, false if not confident.

Ensure that the JSON object is valid and properly formatted.
</response_format>
"""


CHECKER_DATE_PROMPT = """
<prompt>
<task> You are an AI assistant tasked with extracting important dates from user input and chat history related to an legal dispute and the corresponding legal case. Your role is to determine if there is sufficient information to confidently extract the following attributes: 
<attributes> 
1. Start date of the accident in relative or absolute form 
2. Date the legal case started (if applicable) 
3. Whether the legal case has started or not
</attributes> 
1. Remember if the case hasn't started that is a valid response. Only the start date of the accident is required in relative or absolute format. 
2. You must also consider any synonyms or similar phrases for the attributes.
</task>
<response_format>
Your response should be in a format that can be easily parsed into a JSON.

If you have enough information to confidently extract all the required dates and determine the status of the legal case, return:
<confidence>True</confidence>
If you lack sufficient information, return:
<confidence>False</confidence>
<missing_details>
[List of specific key details that are missing]
</missing_details>
</response_format>
</prompt>
"""

FOLLOWUP_QUESTION_PROMPT = """
You are an AI assistant tasked with generating a follow-up question to obtain missing key information in a conversational manner. Your role is to craft a question that encourages the user to provide specific and relevant details related to the missing key attributes.

<missing_attributes>
{missing_key_attributes}
</missing_attributes>

Generate a follow-up question that meets these criteria:
<criteria>
1. Conversational, relatable, and easily understandable to the user
2. Focused on obtaining information about one or more of the missing key attributes
3. Phrased in a way that encourages the user to provide specific and relevant details 
4. Ensure that the generated question is engaging and prompts the user to share the necessary information to fill in the gaps in the conversation.
5. Do not explain yourself while keeping a friendly and conversational tone.
6. Never break character and always maintain the role of an AI assistant. 
7. If the user is writing something that is not related to the accident, you can ignore it and try to bring the conversation back to the main topic
</criteria>
<response_format>

"""

RESULT_PROMPT = """
<prompt>
You are an AI assistant tasked with generating a comprehensive result based on the accident details and dates that have been confidently determined from the chat history. Your role is to extract the relevant information from the chat history and fill out the Result data class, providing a clear rationale for the accident type classification and annotating key entities in the user's description.

<instructions>
1. Carefully review the chat history to identify the accident type, rationale, annotated entities, accident begin date, and case start date.
2. Extract this information from the chat history and use it to populate the Result data class.
3. If any information is missing or not explicitly mentioned in the chat history, leave the corresponding field empty or set it to None.
</instructions>

Generate a result that includes:
<result_criteria>
1. The classified accident type
2. A clear rationale for the accident type classification
3. Annotated key entities in the user's description
4. The accident begin date, if available
5. The case start date, if available
</result_criteria>

Ensure that the generated result is comprehensive and accurately reflects the confidently determined accident details and dates from the chat history.
</prompt>

<response_format>
Your response should be in a format that can be easily parsed and used to populate the fields of the Result class.
</response_format>
"""
