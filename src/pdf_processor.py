"""
PDF Text Extraction Module

This module handles downloading and extracting text from PDF files,
with support for arXiv papers and local PDF files.
"""

import os
import requests
from typing import Optional, Dict
import pdfplumber
from pathlib import Path
import re


class PDFProcessor:
    """
    Handles PDF downloading and text extraction.
    
    Supports both downloading from URLs and processing local PDF files.
    """
    
    def __init__(self, download_dir: str = "data/pdfs"):
        """
        Initialize the PDF processor.
        
        Args:
            download_dir: Directory to store downloaded PDFs
        """
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
    
    def download_pdf(self, pdf_url: str, arxiv_id: str) -> Optional[str]:
        """
        Download a PDF from a URL.
        
        Args:
            pdf_url: URL to the PDF
            arxiv_id: arXiv ID for naming the file
        
        Returns:
            Local path to downloaded PDF, or None if failed
        """
        try:
            response = requests.get(pdf_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Create filename
            filename = f"{arxiv_id.replace('/', '_')}.pdf"
            filepath = os.path.join(self.download_dir, filename)
            
            # Download with progress
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"Downloaded PDF to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Failed to download PDF from {pdf_url}: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Extracted text, or None if failed
        """
        try:
            text_parts = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    # Extract text from page
                    page_text = page.extract_text()
                    
                    if page_text:
                        # Clean up the text
                        page_text = self._clean_text(page_text)
                        text_parts.append(page_text)
            
            full_text = "\n\n".join(text_parts)
            
            # Post-process to identify sections
            full_text = self._identify_sections(full_text)
            
            return full_text
            
        except Exception as e:
            print(f"Failed to extract text from {pdf_path}: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing common artifacts.
        
        Args:
            text: Raw extracted text
        
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common PDF artifacts
        text = re.sub(r'\f', '\n\n', text)  # Form feed
        text = re.sub(r'\x0c', '\n\n', text)  # Form feed alternative
        
        # Fix common OCR/extraction issues
        text = text.replace('ﬁ', 'fi')
        text = text.replace('ﬂ', 'fl')
        text = text.replace('ﬀ', 'ff')
        
        return text.strip()
    
    def _identify_sections(self, text: str) -> str:
        """
        Add section markers to help with parsing.
        
        Args:
            text: Extracted text
        
        Returns:
            Text with section markers
        """
        # Common section headers in academic papers
        section_patterns = [
            r'\bAbstract\b',
            r'\bIntroduction\b',
            r'\bRelated Work\b',
            r'\bBackground\b',
            r'\bMethodology\b',
            r'\bMethods\b',
            r'\bApproach\b',
            r'\bExperiments\b',
            r'\bExperimental Setup\b',
            r'\bResults\b',
            r'\bDiscussion\b',
            r'\bConclusion\b',
            r'\bConclusions\b',
            r'\bFuture Work\b',
            r'\bLimitations\b',
            r'\bReferences\b',
            r'\bAcknowledgments\b',
            r'\bAppendix\b'
        ]
        
        # Add section markers (make them stand out)
        for pattern in section_patterns:
            text = re.sub(
                pattern,
                lambda m: f"\n## {m.group(0)} ##\n",
                text,
                flags=re.IGNORECASE
            )
        
        return text
    
    def process_arxiv_paper(self, arxiv_id: str, pdf_url: str) -> Optional[Dict]:
        """
        Download and extract text from an arXiv paper.
        
        Args:
            arxiv_id: arXiv ID of the paper
            pdf_url: URL to the PDF
        
        Returns:
            Dictionary with 'pdf_path' and 'extracted_text', or None if failed
        """
        # Download PDF
        pdf_path = self.download_pdf(pdf_url, arxiv_id)
        if not pdf_path:
            return None
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return None
        
        return {
            'arxiv_id': arxiv_id,
            'pdf_path': pdf_path,
            'extracted_text': text,
            'text_length': len(text)
        }
    
    def process_local_pdf(self, pdf_path: str) -> Optional[Dict]:
        """
        Extract text from a local PDF file.
        
        Args:
            pdf_path: Path to local PDF file
        
        Returns:
            Dictionary with 'pdf_path' and 'extracted_text', or None if failed
        """
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return None
        
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return None
        
        return {
            'pdf_path': pdf_path,
            'extracted_text': text,
            'text_length': len(text)
        }
    
    def get_pdf_files_in_directory(self, directory: str) -> list:
        """
        Get all PDF files in a directory.
        
        Args:
            directory: Directory to search
        
        Returns:
            List of PDF file paths
        """
        pdf_dir = Path(directory)
        if not pdf_dir.exists():
            return []
        
        return list(pdf_dir.glob("*.pdf"))


def main():
    """Example usage of the PDF processor."""
    processor = PDFProcessor()
    
    # Example: Process a local PDF if it exists
    pdf_files = processor.get_pdf_files_in_directory("data/pdfs")
    
    if pdf_files:
        print(f"Found {len(pdf_files)} PDF files in data/pdfs/")
        for pdf_path in pdf_files:
            print(f"\nProcessing: {pdf_path}")
            result = processor.process_local_pdf(str(pdf_path))
            if result:
                print(f"Extracted {result['text_length']} characters")
                print(f"Preview: {result['extracted_text'][:500]}...")
    else:
        print("No PDF files found in data/pdfs/")
        print("To test PDF processing:")
        print("1. Place PDF files in data/pdfs/")
        print("2. Or use process_arxiv_paper() with an arXiv ID")


if __name__ == '__main__':
    main()
