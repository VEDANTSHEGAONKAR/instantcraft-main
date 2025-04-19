from http.server import BaseHTTPRequestHandler
import os
import json
from google import genai
from google.generativeai import types
from dotenv import load_dotenv
import traceback

load_dotenv()

# Initialize Gemini client
try:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    print(f"Error initializing Gemini client: {str(e)}")
    traceback.print_exc()

def handle_request(request_body):
    try:
        if not request_body:
            return {'error': 'No JSON data received'}, 400

        modification = request_body.get('modificationDescription')
        current_html = request_body.get('currentHtml')
        current_css = request_body.get('currentCss')
        current_js = request_body.get('currentJs', '')

        if not all([modification, current_html, current_css]):
            return {'error': 'Missing required fields'}, 400

        prompt = f"""
        Modify this website according to this description: {modification}
        
        MOST IMPORTANT:
        1. For ANY new or changed images, use REAL IMAGES that directly relate to the modification
        2. Each new image must use a DIFFERENT keyword from the modification description
        3. Use valid, working image URLs from Unsplash for ALL images
        
        For ANY image you add or change, use this EXACT format:
        <img src="https://source.unsplash.com/random/800x600/?[keyword]" alt="[description]">
        
        Replace [keyword] with SPECIFIC words from the modification description.
        DO NOT use placeholder text or broken image URLs.
        Make each image URL UNIQUE and SPECIFIC to the content it represents.
        
        When modifying the website:
        - Keep existing structure where appropriate
        - Add requested animations and effects 
        - Maintain responsive design
        - Ensure all code remains functional

        Current HTML:
        ```html
        {current_html}
        ```

        Current CSS:
        ```css
        {current_css}
        ```

        Current JavaScript:
        ```javascript
        {current_js}
        ```

        Return only the modified code in this format:
        ```html
        [FULL MODIFIED HTML]
        ```
        ```css
        [FULL MODIFIED CSS]
        ```
        ```javascript
        [FULL MODIFIED JS]
        ```
        """

        response = model.generate_content(
            contents=prompt,
            generation_config=types.GenerationConfig(
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