from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import traceback

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Gemini client with error handling
try:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error initializing Gemini client: {str(e)}")
    traceback.print_exc()

def stream_response(response):
    try:
        for chunk in response:
            if hasattr(chunk, 'text'):
                yield f"data: {json.dumps({'text': chunk.text})}\n\n"
    except Exception as e:
        print(f"Error in stream_response: {str(e)}")
        traceback.print_exc()
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.route('/api/generate-website', methods=['POST'])
def generate_website():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        description = data.get('description')
        if not description:
            return jsonify({'error': 'No description provided'}), 400

        # Prompt engineering for website generation
        prompt = f"""
        Create a website based on this description: {description}
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

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            ),
            stream=True
        )

        return Response(
            stream_response(response),
            mimetype='text/event-stream'
        )

    except Exception as e:
        print(f"Error in generate_website: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# Vercel serverless function handler
def handler(event, context):
    return app(event, context)