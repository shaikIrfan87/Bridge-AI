"""
Text Extractor Utility
Handles parsing of PDF and DOCX files to extract raw text.
"""

import re
from typing import Optional
from pypdf import PdfReader
from docx import Document
import io

class TextExtractor:
    """
    Extracts and cleans text from various file formats.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean extracted text:
        - Remove extra whitespace
        - Normalize line breaks
        - Remove non-printable characters
        """
        if not text:
            return ""
            
        # Replace multiple newlines with a single newline (to preserve section breaks roughly)
        # But first, replace multiple spaces with single space
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Replace 3 or more newlines with 2 (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Remove null bytes or control characters if any
        text = text.replace('\x00', '')
        
        return text

    @staticmethod
    def extract_from_pdf(file_path: str) -> str:
        """Extract text from a PDF file."""
        text_content = []
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
            
            full_text = "\n".join(text_content)
            return TextExtractor.clean_text(full_text)
        except Exception as e:
            raise ValueError(f"Failed to extract PDF text: {str(e)}")

    @staticmethod
    def extract_from_docx(file_path: str) -> str:
        """Extract text from a DOCX file."""
        try:
            doc = Document(file_path)
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text_content.append(paragraph.text)
            
            full_text = "\n".join(text_content)
            return TextExtractor.clean_text(full_text)
        except Exception as e:
            raise ValueError(f"Failed to extract DOCX text: {str(e)}")

    @staticmethod
    def extract_text(file_path: str, file_extension: str) -> str:
        """
        Main entry point for text extraction.
        """
        ext = file_extension.lower().replace('.', '')
        
        if ext == 'pdf':
            return TextExtractor.extract_from_pdf(file_path)
        elif ext == 'docx':
            return TextExtractor.extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format for text extraction: {ext}")
