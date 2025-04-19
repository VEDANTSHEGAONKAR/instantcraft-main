from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import traceback

load_dotenv()

app = Flask(__name__)
# Configure CORS to allow requests from your React app
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize Gemini client with error handling
try:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    genai.configure(api_key=api_key)
    # Use a higher capability model
    model = genai.GenerativeModel('gemini-1.5-pro')
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

        print(f"Received description: {description}")  # Debug log

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

        print("Sending request to Gemini...")  # Debug log

        # Adjust parameters to ensure better completion
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.6,  # Lower temperature for more deterministic results
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,  # Increased token limit for complete response
            ),
            stream=True
        )

        print("Received response from Gemini")  # Debug log

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

@app.route('/api/modify-website', methods=['POST'])
def modify_website():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        modification = data.get('modificationDescription')
        current_html = data.get('currentHtml')
        current_css = data.get('currentCss')
        current_js = data.get('currentJs', '')  # Optional JavaScript code

        if not all([modification, current_html, current_css]):
            return jsonify({'error': 'Missing required fields'}), 400

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

        # Adjust parameters to ensure better completion
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.6,  # Lower temperature for more deterministic results
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,  # Increased token limit for complete response
            ),
            stream=True
        )

        return Response(
            stream_response(response),
            mimetype='text/event-stream'
        )

    except Exception as e:
        print(f"Error in modify_website: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(port=3001, debug=True)