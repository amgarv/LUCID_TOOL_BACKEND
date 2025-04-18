# -*- coding: utf-8 -*-
# Imports - REMOVED flask_cors
from flask import Flask, request, jsonify
import json # Keep for potential future use if needed
import os # Keep for potential future use if needed
import requests # Keep for potential future use if needed
import logging

# App Setup
app = Flask(__name__)

# Basic Logging Setup
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Root Route - No CORS
@app.route('/')
def hello_world():
    # Corrected indentation with standard spaces
    return 'Hello world!'

# Chatgolem Route - Drastically Simplified for Debugging Entry
@app.route('/chatgolem', methods=['POST']) # Only POST
# --- NO CORS HANDLING AT ALL ---
def chatgolem():
    # *** Entry log - This is the PRIMARY thing we want to see ***
    logging.info(f"------ Entered chatgolem function with method: {request.method} ------")

    # --- NO OPTIONS block ---

    # --- Handle POST request ---
    # For this specific diagnostic test, immediately log success and return OK.
    # We are ONLY checking if the request *reaches* this point in the Vercel Preview logs.
    # The browser WILL still show a CORS error because no Allow-Origin header is sent.
    logging.info("Simplification Test: Request reached function successfully.")
    return jsonify({'status': 'simplification_test_received_ok'}), 200

    # --- Original POST logic completely commented out/removed for this entry test ---


# --- Validation function stub (no longer called in this simplified version) ---
# def validate_chat_input(data): ...

# Main execution block
if __name__ == '__main__':
    app.run(debug=True)