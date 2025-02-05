from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import logging
import json
import time
import os
from dotenv import load_dotenv
import requests

from utils import read_prompt_template, create_prompt, authenticate
from vertex_client import VertexClient, TOKEN_REFRESH_THRESHOLD
from vertexai.generative_models import GenerativeModel, GenerationConfig, SafetySetting, HarmCategory, HarmBlockThreshold

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vertex AI client
client = VertexClient()

# Generation configurations
generation_config = GenerationConfig()
safety_config = [
    SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_NONE),
]

def generate_content(prompt: str):
    """Generates content using Gemini model with retries."""
    for attempt in range(1, 4):
        try:
            if time.time() + TOKEN_REFRESH_THRESHOLD >= client.token_expiry:
                client.refresh_token()

            model = GenerativeModel("gemini-1.5-pro-001")
            response = model.generate_content(prompt, generation_config=generation_config, safety_settings=safety_config, metadata=client.metadata)
            text = response.candidates[0].content.parts[0].text

            return text
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            if attempt == 3:
                raise HTTPException(status_code=500, detail="Failed to generate content after multiple attempts.")
            time.sleep(2**attempt)  # Exponential backoff

class LogAnalysisRequest(BaseModel):
    cloud_provider: str
    logs: list

@app.post("/analyze_logs")
def analyze_logs(request: LogAnalysisRequest):
    """Analyzes logs based on cloud provider and log data."""
    template_content = read_prompt_template("prompts/soc_cloud_evidence_analyzer/analyze_prompt")
    prompt = create_prompt(template_content, cloud_provider=request.cloud_provider, logs=request.logs)
    response = generate_content(prompt)
    return {"analysis_response": response}

class SummaryRequest(BaseModel):
    analysis_response: str

@app.post("/summarize_events")
def summarize_events(request: SummaryRequest):
    """Summarizes events from the analysis response."""
    template_content = read_prompt_template("prompts/soc_cloud_evidence_analyzer/summarize_prompt")
    prompt = create_prompt(template_content, analysis_response=request.analysis_response)
    response = generate_content(prompt)
    return {"summary_response": response}

class DiagramRequest(BaseModel):
    analysis_response: str

@app.post("/generate_diagram")
def generate_diagram(request: DiagramRequest):
    """Generates a Mermaid diagram based on the analysis response."""
    template_content = read_prompt_template("prompts/soc_cloud_evidence_analyzer/diagram_prompt")
    prompt = create_prompt(template_content, analysis_response=request.analysis_response)
    response = generate_content(prompt)
    return {"diagram_response": response}