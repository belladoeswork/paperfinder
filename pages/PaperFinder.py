import streamlit as st
import arxiv
from urllib.error import URLError
import PyPDF2
import io
import requests
import openai
from dotenv import load_dotenv
import os
from openai import OpenAI


load_dotenv()

client = OpenAI(api_key = os.environ.get("OPENAI_API_KEY"))

st.set_page_config(page_title="PaperFinder", page_icon="📄", layout="wide")

st.markdown("# PaperFinder")
st.sidebar.header("PaperFinder")
st.write(
    """Search, find and interact with papers from the arXiv repository."""
)

if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'selected_paper' not in st.session_state:
    st.session_state.selected_paper = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}

@st.cache_data
def get_arxiv_data(query, max_results=10, sort_by=arxiv.SortCriterion.Relevance):
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=sort_by
    )
    results =list(client.results(search))
    return results

@st.cache_data
def get_pdf_text(pdf_url):
    response = requests.get(pdf_url)
    pdf_file = io.BytesIO(response.content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def generate_summary(text):
    max_tokens = 4000
    truncated_text = text[:max_tokens]
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes academic papers."},
                {"role": "user", "content": f"Please provide a concise summary of the following academic paper for someone that is non-technical. Focus on the main ideas, methodology, and conclusions:\n\n{truncated_text}"}
            ],
            max_tokens=300,
            temperature=0.5 
        )
        
        summary = response.choices[0].message.content.strip()
        return summary
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Unable to generate summary at this time."

def get_citation(paper, style):
    authors = ', '.join([author.name for author in paper.authors])
    year = paper.published.year
    title = paper.title
    url = paper.entry_id

    if style == "APA":
        return f"{authors} ({year}). {title}. arXiv. {url}"
    elif style == "MLA":
        return f"{authors}. \"{title}.\" arXiv, {year}, {url}."
    elif style == "Chicago":
        return f"{authors}. \"{title}.\" arXiv ({year}). {url}."
    else:
        return f"Citation in {style} format is not implemented yet."

def display_paper_details(paper):
    st.write(f"## {paper.title}")
    st.write(f"**Authors:** {', '.join(author.name for author in paper.authors)}")
    st.write(f"**Published:** {paper.published.date()}")
    st.write(f"[Link to paper]({paper.pdf_url})")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary", "Abstract", "Citation", "PDF", "Chat"])
    
    with tab1:
        summary_key = f"summary_{paper.entry_id}"
        if summary_key not in st.session_state:
            st.session_state[summary_key] = ""
        st.write(st.session_state[summary_key])
        if st.button("Generate Summary", key=f"generate_{paper.entry_id}"):
            with st.spinner("Generating summary..."):
                pdf_text = get_pdf_text(paper.pdf_url)
                st.session_state[summary_key] = generate_summary(pdf_text)
            st.rerun()
    
    with tab2:
        st.write(paper.summary)
    
    with tab3:
        citation_format = st.selectbox("Citation Format", ["APA", "MLA", "Chicago", "Harvard", "IEEE", "BibTeX"], key=f"citation_{paper.entry_id}")
        citation = get_citation(paper, citation_format)
        st.text(citation)
        if st.button("Copy Citation", key=f"copy_{paper.entry_id}"):
            st.write("Citation copied to clipboard!")
    
    with tab4:
        st.write(f"<iframe src='{paper.pdf_url}' width='100%' height='600px'></iframe>", unsafe_allow_html=True)
    
    with tab5:
        chat_key = f"chat_{paper.entry_id}"
        if chat_key not in st.session_state.chat_history:
            st.session_state.chat_history[chat_key] = []

        for message in st.session_state.chat_history[chat_key]:
            st.write(f"{'You' if message['role'] == 'user' else 'Bot'}: {message['content']}")

        question = st.text_input("Ask a question about the paper:", key=f"question_input_{paper.entry_id}")
        if st.button("Send", key=f"send_{paper.entry_id}"):
            if question:
                st.session_state.chat_history[chat_key].append({"role": "user", "content": question})
                with st.spinner("Generating response..."):
                    pdf_text = get_pdf_text(paper.pdf_url)
                    try:
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant that answers questions about academic papers."},
                                {"role": "user", "content": f"Based on the following paper, please answer this question: {question}\n\nPaper content: {pdf_text[:4000]}"}
                            ],
                            max_tokens=500
                        )
                        ai_response = response.choices[0].message.content.strip()
                        st.session_state.chat_history[chat_key].append({"role": "assistant", "content": ai_response})
                    except Exception as e:
                        st.error(f"An error occurred while generating the response: {str(e)}")
                        st.session_state.chat_history[chat_key].append({"role": "assistant", "content": "Unable to generate response at this time."})
                st.rerun()
    
def main():

    with st.sidebar:
        st.header("Search Options")
        with st.form(key='search_form'):
            query = st.text_input("Enter search query:", "AI")
            sort_options = {
                "Relevance": arxiv.SortCriterion.Relevance,
                "Last Updated Date": arxiv.SortCriterion.LastUpdatedDate,
                "Submitted Date": arxiv.SortCriterion.SubmittedDate
            }
            sort_by = st.selectbox("Sort by", list(sort_options.keys()))
            max_results = st.slider("Number of results", 1, 50, 10)
            search_button = st.form_submit_button(label='Search')

        if search_button:
            with st.spinner("Searching..."):
                st.session_state.search_results = get_arxiv_data(query, max_results, sort_options[sort_by]) or []
            st.session_state.selected_paper = None

        if st.session_state.search_results:
            st.write("## Search Results")
            for i, paper in enumerate(st.session_state.search_results):
                color = ["#FFA07A", "#98FB98", "#87CEFA", "#DDA0DD", "#F0E68C"][i % 5]
                is_selected = st.session_state.selected_paper and st.session_state.selected_paper.entry_id == paper.entry_id
                
                tile_style = f"""
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    background-color: {color};
                    border-radius: 10px;
                    padding: 10px;
                    margin: 5px 0;
                    height: 150px;
                    width: 150px;
                    text-align: center;
                    cursor: pointer;
                    word-wrap: break-word;
                    overflow: hidden;
                    {'border: 3px solid #000;' if is_selected else ''}
                """
                
                if st.button(paper.title, key=f"paper_{i}", help=paper.title, use_container_width=True):
                    st.session_state.selected_paper = paper
                    st.rerun()

    if st.session_state.selected_paper:
        display_paper_details(st.session_state.selected_paper)
    else:
        st.write("Select a paper from the search results to view details.")

if __name__ == "__main__":
    main()
