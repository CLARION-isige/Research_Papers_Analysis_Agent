"""
Research Paper Summarization for Literature Reviews

This package provides tools for automated research paper summarization,
including baseline and agent-based approaches.
"""

from .baseline_summarizer import BaselineSummarizer
from .agent_summarizer import PaperSummarizerAgent
from .arxiv_fetcher import ArxivFetcher
from .pdf_processor import PDFProcessor
from .evaluator import SummarizationEvaluator, EvaluationResult

__version__ = "0.3.0"
__all__ = [
    "BaselineSummarizer",
    "PaperSummarizerAgent",
    "ArxivFetcher",
    "PDFProcessor",
    "SummarizationEvaluator",
    "EvaluationResult"
]
