import streamlit as st
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://127.0.0.1:8000"  # Change if deployed

st.set_page_config(
    page_title="SOC Cloud Evidence Analyzer",
    layout="centered",
)

st.image("assets/Citi_Blue-RedArc_RGB.png")
st.title("SOC Cloud Evidence Analyzer")

# Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Enter Access Code:", type="password")
    if st.button("Login"):
        if password == "securepassword":  # Replace with actual authentication check
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid Access Code")
else:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

# File upload
st.markdown("### Upload Log File")
uploaded_file = st.file_uploader("Upload a JSON or CSV file", type=["json", "csv"])

if uploaded_file:
    files = {"file": uploaded_file.getvalue()}
    response = requests.post(f"{API_URL}/upload/", files=files)
    if response.status_code == 200:
        st.session_state.logs = response.json()["logs"]
        st.success("File uploaded successfully.")
    else:
        st.error("Failed to upload file.")

# Cloud provider selection
cloud_provider = st.selectbox("Select Cloud Provider", ["AWS", "Azure", "GCP"])

# Tabs
tab1, tab2, tab3 = st.tabs(["Analyze Logs", "Summarize Events", "Generate Diagram"])

with tab1:
    if st.button("Analyze Logs"):
        if "logs" in st.session_state:
            st.session_state.analysis_response = requests.post(
                f"{API_URL}/analyze/",
                json={"cloud_provider": cloud_provider, "logs": json.dumps(st.session_state.logs)}
            ).json()["analysis_response"]
            st.json(st.session_state.analysis_response)
        else:
            st.error("Please upload a log file first.")

with tab2:
    if st.button("Summarize Events"):
        if "analysis_response" in st.session_state:
            st.session_state.summary_response = requests.post(
                f"{API_URL}/summarize/",
                json={"analysis_response": st.session_state.analysis_response}
            ).json()["summary_response"]
            st.markdown(st.session_state.summary_response)
        else:
            st.error("Please analyze logs first.")

with tab3:
    if st.button("Generate Diagram"):
        if "analysis_response" in st.session_state:
            st.session_state.diagram_response = requests.post(
                f"{API_URL}/generate-diagram/",
                json={"analysis_response": st.session_state.analysis_response}
            ).json()["diagram_response"]
            st.code(st.session_state.diagram_response)
        else:
            st.error("Please analyze logs first.")