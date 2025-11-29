# HR Assistant — Multi-Tenant Document QA Chatbot

A smart, multi-tenant HR chatbot that allows companies to upload internal documents and enables users to ask questions strictly from the documents related to that specific company.  
The assistant uses local LLMs via Ollama, FAISS/Chroma vector search, and a full Django + React stack.



# Features

- Upload and manage company documents via an Admin HR portal.  
- Users can ask questions and get answers strictly based on uploaded documents (RAG pipeline).  
- Runs locally using Ollama with the Llama 3.2B model.  
- Uses text chunking + embeddings for accurate similarity search.  
- Vector database implemented using FAISS / ChromaDB.  
- Completely offline, private, and supports multi-client separation.  
- React frontend with real-time chat interface.  
- Django backend handles file uploads, embedding, indexing, and LLM querying.



# Installation Guide

## 1. Clone the Repository

```bash
git clone https://github.com/anuroopa131/HR-Assistant.git
cd HR-Assistant
```

---

# Backend Setup (Django)

## 2. Create & Activate Virtual Environment

```bash
python -m venv venv


### Windows
```bash
venv\Scripts\activate


### Linux/macOS
```bash
source venv/bin/activate


## 3. Install Requirements

Install FAISS:
```bash
pip install faiss-cpu


Install all backend dependencies:
```bash
pip install -r requirements.txt



# Ollama Setup

Download and install Ollama:  
https://ollama.com

Pull the Llama model:
```bash
ollama pull llama3.2


Ensure Ollama is running in the background.


# 4. Run the Django Backend

```bash
python manage.py runserver

Backend URL:  
http://127.0.0.1:8000


# Frontend Setup (React)

Navigate to frontend:
```bash
cd frontend
npm install
npm start


Frontend URL:  
http://localhost:3000


# Running the Full Project
1. Start Ollama  
2. Run Django backend  
3. Start React frontend  
4. Upload documents → embeddings generate automatically  
5. Start asking questions


#Demonstartion video:
https://drive.google.com/file/d/1AW2GNrn7SQL4XdryeZsgW8reZuKCyoRl/view?usp=sharing

# Performance Note
- CPU model inference: ~20–25 seconds per response  
- GPU inference: ~3–5 seconds per response  
- Large PDF embeddings may take time initially


# Potential Improvements
- Add user authentication (JWT/session).  
- Faster GPU-based model serving (vLLM / TGI).  
- Multi-language support.  
- Document version history.   
- OCR for scanned PDFs.  
- Cloud deployment.

