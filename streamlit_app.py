import streamlit as st

st.set_page_config(page_title="DFIR TTX Platform", layout="wide")

st.title("DFIR Tabletop Exercise Platform")

st.sidebar.title("Navigation")

page = st.sidebar.selectbox("Go to", ["Home", "Scenario", "Results"])

if page == "Home":
    st.write("Welcome to the DFIR TTX Platform.")
    st.write("This will simulate cyber incident decision-making.")

elif page == "Scenario":
    st.header("Scenario Simulation")
    st.write("Scenario engine will connect to backend here.")

elif page == "Results":
    st.header("Results Dashboard")
    st.write("Decision tracking and scoring will appear here.")
