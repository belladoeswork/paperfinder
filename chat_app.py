import os
import sys
import streamlit as st
from streamlit_chat import message
from PyPDF2 import PdfReader
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.cassandra import Cassandra
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv
import cassio

import urllib
import arxiv

# Load env variables
load_dotenv()

# API keys and database connection
ASTRA_DB_APPLICATION_TOKEN = os.environ.get("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_ID = os.environ.get("ASTRA_DB_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# init DB connection
cassio.init(token=ASTRA_DB_APPLICATION_TOKEN, database_id=ASTRA_DB_ID)

# Load model
def load_llm():
    return OpenAI(openai_api_key=OPENAI_API_KEY)

# app title
st.title("ABA(Ask Bot Anything) - 📄💬")

# file uploader in the sidebar
uploaded_file = st.sidebar.file_uploader("Upload PDF File", type="pdf")

# file upload
if uploaded_file:
    # Read PDF
    pdf_reader = PdfReader(uploaded_file)
    
    # Extract text from PDF
    raw_text = ''
    for page in pdf_reader.pages:
        content = page.extract_text()
        if content:
            raw_text += content

    # Split text into chunks
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=800,
        chunk_overlap=200,
        length_function=len,
    )
    texts = text_splitter.split_text(raw_text)

    # embeddings
    embedding = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    # vector store
    vector_store = Cassandra(
        embedding=embedding,
        table_name="pdf_qa",
        session=None,
        keyspace=None,
    )

    # Load data 
    vector_store.add_texts(texts[:50])
    
    # vector store
    astra_vector_index = VectorStoreIndexWrapper(vectorstore=vector_store)

    # language model
    llm = load_llm()

    # conversational chain
    chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=vector_store.as_retriever())

    # chat function
    def conversational_chat(query):
        result = chain({"question": query, "chat_history": st.session_state['history']})
        st.session_state['history'].append((query, result["answer"]))
        return result["answer"]
    

    # Init chat history
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    # Init messages
    if 'generated' not in st.session_state:
        st.session_state['generated'] = [f"Hello! Ask me about the PDF {uploaded_file.name} 📄"]

    if 'past' not in st.session_state:
        st.session_state['past'] = ["Hey! 👋"]

    # containers for chat history and user input
    response_container = st.container()
    container = st.container()

    # User input form
    with container:
        with st.form(key='my_form', clear_on_submit=True):
            user_input = st.text_input("Query:", placeholder="Ask about the PDF content 👉", key='input')
            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            output = conversational_chat(user_input)
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(output)

    # Display chat history
    if st.session_state['generated']:
        with response_container:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="big-smile")
                message(st.session_state["generated"][i], key=str(i), avatar_style="thumbs")

else:
    st.write("Please upload a PDF file to begin.")
    
