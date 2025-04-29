# Interview Video Evaluation

This project provides an API for evaluating interview videos. It processes video files, extracts audio, transcribes speech, analyzes content, and returns various evaluation metrics.

## Features

- Download and process video files from URLs
- Extract and transcribe audio
- Analyze transcript for similarity, grammar, emotion, and more
- Return structured evaluation scores

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd interview-video-evalution
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env` and update as needed.

## Running the API

Start the FastAPI server:

```bash
uvicorn app.__init__:app --reload
```

The API will be available at `http://127.0.0.1:8000/`.

## API Endpoints

### `GET /`

Returns a welcome message.

**Response:**
```json
{"message": "Welcome to the home page"}
```

### `POST /predict`

Evaluates interview videos.

**Request Body:**  
A JSON array of objects, each containing at least a `VideoPath` key with a URL to a video file and other metadata.

Example:
```json
[
  {
    "VideoPath": "https://example.com/video.mp4",
    "department_group": "Academic",
    "subject": "Mathematics"
    // ...other fields as required
  }
]
```

**Response:**  
A JSON array of objects, each containing the original input fields plus a `message` field with the evaluation results or an error message.

Example:
```json
[
  {
    "VideoPath": "https://example.com/video.mp4",
    "department_group": "Academic",
    "subject": "Mathematics",
    "message": {
      "confidence": 0.85,
      "similarity_score": 0.9,
      "introduction_score": 0.8,
      "emotion_score": 0.7,
      "grammar_score": 0.95,
      "example_score": 0.75,
      "methodology_score": 0.8,
      "time_management_score": 0.9
    }
  }
]
```

If the video cannot be downloaded or processed, the `message` field will contain an error string.

## Input & Output Details

- **Input:**  
  - List of dictionaries with at least `VideoPath` (URL to video) and other metadata.
- **Output:**  
  - List of dictionaries with evaluation scores or error messages.

## Notes

- Only `.mp4` videos are supported.
- The API downloads the video, processes it, and deletes temporary files after processing.
- Make sure the server has internet access to download videos.

## License

MIT License (add your license here)
