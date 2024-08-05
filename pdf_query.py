# query pdf file in the terminal

import os
from langchain_astradb import AstraDBVectorStore
from langchain_community.llms import OpenAI
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from PyPDF2 import PdfReader
from datasets import load_dataset
from dotenv import load_dotenv
from typing_extensions import Concatenate

# LangChain components
from langchain.vectorstores.cassandra import Cassandra
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain_openai import OpenAI
# from langchain.embeddings import OpenAIEmbeddings

from datasets import load_dataset

import cassio


load_dotenv()

ASTRA_DB_APPLICATION_TOKEN = os.environ.get("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.environ.get("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_NAMESPACE = os.environ.get("ASTRA_DB_NAMESPACE")
ASTRA_DB_ID = os.environ.get("ASTRA_DB_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# pdf file/files.
pdfreader = PdfReader('Youtube-2.pdf')

# read text from pdf
raw_text = ''
for i, page in enumerate(pdfreader.pages):
    content = page.extract_text()
    if content:
        raw_text += content
        
print(raw_text)

# init connection to db
cassio.init(token=ASTRA_DB_APPLICATION_TOKEN, database_id=ASTRA_DB_ID)


# llm embeddings
llm = OpenAI(openai_api_key=OPENAI_API_KEY)
embedding = OpenAIEmbeddings()


# create vector store
vector_store = Cassandra(
    embedding=embedding,
    table_name="yt_qa",
    session=None,
    keyspace=None,
)

# text split such to avoid increased token size
text_splitter = CharacterTextSplitter(
    separator = "\n",
    chunk_size = 800,
    chunk_overlap  = 200,
    length_function = len,
)
texts = text_splitter.split_text(raw_text)

print(texts[:50])

# load data to vector store
vector_store.add_texts(texts[:50])

print("Inserted %i headlines." % len(texts[:50]))

astra_vector_index = VectorStoreIndexWrapper(vectorstore=vector_store)

# asking questions
first_question = True
while True:
    if first_question:
        query_text = input("\nEnter your question (or type 'quit' to exit): ").strip()
    else:
        query_text = input("\nWhat's your next question (or type 'quit' to exit): ").strip()

    if query_text.lower() == "quit":
        break

    if query_text == "":
        continue

    first_question = False

    print("\nQUESTION: \"%s\"" % query_text)
    answer = astra_vector_index.query(query_text, llm=llm).strip()
    print("ANSWER: \"%s\"\n" % answer)

    print("FIRST DOCUMENTS BY RELEVANCE:")
    for doc, score in vector_store.similarity_search_with_score(query_text, k=4):
        print("    [%0.4f] \"%s ...\"" % (score, doc.page_content[:84]))
        
