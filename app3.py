import streamlit as st
import requests
import json
from dotenv import load_dotenv
from io import StringIO
import csv

# Load environment variables
load_dotenv()

# FastAPI backend URL
API_BASE_URL = "http://localhost:8000"  # Update if hosted elsewhere

# Set Streamlit page config
st.set_page_config(page_title="SOC Cloud Evidence Analyzer")

# Sidebar authentication
with st.sidebar:
    st.image("assets/Citi_Blue-RedArc_RGB.png")
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        password = st.text_input("Experiment Access Code", type="password")
        if st.button("Login"):
            if password == "valid_code":  # Replace with actual authentication logic
                st.session_state.authenticated = True
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Incorrect access code")
    else:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.success("You have been logged out")
            st.rerun()

# Main UI
st.title("SOC Cloud Evidence Analyzer")
st.markdown("---")

st.session_state.cloud_provider = st.selectbox("Select Cloud Provider", ["AWS", "Azure", "GCP"])

uploaded_file = st.file_uploader("Upload a file", type=["json", "csv"])
if uploaded_file:
    file_content = uploaded_file.read().decode()

tabs = st.tabs(["Analyze Logs", "Summarize Events", "Generate Diagram"])

with tabs[0]:
    if st.button("Analyze Logs") and uploaded_file:
        try:
            logs = []
            if uploaded_file.type == "text/csv":
                csv_reader = csv.DictReader(StringIO(file_content))
                logs = [row for row in csv_reader]
            else:
                logs = json.loads(file_content)

            response = requests.post(f"{API_BASE_URL}/analyze_logs", json={"cloud_provider": st.session_state.cloud_provider, "logs": logs})
            if response.status_code == 200:
                st.session_state.analysis_response = response.json()["analysis_response"]
                st.json(st.session_state.analysis_response)
            else:
                st.error("Error analyzing logs")

        except Exception as e:
            st.error(f"Error: {e}")

with tabs[1]:
    if "analysis_response" in st.session_state:
        if st.button("Summarize Events"):
            response = requests.post(f"{API_BASE_URL}/summarize_events", json={"analysis_response": st.session_state.analysis_response})
            if response.status_code == 200:
                st.session_state.summary_response = response.json()["summary_response"]
                st.write(st.session_state.summary_response)
                st.download_button("Download Summary", data=st.session_state.summary_response, file_name="summary.txt", mime="text/plain")
            else:
                st.error("Error summarizing events")
    else:
        st.warning("Analyze logs first")

with tabs[2]:
    if "analysis_response" in st.session_state:
        if st.button("Generate Mermaid Diagram"):
            response = requests.post(f"{API_BASE_URL}/generate_diagram", json={"analysis_response": st.session_state.analysis_response})
            if response.status_code == 200:
                st.session_state.diagram_response = response.json()["diagram_response"]
                st.markdown(st.session_state.diagram_response)
                st.download_button("Download Diagram", data=st.session_state.diagram_response, file_name="diagram.txt", mime="text/plain")
            else:
                st.error("Error generating diagram")
    else:
        st.warning("Analyze logs first")