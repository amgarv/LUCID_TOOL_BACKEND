# -*- coding: utf-8 -*-
# Imports
from flask import Flask, request, jsonify
from flask_cors import CORS # Import CORS, not cross_origin
import json
import os
import requests
import logging

# App Setup
app = Flask(__name__)

# Basic Logging Setup -> Vercel Runtime Logs
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configure CORS Globally with Explicit Parameters ---
CORS(app,
     origins=os.getenv('ALLOWED_ORIGINS', '*'),
     methods=["POST", "OPTIONS"],
     allow_headers=["Content-Type"],
     supports_credentials=False,
     automatic_options=True
)

# Root Route
@app.route('/')
# No decorator needed, handled by CORS(app)
def hello_world():
    # Corrected indentation with standard spaces
    return 'Hello world!' # Original message

# Chatgolem Route
@app.route('/chatgolem', methods=['POST', 'OPTIONS'])
# No decorator needed, handled by CORS(app)
def chatgolem():
    # Entry log
    logging.info(f"------ Entered chatgolem function with method: {request.method} ------")

    # --- NO explicit OPTIONS check needed inside function ---
    # Rely on the global CORS(app) with automatic_options=True to handle it.

    # --- Handle POST request ---
    post_data = request.data
    logging.info("Handling POST request.")
    logging.info(f"Received POST request for /chatgolem (size: {len(post_data)} bytes)")

    # Decode and Validate Request Body
    try:
        body = json.loads(post_data.decode('utf-8'))
    except json.JSONDecodeError as e:
        logging.error(f'Error decoding JSON: {e}')
        return jsonify({'error': 'INVALID_JSON', 'message': 'Invalid request payload'}), 400
    except Exception as e:
        logging.error(f'Error decoding request body: {e}')
        return jsonify({'error': 'DECODING_ERROR', 'message': 'Could not decode request body'}), 400

    is_valid, error_message = validate_chat_input(body)
    if not is_valid:
        logging.warning(f"Invalid chat input received: {error_message}")
        return jsonify({'error': 'INVALID_INPUT', 'message': error_message}), 400

    # Get OpenAI API Key
    openai_api_key = os.getenv('openai_api_key')
    if not openai_api_key:
        logging.error('CRITICAL: OpenAI API key not found in environment variables.')
        return jsonify({'error': 'CONFIG_ERROR', 'message': 'Server configuration error: API key missing.'}), 500

    # Prepare Data for OpenAI
    model = body.get('model', 'gpt-3.5-turbo')
    messages = body.get('messages', [])
    openai_url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}'
    }
    data_payload = {
        'model': model,
        'messages': messages
    }

    # Call OpenAI API
    try:
        logging.info(f"Sending request to OpenAI API ({openai_url}) for model {model}")
        response = requests.post(openai_url, headers=headers, json=data_payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()

        # Extract Response
        if not response_data.get('choices') or not isinstance(response_data['choices'], list) or len(response_data['choices']) == 0:
             logging.error(f"OpenAI response missing 'choices' array: {response_data}")
             return jsonify({'error': 'OPENAI_RESPONSE_MALFORMED', 'message': 'Received unexpected response format from AI.'}), 500
        first_choice = response_data['choices'][0]
        if not first_choice.get('message') or not isinstance(first_choice['message'], dict) or 'content' not in first_choice['message']:
             logging.error(f"OpenAI choice missing 'message.content': {first_choice}")
             return jsonify({'error': 'OPENAI_RESPONSE_MALFORMED', 'message': 'Received unexpected choice format from AI.'}), 500
        generated_text = first_choice['message']['content']
        usage = response_data.get('usage')
        if usage:
             logging.info(f"OpenAI API Usage for {model}: Prompt={usage.get('prompt_tokens', 'N/A')}, Completion={usage.get('completion_tokens', 'N/A')}, Total={usage.get('total_tokens', 'N/A')}")
        logging.info(f"Successfully received response from OpenAI for {model}")
        return jsonify({'generated_text': generated_text})

    # Handle Errors during OpenAI Call
    except requests.exceptions.Timeout:
        logging.warning(f"Request to OpenAI timed out ({openai_url})")
        return jsonify({'error': 'OPENAI_TIMEOUT', 'message': 'The request to the AI service timed out.'}), 504
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_details = e.response.text
        logging.error(f"HTTPError from OpenAI API ({status_code}): {error_details}")
        return jsonify({'error': 'OPENAI_API_ERROR', 'message': f'Failed getting OpenAI response (HTTP {status_code})'}), status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error communicating with OpenAI API: {e}")
        return jsonify({'error': 'NETWORK_ERROR', 'message': 'Could not connect to the AI service.'}), 503
    except Exception as e:
        logging.exception("An unexpected error occurred processing the POST request.")
        return jsonify({'error': 'INTERNAL_SERVER_ERROR', 'message': 'An unexpected server error occurred.'}), 500

# Basic Input Validation Function
def validate_chat_input(data):
    if not isinstance(data, dict): return False, "Request body must be a JSON object."
    if 'messages' not in data or not isinstance(data['messages'], list): return False, "Missing or invalid 'messages' field (must be a list)."
    if not data['messages']: return False, "'messages' list cannot be empty."
    for msg in data['messages']:
        if not isinstance(msg, dict): return False, "Each item in 'messages' must be an object."
        if 'role' not in msg or not isinstance(msg['role'], str) or msg['role'] not in ['system', 'user', 'assistant']: return False, f"Invalid or missing 'role' in message."
        if 'content' not in msg or not isinstance(msg['content'], str): return False, f"Invalid or missing 'content' in message."
    return True, ""

# Main execution block
if __name__ == '__main__':
    app.run(debug=True)