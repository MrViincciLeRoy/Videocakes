from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

MODAL_URL = os.getenv("MODAL_WEBHOOK_URL")

@app.route('/')
def home():
    return jsonify({
        "service": "ComfyUI API",
        "endpoints": {
            "generate": "/generate [POST]",
            "health": "/health [GET]"
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    
    prompt = data.get('prompt', 'A cat walking on the beach')
    seed = data.get('seed', 42)
    negative = data.get('negative_prompt', 'low quality, blurry')
    steps = data.get('steps', 30)
    
    try:
        response = requests.post(
            MODAL_URL,
            json={
                "prompt": prompt,
                "seed": seed,
                "negative_prompt": negative,
                "steps": steps
            },
            timeout=600
        )
        
        return jsonify(response.json())
    
    except requests.exceptions.Timeout:
        return jsonify({"error": "Generation timeout"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
