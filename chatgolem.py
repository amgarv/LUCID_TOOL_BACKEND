from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

import json
import os
import requests

app = Flask(__name__)
CORS(app)

@app.route('/')
@cross_origin()
def hello_world():
    return 'Hello, World!'

@app.route('/chatgolem', methods=['POST'])
@cross_origin(origins='*')
def chatgolem():    
    # Read the request body
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
        'model': 'gpt-3.5-turbo',
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