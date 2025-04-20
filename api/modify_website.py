from http.server import BaseHTTPRequestHandler
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

        modification = request_body.get('modificationDescription')
        current_html = request_body.get('currentHtml')
        current_css = request_body.get('currentCss')
        current_js = request_body.get('currentJs', '')

        if not all([modification, current_html, current_css]):
            return {'error': 'Missing required fields'}, 400

        prompt = f"""
        Modify this website according to this description: {modification}

        Important:
        1. Maintain or enhance any existing animations and visual effects
        2. Ensure all gradient animations and visual styling remain intact
        3. Keep the design modern, responsive and visually appealing
        4. If adding new elements, match the existing style and add appropriate animations
        5. Use high-quality placeholder images where needed (lorem picsum or unsplash URLs)
        6. Ensure all interactive elements have proper hover/focus states

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

        Return only the modified HTML, CSS, and JavaScript code without any explanations.
        Format the response exactly as:
        ```html
        [Modified HTML code here]
        ```
        ```css
        [Modified CSS code here]
        ```
        ```javascript
        [Modified JavaScript code here]
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