# pdf_processor.py
from agents import function_tool
import fitz  # PyMuPDF
import os
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import chromadb

# Initialize components
pdf_embedder = None
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("pdf_documents")

def initialize_pdf_system():
    """Initialize the PDF processing system"""
    global pdf_embedder
    
    if pdf_embedder is None:
        try:
            pdf_embedder = SentenceTransformer('all-MiniLM-L6-v2')
            print("PDF embedding model loaded successfully")
            return True
        except Exception as e:
            print(f"Error loading PDF embedding model: {str(e)}")
            return False

@function_tool
def process_pdf(pdf_path: str):
    """
    Process a PDF document and store its content for later retrieval
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        A summary of the PDF content
    """
    if not os.path.exists(pdf_path):
        return f"Error: File {pdf_path} not found."
    
    try:
        # Initialize the system if not already done
        if not initialize_pdf_system():
            return "Could not initialize PDF processing system."
        
        # Extract text from PDF
        doc = fitz.open(pdf_path)
        text_chunks = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            # Split into smaller chunks if needed
            if len(text) > 500:
                # Simple splitting by paragraphs
                paragraphs = text.split('\n\n')
                text_chunks.extend([p for p in paragraphs if len(p.strip()) > 50])
            else:
                text_chunks.append(text)
        
        # Store in vector database
        for i, chunk in enumerate(text_chunks):
            # Generate embeddings
            embedding = pdf_embedder.encode(chunk).tolist()
            
            # Store in ChromaDB
            collection.add(
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{"source": pdf_path, "page": i // 5}],
                ids=[f"{os.path.basename(pdf_path)}_chunk_{i}"]
            )
        
        return f"Successfully processed PDF: {pdf_path}. Extracted {len(text_chunks)} text chunks."
    
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

@function_tool
def query_pdf_knowledge(query: str, top_k: int = 3):
    """
    Query the PDF knowledge base for information related to the query
    
    Args:
        query: The user's question
        top_k: Number of most relevant chunks to retrieve
    
    Returns:
        Relevant information from processed PDFs
    """
    try:
        # Initialize the system if not already done
        if not initialize_pdf_system():
            return "Could not initialize PDF processing system."
        
        # Generate query embedding
        query_embedding = pdf_embedder.encode(query).tolist()
        
        # Search in ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        if not results["documents"]:
            return "No relevant information found in the processed PDFs."
        
        # Format results
        context = "\n\n".join([f"Document chunk: {doc}" for doc in results["documents"][0]])
        
        return context
    
    except Exception as e:
        return f"Error querying PDF knowledge base: {str(e)}"
