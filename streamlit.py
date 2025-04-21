import streamlit as st
from utils import (
    get_vector_store,
    getLLM,
    getPromptTemplate,
    hyde_rag_response
)

pc_index_name = "qa-assistant"
csv_files = ["Schemes.csv"]

st.set_page_config(page_title="Govt Scheme Assistant", layout="wide")
st.title("🗂️ Government Scheme Q&A Assistant")

with st.sidebar:
    st.header("Settings")
    selected_state = st.selectbox("Select Your State (optional):", [
        "-- All India --",
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
        "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
        "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
    ])
    if st.button("Start New Chat"):
        st.session_state.chat_history = []

    st.markdown("You can ask about any government scheme available in the database.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

@st.cache_resource(show_spinner="Initializing models...")
def initialize(state_filter):
    vector_store = get_vector_store(pc_index_name, csv_files, state_filter)
    llm = getLLM()
    prompt_template = getPromptTemplate()
    return vector_store, llm, prompt_template

vector_store, llm, prompt_template = initialize(selected_state)

st.subheader("💬 Ask me about government schemes")
user_query = st.text_input("Type your question here and press Enter")

if user_query:
    with st.spinner("Assistant is thinking..."):
        answer, docs = hyde_rag_response(llm, vector_store, prompt_template, user_query)

    st.session_state.chat_history.append((user_query, answer))

for user_msg, bot_msg in reversed(st.session_state.chat_history):
    with st.chat_message("user"):
        st.markdown(user_msg)
    with st.chat_message("assistant"):
        st.markdown(bot_msg)
