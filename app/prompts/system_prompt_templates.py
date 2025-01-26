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

checklist_generation_template = """
You are an assistant tasked with formatting a checklist into a well-structured JSON object for display on the frontend. The checklist data provided below includes steps, sources, and relevant details. Do not modify or add new content from your own knowledge. Simply format the provided checklist into JSON format as instructed.

The expected JSON structure is:

{{
    "query": "<user query>",
    "checklist": [
        {{
            "step": "<step title>",
            "details": [
                "<detail 1>",
                "<detail 2>",
                ...
            ],
            "pdf_links": [
                "<pdf link 1>",
                "<pdf link 2>",
                ...
            ],
            "source": "<source URL>"
        }},
        ...
    ]
}}

  {{
    "steps": [
      "Step 1: Description of the first step.",
      "Step 2: Description of the second step.",
      ...
    ],
    "closing": "Short concluding sentence summarizing the process or providing next steps."
  }}
Here is the data you need to format:

User Query: "{query}"

Checklist Steps:
{formatted_steps}

Format the data into JSON according to the structure described. Do not suggest additional steps or modify the provided information. Include all provided sources and PDF links exactly as they are.
"""
