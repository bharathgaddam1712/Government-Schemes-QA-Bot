from langchain.chains import RetrievalQA
from utils import (
    get_vector_store,
    getLLM,
    getPromptTemplate,
    printResponse
)

# Define the vector store index and the CSV file to use
pc_index_name = "qa-assistant"
csv_files = ["Schemes.csv"]

# Initialize the vector store from the CSV
vector_store = get_vector_store(pc_index_name, csv_files)

# Initialize LLM and prompt template
llm = getLLM()
prompt_template = getPromptTemplate()

print("\nInitializing CSV-based RAG QA system...")

# Create the RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
    chain_type="stuff",
    return_source_documents=True,
    chain_type_kwargs={"prompt": prompt_template}
)

print("✅ RAG system initialized using Schemes.csv")

# Loop for Q&A
try:
    while True:
        query = input("\nAsk your question (Ctrl+C to exit): ")
        if query.strip():
            print("🔍 Processing...")
            response = qa_chain.invoke({"query": query})
            printResponse(response)
except KeyboardInterrupt:
    print("\n🛑 Exiting RAG assistant.")
