import requests, base64, json, io
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile
from PIL import Image

app = FastAPI()
origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def redirect_root_to_docs():
    return {"Hi": "Welcome to the Nvidia Backend"}

def image_to_base64(image_data):
    encoded_string = base64.b64encode(image_data)
    return encoded_string.decode("utf-8")
        
def load_image(image_data):
    return Image.open(io.BytesIO(image_data))

invoke_url = "https://ai.api.nvidia.com/v1/vlm/community/llava16-mistral-7b"
stream = True

headers = {
    "Authorization": "Bearer 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",
    "Accept": "text/event-stream" if stream else "application/json"
}

params = {
    'models': 'quality',
    'api_user': '1276533234',
    'api_secret': 'fLqocaoDSMvC7BvwdFZbeJbfmq3KP4Gk'
}

def blur_score(image_data):
    files = {'media': io.BytesIO(image_data)}
    r = requests.post('https://api.sightengine.com/1.0/check.json', files=files, data=params)
    score = json.loads(r.text)['quality']['score']
    return score

def generate_response(prompt, image_data):
    base64_image = image_to_base64(image_data)
    payload = {
        "messages": [
            {
                "role": "user",
                "content": f'{prompt} <img src="data:image/jpeg;base64,{base64_image}" />'
            }
        ],
        "max_tokens": 512,
        "temperature": 1.00,
        "top_p": 0.70,
        "stream": stream
    }
    response = requests.post(invoke_url, headers=headers, json=payload)
    if stream:
        complete_content = ""
        for line in response.iter_lines():
            if line:
                data = line.decode("utf-8")
                try:
                    complete_content += json.loads(data[6:])['choices'][0]['delta']['content']
                except:
                    pass    
    print(complete_content)
    return complete_content

@app.post("/caption")
async def UploadImage(file: UploadFile = File(...)):
    image_data = await file.read()
    if blur_score(image_data) <= 0.35:
        return {"title": "Quality issues are too severe to recognize visual content."}

    complete_content = generate_response("Generate a vivid, short and engaging caption that captures the essence of the provided image.", image_data)
    return {"title": complete_content}

@app.post("/chat")
async def Chat(prompt: str, file: UploadFile = File(...)):
    image_data = await file.read()
    response = generate_response(prompt, image_data)
    print(response)
    return {"content": response}


# os.system(f"ngrok authtoken 2fX4X2BATxalJmNiCutMXV1qR6k_4RXntzTaGfFuGwYpRuKcE")

# # Connect to ngrok
# connection_string = ngrok.connect(8000,bind_tls = True)

# # Print the public URL
# print('Public URL:', connection_string)
# nest_asyncio.apply()
# uvicorn.run(app,port = 8000,reload = False)
