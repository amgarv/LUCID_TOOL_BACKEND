# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, make_response # Keep make_response
# No Flask-CORS needed
import json
import os
import requests
# REMOVED import logging

app = Flask(__name__)
# REMOVED CORS(app)

# REMOVED logging.basicConfig(...)

# Helper function to get allowed origins list OR the wildcard default
def get_allowed_origins_config():
    origins_str = os.getenv('ALLOWED_ORIGINS')
    # <<< REPLACED logging with print >>>
    print(f"DEBUG ENV VAR: Raw value from os.getenv('ALLOWED_ORIGINS'): '{origins_str}'")
    if not origins_str:
        print("WARNING: ALLOWED_ORIGINS environment variable not set or empty. Defaulting CORS policy to allow all origins ('*').") # Replaced logging.warning
        return ['*'] # Default to Wildcard list
    # Parse comma-separated list
    allowed_list = [origin.strip() for origin in origins_str.split(',') if origin.strip()]
    # <<< REPLACED logging with print >>>
    print(f"DEBUG ENV VAR: Parsed list of allowed origins: {allowed_list}")
    return allowed_list

# Manual OPTIONS Preflight Handler using Environment Variable or Default
@app.before_request
def handle_preflight():
    # Handle OPTIONS requests for the specific chat endpoint
    if request.method.upper() == 'OPTIONS' and request.path == '/chatgolem':
        print(f"INFO: Intercepting OPTIONS request for {request.path}") # Replaced logging.info
        origin = request.headers.get('Origin')
        allowed_origins = get_allowed_origins_config() # Reads env var, includes DEBUG prints inside

        # <<< REPLACED logging with print >>>
        print(f"DEBUG PREFLIGHT: Received Origin header: '{origin}'")
        print(f"DEBUG PREFLIGHT: Checking Origin against Allowed list: {allowed_origins}")

        origin_to_send_in_header = None
        allow_credentials_value = 'false'
        policy_applied = "Denied" # Default log message

        # Determine appropriate CORS headers based on config and request origin
        if '*' in allowed_origins: # Check if wildcard is the policy
            origin_to_send_in_header = '*'
            allow_credentials_value = 'false'
            policy_applied = "Allowed Wildcard (*)"
            # <<< REPLACED logging with print >>>
            print("DEBUG PREFLIGHT: Wildcard check PASSED.")
        elif origin and origin in allowed_origins: # Check if specific origin is allowed
            origin_to_send_in_header = origin # Reflect the specific origin
            allow_credentials_value = 'true'
            policy_applied = f"Allowed Specific Origin ({origin})"
            # <<< REPLACED logging with print >>>
            print(f"DEBUG PREFLIGHT: Specific origin check PASSED for '{origin}'.")
        else:
             # Neither wildcard nor specific match
            # <<< REPLACED logging with print >>>
            print(f"DEBUG PREFLIGHT: Origin '{origin}' check FAILED against list {allowed_origins}.")
            policy_applied = f"Denied Origin ({origin})"

        # <<< REPLACED logging with print >>>
        print(f"DEBUG PREFLIGHT: Final policy decision: {policy_applied}")

        # If request origin is allowed (either specific or via wildcard)
        if origin_to_send_in_header:
            cors_headers = {
                'Access-Control-Allow-Origin': origin_to_send_in_header,
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Credentials': allow_credentials_value,
                'Access-Control-Max-Age': '86400'
            }
            print(f"INFO: Preflight OK. Sending 204 with headers: {cors_headers}") # Replaced logging.info
            return make_response('', 204, cors_headers)
        else:
            # Origin not allowed
            print(f"WARNING: Preflight origin '{origin}' denied by policy.") # Replaced logging.warning
            return make_response('Origin not permitted for CORS preflight', 403)
    # If it's not this specific OPTIONS request, continue normally

# Root Route - Also uses manual CORS handling now
@app.route('/')
def hello_world():
    # Added basic print for visibility
    print("INFO: Root route '/' accessed.")
    origin = request.headers.get('Origin')
    allowed_origins = get_allowed_origins_config() # Includes DEBUG prints inside
    response_text = 'Hello world!'
    resp = make_response(response_text)

    origin_to_send = None
    allow_credentials = 'false'

    if '*' in allowed_origins:
         origin_to_send = '*'
    elif origin and origin in allowed_origins:
         origin_to_send = origin
         allow_credentials = 'true'

    if origin_to_send:
        resp.headers['Access-Control-Allow-Origin'] = origin_to_send
        resp.headers['Vary'] = 'Origin'
        resp.headers['Access-Control-Allow-Credentials'] = allow_credentials
    return resp

# Chatgolem Route - Handles POST, adds manual CORS headers to response
@app.route('/chatgolem', methods=['POST']) # Only POST needed now
def chatgolem():
    # --- Check Origin header for the actual POST request ---
    origin = request.headers.get('Origin')
    allowed_origins = get_allowed_origins_config() # Includes DEBUG prints inside

    # <<< REPLACED logging with print >>>
    print(f"DEBUG POST: Received Origin header: '{origin}'")
    print(f"DEBUG POST: Checking against Allowed list: {allowed_origins}")

    origin_to_send = None
    allow_credentials = 'false'
    is_request_allowed = False
    policy_applied = "Denied" # Default log message

    # <<< REPLACED logging with print >>>
    # Determine if request is allowed based on origin and config
    if '*' in allowed_origins:
        origin_to_send = '*'
        is_request_allowed = True
        policy_applied = "Allowed Wildcard (*)"
        print("DEBUG POST: Wildcard check PASSED.")
    elif origin and origin in allowed_origins:
        origin_to_send = origin
        is_request_allowed = True
        allow_credentials = 'true'
        policy_applied = f"Allowed Specific Origin ({origin})"
        print(f"DEBUG POST: Specific origin check PASSED for '{origin}'.")
    else:
        # Neither wildcard nor specific match
        print(f"DEBUG POST: Origin '{origin}' check FAILED against list {allowed_origins}.")
        policy_applied = f"Denied Origin ({origin})"

    # <<< REPLACED logging with print >>>
    print(f"DEBUG POST: Final policy decision: {policy_applied}")

    # Deny if origin not allowed by configuration EARLY
    if not is_request_allowed:
        print(f"WARNING: POST request from disallowed/missing origin: {origin}. Denying with 403.") # Replaced logging.warning
        return jsonify({'error': 'Forbidden', 'message': 'Origin not permitted.'}), 403

    # --- Origin is allowed, proceed ---
    print(f"INFO: ------ Entered chatgolem function with method: {request.method} from allowed origin: {origin} ------") # Replaced logging.info
    post_data = request.data
    print(f"INFO: Handling POST request. Received {len(post_data)} bytes.") # Replaced logging.info

    response_data = {}
    status_code = 500 # Default to internal error

    # --- Start Original POST Logic (Try...Except block) ---
    try:
        body = json.loads(post_data.decode('utf-8'))
        openai_api_key = os.getenv('openai_api_key')

        # Keep DIAGNOSTIC checks using print
        if isinstance(openai_api_key, str) and len(openai_api_key) > 7:
            print(f"DIAGNOSTIC: API Key Check: Found key, Type={type(openai_api_key)}, Length={len(openai_api_key)}, Start='{openai_api_key[:3]}...', End='...{openai_api_key[-4:]}'") # Replaced logging.info
        elif not openai_api_key:
            print("CRITICAL DIAGNOSTIC: os.getenv('openai_api_key') returned None or empty!") # Replaced logging.error

        if not openai_api_key:
            print('CRITICAL: OpenAI API key check failed.') # Replaced logging.error
            response_data = {'error': 'OpenAI API key not found'}
            status_code = 500
        else:
            model = body.get('model', 'gpt-3.5-turbo')
            messages = body.get('messages', [])
            if not messages:
                 print("WARNING: Received empty 'messages' list.") # Replaced logging.warning
                 response_data = {'error': 'Invalid input', 'message': 'Messages list cannot be empty.'}
                 status_code = 400
            else:
                # ---- Parameter Handling Logic ----
                # Get temperature from frontend payload, default to 1.0 if not provided/invalid
                temp_from_frontend = body.get('temperature')
                used_temperature = 1.0 # Default
                if temp_from_frontend is not None:
                    try:
                        # Attempt conversion, keep default if invalid format
                        parsed_temp = float(temp_from_frontend)
                        # Basic validation for typical range (optional but good practice)
                        if 0.0 <= parsed_temp <= 2.0:
                            used_temperature = parsed_temp
                            print(f"INFO: Using temperature provided by frontend: {used_temperature}") # Replaced logging.info
                        else:
                            print(f"WARNING: Temperature value '{parsed_temp}' out of typical range (0.0-2.0), using default: {used_temperature}") # Replaced logging.warning
                    except (ValueError, TypeError):
                        print(f"WARNING: Invalid temperature format received ('{temp_from_frontend}'), using default: {used_temperature}") # Replaced logging.warning
                else:
                    print(f"INFO: No temperature provided by frontend, using default: {used_temperature}") # Replaced logging.info


                # Get seed from frontend payload, keep as None if not provided/invalid
                seed_from_frontend = body.get('seed')
                used_seed = None # Default
                if seed_from_frontend is not None:
                    try:
                        # Attempt conversion, keep default (None) if invalid format
                        parsed_seed = int(seed_from_frontend)
                        used_seed = parsed_seed
                        print(f"INFO: Using seed provided by frontend: {used_seed}") # Replaced logging.info
                    except (ValueError, TypeError):
                        print(f"WARNING: Invalid seed format received ('{seed_from_frontend}'), using default (None)") # Replaced logging.warning
                else:
                    print(f"INFO: No seed provided by frontend.") # Replaced logging.info
                # ---- End Parameter Handling Logic ----
                # ---- OpenAI Call Logic ----
                openai_url = 'https://api.openai.com/v1/chat/completions'
                headers = { 'Content-Type': 'application/json', 'Authorization': f'Bearer {openai_api_key}' }
                # ** MODIFIED: Prepare payload with new parameters **
                data_payload = {
                    'model': model,
                    'messages': messages,
                    'temperature': used_temperature # Always include temperature now
                }
                if used_seed is not None:
                    data_payload['seed'] = used_seed # Conditionally include seed if it was provided
                print(f"INFO: Attempting requests.post to OpenAI API (model: {model})...") # Replaced logging.info
                response_openai = requests.post(openai_url, headers=headers, json=data_payload, timeout=30) # Keep timeout
                openai_status = response_openai.status_code
                openai_response_text = response_openai.text

                if openai_status == 200:
                    print("INFO: OpenAI call successful (Status 200).") # Replaced logging.info
                    resp_json = response_openai.json()
                    if resp_json.get('choices') and len(resp_json['choices']) > 0 and resp_json['choices'][0].get('message') and 'content' in resp_json['choices'][0]['message']:
                         generated_text = resp_json['choices'][0]['message']['content']
                         # ** MODIFIED: Prepare response payload including used parameters **
                         response_data = {
                             'generated_text': generated_text,
                             'used_temperature': used_temperature # Always include the temperature used
                         }
                         if used_seed is not None:
                             # You could potentially try to get seed from resp_json if OpenAI returns it reliably,
                             # but for now, we return the seed we intended to use.
                             response_data['used_seed'] = used_seed # Include seed only if one was sent

                         status_code = 200
                    else:
                         print(f"ERROR: OpenAI response format unexpected: {resp_json}") # Replaced logging.error
                         response_data = {'error': 'INTERNAL_SERVER_ERROR', 'message': 'Invalid response format from AI.'}
                         status_code = 500
                else:
                    print(f"ERROR DIAGNOSTIC: OpenAI API returned non-200 status: {openai_status}") # Replaced logging.error
                    print(f"ERROR DIAGNOSTIC: OpenAI Response Body: {openai_response_text}") # Replaced logging.error
                    response_data = {'error': f'Failed OpenAI Call ({openai_status})', 'details': openai_response_text}
                    status_code = openai_status
                # ---- End OpenAI Call Logic ----

    # Handle exceptions during POST processing using print
    except requests.exceptions.Timeout:
        print("WARNING: Request to OpenAI timed out.") # Replaced logging.warning
        response_data = {'error': 'OPENAI_TIMEOUT', 'message': 'The request to the AI service timed out.'}
        status_code = 504
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error during OpenAI call: {e}") # Replaced logging.exception
        response_data = {'error': 'NETWORK_ERROR', 'message': 'Could not connect to OpenAI.'}
        status_code = 503
    except Exception as e:
        print(f"ERROR: Unexpected error during POST processing: {e}") # Replaced logging.exception
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