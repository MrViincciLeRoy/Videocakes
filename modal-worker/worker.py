import modal
import json

stub = modal.Stub("comfyui-video")

comfyui_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "wget", "ffmpeg")
    .run_commands(
        "git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui",
        "cd /comfyui && pip install -r requirements.txt",
        "pip install xformers gguf",
        "cd /comfyui && git clone https://github.com/city96/ComfyUI-GGUF.git custom_nodes/ComfyUI-GGUF",
        "cd /comfyui && git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git custom_nodes/ComfyUI-VideoHelperSuite",
        "cd /comfyui/custom_nodes/ComfyUI-VideoHelperSuite && pip install -r requirements.txt",
    )
)

@stub.function(
    image=comfyui_image,
    gpu="T4",
    timeout=900,
    volumes={"/models": modal.Volume.from_name("comfyui-models", create_if_missing=True)}
)
def download_models():
    import subprocess
    
    commands = [
        "mkdir -p /models/unet /models/vae /models/clip",
        "wget -O /models/unet/wan2.2-ti2v-5b-Q8_0.gguf https://huggingface.co/QuantStack/Wan2.2-TI2V-5B-GGUF/resolve/main/Wan2.2-TI2V-5B-Q8_0.gguf",
        "wget -O /models/vae/wan_vae.safetensors https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B/resolve/main/vae/diffusion_pytorch_model.safetensors",
        "wget -O /models/clip/t5xxl_fp16.safetensors https://huggingface.co/mcmonkey/google_t5-v1_1-xxl_encoderonly/resolve/main/t5xxl_fp16.safetensors",
    ]
    
    for cmd in commands:
        subprocess.run(cmd, shell=True, check=True)
    
    return "Models downloaded"

@stub.function(
    image=comfyui_image,
    gpu="T4",
    timeout=900,
    volumes={"/models": modal.Volume.from_name("comfyui-models")}
)
def generate_video(prompt: str, seed: int = 42, negative_prompt: str = "low quality", steps: int = 30):
    import subprocess
    import time
    import requests
    import os
    import sys
    
    sys.path.insert(0, '/comfyui')
    
    os.system("ln -sf /models /comfyui/models")
    
    proc = subprocess.Popen(
        ['python', 'main.py', '--listen', '127.0.0.1', '--port', '8188'],
        cwd='/comfyui',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(45)
    
    workflow = {
        "6": {"inputs": {"text": prompt, "clip": ["11", 0]}, "class_type": "CLIPTextEncode"},
        "8": {"inputs": {"samples": ["13", 0], "vae": ["10", 0]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"filename_prefix": "video", "images": ["8", 0]}, "class_type": "VHS_VideoCombine"},
        "10": {"inputs": {"vae_name": "wan_vae.safetensors"}, "class_type": "VAELoader"},
        "11": {"inputs": {"clip_name": "t5xxl_fp16.safetensors"}, "class_type": "CLIPLoader"},
        "12": {"inputs": {"unet_name": "wan2.2-ti2v-5b-Q8_0.gguf"}, "class_type": "UNETLoader"},
        "13": {"inputs": {"seed": seed, "steps": steps, "cfg": 6.0, "sampler_name": "euler", 
                          "scheduler": "normal", "denoise": 1, "model": ["12", 0], 
                          "positive": ["6", 0], "negative": ["15", 0], 
                          "latent_image": ["14", 0]}, "class_type": "KSampler"},
        "14": {"inputs": {"width": 1280, "height": 704, "length": 121, "batch_size": 1}, 
               "class_type": "EmptyLatentVideo"},
        "15": {"inputs": {"text": negative_prompt, "clip": ["11", 0]}, "class_type": "CLIPTextEncode"}
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:8188/prompt',
            json={"prompt": workflow},
            timeout=30
        )
        prompt_id = response.json()['prompt_id']
        
        while True:
            history = requests.get(f'http://127.0.0.1:8188/history/{prompt_id}').json()
            if prompt_id in history:
                break
            time.sleep(10)
        
        output_dir = '/comfyui/output'
        files = [f for f in os.listdir(output_dir) if f.endswith(('.mp4', '.webm'))]
        
        if files:
            video_path = os.path.join(output_dir, files[-1])
            with open(video_path, 'rb') as f:
                video_data = f.read()
            
            import base64
            video_b64 = base64.b64encode(video_data).decode()
            
            return {
                "status": "success",
                "prompt_id": prompt_id,
                "video": video_b64,
                "filename": files[-1]
            }
        
        return {"status": "error", "message": "No video generated"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    finally:
        proc.kill()

@stub.webhook(method="POST")
def webhook(data: dict):
    prompt = data.get("prompt", "A cat walking on the beach")
    seed = data.get("seed", 42)
    negative = data.get("negative_prompt", "low quality, blurry")
    steps = data.get("steps", 30)
    
    result = generate_video.remote(prompt, seed, negative, steps)
    return result

@stub.local_entrypoint()
def setup():
    download_models.remote()
    print("Setup complete!")
