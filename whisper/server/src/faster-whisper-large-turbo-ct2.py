from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel
import torch
import uvicorn
import zhconv

# Configure device - use CUDA if available, otherwise fall back to CPU
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Load the Whisper model
model = WhisperModel("models/faster-whisper-large-v3-turbo-ct2")

# Create FastAPI application
app = FastAPI()


@app.post("/transcribe/")
async def transcribe(file: UploadFile = File(...)):
    """
    Transcribe audio file endpoint

    Args:
        file (UploadFile): Audio file to transcribe

    Returns:
        JSONResponse: Contains either:
            - transcribed text (converted to simplified Chinese)
            - error message if transcription fails
    """
    try:
        # Read uploaded file into memory
        audio_data = await file.read()

        # Save to temporary file for processing
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as f:
            f.write(audio_data)

        # Transcribe audio using Whisper model
        segments, info = model.transcribe(temp_file_path)
        text = ""
        for segment in segments:
            text += segment.text

        # Return transcription with traditional to simplified Chinese conversion
        return JSONResponse(content={"text": zhconv.convert(text, "zh-cn")})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)
