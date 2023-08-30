# -*- coding: utf-8 -*-
"""Multi-Turn chatbot with multiple user interface.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1SScDVtT5hnaE3JgeGOOS5JLp__baEMq5
"""

pip install openai langchain pypdf chromadb tiktoken

import os
import json
import sqlite3
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

# Set up OpenAI API credentials
os.environ["OPENAI_API_KEY"] = "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"

# Load PDF document
pdf_file_path = 'DP1Merrill_Manual_en.pdf'
loader = PyPDFLoader(pdf_file_path)
documents = loader.load()

# Initialize SQLite database connection
conn = sqlite3.connect('user_conversations.db')
cursor = conn.cursor()

# Create table to store user conversations
cursor.execute('CREATE TABLE IF NOT EXISTS conversations (user_id TEXT PRIMARY KEY, history TEXT)')
conn.commit()

# Initialize LangChain components
k = 2
chain_type = 'map_reduce'
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_documents(documents)
embeddings = OpenAIEmbeddings()
db = Chroma.from_documents(texts, embeddings)
retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": k})
qa_chain = RetrievalQA.from_chain_type(llm=OpenAI(), chain_type=chain_type, retriever=retriever, return_source_documents=True)

def run_user_conversation(user_id):
    while True:
        user_input = input(f"{user_id}: ")

        if user_input.lower() == 'exit':
            print("Bot: Goodbye!")
            break

        # Retrieve user's conversation history from the database
        cursor.execute('SELECT history FROM conversations WHERE user_id=?', (user_id,))
        row = cursor.fetchone()
        user_history = json.loads(row[0]) if row else []

        # Prepare conversation and get results
        result = qa_chain({"query": user_input, "context": user_history})
        bot_response = result['result']

        # Update user's conversation history in the database
        user_history.append(user_input)
        user_history.append(bot_response)
        cursor.execute('INSERT OR REPLACE INTO conversations (user_id, history) VALUES (?, ?)', (user_id, json.dumps(user_history)))
        conn.commit()

        # Print bot's response
        print("Bot:", bot_response)

# Main loop
while True:
    user_id = input("Enter your user ID: ")
    if user_id.lower() == 'exit':
        break

    print(f"Bot: Hello {user_id}! Ask me anything or type 'exit' to end.")

    run_user_conversation(user_id)

# Close database connection
conn.close()
