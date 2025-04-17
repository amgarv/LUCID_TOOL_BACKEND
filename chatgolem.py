from flask import Flask, request, jsonify
# Only import cross_origin from flask_cors
from flask_cors import cross_origin
import json
import os
import requests
import logging

app = Flask(__name__)
# Global CORS(app) is removed

# --- Basic Logging Setup ---
# Logs will go to Vercel's runtime logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Root Route ---
@app.route('/')
@cross_origin() # Add cross_origin here too if needed for health checks from browser
def hello_world():
    # You can change this message back if needed
    return 'This is a LUCID endpoint'

# --- Chatgolem Route ---
@app.route('/chatgolem', methods=['POST', 'OPTIONS']) # Add 'OPTIONS' to methods list
@cross_origin(
    # Use environment variable for allowed origins, defaulting to '*' if not set
    origins=os.getenv('ALLOWED_ORIGINS', '*'),
    # Explicitly allow POST and OPTIONS methods
    methods=['POST', 'OPTIONS'],
    # Explicitly allow headers needed by the request (Content-Type is crucial for JSON POST)
    allow_headers=['Content-Type']
)
def chatgolem():
    # <<< --- ADDED THIS LOGGING LINE --- >>>
    logging.info(f"------ Entered chatgolem function with method: {request.method} ------")

    # --- Handle OPTIONS request ---
    if request.method == 'OPTIONS':
        logging.info("Handling OPTIONS request (preflight)") # Optional: log OPTIONS handling
        return jsonify({'status': 'ok'}), 200 # Return OK for preflight

    # --- Handle POST request ---
    if request.method == 'POST':
        logging.info("Handling POST request") # Optional: log POST handling
        post_data = request.data
        logging.info(f"Received POST request for /chatgolem (size: {len(post_data)} bytes)")

        # --- Decode and Validate Request Body ---
        try:
            body = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError as e:
            logging.error(f'Error decoding JSON: {e}')
            return jsonify({'error': 'INVALID_JSON', 'message': 'Invalid request payload'}), 400
        except Exception as e: # Catch potential other decoding errors
            logging.error(f'Error decoding request body: {e}')
            return jsonify({'error': 'DECODING_ERROR', 'message': 'Could not decode request body'}), 400

        is_valid, error_message = validate_chat_input(body)
        if not is_valid:
            logging.warning(f"Invalid chat input received: {error_message}")
            return jsonify({'error': 'INVALID_INPUT', 'message': error_message}), 400

        # --- Get OpenAI API Key ---
        openai_api_key = os.getenv('openai_api_key')
        if not openai_api_key:
            logging.error('CRITICAL: OpenAI API key not found in environment variables.')
            return jsonify({'error': 'CONFIG_ERROR', 'message': 'Server configuration error: API key missing.'}), 500

        # --- Prepare Data for OpenAI ---
        model = body.get('model', 'gpt-3.5-turbo') # Use your preferred default
        messages = body.get('messages', [])
        openai_url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {openai_api_key}'
        }
        data = {
            'model': model,
            'messages': messages
            # Add other OpenAI parameters here if needed, e.g., temperature
        }

        # --- Call OpenAI API ---
        try:
            logging.info(f"Sending request to OpenAI API ({openai_url}) for model {model}")
            response = requests.post(openai_url, headers=headers, json=data, timeout=30) # 30-second timeout
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            response_data = response.json()

            # --- Extract Response ---
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

        # --- Handle Errors during OpenAI Call ---
        except requests.exceptions.Timeout:
            logging.warning(f"Request to OpenAI timed out ({openai_url})")
            return jsonify({'error': 'OPENAI_TIMEOUT', 'message': 'The request to the AI service timed out.'}), 504 # Gateway Timeout
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_details = e.response.text # Get potential error details from OpenAI
            logging.error(f"HTTPError from OpenAI API ({status_code}): {error_details}")
            if status_code == 401:
                logging.error("CRITICAL: OpenAI API Key is invalid or expired.")
                # Don't return OpenAI's raw 401 error to the client
                return jsonify({'error': 'AUTHENTICATION_ERROR', 'message': 'AI service authentication failed.'}), 500
            elif status_code == 429:
                return jsonify({'error': 'RATE_LIMIT_EXCEEDED', 'message': 'AI service rate limit hit. Please try again shortly.'}), 429
            elif status_code == 400:
                 return jsonify({'error': 'OPENAI_BAD_REQUEST', 'message': f'Invalid request sent to AI service.', 'details': error_details}), 400
            else:
                # General OpenAI client/server error
                return jsonify({'error': 'OPENAI_API_ERROR', 'message': f'Failed to get response from AI service (HTTP {status_code}).', 'details': error_details}), status_code
        except requests.exceptions.RequestException as e:
            # Catch other network/connection errors
            logging.error(f"Network error communicating with OpenAI API: {e}")
            return jsonify({'error': 'NETWORK_ERROR', 'message': 'Could not connect to the AI service.'}), 503 # Service Unavailable
        except Exception as e:
            # Catch-all for unexpected errors during POST processing
            logging.exception("An unexpected error occurred processing the POST request.") # Logs traceback
            return jsonify({'error': 'INTERNAL_SERVER_ERROR', 'message': 'An unexpected server error occurred.'}), 500

    # Fallback for methods not explicitly handled (shouldn't be reached with current route)
    return jsonify({'error': 'Method not allowed'}), 405


# --- Basic Input Validation Function ---
# You might want to add more checks here later
def validate_chat_input(data):
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object."
    if 'messages' not in data or not isinstance(data['messages'], list):
        return False, "Missing or invalid 'messages' field (must be a list)."
    if not data['messages']: # Ensure messages list is not empty
         return False, "'messages' list cannot be empty."
    # Check individual messages (optional but good)
    for msg in data['messages']:
        if not isinstance(msg, dict): return False, "Each item in 'messages' must be an object."
        if 'role' not in msg or not isinstance(msg['role'], str) or msg['role'] not in ['system', 'user', 'assistant']: return False, f"Invalid or missing 'role' in message: {msg}"
        if 'content' not in msg or not isinstance(msg['content'], str): return False, f"Invalid or missing 'content' in message: {msg}"
    # Add other checks if needed (e.g., model format)
    return True, ""


# --- Main execution block (for local testing, not used by Vercel) ---
if __name__ == '__main__':
    # Runs locally on port 5000 by default
    app.run(debug=True)