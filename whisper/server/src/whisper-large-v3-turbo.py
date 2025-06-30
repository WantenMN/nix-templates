from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import torch
import uvicorn
import zhconv

# Configure computing device, prioritize GPU if available
device = "cuda:0" if torch.cuda.is_available() else "cpu"
# Use float16 precision for GPU to improve performance, otherwise use float32
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Load the pre-trained speech recognition model
model_id = "models/whisper-large-v3-turbo"
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id,
    torch_dtype=torch_dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True,
)
# Move the model to the configured device
model.to(device)
# Load the processor for feature extraction and tokenization
processor = AutoProcessor.from_pretrained(model_id)
# Create a pipeline for automatic speech recognition
pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device,
)

# Initialize FastAPI application
app = FastAPI()


# Define the API endpoint for speech transcription
@app.post("/transcribe/")
async def transcribe(file: UploadFile = File(...)):
    try:
        # Asynchronously read the uploaded audio file
        audio_data = await file.read()

        # Save the audio data to a temporary file
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as f:
            f.write(audio_data)

        # Perform speech recognition using the loaded model
        result = pipe(
            temp_file_path,
            generate_kwargs={"language": "zh"},  # Specify Chinese language
        )
        # Extract transcribed text and convert to Simplified Chinese
        text = result.get("text", "")
        return JSONResponse(content={"text": zhconv.convert(text, "zh-cn")})
    except Exception as e:
        # Error handling, return error message with HTTP 500 status code
        return JSONResponse(content={"error": str(e)}, status_code=500)


# Application entry point
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
