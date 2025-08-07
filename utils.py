"""
Utility functions for document processing and text extraction
"""
import PyPDF2
from docx import Document
import streamlit as st
import re
from datetime import datetime, timedelta

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return ""

def extract_text_from_docx(docx_file):
    """Extract text from uploaded DOCX file"""
    try:
        doc = Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading DOCX: {str(e)}")
        return ""

def extract_text_from_txt(txt_file):
    """Extract text from uploaded TXT file"""
    try:
        text = str(txt_file.read(), "utf-8")
        return text
    except Exception as e:
        st.error(f"Error reading TXT: {str(e)}")
        return ""

def extract_document_text(uploaded_file):
    """Main function to extract text from any supported document type"""
    if uploaded_file is None:
        return ""
    
    file_type = uploaded_file.type
    
    if file_type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(uploaded_file)
    elif file_type == "text/plain":
        return extract_text_from_txt(uploaded_file)
    else:
        st.error("Unsupported file type!")
        return ""

def clean_text(text):
    """Clean and preprocess extracted text"""
    # Remove extra whitespace and newlines
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def calculate_finish_date(start_date, duration_days):
    """Calculate finish date based on start date and duration"""
    try:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        finish_date = start_date + timedelta(days=duration_days)
        return finish_date.strftime("%Y-%m-%d")
    except:
        return ""

def validate_project_data(df):
    """Validate project plan data"""
    required_columns = ['ID', 'Name', 'Active', 'Task Mode', 'Duration', 'Start', 'Finish']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"Missing required columns: {missing_columns}")
        return False
    
    return True