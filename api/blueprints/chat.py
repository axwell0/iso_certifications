from flask import current_app, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
import google.generativeai as genai
from marshmallow import Schema, fields
import uuid
from collections import deque

chat_bp = Blueprint('chat', __name__, url_prefix='/chat', description='Chat operations')

SYSTEM_PROMPT = """You are a highly knowledgeable ISO certification expert and consultant. You are embedded within a application designed to provide business users with information about ISO certifications.

Your primary role is to respond to business users' queries about ISO certifications in a way that is business-focused, informative, and actionable.  Imagine you are speaking directly to a business owner, manager, or decision-maker who needs to understand the business value and practical implications of ISO certifications for their organization.

When responding, prioritize clarity, conciseness, and a helpful tone.  Structure your answers to address common business user concerns.  Specifically, when answering questions related to a particular ISO certification, aim to cover these key areas (where applicable and relevant to the user's question):

Business-Friendly Definition: Clearly explain what the ISO certification is in simple, business terms. Avoid technical jargon and focus on the core concept.

Business Benefits & Value Proposition:  Explicitly highlight the business advantages of achieving this certification.  Why should a business invest time and resources? (e.g., improved efficiency, enhanced reputation, market access, risk mitigation, customer satisfaction).

Key Requirements & Implementation:  Provide a practical overview of the essential requirements for obtaining the certification. What are the key steps and changes a business needs to make?

Getting Started Guidance: Offer advice on how a business can begin the certification process.  What are the initial steps they should take?

Common Challenges & Considerations:  Address potential challenges, common misconceptions, or important factors businesses should be aware of regarding this certification. Be realistic and provide helpful advice.

Further Resources & Next Steps:  Point users towards relevant resources for more detailed information or assistance (e.g., ISO standards websites, certification bodies, consultants)"""

CHAT_HISTORY = {}


class ChatRequestSchema(Schema):
    message = fields.String(required=True, description="User's query about ISO certification")
    iso = fields.String(required=False, description="Optional ISO standard reference")
    session_id = fields.String(required=False, description="Existing conversation session ID")


class ChatResponseSchema(Schema):
    response = fields.String(description="AI-generated response")
    session_id = fields.String(description="Conversation session ID")
    iso = fields.String(description="Relevant ISO standard")


@chat_bp.route('/')
class ChatResource(MethodView):
    @chat_bp.arguments(ChatRequestSchema, location='json')
    @chat_bp.response(200, ChatResponseSchema)
    def post(self, chat_data):
        """Get ISO-related responses with chat history"""
        try:
            session_id = chat_data.get('session_id') or str(uuid.uuid4())

            if session_id not in CHAT_HISTORY:
                CHAT_HISTORY[session_id] = {
                    'history': deque(maxlen=10),
                    'iso': chat_data.get('iso')
                }

            if chat_data.get('iso') and CHAT_HISTORY[session_id]['iso'] != chat_data.get('iso'):
                abort(400, message="ISO parameter cannot change within an existing session")

            api_key = current_app.config.get('GEMINI_API_KEY')
            if not api_key:
                abort(500, message="Server configuration error: Missing Gemini API key")

            genai.configure(api_key=api_key)
            generation_config = {
                "temperature": 0.5,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
            }

            model = genai.GenerativeModel(
                model_name="gemini-exp-1206",
                generation_config=generation_config,
            )

            history = CHAT_HISTORY[session_id]['history']
            user_message = self._format_message(chat_data['message'], chat_data.get('iso'))
            full_prompt = self._build_full_prompt(history, user_message)

            response = model.generate_content(full_prompt)
            history.append({'role': 'user', 'content': user_message})
            history.append({'role': 'assistant', 'content': response.text})

            return {
                "response": response.text,
                "session_id": session_id,
                "iso": CHAT_HISTORY[session_id]['iso']
            }

        except Exception as e:
            current_app.logger.error(f"Chat error: {str(e)}")
            abort(500, message=f"Error processing request: {str(e)}")

    def _format_message(self, message, iso=None):
        if iso:
            return f"[Regarding ISO {iso}] {message}"
        return message

    def _build_full_prompt(self, history, new_message):
        prompt_parts = [SYSTEM_PROMPT]

        for entry in history:
            prefix = "USER: " if entry['role'] == 'user' else "ASSISTANT: "
            prompt_parts.append(f"\n\n{prefix}{entry['content']}")

        prompt_parts.append(f"\n\nUSER: {new_message}")
        prompt_parts.append("\nASSISTANT: ")

        return "".join(prompt_parts)