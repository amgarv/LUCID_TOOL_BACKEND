# -*- coding: utf-8 -*-
"""
Flask backend server for the LUCID Qualtrics chat interface.

Acts as a proxy between the Qualtrics frontend JavaScript and the OpenAI API.
Handles CORS, fetches configuration from environment variables, makes API calls,
and returns responses. Includes a root endpoint to display deployment status
and the necessary Qualtrics URL.
"""
from flask import Flask, request, jsonify, make_response
import json
import os      # Used for accessing environment variables (API keys, config)
import requests # Used for making HTTP requests to the OpenAI API

# Initialize the Flask application
app = Flask(__name__)

# --- Configuration & CORS ---

def get_allowed_origins_config():
    """
    Reads the ALLOWED_ORIGINS environment variable and parses it into a list.
    Defaults to allowing all origins ('*') if the variable is not set.
    Uses print for logging and visible in Vercel Function Logs.
    """
    origins_str = os.getenv('ALLOWED_ORIGINS')
    print(f"[DEBUG ENV] Raw ALLOWED_ORIGINS: '{origins_str}'") # Vercel Log

    if not origins_str:
        # Default to wildcard if environment variable is missing or empty
        print("[WARN ENV] ALLOWED_ORIGINS not set. Defaulting CORS to allow all ('*').") # Vercel Log
        return ['*']

    # Parse comma-separated list, removing empty strings and stripping whitespace
    allowed_list = [origin.strip() for origin in origins_str.split(',') if origin.strip()]
    print(f"[DEBUG ENV] Parsed ALLOWED_ORIGINS: {allowed_list}") # Vercel Log
    return allowed_list

@app.before_request
def handle_preflight():
    """
    Handles CORS preflight (OPTIONS) requests specifically for the /lucid endpoint.
    Checks the request's Origin header against the ALLOWED_ORIGINS config
    and returns appropriate CORS headers if allowed, or a 403 if denied.
    """
    # Intercept only OPTIONS requests targetting the main API endpoint
    if request.method.upper() == 'OPTIONS' and request.path == '/lucid':
        print(f"[INFO] Intercepting OPTIONS request for {request.path}") # Vercel Log
        origin = request.headers.get('Origin') # Get the origin of the requesting domain
        allowed_origins = get_allowed_origins_config() # Fetch the configured allowed origins

        print(f"[DEBUG PREFLIGHT] Request Origin: '{origin}'") # Vercel Log
        print(f"[DEBUG PREFLIGHT] Checking against Allowed: {allowed_origins}") # Vercel Log

        origin_to_send_in_header = None # The value for Access-Control-Allow-Origin
        allow_credentials_value = 'false' # Whether credentials (cookies) are allowed
        policy_applied = "Denied" # For logging

        # Determine CORS policy based on configuration
        if '*' in allowed_origins:
            # Allow any origin (wildcard)
            origin_to_send_in_header = '*'
            allow_credentials_value = 'false' # Credentials cannot be used with wildcard origin
            policy_applied = "Allowed Wildcard (*)"
            print("[DEBUG PREFLIGHT] Policy: Allowed Wildcard (*)") # Vercel Log
        elif origin and origin in allowed_origins:
            # Allow specific origin from the list
            origin_to_send_in_header = origin # Reflect the requesting origin
            allow_credentials_value = 'true'  # Allow credentials for specific origins
            policy_applied = f"Allowed Specific Origin ({origin})"
            print(f"[DEBUG PREFLIGHT] Policy: Allowed Specific Origin ({origin})") # Vercel Log
        else:
            # Origin not allowed by configuration
            print(f"[DEBUG PREFLIGHT] Policy: Denied Origin ({origin})") # Vercel Log

        print(f"[DEBUG PREFLIGHT] Final policy decision: {policy_applied}") # Vercel Log

        # Construct and return the preflight response
        if origin_to_send_in_header:
            # If allowed, send 204 No Content with appropriate CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': origin_to_send_in_header,
                'Access-Control-Allow-Methods': 'POST, OPTIONS', # Allowed methods for the actual request
                'Access-Control-Allow-Headers': 'Content-Type',   # Allowed headers for the actual request
                'Access-Control-Allow-Credentials': allow_credentials_value,
                'Access-Control-Max-Age': '86400' # Cache preflight response for 1 day
            }
            print(f"[INFO] Preflight OK for /lucid. Sending 204 with headers: {cors_headers}") # Vercel Log
            return make_response('', 204, cors_headers)
        else:
            # If denied, send 403 Forbidden
            print(f"[WARN] Preflight origin '{origin}' denied by policy for /lucid.") # Vercel Log
            return make_response('Origin not permitted for CORS preflight', 403)

    # If not an OPTIONS request for /lucid, proceed to the actual route function
    pass

# --- Application Routes ---

@app.route('/')
def hello_world():
    """
    Root endpoint (/). Primarily serves as a status check and provides a helpful
    HTML page displaying the correct URL needed for the Qualtrics setup,
    if deployed on Vercel (detects via VERCEL_URL env var).
    Also handles basic CORS headers for GET requests to the root.
    """
    print("[INFO] Root route '/' accessed.") # Vercel Log
    origin = request.headers.get('Origin')
    allowed_origins = get_allowed_origins_config()

    # Attempt to get the Vercel deployment URL from environment variables
    deployment_url = os.getenv('VERCEL_URL')
    display_html = "" # Initialize HTML content

    if deployment_url:
        # If running on Vercel, construct the help page
        # Ensure protocol is included and append the correct endpoint path
        qualtrics_url = f"https://{deployment_url}/lucid" if not deployment_url.startswith("http") else f"{deployment_url}/lucid"

        # Simple HTML page with instructions and a copy button
        display_html = f"""
        <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>LUCID Backend Deployed</title>
        <style>body {{ font-family: system-ui, sans-serif; padding: 20px; line-height: 1.6; background-color: #fafafa; color: #333; }}.container {{ max-width: 700px; margin: 40px auto; padding: 30px; border: 1px solid #eaeaea; border-radius: 8px; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}h1 {{ color: #0070f3; }}code {{ background-color: #f0f0f0; padding: 0.2em 0.4em; border-radius: 3px; font-family: monospace;}}.url-box {{ background-color: #f3f3f3; padding: 10px 15px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; word-wrap: break-word; margin-bottom: 15px; font-size: 1.1em;}}button {{ padding: 10px 18px; cursor: pointer; border-radius: 5px; border: none; background-color: #0070f3; color: white; font-size: 15px; }}button:hover {{ background-color: #0056b3; }}.copied-message {{ color: green; font-weight: bold; display: none; margin-left: 10px;}}</style>
        </head><body><div class="container"><h1>LUCID Backend Successfully Deployed!</h1><p>To use this backend with your Qualtrics survey:</p><ol><li><strong>Copy the full URL below.</strong></li><li>In your Qualtrics Survey Flow, set the Embedded Data field named <code>LUCIDBackendURL</code> to this value.</li></ol><p><strong>Qualtrics URL (Value for <code>LUCIDBackendURL</code>):</strong></p><div id="qualtricsUrlBox" class="url-box">{qualtrics_url}</div><button onclick="copyUrl()">Copy URL</button><span id="copiedMsg" class="copied-message">Copied!</span></div>
        <script>function copyUrl() {{ const urlText = document.getElementById('qualtricsUrlBox').innerText; navigator.clipboard.writeText(urlText).then(() => {{ const msg = document.getElementById('copiedMsg'); msg.style.display = 'inline'; setTimeout(() => {{ msg.style.display = 'none'; }}, 2500); }}).catch(err => {{ console.error('Failed to copy: ', err); alert('Failed to copy URL.'); }}); }}</script>
        </body></html>"""
    else:
        # Fallback HTML if not running on Vercel (e.g., local development)
        display_html = """<!DOCTYPE html><html lang="en"><head><title>LUCID Backend</title><style>body{font-family: sans-serif; padding: 20px;}</style></head><body><h1>LUCID Backend Running</h1><p>This is the backend server for the LUCID Qualtrics tool.</p><p><em>(Could not detect Vercel deployment URL. Append /lucid to your deployment URL for Qualtrics.)</em></p></body></html>"""

    # Create Flask response object with the HTML
    resp = make_response(display_html)
    resp.headers['Content-Type'] = 'text/html' # Set correct MIME type

    # Apply basic CORS headers for the root route as well
    origin_to_send = None
    allow_credentials = 'false'
    if '*' in allowed_origins:
        origin_to_send = '*'
    elif origin and origin in allowed_origins:
        origin_to_send = origin
        allow_credentials = 'true' # Credentials generally not needed for root, but consistent
    if origin_to_send:
        resp.headers['Access-Control-Allow-Origin'] = origin_to_send
        resp.headers['Vary'] = 'Origin'
        resp.headers['Access-Control-Allow-Credentials'] = allow_credentials
    return resp

@app.route('/lucid', methods=['POST'])
def lucid():
    """
    Main API endpoint (/lucid).
    Receives chat messages and configuration from Qualtrics frontend via POST request.
    Validates request origin using CORS settings.
    Calls the OpenAI Chat Completions API.
    Returns the AI's response or an error message in JSON format.
    Includes necessary CORS headers on the response.
    """
    # --- Step 1: CORS Check for POST request ---
    origin = request.headers.get('Origin')
    allowed_origins = get_allowed_origins_config()
    print(f"[DEBUG POST /lucid] Request Origin: '{origin}' vs Allowed: {allowed_origins}") # Vercel Log

    origin_to_send = None # Header value for Access-Control-Allow-Origin
    allow_credentials = 'false' # Header value for Access-Control-Allow-Credentials
    is_request_allowed = False # Flag to track if request passes CORS check

    # Determine if the request origin is permitted
    if '*' in allowed_origins:
        origin_to_send = '*'
        is_request_allowed = True
        allow_credentials = 'false'
        print("[DEBUG POST /lucid] Policy: Allowed Wildcard (*)") # Vercel Log
    elif origin and origin in allowed_origins:
        origin_to_send = origin
        is_request_allowed = True
        allow_credentials = 'true'
        print(f"[DEBUG POST /lucid] Policy: Allowed Specific Origin ({origin})") # Vercel Log
    else:
        # Origin is not in the allowed list (and not wildcard)
        is_request_allowed = False
        print(f"[DEBUG POST /lucid] Policy: Denied Origin ({origin})") # Vercel Log

    # If CORS check fails, return 403 Forbidden immediately
    if not is_request_allowed:
        print(f"[WARN] POST to /lucid denied for origin: {origin}.") # Vercel Log
        error_resp = make_response(jsonify({'error': 'Forbidden', 'message': 'Origin not permitted.'}), 403)
        # Add CORS headers even on error where possible, though browser might ignore on 403
        if origin_to_send:
             error_resp.headers['Access-Control-Allow-Origin'] = origin_to_send
             error_resp.headers['Vary'] = 'Origin'
             error_resp.headers['Access-Control-Allow-Credentials'] = allow_credentials
        return error_resp
    # --- End CORS Check ---

    # --- Step 2: Process Request Body ---
    print(f"[INFO] ------ Entered lucid function from allowed origin: {origin} ------") # Vercel Log
    post_data = request.data # Get raw request body
    print(f"[INFO /lucid] Received {len(post_data)} bytes.") # Vercel Log

    response_data = {} # Dictionary to hold the JSON response data
    status_code = 500  # Default to Internal Server Error

    try:
        # Decode body as UTF-8 and parse JSON
        body = json.loads(post_data.decode('utf-8'))

        # Retrieve OpenAI API key from environment variables
        openai_api_key = os.getenv('openai_api_key')

        # Basic check/log for the API key (without exposing the key itself)
        if isinstance(openai_api_key, str) and len(openai_api_key) > 7:
            print(f"[DIAGNOSTIC /lucid] API Key Found (Length: {len(openai_api_key)}).") # Vercel Log
        elif not openai_api_key:
            print("[CRITICAL DIAGNOSTIC /lucid] os.getenv('openai_api_key') returned None or empty!") # Vercel Log

        # --- Step 3: Check for API Key ---
        if not openai_api_key:
            print('[CRITICAL /lucid] OpenAI API key not found in environment variables.') # Vercel Log
            # Set error response if key is missing
            response_data = {'error': 'Configuration Error', 'message':'OpenAI API key not configured on server.'}
            status_code = 500 # Indicate server configuration error
        else:
            # API Key found, proceed to extract data and call OpenAI

            # Extract parameters sent from Qualtrics frontend
            model = body.get('model', 'gpt-4o') # Use model from request, default to gpt-4o if not sent (JS usually sends its default)
            messages = body.get('messages', []) # Get message history array
            temp_from_frontend = body.get('temperature') # Get optional temperature
            seed_from_frontend = body.get('seed') # Get optional seed

            # Validate messages list (must not be empty)
            if not messages or not isinstance(messages, list):
                print("[WARN /lucid] Invalid or empty 'messages' list received.") # Vercel Log
                response_data = {'error': 'Bad Request', 'message': 'Messages list is missing, empty, or invalid.'}
                status_code = 400 # Bad Request
            else:
                # Process temperature (use value from frontend if valid, otherwise default to 1.0)
                used_temperature = 1.0 # Default temperature
                if temp_from_frontend is not None:
                    try:
                        parsed_temp = float(temp_from_frontend)
                        if 0.0 <= parsed_temp <= 2.0: used_temperature = parsed_temp
                        else: print(f"[WARN /lucid] Temp '{parsed_temp}' out of range, using default.") # Vercel Log
                    except (ValueError, TypeError): print(f"[WARN /lucid] Invalid temp format ('{temp_from_frontend}'), using default.") # Vercel Log
                print(f"[INFO /lucid] Using temperature: {used_temperature}") # Vercel Log

                # Process seed (use value from frontend if valid, otherwise default to None)
                used_seed = None # Default: OpenAI handles randomness
                if seed_from_frontend is not None:
                    try: used_seed = int(seed_from_frontend)
                    except (ValueError, TypeError): print(f"[WARN /lucid] Invalid seed format ('{seed_from_frontend}'), using default (None).") # Vercel Log
                print(f"[INFO /lucid] Using seed: {used_seed}") # Vercel Log

                # --- Step 4: Call OpenAI API ---
                openai_url = 'https://api.openai.com/v1/chat/completions'
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {openai_api_key}' # Use API key for authorization
                }
                # Construct payload for OpenAI
                data_payload = {
                    'model': model,
                    'messages': messages,
                    'temperature': used_temperature
                }
                # Only include seed if one was provided and valid
                if used_seed is not None:
                    data_payload['seed'] = used_seed

                print(f"[INFO /lucid] Calling OpenAI API (model: {model}). Payload keys: {list(data_payload.keys())}") # Vercel Log

                # Make the POST request to OpenAI with a timeout
                response_openai = requests.post(openai_url, headers=headers, json=data_payload, timeout=30)
                openai_status = response_openai.status_code
                openai_response_text = response_openai.text # Get raw text for potential error logging
                print(f"[INFO /lucid] OpenAI response status: {openai_status}") # Vercel Log

                # --- Step 5: Process OpenAI Response ---
                if openai_status == 200:
                    # Successful call
                    print("[INFO /lucid] Successfully processed OpenAI response.") # Vercel Log
                    try:
                        # Parse the JSON response from OpenAI
                        resp_json = response_openai.json()
                        # Extract the generated text content safely
                        generated_text = resp_json['choices'][0]['message']['content']

                        # Prepare the successful response data for Qualtrics frontend
                        response_data = {
                            'generated_text': generated_text,
                            'used_temperature': used_temperature # Echo back parameters used
                        }
                        if used_seed is not None:
                            response_data['used_seed'] = used_seed # Echo back seed if used

                        status_code = 200 # OK
                    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
                        # Handle cases where OpenAI gives 200 but response format is unexpected
                        print(f"[ERROR /lucid] OpenAI response format unexpected (Status 200): {openai_response_text} - Error: {e}") # Vercel Log
                        response_data = {'error': 'Internal Server Error', 'message': 'Invalid response format from AI service.'}
                        status_code = 500
                else:
                    # Handle error responses from OpenAI (non-200 status)
                    print(f"[ERROR DIAGNOSTIC /lucid] OpenAI API Error ({openai_status}): {openai_response_text}") # Vercel Log
                    # Try to extract a cleaner error message from OpenAI's response JSON
                    error_details = openai_response_text
                    try:
                       error_json = response_openai.json()
                       if 'error' in error_json and 'message' in error_json['error']:
                           error_details = error_json['error']['message']
                    except json.JSONDecodeError:
                        pass # Use raw text if parsing fails
                    response_data = {'error': f'AI Service Error ({openai_status})', 'message': error_details}
                    # Use OpenAI's status code if it's a standard error, otherwise default to 500
                    status_code = openai_status if openai_status < 600 else 500

    # --- Step 6: Handle Exceptions during Request Processing ---
    except requests.exceptions.Timeout:
        print("[ERROR /lucid] Request to OpenAI timed out.") # Vercel Log
        response_data = {'error': 'Gateway Timeout', 'message': 'Request to AI service timed out.'}
        status_code = 504 # Gateway Timeout
    except requests.exceptions.RequestException as e:
        # Handle network errors connecting to OpenAI
        print(f"[ERROR /lucid] Network error connecting to OpenAI: {e}") # Vercel Log
        response_data = {'error': 'Service Unavailable', 'message': 'Network error connecting to AI service.'}
        status_code = 503 # Service Unavailable
    except json.JSONDecodeError:
        # Handle invalid JSON sent from the frontend
        print(f"[ERROR /lucid] Invalid JSON received from client.") # Vercel Log
        response_data = {'error': 'Bad Request', 'message': 'Invalid JSON format in request body.'}
        status_code = 400 # Bad Request
    except Exception as e:
        # Catch-all for any other unexpected errors
        print(f"[ERROR /lucid] Unexpected server error: {e}") # Vercel Log
        # Consider logging the full traceback here if possible in production
        response_data = {'error': 'Internal Server Error', 'message': f'An unexpected error occurred processing the request.'}
        status_code = 500

    # --- Step 7: Create and Return Final Flask Response ---
    final_response = make_response(jsonify(response_data), status_code)

    # Add required CORS headers to the actual response
    final_response.headers['Access-Control-Allow-Origin'] = origin_to_send
    final_response.headers['Vary'] = 'Origin' # Important for caching proxies
    final_response.headers['Access-Control-Allow-Credentials'] = allow_credentials
    final_response.headers['Content-Type'] = 'application/json' # Ensure correct content type

    print(f"[INFO /lucid] Responding with status code: {status_code}") # Vercel Log
    return final_response

# --- Main Execution Block (for local development) ---
if __name__ == '__main__':
    # This block only runs when the script is executed directly (e.g., `python lucid_api.py`)
    # It's ignored when run by a WSGI server like Vercel's Python runtime.
    print("[INFO] Starting Flask development server...")

    # Optional: Set environment variables locally for testing
    # os.environ['openai_api_key'] = 'YOUR_LOCAL_TEST_KEY_HERE' # Replace with your key for local tests
    # os.environ['ALLOWED_ORIGINS'] = '*' # Example: Allow all for local testing
    # os.environ['VERCEL_URL'] = 'localhost:8080' # Example for testing the root page

    # Run the Flask development server
    # Debug=True enables auto-reloading and provides detailed error pages (DO NOT use in production)
    local_port = int(os.getenv('PORT', 8080)) # Use PORT env var if set, otherwise default to 8080
    app.run(debug=True, port=local_port, host='0.0.0.0') # Host 0.0.0.0 makes it accessible on network