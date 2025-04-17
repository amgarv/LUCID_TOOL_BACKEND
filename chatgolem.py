from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import json
import os
import requests
import logging # Import logging

app = Flask(__name__)
CORS(app) # Consider restricting origins in production later

# --- Basic Logging Setup ---
# Logs will go to Vercel's runtime logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper for Validation ---
def validate_chat_input(data):
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object."
    if 'messages' not in data or not isinstance(data['messages'], list):
        return False, "Missing or invalid 'messages' field (must be a list)."
    if not data['messages']: # Ensure messages list is not empty
         return False, "'messages' list cannot be empty."

    for msg in data['messages']:
        if not isinstance(msg, dict):
            return False, "Each item in 'messages' must be an object."
        if 'role' not in msg or not isinstance(msg['role'], str) or msg['role'] not in ['system', 'user', 'assistant']:
            return False, f"Invalid or missing 'role' in message: {msg}"
        if 'content' not in msg or not isinstance(msg['content'], str):
            return False, f"Invalid or missing 'content' in message: {msg}"
    # Optional: Validate model if needed, maybe check against known values
    if 'model' in data and not isinstance(data['model'], str):
         return False, "Invalid 'model' field (must be a string)."

    return True, ""

@app.route('/')
@cross_origin()
def hello_world():
    return 'Hello world!'

@app.route('/chatgolem', methods=['POST'])
@cross_origin(origins=os.getenv('ALLOWED_ORIGINS', '*')) # Allow configuration via env var
def chatgolem():
    # Read the request body
    post_data = request.data
    logging.info(f"Received request for /chatgolem (size: {len(post_data)} bytes)") # Log incoming request

    try:
        body = json.loads(post_data.decode('utf-8'))
    except json.JSONDecodeError as e:
        logging.error(f'Error decoding JSON: {e}') # Log JSON errors
        return jsonify({'error': 'INVALID_JSON', 'message': 'Invalid request payload'}), 400
    except Exception as e: # Catch potential decoding errors too
        logging.error(f'Error decoding request body: {e}')
        return jsonify({'error': 'DECODING_ERROR', 'message': 'Could not decode request body'}), 400

    # --- Input Validation Step ---
    is_valid, error_message = validate_chat_input(body)
    if not is_valid:
        logging.warning(f"Invalid chat input received: {error_message}") # Log validation failures
        return jsonify({'error': 'INVALID_INPUT', 'message': error_message}), 400

    # Retrieve the OpenAI API key
    openai_api_key = os.getenv('openai_api_key')
    if not openai_api_key: # Basic check is fine, OpenAI call will fail if invalid
        logging.error('CRITICAL: OpenAI API key not found in environment variables.')
        return jsonify({'error': 'CONFIG_ERROR', 'message': 'Server configuration error: API key missing.'}), 500

    # Extract model and messages (already validated)
    # Defaulting model here is fine since JS also provides a default
    model = body.get('model', 'gpt-3.5-turbo')
    messages = body.get('messages', []) # Should always be present due to validation

    logging.info(f"Processing request for model: {model}, message count: {len(messages)}")

    # Define OpenAI API details
    openai_url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}'
    }
    data = {
        'model': model,
        'messages': messages
        # --- Potential Improvement: Add optional parameters here ---
        # e.g., 'temperature': body.get('temperature', 0.7) # Validate first!
        # e.g., 'max_tokens': body.get('max_tokens', 150) # Validate first!
    }

    try:
        # Make the request to the OpenAI API
        logging.info(f"Sending request to OpenAI API ({openai_url}) for model {model}")
        response = requests.post(openai_url, headers=headers, json=data, timeout=30) # Add a timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        response_data = response.json()
        # --- Robust Extraction ---
        if not response_data.get('choices') or not isinstance(response_data['choices'], list) or len(response_data['choices']) == 0:
             logging.error(f"OpenAI response missing 'choices' array: {response_data}")
             return jsonify({'error': 'OPENAI_RESPONSE_MALFORMED', 'message': 'Received unexpected response format from AI.'}), 500
        first_choice = response_data['choices'][0]
        if not first_choice.get('message') or not isinstance(first_choice['message'], dict) or 'content' not in first_choice['message']:
             logging.error(f"OpenAI choice missing 'message.content': {first_choice}")
             return jsonify({'error': 'OPENAI_RESPONSE_MALFORMED', 'message': 'Received unexpected choice format from AI.'}), 500

        generated_text = first_choice['message']['content']
        # --- Log Token Usage (Optional but useful) ---
        usage = response_data.get('usage')
        if usage:
             logging.info(f"OpenAI API Usage for {model}: Prompt={usage.get('prompt_tokens', 'N/A')}, Completion={usage.get('completion_tokens', 'N/A')}, Total={usage.get('total_tokens', 'N/A')}")

        logging.info(f"Successfully received response from OpenAI for {model}")
        return jsonify({'generated_text': generated_text})

    # --- More Granular Error Handling ---
    except requests.exceptions.Timeout:
        logging.warning(f"Request to OpenAI timed out ({openai_url})")
        return jsonify({'error': 'OPENAI_TIMEOUT', 'message': 'The request to the AI service timed out.'}), 504 # Gateway Timeout
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_details = e.response.text
        logging.error(f"HTTPError from OpenAI API ({status_code}): {error_details}")
        if status_code == 401:
            # Log minimally, don't expose details of key issues
            logging.error("CRITICAL: OpenAI API Key is invalid or expired.")
            return jsonify({'error': 'AUTHENTICATION_ERROR', 'message': 'AI service authentication failed.'}), 500 # Internal Server Error better hides this
        elif status_code == 429:
            return jsonify({'error': 'RATE_LIMIT_EXCEEDED', 'message': 'AI service rate limit hit. Please try again shortly.'}), 429
        elif status_code == 400:
             # Often means bad input format not caught by our validation, or model issues
             return jsonify({'error': 'OPENAI_BAD_REQUEST', 'message': f'Invalid request sent to AI service.', 'details': error_details}), 400
        else:
            # General OpenAI client/server error
            return jsonify({'error': 'OPENAI_API_ERROR', 'message': f'Failed to get response from AI service (HTTP {status_code}).', 'details': error_details}), status_code
    except requests.exceptions.RequestException as e:
        # Catch other network/connection errors
        logging.error(f"Network error communicating with OpenAI API: {e}")
        return jsonify({'error': 'NETWORK_ERROR', 'message': 'Could not connect to the AI service.'}), 503 # Service Unavailable
    except Exception as e:
        # Catch-all for unexpected errors during processing
        logging.exception("An unexpected error occurred processing the chat request.") # Logs traceback
        return jsonify({'error': 'INTERNAL_SERVER_ERROR', 'message': 'An unexpected server error occurred.'}), 500


if __name__ == '__main__':
    app.run(debug=True)