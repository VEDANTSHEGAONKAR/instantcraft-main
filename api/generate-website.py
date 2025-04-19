from http.server import BaseHTTPRequestHandler
from flask import Response
import os
import json
from google import genai
from google.generativeai import types
from dotenv import load_dotenv
import traceback
import sys

# Enable logging
print("Starting generate-website API handler...")

load_dotenv()

# Debug environment
print(f"Environment variables: GOOGLE_API_KEY exists: {bool(os.getenv('GOOGLE_API_KEY'))}")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Initialize Gemini client
try:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    print("Configuring Gemini API...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    print("Gemini API initialized successfully")
except Exception as e:
    print(f"Error initializing Gemini client: {str(e)}")
    traceback.print_exc()

def handle_request(request_body):
    try:
        print(f"Received request: {json.dumps(request_body)[:100]}...")

        if not request_body:
            return {'error': 'No JSON data received'}, 400

        description = request_body.get('description')
        if not description:
            return {'error': 'No description provided'}, 400
            
        print(f"Processing description: {description[:50]}...")

        # Direct, simplified prompt focused on professional websites with real images
        prompt = f"""
        Create a professional website based on this description: {description}
        
        MOST IMPORTANT:
        1. The website MUST use REAL IMAGES that directly relate to the description
        2. Each image must use a DIFFERENT keyword from the description
        3. Use valid, working image URLs from Unsplash for ALL images
        
        For ANY image in the website, use this EXACT format:
        <img src="https://source.unsplash.com/random/800x600/?[keyword]" alt="[description]">
        
        Replace [keyword] with words FROM THE DESCRIPTION such as:
        - For portfolio: portfolio, design, work, project, creative, etc.
        - For shop: product, store, item, clothing, electronics, etc.
        - For business: office, business, professional, corporate, etc.
        
        DO NOT use placeholder text or broken image URLs.
        Make each image URL UNIQUE and SPECIFIC to the content it represents.
        
        The website must:
        - Be professionally designed and responsive
        - Include appropriate animations/transitions
        - Follow modern web design principles
        - Have complete, working HTML/CSS/JS
        
        Return only code in this format:
        ```html
        [FULL HTML]
        ```
        ```css
        [FULL CSS]
        ```
        ```javascript
        [FULL JS]
        ```
        """

        print("Sending request to Gemini API...")
        try:
            response = model.generate_content(
                contents=prompt,
                generation_config=types.GenerationConfig(
                    temperature=0.6,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=8192,
                )
            )
            print("Received response from Gemini API")
            return {'result': response.text}, 200
        except Exception as api_error:
            print(f"Gemini API error: {str(api_error)}")
            return {'error': f"Gemini API error: {str(api_error)}"}, 500

    except Exception as e:
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(f"Error in handle_request: {error_details}")
        return error_details, 500

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            print(f"Received POST request to {self.path}")
            content_length = int(self.headers['Content-Length'])
            request_body = self.rfile.read(content_length)
            print(f"Request body length: {len(request_body)} bytes")
            
            try:
                data = json.loads(request_body)
            except json.JSONDecodeError as json_error:
                print(f"JSON decode error: {str(json_error)}")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f"Invalid JSON: {str(json_error)}"}).encode())
                return

            response_data, status_code = handle_request(data)
            print(f"API response status: {status_code}")

            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            self.wfile.write(json.dumps(response_data).encode())
        except Exception as e:
            print(f"Unhandled exception in do_POST: {str(e)}")
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': str(e),
                'traceback': traceback.format_exc()
            }).encode())

    def do_OPTIONS(self):
        print("Received OPTIONS request")
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 