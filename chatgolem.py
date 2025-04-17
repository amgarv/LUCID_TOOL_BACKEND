from flask import Flask, request, jsonify
# Only import cross_origin from flask_cors
from flask_cors import cross_origin
import json
import os
import requests
import logging

app = Flask(__name__)
# CORS(app) # <<< REMOVE THIS LINE (Let's rely solely on the decorator for this route)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Add CORS to the root route as well if needed ---
@app.route('/')
@cross_origin()
def hello_world():
    return 'This is LUCID'

# --- Explicitly handle OPTIONS and configure cross_origin for chatgolem ---
@app.route('/chatgolem', methods=['POST', 'OPTIONS']) # Add 'OPTIONS' to methods list
@cross_origin(
    # Use environment variable for allowed origins, defaulting to '*' if not set
    origins=os.getenv('ALLOWED_ORIGINS', '*'),
    # Explicitly allow POST and OPTIONS methods
    methods=['POST', 'OPTIONS'],
    # Explicitly allow headers needed by the request (Content-Type is crucial for JSON POST)
    # Add others like 'Authorization' if your frontend ever sends them
    allow_headers=['Content-Type']
)
def chatgolem():
    # --- Add this check for OPTIONS preflight requests ---
    # Flask-CORS usually handles this automatically with @cross_origin,
    # but explicitly returning OK for OPTIONS can sometimes help debugging.
    # This part might not be strictly necessary if Flask-CORS is working perfectly.
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200 # Return OK for preflight

    # --- Existing POST logic starts here ---
    if request.method == 'POST':
        post_data = request.data
        logging.info(f"Received POST request for /chatgolem (size: {len(post_data)} bytes)")

        try:
            body = json.loads(post_data.decode('utf-8'))
        # ... (rest of your validation and OpenAI call logic) ...
        # ... (make sure this part is properly indented under the if request.method == 'POST':)
        except json.JSONDecodeError as e:
             logging.error(f'Error decoding JSON: {e}')
             return jsonify({'error': 'INVALID_JSON', 'message': 'Invalid request payload'}), 400
        # ... etc ...

        # Your existing logic for handling the POST request
        # Ensure proper indentation for the entire POST handling block

        # Example placeholder for rest of POST logic indentation:
        is_valid, error_message = validate_chat_input(body) # Assuming you have this function
        if not is_valid:
             logging.warning(f"Invalid chat input received: {error_message}")
             return jsonify({'error': 'INVALID_INPUT', 'message': error_message}), 400

        openai_api_key = os.getenv('openai_api_key')
        if not openai_api_key:
             logging.error('CRITICAL: OpenAI API key not found in environment variables.')
             return jsonify({'error': 'CONFIG_ERROR', 'message': 'Server configuration error: API key missing.'}), 500

        # ... rest of your successful POST handling logic ...
        # Example: return jsonify({'generated_text': 'some text'})


    # Fallback if method is somehow not OPTIONS or POST (shouldn't happen with route config)
    return jsonify({'error': 'Method not allowed'}), 405


# --- Assuming validate_chat_input function exists ---
def validate_chat_input(data):
    # ... (your validation logic) ...
    return True, ""


# --- Main execution block ---
if __name__ == '__main__':
    app.run(debug=True)