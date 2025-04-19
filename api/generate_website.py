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

        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.6,
                top_p=0.95,
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