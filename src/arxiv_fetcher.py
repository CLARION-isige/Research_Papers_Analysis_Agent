"""
arXiv Paper Fetcher

This module handles fetching research papers from arXiv, including metadata
and full text content. Uses the arXiv API for metadata and PDF processing
for full text extraction.
"""

import requests
import time
from typing import Dict, List, Optional
import re
from urllib.parse import quote
import xml.etree.ElementTree as ET
from pdf_processor import PDFProcessor


class ArxivFetcher:
    """
    Fetches research papers from arXiv using their public API.
    
    Handles both metadata retrieval and PDF text extraction.
    """
    
    BASE_URL = "http://export.arxiv.org/api/query"
    PDF_BASE_URL = "https://arxiv.org/pdf/"
    
    def __init__(self, delay: float = 3.0, download_dir: str = "data/pdfs"):
        """
        Initialize the fetcher.
        
        Args:
            delay: Delay between requests to respect rate limits (seconds)
            download_dir: Directory to store downloaded PDFs
        """
        self.delay = delay
        self.last_request_time = 0
        self.pdf_processor = PDFProcessor(download_dir=download_dir)
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.delay:
            time.sleep(self.delay - time_since_last)
        self.last_request_time = time.time()
    
    def search_by_query(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search arXiv papers using a query string.
        
        Args:
            query: Search query (e.g., "machine learning", "cat:cs.AI")
            max_results: Maximum number of results to return
        
        Returns:
            List of paper metadata dictionaries
        """
        self._rate_limit()
        
        params = {
            'search_query': query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        
        return self._parse_arxiv_response(response.text)
    
    def fetch_by_ids(self, arxiv_ids: List[str]) -> List[Dict]:
        """
        Fetch specific papers by their arXiv IDs.
        
        Args:
            arxiv_ids: List of arXiv IDs (e.g., ["1706.03762", "1810.04805"])
        
        Returns:
            List of paper metadata dictionaries
        """
        self._rate_limit()
        
        id_list = " OR ".join([f"id:{aid}" for aid in arxiv_ids])
        params = {
            'search_query': id_list,
            'start': 0,
            'max_results': len(arxiv_ids)
        }
        
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        
        return self._parse_arxiv_response(response.text)
    
    def _parse_arxiv_response(self, xml_response: str) -> List[Dict]:
        """
        Parse arXiv API XML response into paper dictionaries.
        
        Args:
            xml_response: XML string from arXiv API
        
        Returns:
            List of paper dictionaries
        """
        papers = []
        root = ET.fromstring(xml_response)
        
        # Define namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom',
              'arxiv': 'http://arxiv.org/schemas/atom'}
        
        for entry in root.findall('atom:entry', ns):
            # Extract arXiv ID from URL
            id_url = entry.find('atom:id', ns).text
            arxiv_id = id_url.split('/')[-1]
            
            # Extract title
            title = entry.find('atom:title', ns).text.strip()
            
            # Extract abstract
            abstract = entry.find('atom:summary', ns).text.strip()
            
            # Extract authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns).text
                authors.append(name)
            
            # Extract publication date
            published = entry.find('atom:published', ns).text
            year = published.split('-')[0]
            
            # Extract categories
            categories = []
            for category in entry.findall('atom:category', ns):
                categories.append(category.get('term'))
            
            # Extract PDF URL
            pdf_url = f"{self.PDF_BASE_URL}{arxiv_id}.pdf"
            
            papers.append({
                'arxiv_id': arxiv_id,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'year': year,
                'published': published,
                'categories': categories,
                'pdf_url': pdf_url,
                'id_url': id_url
            })
        
        return papers
    
    def extract_text_from_pdf_url(self, pdf_url: str, arxiv_id: str) -> Optional[str]:
        """
        Extract text from a PDF URL by downloading and processing.
        
        Args:
            pdf_url: URL to the PDF
            arxiv_id: arXiv ID for naming the downloaded file
        
        Returns:
            Extracted text or None if extraction fails
        """
        result = self.pdf_processor.process_arxiv_paper(arxiv_id, pdf_url)
        if result:
            return result['extracted_text']
        return None
    
    def fetch_paper_with_full_text(self, arxiv_id: str) -> Optional[Dict]:
        """
        Fetch paper metadata and download/extract full PDF text.
        
        Args:
            arxiv_id: arXiv ID of the paper
        
        Returns:
            Dictionary with metadata and full text, or None if failed
        """
        # Fetch metadata
        papers = self.fetch_by_ids([arxiv_id])
        if not papers:
            return None
        
        paper = papers[0]
        
        # Download and extract PDF text
        full_text = self.extract_text_from_pdf_url(paper['pdf_url'], arxiv_id)
        
        if full_text:
            paper['full_text'] = full_text
            paper['has_full_text'] = True
        else:
            paper['full_text'] = paper['abstract']  # Fallback to abstract
            paper['has_full_text'] = False
        
        return paper
    
    def get_recent_papers(self, category: str = "cs.AI", days: int = 7, max_results: int = 10) -> List[Dict]:
        """
        Get recent papers from a specific category.
        
        Args:
            category: arXiv category (e.g., "cs.AI", "cs.LG", "stat.ML")
            days: Number of recent days to search
            max_results: Maximum number of results
        
        Returns:
            List of recent paper dictionaries
        """
        # arXiv doesn't have a direct date filter, so we search by category
        # and sort by date
        query = f"cat:{category}"
        papers = self.search_by_query(query, max_results=max_results)
        
        # Filter by recent date (approximate)
        # Note: This is a simplified approach
        return papers[:max_results]


def main():
    """Example usage of the arXiv fetcher."""
    fetcher = ArxivFetcher()
    
    # Search for recent machine learning papers
    print("Searching for recent machine learning papers...")
    papers = fetcher.search_by_query("machine learning", max_results=3)
    
    for paper in papers:
        print(f"\nTitle: {paper['title']}")
        print(f"arXiv ID: {paper['arxiv_id']}")
        print(f"Authors: {', '.join(paper['authors'][:3])}")
        print(f"Year: {paper['year']}")
        print(f"Abstract: {paper['abstract'][:200]}...")


if __name__ == '__main__':
    main()
