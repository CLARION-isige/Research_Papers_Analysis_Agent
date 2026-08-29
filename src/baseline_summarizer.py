"""
Baseline Summarizer - Abstract-Only Summarization

This module implements a simple baseline that uses only the paper's abstract
to generate a summary. This serves as the comparison point for the agent-based
approach that analyzes the full paper.
"""

from typing import Dict, List, Optional
import re


class BaselineSummarizer:
    """
    A simple baseline summarizer that extracts and formats the abstract.
    
    This represents the minimal approach: using only the abstract without
    any deeper analysis of the full paper content.
    """
    
    def __init__(self):
        self.name = "Abstract-Only Baseline"
        self.description = "Uses only the paper abstract as the summary"
    
    def summarize(self, paper_data: Dict) -> Dict:
        """
        Generate a baseline summary using only the abstract.
        
        Args:
            paper_data: Dictionary containing paper information with keys:
                - title: Paper title
                - abstract: Paper abstract
                - authors: List of authors
                - year: Publication year
                - arxiv_id: arXiv identifier
        
        Returns:
            Dictionary containing:
                - summary: The abstract text
                - methodology: Extracted from abstract if present
                - key_findings: Extracted from abstract if present
                - limitations: Empty (not in abstract)
                - related_work: Empty (not in abstract)
        """
        abstract = paper_data.get('abstract', '')
        
        # Simple extraction based on common abstract patterns
        methodology = self._extract_methodology(abstract)
        key_findings = self._extract_key_findings(abstract)
        
        return {
            'summary': abstract,
            'methodology': methodology,
            'key_findings': key_findings,
            'limitations': "Not available in abstract-only baseline",
            'related_work': "Not available in abstract-only baseline",
            'paper_metadata': {
                'title': paper_data.get('title', ''),
                'authors': paper_data.get('authors', []),
                'year': paper_data.get('year', ''),
                'arxiv_id': paper_data.get('arxiv_id', '')
            }
        }
    
    def _extract_methodology(self, abstract: str) -> str:
        """
        Attempt to extract methodology from abstract using simple patterns.
        
        Args:
            abstract: The abstract text
        
        Returns:
            Extracted methodology or placeholder
        """
        # Look for methodology indicators
        methodology_patterns = [
            r'(?:We propose|We present|This paper proposes|This work presents|Our approach)[^.]*\.',
            r'(?:method|approach|technique|framework)[^.]*\.',
        ]
        
        for pattern in methodology_patterns:
            match = re.search(pattern, abstract, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Methodology not explicitly stated in abstract"
    
    def _extract_key_findings(self, abstract: str) -> str:
        """
        Attempt to extract key findings from abstract using simple patterns.
        
        Args:
            abstract: The abstract text
        
        Returns:
            Extracted findings or placeholder
        """
        # Look for findings indicators
        findings_patterns = [
            r'(?:Our results show|We demonstrate|We find|Experiments show)[^.]*\.',
            r'(?:achieves|improves|outperforms)[^.]*\.',
        ]
        
        for pattern in findings_patterns:
            match = re.search(pattern, abstract, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Key findings not explicitly stated in abstract"
    
    def summarize_batch(self, papers: List[Dict]) -> List[Dict]:
        """
        Summarize multiple papers.
        
        Args:
            papers: List of paper data dictionaries
        
        Returns:
            List of summary dictionaries
        """
        return [self.summarize(paper) for paper in papers]


def main():
    """Example usage of the baseline summarizer."""
    sample_paper = {
        'title': 'Attention Is All You Need',
        'abstract': 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms. Our model achieves state-of-the-art results on machine translation tasks.',
        'authors': ['Vaswani et al.'],
        'year': '2017',
        'arxiv_id': '1706.03762'
    }
    
    summarizer = BaselineSummarizer()
    summary = summarizer.summarize(sample_paper)
    
    print(f"Baseline Summary for: {summary['paper_metadata']['title']}")
    print(f"Methodology: {summary['methodology']}")
    print(f"Key Findings: {summary['key_findings']}")
    print(f"Full Summary: {summary['summary']}")


if __name__ == '__main__':
    main()
