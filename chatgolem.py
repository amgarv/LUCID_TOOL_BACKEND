from flask import Flask, request, jsonify, make_response # ADDED make_response
from flask_cors import CORS, cross_origin

import json
import os
import requests

app = Flask(__name__)
CORS(app)

# --- ADDED: Manual OPTIONS Preflight Handler ---
@app.before_request
def handle_preflight():
    if request.method.upper() == 'OPTIONS' and request.path == '/chatgolem':
        # This handler will intercept OPTIONS /chatgolem requests
        origin = request.headers.get('Origin')
        allowed_origin = None
        # --- Allow specific Qualtrics origin ---
        # Replace '*' with this line if you want to be specific:
        # if origin == 'https://uky.pdx1.qualtrics.com':
        #      allowed_origin = origin
        # --- OR allow wildcard (used '*' based on original decorator) ---
        allowed_origin = '*' # Using '*' as per your original @cross_origin setting

        if allowed_origin:
            # Manually construct the necessary CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': allowed_origin,
                'Access-Control-Allow-Methods': 'POST, OPTIONS', # Methods route allows
                'Access-Control-Allow-Headers': 'Content-Type', # Headers client sends
                'Access-Control-Max-Age': '86400' # Cache preflight for 1 day
            }
            # Send 204 No Content response with the headers
            # print(f"DEBUG: Sending preflight headers: {cors_headers}") # Optional: temporary print for debugging
            return make_response('', 204, cors_headers)
        else:
            # Origin not allowed by this handler (shouldn't happen with '*')
            # print(f"DEBUG: Preflight origin {origin} not allowed.") # Optional: temporary print
            return make_response('Origin not allowed', 403)
    # If not the specific OPTIONS request, continue normally (Flask handles it)

@app.route('/')
@cross_origin()
def hello_world():
    return 'Hello world!'

# Make sure methods includes OPTIONS
@app.route('/chatgolem', methods=['POST', 'OPTIONS'])
@cross_origin(origins='*') # Keep original decorator for POST handling consistency
def chatgolem():
    # ... rest of your original function ...
    # IMPORTANT: Add a check inside chatgolem if you DON'T want POST logic to run for OPTIONS method
    if request.method == 'OPTIONS':
         # This might be reached if before_request doesn't send response,
         # though it should. Return OK just in case.
         return jsonify(message="OPTIONS request handled by route"), 200

    # --- Original POST logic starts here ---
    post_data = request.data

    try:
        body = json.loads(post_data.decode('utf-8'))
    except json.JSONDecodeError as e:
        print(f'Error decoding JSON: {e}')
        return jsonify({'error': 'Invalid request payload'}), 400

    # Retrieve the OpenAI API key set as an environment variable
    openai_api_key = os.getenv('openai_api_key')
    if not openai_api_key:
        print('OpenAI API key not found')
        return jsonify({'error': 'OpenAI API key not found'}), 500

    # Extract the model specification from the incoming JSON, defaulting to 'gpt-3.5-turbo' if not specified
    model = body.get('model', 'gpt-3.5-turbo')

    # Define the URL for the OpenAI API endpoint specifically for chat completions
    openai_url = 'https://api.openai.com/v1/chat/completions'

    # Ensure the messages structure aligns with OpenAI API requirements
    messages = body.get('messages', [])

    # Set up the headers for the OpenAI API request
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}'
    }

    # Prepare the data for the OpenAI API request to maintain conversation context
    data = {
        'model': model,  # Use the model specified in the request, if any
        'messages': messages  # This directly uses the 'messages' array from the event body
    }

    # Make the request to the OpenAI API
    response = requests.post(openai_url, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        # Extract the generated text from the first choice's message content
        generated_text = response_data['choices'][0]['message']['content']
        return jsonify({'generated_text': generated_text})
    else:
        print(f'Failed to get a response from OpenAI API: {response.text}')
        return jsonify({'error': 'Failed to get a response from OpenAI API', 'details': response.text}), response.status_code

if __name__ == '__main__':
    app.run(debug=True) 
