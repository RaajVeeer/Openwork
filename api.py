from fastapi import FastAPI, HTTPException, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
import json
import csv
import io
import time
import logging
from pydantic import BaseModel
from vertexai.generative_models import GenerativeModel, GenerationConfig, SafetySetting, HarmCategory, HarmBlockThreshold
from utils import read_prompt_template, create_prompt, authenticate
from vertex_client import VertexClient, TOKEN_REFRESH_THRESHOLD

# Initialize FastAPI app
app = FastAPI()

# Logger setup
logging.basicConfig(filename="soc_cloud_evidence_analyzer.log", level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Vertex AI client
client = VertexClient()

# Generation settings
generation_config = GenerationConfig(temperature=0)
safety_config = [
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    )
]

# Define models
class AnalysisRequest(BaseModel):
    cloud_provider: str
    logs: str

class SummaryRequest(BaseModel):
    analysis_response: str

class DiagramRequest(BaseModel):
    analysis_response: str


def generate_content(prompt: str):
    """Generates content using the Gemini model with retries and logging."""
    for attempt in range(1, 4):  # Retry up to 3 times
        try:
            # Ensure token is valid before making API call
            if time.time() + TOKEN_REFRESH_THRESHOLD >= client.token_expiry:
                client.refresh_token()

            model = GenerativeModel("gemini-1.5-pro-001")
            response = model.generate_content(prompt, generation_config=generation_config, safety_settings=safety_config)
            
            text = response.candidates[0].content.parts[0].text if response.candidates else ""

            # Log interaction
            logger.info(f"Generated response: {text}")

            return text
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            if attempt == 3:
                raise HTTPException(status_code=500, detail="Failed to generate content after multiple attempts.")
            time.sleep(2 ** attempt)  # Exponential backoff


@app.post("/analyze/")
async def analyze_logs(request: AnalysisRequest):
    """Analyze logs using Gemini model"""
    template_content = read_prompt_template("prompts/soc_cloud_evidence_analyzer/analyze_prompt")
    prompt = create_prompt(template_content, cloud_provider=request.cloud_provider, logs=request.logs)
    response = generate_content(prompt)
    return JSONResponse(content={"analysis_response": response})


@app.post("/summarize/")
async def summarize_events(request: SummaryRequest):
    """Summarize log analysis"""
    template_content = read_prompt_template("prompts/soc_cloud_evidence_analyzer/summarize_prompt")
    prompt = create_prompt(template_content, analysis_response=request.analysis_response)
    response = generate_content(prompt)
    return JSONResponse(content={"summary_response": response})


@app.post("/generate-diagram/")
async def generate_diagram(request: DiagramRequest):
    """Generate threat model diagram"""
    template_content = read_prompt_template("prompts/soc_cloud_evidence_analyzer/diagram_prompt")
    prompt = create_prompt(template_content, analysis_response=request.analysis_response)
    response = generate_content(prompt)
    return JSONResponse(content={"diagram_response": response})


@app.post("/upload/")
async def upload_file(file: UploadFile):
    """Handle log file upload and return JSON response"""
    if file.content_type == "application/json":
        content = await file.read()
        logs = json.loads(content)
    elif file.content_type == "text/csv":
        content = await file.read()
        decoded = content.decode()
        reader = csv.DictReader(io.StringIO(decoded))
        logs = [row for row in reader]
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use JSON or CSV.")

    return {"logs": logs}