f# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin # Original imports
import json
import os
import requests
import logging # Keep logging for visibility

app = Flask(__name__)
# Original global CORS setup
CORS(app)

# Basic Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/')
@cross_origin() # Original decorator
def hello_world():
    # Ensure standard spaces for indentation
    return 'Hello world!' # Original message

# --- ADDED 'OPTIONS' to methods list ---
@app.route('/chatgolem', methods=['POST', 'OPTIONS'])
# Original simple decorator
@cross_origin(origins='*')
def chatgolem():
    # Entry log (Optional but helpful)
    logging.info(f"------ Entered chatgolem function with method: {request.method} ------")

    # NOTE: Flask-CORS with automatic_options=True (default) should handle
    # the OPTIONS method implicitly here, responding correctly IF the request reaches it
    # and IF this CORS config works in Vercel Preview. We don't need an explicit
    # 'if request.method == "OPTIONS":' block when relying on the decorator/CORS(app).

    # Original POST Logic (only runs if method is POST)
    if request.method == 'POST':
        logging.info("Handling POST request.")
        post_data = request.data
        try:
            body = json.loads(post_data.decode('utf-8'))
        except Exception as e:
            print(f'Error decoding JSON/Body: {e}') # Original print
            logging.error(f'Error decoding JSON/Body: {e}') # Log too
            return jsonify({'error': 'Invalid request payload'}), 400

        openai_api_key = os.getenv('openai_api_key')
        if not openai_api_key:
            print('OpenAI API key not found') # Original print
            logging.error('CRITICAL: OpenAI API key not found') # Log too
            return jsonify({'error': 'OpenAI API key not found'}), 500

        model = body.get('model', 'gpt-3.5-turbo')
        messages = body.get('messages', [])
        openai_url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {openai_api_key}'
        }
        # Renamed data -> data_payload to avoid potential conflicts
        data_payload = {'model': model, 'messages': messages}

        try:
            logging.info(f"Sending request to OpenAI API...")
            # Added timeout
            response = requests.post(openai_url, headers=headers, json=data_payload, timeout=30)
            if response.status_code == 200:
                response_data = response.json()
                generated_text = response_data['choices'][0]['message']['content']
                logging.info("Successfully received response from OpenAI")
                return jsonify({'generated_text': generated_text})
            else:
                print(f'Failed getting OpenAI response: {response.text}') # Original print
                logging.error(f'Failed getting OpenAI response: {response.status_code} - {response.text}') # Log too
                return jsonify({'error': 'Failed OpenAI Call', 'details': response.text}), response.status_code
        except requests.exceptions.Timeout:
             print("Request to OpenAI timed out")
             logging.warning("Request to OpenAI timed out")
             return jsonify({'error': 'OPENAI_TIMEOUT', 'message': 'The request to the AI service timed out.'}), 504
        except Exception as e:
            print(f"An unexpected error occurred during OpenAI call: {e}")
            logging.exception("An unexpected error occurred during OpenAI call.") # Log traceback
            return jsonify({'error': 'INTERNAL_SERVER_ERROR', 'message': 'Error processing request'}), 500
    else:
        # If method is OPTIONS, Flask-CORS should handle it.
        # If for some reason it reaches here (it shouldn't with automatic_options=True),
        # returning something generic might be needed, but let's rely on Flask-CORS first.
        # A simple OK response might be suitable if Flask-CORS fails to intercept.
        logging.warning(f"Method {request.method} reached end of function unexpectedly.")
        return jsonify(message="OPTIONS handled implicitly or unexpected method"), 200


# Validation function stub (keep if called later, otherwise optional)
def validate_chat_input(data):
    # Add validation logic if/when needed
    return True, ""

# Main block
if __name__ == '__main__':
    app.run(debug=True)