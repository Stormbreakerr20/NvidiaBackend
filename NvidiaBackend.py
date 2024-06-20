import requests, base64, json
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI ,File
from PIL import Image
# import nest_asyncio
# from pyngrok import ngrok
import os
# import uvicorn

app = FastAPI()
origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# @app.get("/")
# async def redirect_root_to_docs():
#     return RedirectResponse("/docs")

def image_to_base64(image_path):
    if image_path.startswith('http://') or image_path.startswith('https://'):
        response = requests.get(image_path)
        if response.status_code == 200:
            encoded_string = base64.b64encode(response.content)
            return encoded_string.decode("utf-8")
        else:
            print("Failed to fetch image from URL:", image_path)
            return None
    else:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            return encoded_string.decode("utf-8")
        
def load_image(image_path):
    if is_url(image_path):
        return Image.open(requests.get(image_path, stream=True).raw)
    elif os.path.exists(image_path):
        return Image.open(image_path)


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
def blur_score():
    files = {'media': open('./image.jpg', 'rb')}
    r = requests.post('https://api.sightengine.com/1.0/check.json', files=files, data=params)

    score = json.loads(r.text)['quality']['score']
    return score

def generate_response(prompt):
    payload = {
    "messages": [
        {
        "role": "user",
        "content": f'{prompt} <img src="data:image/jpeg;base64,{str(image_to_base64(str("./image.jpg")))}" />'
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
    
    return complete_content

@app.post("/caption")
async def UploadImage(file: bytes = File(...)):
    with open('image.jpg','wb') as image:
      image.write(file)
      image.close()

    if blur_score() <= 0.35:
        return {"title":"Quality issues are too severe to recognize visual content."}

    complete_content = generate_response("Generate a vivid, short and engaging caption that captures the essence of the provided image.")
    return {"title":complete_content}

@app.post("/chat")
async def Chat(prompt:str,file: bytes = File(...)):
  with open('image.jpg','wb') as image:
    image.write(file)
    image.close()
  
  response = generate_response(prompt)
  return {"content":response}

# os.system(f"ngrok authtoken 2fX4X2BATxalJmNiCutMXV1qR6k_4RXntzTaGfFuGwYpRuKcE")

# # Connect to ngrok
# connection_string = ngrok.connect(8000,bind_tls = True)

# # Print the public URL
# print('Public URL:', connection_string)
# nest_asyncio.apply()
# uvicorn.run(app,port = 8000,reload = False)
