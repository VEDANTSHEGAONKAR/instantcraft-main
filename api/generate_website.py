from http.server import BaseHTTPRequestHandler
from flask import Response
import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
import traceback

load_dotenv()

# Initialize Gemini client
try:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Error initializing Gemini client: {str(e)}")
    traceback.print_exc()

def handle_request(request_body):
    try:
        if not request_body:
            return {'error': 'No JSON data received'}, 400

        description = request_body.get('description')
        if not description:
            return {'error': 'No description provided'}, 400

        prompt = f"""
        Create a visually appealing, professional website based on this description: {description}
        
        Important requirements:
        1. Include a gradient animated background that smoothly transitions between colors
        2. Use modern CSS features including animations, transitions, and flexbox/grid layouts
        3. Make the design visually striking with proper spacing, typography, and color harmony
        4. Include placeholder images with proper styling (use lorem picsum or unsplash source URLs)
        5. Ensure the website is fully responsive and mobile-friendly
        6. Add subtle animations for UI elements (buttons, links, sections) to enhance user experience
        
        Return only the HTML, CSS, and JavaScript code without any explanations.
        Format the response exactly as:
        ```html
        [HTML code here]
        ```
        ```css
        [CSS code here]
        ```
        ```javascript
        [JavaScript code here]
        ```
        Make sure the code is complete, functional, and properly handles user interactions.
        The JavaScript code should be properly scoped and not interfere with the parent window.
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash-preview-04-17',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                top_p=0.9,
                top_k=40,
                max_output_tokens=8192,
            )
        )

        return {'result': response.text}, 200

    except Exception as e:
        return {
            'error': str(e),
            'traceback': traceback.format_exc()
        }, 500

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            request_body = self.rfile.read(content_length)
            data = json.loads(request_body)

            response_data, status_code = handle_request(data)

            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            self.wfile.write(json.dumps(response_data).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()