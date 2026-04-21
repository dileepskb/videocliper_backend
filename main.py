from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import os
import subprocess
import whisper

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev ke liye (sab allow)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Whisper model load (ek baar)
model = whisper.load_model("base")


@app.get("/")
def read_root():
    return {"message": "Backend is running 🚀"}


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename}


@app.post("/extract-audio")
async def extract_audio(file: UploadFile = File(...)):
    video_path = os.path.join(UPLOAD_FOLDER, file.filename)
    audio_filename = file.filename.split(".")[0] + ".mp3"
    audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "libmp3lame",
        audio_path
    ]

    subprocess.run(command)

    return {
        "audio_file": audio_filename,
        "url": f"/download/{audio_filename}"
    }


@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    return FileResponse(file_path, media_type="audio/mpeg", filename=filename)


@app.post("/generate-captions")
async def generate_captions(file: UploadFile = File(...)):
    audio_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = model.transcribe(audio_path)

    return {
        "text": result["text"]
    }