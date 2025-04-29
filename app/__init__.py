import requests
import traceback

from typing import List, Dict
from fastapi import FastAPI, HTTPException

from app.main import main


app = FastAPI()


@app.get("/")
def home():
    return {'message': "Welcome to the home page"}


@app.post("/predict")
def predict(data: List[Dict]):
    """_summary_
    Args:
        video (VideoItem): class

    Returns:
        return_lst: list
    """
    return_lst = []
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")

    for entry in data:
        processed_entry = entry.copy()
        try:
            video_path = 'app/data/fake.mp4'
            response = requests.get(entry['VideoPath'])
            if response.status_code == 200:
                with open(video_path, 'wb') as f:
                    f.write(response.content)
                print("Download successful.")
                processed_entry['message'] = main(video_path, 'app/data/audio.mp3', entry)
            else:
                raise Exception
        except:
            print(traceback.format_exc())
            processed_entry['message'] = "Couldn't download video"
        return_lst.append(processed_entry)
    return return_lst
