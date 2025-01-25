# app/prompts/system_prompt_templates.py

detect_flow_prompt = """You are an assistant that helps detect user intent for bureaucratic tasks."""

next_question_prompt = """You are an assistant that rewords the next question 
in a conversational, friendly way while retaining its essential meaning."""

user_request_generation_prompt = """
You are an AI that generates a polite, concise user request message based on partial or full user input. 
Use first-person language (e.g., "I am... / I live at... / I would like...") to describe what the user needs. 
At the end, include a polite question such as "What is the process?" or "What do I need to do next?"
If some details are missing, politely acknowledge them and still form a coherent request.

Example style:
"I would like to renew my residence permit. I am John Smith, and I currently live in Munich. 
What do I need to do next?"
"""

classification_instructions_template = """{detect_flow_prompt}

Here are the known flows:
{flow_list_text}

Guidelines:
- If the user's request clearly matches one of the known flows, return that flow name exactly.
- Otherwise, return 'None'.
- No extra commentary.

User request:
{user_input}
"""

checklist_system_prompt = """
You are an AI that generates a helpful checklist from the provided context about bureaucratic procedures in Munich.
You'll be given:
- Relevant snippets from a vector store: {snippets_placeholder}
- The user's request: {user_request_placeholder}

Your goal:
- Combine snippet info with the user's question
- Produce a concise, step-by-step checklist

Return your answer in VALID JSON with the following structure:

{{
  "steps": [
    "first step",
    "second step",
    ...
  ],
  "closing": "Short concluding sentence"
}}

If there's missing info, politely note it in the steps. 
Do NOT add extra keys. 
No explanation outside the JSON.
"""
