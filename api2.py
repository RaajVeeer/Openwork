from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
import json
import logging
import time
from vertexai.generative_models import GenerativeModel, GenerationConfig
from utils import authenticate, read_prompt_template, create_prompt

app = FastAPI()

# Configure logging
logging.basicConfig(filename="soc_cloud_analyzer.log", level=logging.INFO)
logger = logging.getLogger(__name__)

# Model settings
GENERATION_CONFIG = GenerationConfig(temperature=0)
MODEL_NAME = "gemini-1.5-pro-001"
model = GenerativeModel(MODEL_NAME)

class AnalysisRequest(BaseModel):
    cloud_provider: str
    logs: str

class SummaryRequest(BaseModel):
    analysis_response: str

class DiagramRequest(BaseModel):
    analysis_response: str

def generate_content(prompt: str) -> str:
    """Generates content using Gemini model with retries."""
    for attempt in range(3):
        try:
            response = model.generate_content(prompt, generation_config=GENERATION_CONFIG)
            return response.candidates[0].content.parts[0].text
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            if attempt == 2:
                raise HTTPException(status_code=500, detail="Content generation failed.")
            time.sleep(2 ** attempt)

@app.post("/analyze/")
def analyze_logs(request: AnalysisRequest):
    """Analyzes cloud logs and returns structured data."""
    template = read_prompt_template("prompts/soc_cloud_evidence_analyzer/analyze_prompt")
    prompt = create_prompt(template, cloud_provider=request.cloud_provider, logs=request.logs)
    response = generate_content(prompt)
    
    try:
        response_json = json.loads(response)
        return {"timeline": response_json}
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON response from AI model.")

@app.post("/summarize/")
def summarize_events(request: SummaryRequest):
    """Summarizes analyzed logs into a concise report."""
    template = read_prompt_template("prompts/soc_cloud_evidence_analyzer/summarize_prompt")
    prompt = create_prompt(template, analysis_response=request.analysis_response)
    return {"summary": generate_content(prompt)}

@app.post("/diagram/")
def generate_diagram(request: DiagramRequest):
    """Generates a Mermaid diagram for visualization."""
    template = read_prompt_template("prompts/soc_cloud_evidence_analyzer/diagram_prompt")
    prompt = create_prompt(template, analysis_response=request.analysis_response)
    return {"diagram": generate_content(prompt)}

@app.get("/health/")
def health_check():
    """Checks if the API is running."""
    return {"status": "ok"}