# Videocakes
Videocakes is a video generation API that utilizes ComfyUI and Modal to produce high-quality videos based on user input.
## What it does
The API takes in a prompt, seed, negative prompt, and steps as input, and generates a video using the ComfyUI model.
## Key Features
- Video generation using ComfyUI model
- Supports custom prompts, seeds, and negative prompts
- Utilizes Modal for scalable and efficient processing
## Tech Stack
- ComfyUI: A video generation model
- Modal: A platform for building and deploying scalable applications
- Flask: A web framework for building the API
- Python: The programming language used for the project
## Installation
To install the project, follow these steps:
- Clone the repository: git clone https://github.com/\[username]\/Videocakes.git
- Install the requirements: pip install -r requirements.txt
## Usage
To use the API, send a POST request to the /generate endpoint with the following JSON body:
```\n{\n  "prompt": "A cat walking on the beach",\n  "seed": 42,\n  "negative_prompt": "low quality",\n  "steps": 30\n}\n```
## Environment Variables
The following environment variables are required:
- MODAL_WEBHOOK_URL: The URL of the Modal webhook
- PORT: The port number to run the API on (default: 5000)