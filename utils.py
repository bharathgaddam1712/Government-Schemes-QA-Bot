import os
import re
import time
import pandas as pd
from dotenv import load_dotenv

from huggingface_hub import login
from langchain_core.documents import Document
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_core.runnables import RunnableLambda


load_dotenv()



def clean_text(text):
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

def format_row_as_document(row, row_index):
    content = (
        f"Scheme Name: {clean_text(row['Scheme Name'])}\n"
        f"Ministries/Departments: {clean_text(row['Ministries/Departments'])}\n"
        f"Description & Benefits: {clean_text(row['Description & Benefits'])}\n"
        f"Tags: {clean_text(row['Tags'])}"
    )
    return Document(page_content=content, metadata={"row_index": row_index, "title": row.get("Scheme Name", f"Row {row_index}")})

def getTextSplitter():
    return RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

def create_chunks_from_csv(csv_path, state_filter=None):
    df = pd.read_csv(csv_path)

    if state_filter and state_filter != "-- All India --":
        df = df[df["Ministries/Departments"].str.contains(state_filter, case=False, na=False)]

    documents = []
    for idx, row in df.iterrows():
        doc = format_row_as_document(row, idx)
        documents.append(doc)

    return getTextSplitter().split_documents(documents)

def getEmbeddingModel():
    print("Initializing embedding model...")
    return FastEmbedEmbeddings()

def getLLM():
    print("Initializing LLM model...")
    return GoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=os.getenv("GOOGLE_API_KEY"))

def getPromptTemplate():
    print("Initializing prompt template...")
    return PromptTemplate(
        template="""
            You are a helpful AI assistant for answering questions about government schemes based on structured data.

            Use the following retrieved documents to answer user queries. Each document contains information from a row of the CSV file.

            - If the question is unrelated to government schemes, respond:
              *\"I’m here to assist with questions about government schemes only. Let me know if you have one!\"*

            - If the question relates to government schemes but you can't find an answer in the provided data, say:
              *\"That’s a great question, but I couldn’t find the answer in the available scheme data. You might want to explore more sources or official portals.\"*

            Keep responses:
            - Factual and clear
            - Easy to read
            - Without guessing or making up data

            ---
            Context:  
            {context}

            user: {question}
            Assistant:
        """,
        input_variables=["context", "question"],
    )

def getHyDEPrompt():
    return PromptTemplate(
        input_variables=["question"],
        template="""
You are an assistant knowledgeable in Indian government schemes.

Generate a hypothetical but realistic and informative answer to the following user question, as if you already had access to the correct information.

User Question:
{question}

Hypothetical Answer:
"""
    )

def get_hypothetical_answer(llm, question):
    hyde_prompt = getHyDEPrompt()
    chain = hyde_prompt | llm
    return chain.invoke({"question": question})

def hyde_retrieve(llm, vector_store, question):
    hypo_answer = get_hypothetical_answer(llm, question)
    retriever = vector_store.as_retriever()
    return retriever.get_relevant_documents(hypo_answer)

def hyde_rag_response(llm, vector_store, prompt_template, question):
    docs = hyde_retrieve(llm, vector_store, question)
    context = "\n\n".join([doc.page_content for doc in docs])
    final_prompt = prompt_template.format(context=context, question=question)
    return llm.invoke(final_prompt), docs

def add_documents_to_vector_store(vector_store, csv_files, state_filter=None):
    chunks = []
    for csv_file in csv_files:
        chunks.extend(create_chunks_from_csv(csv_file, state_filter))
    vector_store.add_documents(chunks)

def get_vector_store(pc_index_name, csv_files, state_filter=None):
    print("Initializing Pinecone vector store...")
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    embedding_model = getEmbeddingModel()
    index = pc.Index(pc_index_name)
    vector_store = PineconeVectorStore(index=index, embedding=embedding_model)

    if state_filter and state_filter != "-- All India --":
        print(f"Filtering data for: {state_filter}")
        vector_store.delete(delete_all=True)
        add_documents_to_vector_store(vector_store, csv_files, state_filter)

    return vector_store


### ----------- RESPONSE FORMATTER ----------- ###
def printResponse(response):
    print("\n=== Answer ===")
    print(response["result"])

    print("=== Source Documents ===")
    for doc in response["source_documents"]:
        print(f"\n{doc.metadata['title']} (Row {doc.metadata['row_index']}):")
        print(f"Document content: {doc.page_content}...")