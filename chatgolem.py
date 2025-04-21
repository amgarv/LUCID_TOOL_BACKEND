# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, make_response # Keep make_response
# REMOVE from flask_cors import CORS, cross_origin # Remove Flask-CORS imports
import json
import os
import requests
import logging # Use standard logging

app = Flask(__name__)
# REMOVE CORS(app) # Remove global Flask-CORS initialization

# Basic Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Helper function to get allowed origins list OR the wildcard default
def get_allowed_origins_config():
    # Reads ALLOWED_ORIGINS env var. If not set/empty, defaults to ['*']
    origins_str = os.getenv('ALLOWED_ORIGINS')
    if not origins_str:
        logging.warning("ALLOWED_ORIGINS environment variable not set or empty. Defaulting CORS policy to allow all origins ('*').")
        return ['*'] # Default to Wildcard list
    # Parse comma-separated list
    allowed_list = [origin.strip() for origin in origins_str.split(',') if origin.strip()]
    logging.info(f"Using specific ALLOWED_ORIGINS: {allowed_list}")
    return allowed_list

# Manual OPTIONS Preflight Handler using Environment Variable or Default
@app.before_request
def handle_preflight():
    # Handle OPTIONS requests for the specific chat endpoint
    if request.method.upper() == 'OPTIONS' and request.path == '/chatgolem':
        logging.info(f"Intercepting OPTIONS request for {request.path}")
        origin = request.headers.get('Origin')
        logging.info(f"Request Origin: {origin}")

        # Use the helper function to get configured/default origins
        allowed_origins = get_allowed_origins_config()

        origin_to_send_in_header = None
        allow_credentials_value = 'false' # Default (MUST be false for wildcard)

        # Determine appropriate CORS headers based on config and request origin
        if '*' in allowed_origins: # Check if wildcard is the policy
            origin_to_send_in_header = '*'
            allow_credentials_value = 'false' # Credentials cannot be true with wildcard
            logging.info("CORS Policy Check: Wildcard origin allowed.")
        elif origin and origin in allowed_origins: # Check if specific origin is allowed
            origin_to_send_in_header = origin # Reflect the specific origin
            allow_credentials_value = 'true' # Credentials can be true for specific origins
            logging.info(f"CORS Policy Check: Specific origin {origin} allowed.")
        else:
             logging.info(f"CORS Policy Check: Origin '{origin}' is not in allowed list: {allowed_origins}")
             # Keep origin_to_send_in_header = None

        # If request origin is allowed (either specific or via wildcard)
        if origin_to_send_in_header:
            cors_headers = {
                'Access-Control-Allow-Origin': origin_to_send_in_header,
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type', # Add others if client sends them
                'Access-Control-Allow-Credentials': allow_credentials_value,
                'Access-Control-Max-Age': '86400'
            }
            logging.info(f"Preflight OK. Sending 204 with headers: {cors_headers}")
            return make_response('', 204, cors_headers)
        else:
            # Origin not allowed by ALLOWED_ORIGINS list or missing Origin header
            logging.warning(f"Preflight origin '{origin}' denied by policy.")
            return make_response('Origin not permitted for CORS preflight', 403)
    # If it's not this specific OPTIONS request, continue normally

# Root Route - Also uses manual CORS handling now
@app.route('/')
# REMOVE @cross_origin()
def hello_world():
    origin = request.headers.get('Origin')
    allowed_origins = get_allowed_origins_config()
    response_text = 'Hello world!'
    resp = make_response(response_text)

    origin_to_send = None
    allow_credentials = 'false'

    if '*' in allowed_origins:
         origin_to_send = '*'
    elif origin and origin in allowed_origins:
         origin_to_send = origin
         allow_credentials = 'true'

    # Only add CORS headers if origin was allowed by the policy
    if origin_to_send:
        resp.headers['Access-Control-Allow-Origin'] = origin_to_send
        resp.headers['Vary'] = 'Origin'
        resp.headers['Access-Control-Allow-Credentials'] = allow_credentials
    return resp

# Chatgolem Route - Handles POST, adds manual CORS headers to response
@app.route('/chatgolem', methods=['POST']) # Only POST needed now
# REMOVE @cross_origin decorator
def chatgolem():
    # --- Check Origin header for the actual POST request ---
    origin = request.headers.get('Origin')
    allowed_origins = get_allowed_origins_config() # Gets list or ['*']

    origin_to_send = None
    allow_credentials = 'false'
    is_request_allowed = False

    # Determine if request is allowed based on origin and config
    if '*' in allowed_origins:
        origin_to_send = '*' # Origin value for response header
        is_request_allowed = True
        # Credentials MUST be false for wildcard origin
    elif origin and origin in allowed_origins:
        origin_to_send = origin # Reflect specific origin in response header
        is_request_allowed = True
        allow_credentials = 'true' # Credentials can be true for specific origin

    # Deny if origin not allowed by configuration EARLY
    if not is_request_allowed:
        logging.warning(f"POST request from disallowed/missing origin: {origin}. Allowed config: {allowed_origins}. Denying with 403.")
        # Don't add CORS headers for forbidden response
        return jsonify({'error': 'Forbidden', 'message': 'Origin not permitted.'}), 403

    # --- Origin is allowed, proceed with function logic ---
    logging.info(f"------ Entered chatgolem function with method: {request.method} from allowed origin: {origin} ------")
    post_data = request.data
    logging.info(f"Handling POST request. Received {len(post_data)} bytes.")

    response_data = {}
    status_code = 500 # Default to internal error

    # --- Start Original POST Logic (Try...Except block) ---
    try:
        body = json.loads(post_data.decode('utf-8'))
        openai_api_key = os.getenv('openai_api_key')

        # Optional: Keep diagnostic logging for API Key
        if isinstance(openai_api_key, str) and len(openai_api_key) > 7:
             logging.info(f"DIAGNOSTIC: API Key Check: Found key, Type={type(openai_api_key)}, Length={len(openai_api_key)}, Start='{openai_api_key[:3]}...', End='...{openai_api_key[-4:]}'")
        elif not openai_api_key:
             logging.error("CRITICAL DIAGNOSTIC: os.getenv('openai_api_key') returned None or empty!")

        if not openai_api_key:
            logging.error('CRITICAL: OpenAI API key check failed.')
            response_data = {'error': 'OpenAI API key not found'}
            status_code = 500
        else:
            model = body.get('model', 'gpt-3.5-turbo')
            messages = body.get('messages', [])
            if not messages:
                 logging.warning("Received empty 'messages' list.")
                 response_data = {'error': 'Invalid input', 'message': 'Messages list cannot be empty.'}
                 status_code = 400
            else:
                # ---- OpenAI Call Logic ----
                openai_url = 'https://api.openai.com/v1/chat/completions'
                headers = { 'Content-Type': 'application/json', 'Authorization': f'Bearer {openai_api_key}' }
                data_payload = {'model': model, 'messages': messages}
                logging.info(f"Attempting requests.post to OpenAI API (model: {model})...")
                response_openai = requests.post(openai_url, headers=headers, json=data_payload, timeout=30) # Keep timeout
                openai_status = response_openai.status_code
                openai_response_text = response_openai.text

                if openai_status == 200:
                    logging.info("OpenAI call successful (Status 200).")
                    resp_json = response_openai.json()
                    if resp_json.get('choices') and len(resp_json['choices']) > 0 and resp_json['choices'][0].get('message') and 'content' in resp_json['choices'][0]['message']:
                         generated_text = resp_json['choices'][0]['message']['content']
                         response_data = {'generated_text': generated_text}
                         status_code = 200
                    else:
                         logging.error(f"OpenAI response format unexpected: {resp_json}")
                         response_data = {'error': 'INTERNAL_SERVER_ERROR', 'message': 'Invalid response format from AI.'}
                         status_code = 500
                else:
                    logging.error(f"DIAGNOSTIC: OpenAI API returned non-200 status: {openai_status}")
                    logging.error(f"DIAGNOSTIC: OpenAI Response Body: {openai_response_text}")
                    response_data = {'error': f'Failed OpenAI Call ({openai_status})', 'details': openai_response_text}
                    status_code = openai_status # Return actual error code
                # ---- End OpenAI Call Logic ----

    # Handle exceptions during POST processing
    except requests.exceptions.Timeout:
        logging.warning("Request to OpenAI timed out.")
        response_data = {'error': 'OPENAI_TIMEOUT', 'message': 'The request to the AI service timed out.'}
        status_code = 504
    except requests.exceptions.RequestException as e:
        logging.exception("Network error during OpenAI call.")
        response_data = {'error': 'NETWORK_ERROR', 'message': 'Could not connect to OpenAI.'}
        status_code = 503
    except Exception as e:
        logging.exception("Unexpected error during POST processing.")
        response_data = {'error': 'INTERNAL_SERVER_ERROR', 'message': f'Error processing request: {e}'}
        status_code = 500
    # --- End POST Logic (Try...Except block) ---


    # --- Create Flask response and ADD manual CORS headers ---
    response = make_response(jsonify(response_data), status_code)
    # Use the origin determined by the policy check (specific or '*')
    response.headers['Access-Control-Allow-Origin'] = origin_to_send
    response.headers['Vary'] = 'Origin' # Important for caching
    response.headers['Access-Control-Allow-Credentials'] = allow_credentials
    return response

# Main block (no changes)
if __name__ == '__main__':
    app.run(debug=True)