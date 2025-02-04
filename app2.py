import streamlit as st
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="SOC Cloud Evidence Analyzer", layout="centered")
st.image("assets/Citi_Blue-RedArc_RGB.png")

st.title("SOC Cloud Evidence Analyzer")
st.markdown("---")

st.sidebar.header("User Authentication")
password = st.sidebar.text_input("Experiment Access Code", type="password")

if st.sidebar.button("Login"):
    if password == "your_secure_code":  # Replace with real authentication logic
        st.session_state.authenticated = True
        st.sidebar.success("Login successful")
    else:
        st.sidebar.error("Incorrect access code.")

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to continue.")
    st.stop()

st.sidebar.button("Logout", on_click=lambda: st.session_state.update(authenticated=False))

# Main UI Tabs
tab1, tab2, tab3 = st.tabs(["Analyze Logs", "Summarize Events", "Generate Diagram"])

with tab1:
    st.header("Upload Logs for Analysis")
    cloud_provider = st.selectbox("Select Cloud Provider", ["AWS", "Azure", "GCP"])
    uploaded_file = st.file_uploader("Upload JSON or CSV log file", type=["json", "csv"])

    if uploaded_file:
        file_content = uploaded_file.read().decode("utf-8")

        if st.button("Analyze Logs"):
            response = requests.post(f"{BACKEND_URL}/analyze/", json={
                "cloud_provider": cloud_provider,
                "logs": file_content
            })

            if response.status_code == 200:
                analysis_response = response.json()
                st.session_state.analysis_response = json.dumps(analysis_response, indent=2)
                st.json(analysis_response)
                st.download_button("Download Analysis", json.dumps(analysis_response), "analysis.json", "application/json")
            else:
                st.error("Error analyzing logs.")

with tab2:
    st.header("Summarize Events")

    if "analysis_response" in st.session_state:
        if st.button("Summarize Events"):
            response = requests.post(f"{BACKEND_URL}/summarize/", json={
                "analysis_response": st.session_state.analysis_response
            })

            if response.status_code == 200:
                summary = response.json()["summary"]
                st.session_state.summary_response = summary
                st.write(summary)
                st.download_button("Download Summary", summary, "summary.txt", "text/plain")
            else:
                st.error("Error summarizing events.")
    else:
        st.warning("Please analyze logs first.")

with tab3:
    st.header("Generate Diagram")

    if "analysis_response" in st.session_state:
        if st.button("Generate Diagram"):
            response = requests.post(f"{BACKEND_URL}/diagram/", json={
                "analysis_response": st.session_state.analysis_response
            })

            if response.status_code == 200:
                diagram = response.json()["diagram"]
                st.session_state.diagram_response = diagram
                st.markdown(diagram)
                st.download_button("Download Diagram Code", diagram, "diagram.txt", "text/plain")
            else:
                st.error("Error generating diagram.")
    else:
        st.warning("Please analyze logs first.")