# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, make_response
import json
import os  # <--- Added os import
import requests

app = Flask(__name__)

# Helper function to get allowed origins list OR the wildcard default
def get_allowed_origins_config():
    origins_str = os.getenv('ALLOWED_ORIGINS')
    # <<< Using print for logging as previously established >>>
    print(f"DEBUG ENV VAR: Raw value from os.getenv('ALLOWED_ORIGINS'): '{origins_str}'")
    if not origins_str:
        print("WARNING: ALLOWED_ORIGINS environment variable not set or empty. Defaulting CORS policy to allow all origins ('*').")
        return ['*'] # Default to Wildcard list
    # Parse comma-separated list
    allowed_list = [origin.strip() for origin in origins_str.split(',') if origin.strip()]
    print(f"DEBUG ENV VAR: Parsed list of allowed origins: {allowed_list}")
    return allowed_list

# Manual OPTIONS Preflight Handler using Environment Variable or Default
@app.before_request
def handle_preflight():
    # Handle OPTIONS requests for the specific chat endpoint
    if request.method.upper() == 'OPTIONS' and request.path == '/lucid':
        print(f"INFO: Intercepting OPTIONS request for {request.path}")
        origin = request.headers.get('Origin')
        allowed_origins = get_allowed_origins_config() # Reads env var, includes DEBUG prints inside

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
            print("DEBUG PREFLIGHT: Wildcard check PASSED.")
        elif origin and origin in allowed_origins: # Check if specific origin is allowed
            origin_to_send_in_header = origin # Reflect the specific origin
            allow_credentials_value = 'true'
            policy_applied = f"Allowed Specific Origin ({origin})"
            print(f"DEBUG PREFLIGHT: Specific origin check PASSED for '{origin}'.")
        else:
            # Neither wildcard nor specific match
            print(f"DEBUG PREFLIGHT: Origin '{origin}' check FAILED against list {allowed_origins}.")
            policy_applied = f"Denied Origin ({origin})"

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
            print(f"INFO: Preflight OK. Sending 204 with headers: {cors_headers}")
            return make_response('', 204, cors_headers)
        else:
            # Origin not allowed
            print(f"WARNING: Preflight origin '{origin}' denied by policy.")
            return make_response('Origin not permitted for CORS preflight', 403)
    # If it's not this specific OPTIONS request, continue normally

# --- MODIFIED Root Route ---
# Displays the Qualtrics URL if deployed on Vercel
@app.route('/')
def hello_world():
    print("INFO: Root route '/' accessed.")
    origin = request.headers.get('Origin')
    allowed_origins = get_allowed_origins_config() # Includes DEBUG prints inside

    # --- Get Vercel Deployment URL ---
    deployment_url = os.getenv('VERCEL_URL') # Vercel automatically sets this

    # Construct the Qualtrics URL and display HTML
    if deployment_url:
        # Assuming VERCEL_URL includes https:// based on Vercel docs
        qualtrics_url = f"https://{deployment_url}/lucid" if not deployment_url.startswith("http") else f"{deployment_url}/lucid"

        display_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>LUCID Backend Deployed</title>
            <style>
                body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; padding: 20px; line-height: 1.6; background-color: #fafafa; color: #333; }}
                .container {{ max-width: 700px; margin: 40px auto; padding: 30px; border: 1px solid #eaeaea; border-radius: 8px; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
                h1 {{ color: #0070f3; margin-bottom: 0.5em;}}
                code {{ background-color: #f0f0f0; padding: 0.2em 0.4em; border-radius: 3px; font-family: Menlo, Monaco, Consolas, 'Courier New', monospace;}}
                .url-box {{ background-color: #f3f3f3; padding: 10px 15px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; word-wrap: break-word; margin-bottom: 15px; font-size: 1.1em;}}
                button {{ padding: 10px 18px; cursor: pointer; border-radius: 5px; border: none; background-color: #0070f3; color: white; font-size: 15px; transition: background-color 0.2s ease; }}
                button:hover {{ background-color: #0056b3; }}
                .copied-message {{ color: green; font-weight: bold; display: none; margin-left: 10px;}}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>LUCID Backend Successfully Deployed!</h1>
                <p>To use this backend with your Qualtrics survey:</p>
                <ol>
                    <li><strong>Copy the full URL below.</strong></li>
                    <li>In your Qualtrics survey, go to the <strong>Survey Flow</strong>.</li>
                    <li>Find the Embedded Data element where your <code>LUCID...</code> variables are set.</li>
                    <li>Set the value for the Embedded Data field named <code>LUCIDURL</code> exactly to the copied URL.</li>
                </ol>
                <p><strong>Qualtrics URL (Value for <code>LUCIDURL</code>):</strong></p>
                <div id="qualtricsUrlBox" class="url-box">{qualtrics_url}</div>
                <button onclick="copyUrl()">Copy URL</button>
                <span id="copiedMsg" class="copied-message">Copied!</span>
            </div>
            <script>
                function copyUrl() {{
                    const urlText = document.getElementById('qualtricsUrlBox').innerText;
                    navigator.clipboard.writeText(urlText).then(() => {{
                        const msg = document.getElementById('copiedMsg');
                        msg.style.display = 'inline';
                        setTimeout(() => {{ msg.style.display = 'none'; }}, 2500); // Show "Copied!" for 2.5 seconds
                    }}).catch(err => {{
                        console.error('Failed to copy text: ', err);
                        alert('Failed to copy URL. Please copy it manually.');
                    }});
                }}
            </script>
        </body>
        </html>
        """
    else:
        # Fallback message if VERCEL_URL is not set (e.g., local development)
        display_html = """
        <!DOCTYPE html><html lang="en"><head><title>LUCID Backend</title><style>body{font-family: sans-serif; padding: 20px;}</style></head><body><h1>LUCID Backend Running</h1><p>This is the backend server for the LUCID Qualtrics tool.</p><p><em>(Could not detect Vercel deployment URL. If deployed on Vercel, please check your Vercel project dashboard for the deployment URL and append /lucid to use in Qualtrics.)</em></p></body></html>
        """
    # --- End URL Logic ---

    resp = make_response(display_html) # Serve the generated HTML
    resp.headers['Content-Type'] = 'text/html' # Set content type

    # --- Add CORS Headers (as before) ---
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
# --- End MODIFIED Root Route ---


# lucid Route - Handles POST, adds manual CORS headers to response
@app.route('/lucid', methods=['POST']) # Only POST needed now
def lucid():
    # --- Check Origin header for the actual POST request ---
    origin = request.headers.get('Origin')
    allowed_origins = get_allowed_origins_config() # Includes DEBUG prints inside

    print(f"DEBUG POST: Received Origin header: '{origin}'")
    print(f"DEBUG POST: Checking against Allowed list: {allowed_origins}")

    origin_to_send = None
    allow_credentials = 'false'
    is_request_allowed = False
    policy_applied = "Denied" # Default log message

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

    print(f"DEBUG POST: Final policy decision: {policy_applied}")

    # Deny if origin not allowed by configuration EARLY
    if not is_request_allowed:
        print(f"WARNING: POST request from disallowed/missing origin: {origin}. Denying with 403.")
        # Return CORS headers even on failure for consistency if needed, but 403 usually suffices
        error_resp = make_response(jsonify({'error': 'Forbidden', 'message': 'Origin not permitted.'}), 403)
        if origin_to_send: # Though is_request_allowed is false, origin_to_send might be '*' or a matched origin if logic changes
             error_resp.headers['Access-Control-Allow-Origin'] = origin_to_send # Potentially redundant on 403 but safe
             error_resp.headers['Vary'] = 'Origin'
             error_resp.headers['Access-Control-Allow-Credentials'] = allow_credentials
        return error_resp


    # --- Origin is allowed, proceed ---
    print(f"INFO: ------ Entered lucid function with method: {request.method} from allowed origin: {origin} ------")
    post_data = request.data
    print(f"INFO: Handling POST request. Received {len(post_data)} bytes.")

    response_data = {}
    status_code = 500 # Default to internal error

    # --- Start Original POST Logic (Try...Except block) ---
    try:
        body = json.loads(post_data.decode('utf-8'))
        openai_api_key = os.getenv('openai_api_key')

        # Keep DIAGNOSTIC checks using print
        if isinstance(openai_api_key, str) and len(openai_api_key) > 7:
            print(f"DIAGNOSTIC: API Key Check: Found key, Type={type(openai_api_key)}, Length={len(openai_api_key)}, Start='{openai_api_key[:3]}...', End='...{openai_api_key[-4:]}'")
        elif not openai_api_key:
            print("CRITICAL DIAGNOSTIC: os.getenv('openai_api_key') returned None or empty!")

        if not openai_api_key:
            print('CRITICAL: OpenAI API key check failed.')
            response_data = {'error': 'Configuration Error', 'message':'OpenAI API key not configured on server.'}
            status_code = 500 # Internal server error due to config
        else:
            model = body.get('model', 'gpt-3.5-turbo') # Default model if not provided
            messages = body.get('messages', [])

            # ---- Parameter Handling Logic ----
            temp_from_frontend = body.get('temperature')
            used_temperature = 1.0 # Default temperature
            if temp_from_frontend is not None:
                try:
                    parsed_temp = float(temp_from_frontend)
                    if 0.0 <= parsed_temp <= 2.0: # Typical valid range
                        used_temperature = parsed_temp
                        print(f"INFO: Using temperature provided by frontend: {used_temperature}")
                    else:
                        print(f"WARNING: Temperature value '{parsed_temp}' out of typical range (0.0-2.0), using default: {used_temperature}")
                except (ValueError, TypeError):
                    print(f"WARNING: Invalid temperature format received ('{temp_from_frontend}'), using default: {used_temperature}")
            else:
                print(f"INFO: No temperature provided by frontend, using default: {used_temperature}")


            seed_from_frontend = body.get('seed')
            used_seed = None # Default seed (None means OpenAI default behavior)
            if seed_from_frontend is not None:
                try:
                    parsed_seed = int(seed_from_frontend)
                    used_seed = parsed_seed
                    print(f"INFO: Using seed provided by frontend: {used_seed}")
                except (ValueError, TypeError):
                     print(f"WARNING: Invalid seed format received ('{seed_from_frontend}'), using default (None)")
            else:
                 print(f"INFO: No seed provided by frontend.")
            # ---- End Parameter Handling Logic ----

            if not messages:
                print("WARNING: Received empty 'messages' list.")
                response_data = {'error': 'Bad Request', 'message': 'Messages list cannot be empty.'}
                status_code = 400 # Bad Request
            else:
                # ---- OpenAI Call Logic ----
                openai_url = 'https://api.openai.com/v1/chat/completions'
                headers = { 'Content-Type': 'application/json', 'Authorization': f'Bearer {openai_api_key}' }

                # Prepare payload with processed parameters
                data_payload = {
                    'model': model,
                    'messages': messages,
                    'temperature': used_temperature # Always include temperature
                }
                if used_seed is not None:
                    data_payload['seed'] = used_seed # Conditionally include seed

                print(f"INFO: Attempting requests.post to OpenAI API (model: {model}). Payload keys: {list(data_payload.keys())}")

                # Make the call to OpenAI
                response_openai = requests.post(openai_url, headers=headers, json=data_payload, timeout=30) # 30 second timeout
                openai_status = response_openai.status_code
                openai_response_text = response_openai.text # Get raw text for error logging

                if openai_status == 200:
                    print("INFO: OpenAI call successful (Status 200).")
                    resp_json = response_openai.json() # Parse JSON response

                    # Safely extract the response content
                    try:
                        generated_text = resp_json['choices'][0]['message']['content']

                        # Prepare response payload including used parameters
                        response_data = {
                            'generated_text': generated_text,
                            'used_temperature': used_temperature # Echo back the temp used
                        }
                        if used_seed is not None:
                            # Optional: Could verify seed returned by OpenAI if API changes, for now just echo back what we sent
                            response_data['used_seed'] = used_seed # Echo back seed if we sent one

                        status_code = 200 # OK
                    except (KeyError, IndexError, TypeError) as e:
                         print(f"ERROR: OpenAI response format unexpected: {resp_json} - Error: {e}")
                         response_data = {'error': 'Internal Server Error', 'message': 'Invalid response format from AI.'}
                         status_code = 500 # Internal Server Error

                else: # Handle non-200 responses from OpenAI
                    print(f"ERROR DIAGNOSTIC: OpenAI API returned non-200 status: {openai_status}")
                    print(f"ERROR DIAGNOSTIC: OpenAI Response Body: {openai_response_text}")
                    # Try to parse error details from OpenAI response if possible
                    error_details = openai_response_text
                    try:
                       error_json = response_openai.json()
                       if 'error' in error_json and 'message' in error_json['error']:
                           error_details = error_json['error']['message']
                    except json.JSONDecodeError:
                        pass # Keep raw text if not JSON

                    response_data = {'error': f'AI Service Error ({openai_status})', 'message': error_details}
                    # Try to return a meaningful status code, capping at 599
                    status_code = openai_status if openai_status < 600 else 500
                # ---- End OpenAI Call Logic ----

    # Handle exceptions during POST processing
    except requests.exceptions.Timeout:
        print("ERROR: Request to OpenAI timed out.")
        response_data = {'error': 'Gateway Timeout', 'message': 'The request to the AI service timed out.'}
        status_code = 504 # Gateway Timeout
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error during OpenAI call: {e}")
        response_data = {'error': 'Service Unavailable', 'message': 'Network error connecting to AI service.'}
        status_code = 503 # Service Unavailable
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON received from client.")
        response_data = {'error': 'Bad Request', 'message': 'Invalid JSON format in request body.'}
        status_code = 400 # Bad Request
    except Exception as e:
        print(f"ERROR: Unexpected error during POST processing: {e}")
        response_data = {'error': 'Internal Server Error', 'message': f'An unexpected error occurred: {e}'}
        status_code = 500 # Internal Server Error
    # --- End POST Logic (Try...Except block) ---


    # --- Create Flask response and ADD manual CORS headers ---
    response = make_response(jsonify(response_data), status_code)
    # Use the origin determined by the policy check (specific or '*')
    response.headers['Access-Control-Allow-Origin'] = origin_to_send
    response.headers['Vary'] = 'Origin' # Important for caching
    response.headers['Access-Control-Allow-Credentials'] = allow_credentials
    # Add content type explicitly for JSON response
    response.headers['Content-Type'] = 'application/json'
    return response


# Main block (for local development)
if __name__ == '__main__':
    # Set dummy env vars for local testing if needed
    # os.environ['openai_api_key'] = 'YOUR_LOCAL_TEST_KEY'
    # os.environ['ALLOWED_ORIGINS'] = 'http://localhost:8080,http://127.0.0.1:8080' # Example for local dev
    app.run(debug=True, port=8080) # Example port