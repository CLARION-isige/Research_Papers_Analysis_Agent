"""
Evaluation Framework for Research Paper Summarization

This module provides tools to evaluate both baseline and agent-based summarizers
against expert-generated summaries and various quality metrics.
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re

# Try to import ROUGE for automatic evaluation
try:
    from rouge import Rouge
    ROUGE_AVAILABLE = True
except ImportError:
    ROUGE_AVAILABLE = False


@dataclass
class EvaluationResult:
    """Stores evaluation results for a single paper."""
    paper_id: str
    paper_title: str
    baseline_rouge: Dict[str, float]
    agent_rouge: Dict[str, float]
    baseline_coverage: float
    agent_coverage: float
    baseline_accuracy: float
    agent_accuracy: float
    human_preference: Optional[str] = None  # "baseline", "agent", or "tie"


class SummarizationEvaluator:
    """
    Evaluates summarization quality using multiple metrics.
    
    Metrics include:
    1. ROUGE scores (automatic)
    2. Coverage of key information
    3. Accuracy of extracted information
    4. Human preference (when available)
    """
    
    def __init__(self, expert_summaries_path: Optional[str] = None):
        """
        Initialize the evaluator.
        
        Args:
            expert_summaries_path: Path to JSON file with expert-generated summaries
        """
        self.expert_summaries = {}
        if expert_summaries_path and os.path.exists(expert_summaries_path):
            self.load_expert_summaries(expert_summaries_path)
        
        self.rouge = Rouge() if ROUGE_AVAILABLE else None
    
    def load_expert_summaries(self, path: str):
        """
        Load expert-generated summaries from a JSON file.
        
        Expected format:
        {
            "arxiv_id": {
                "summary": "...",
                "methodology": "...",
                "key_findings": "...",
                "limitations": "...",
                "related_work": "..."
            }
        }
        """
        with open(path, 'r') as f:
            self.expert_summaries = json.load(f)
    
    def calculate_rouge(self, generated: str, reference: str) -> Dict[str, float]:
        """
        Calculate ROUGE scores between generated and reference summaries.
        
        Args:
            generated: Generated summary text
            reference: Reference (expert) summary text
        
        Returns:
            Dictionary with rouge-1, rouge-2, and rouge-l scores
        """
        if not ROUGE_AVAILABLE:
            return {"rouge-1": 0.0, "rouge-2": 0.0, "rouge-l": 0.0}
        
        try:
            scores = self.rouge.get_scores(generated, reference)[0]
            return {
                "rouge-1": scores['rouge-1']['f'],
                "rouge-2": scores['rouge-2']['f'],
                "rouge-l": scores['rouge-l']['f']
            }
        except:
            return {"rouge-1": 0.0, "rouge-2": 0.0, "rouge-l": 0.0}
    
    def calculate_coverage(self, generated: Dict, reference: Dict) -> float:
        """
        Calculate how well the generated summary covers key information.
        
        This checks if key concepts from the reference are present in the generated summary.
        
        Args:
            generated: Generated summary dictionary
            reference: Reference summary dictionary
        
        Returns:
            Coverage score between 0 and 1
        """
        key_fields = ['methodology', 'key_findings', 'limitations', 'related_work']
        coverage_scores = []
        
        for field in key_fields:
            gen_text = generated.get(field, '').lower()
            ref_text = reference.get(field, '').lower()
            
            # Extract key phrases (simple approach: words > 5 chars)
            ref_phrases = set(word for word in ref_text.split() if len(word) > 5)
            gen_phrases = set(word for word in gen_text.split() if len(word) > 5)
            
            if len(ref_phrases) > 0:
                overlap = len(ref_phrases & gen_phrases) / len(ref_phrases)
                coverage_scores.append(overlap)
            else:
                coverage_scores.append(0.0)
        
        return sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0.0
    
    def calculate_accuracy(self, generated: Dict, reference: Dict) -> float:
        """
        Calculate accuracy of extracted information.
        
        This checks if the generated summary contains factual errors
        by comparing key numerical values and claims.
        
        Args:
            generated: Generated summary dictionary
            reference: Reference summary dictionary
        
        Returns:
            Accuracy score between 0 and 1
        """
        # Extract numbers from both summaries
        def extract_numbers(text):
            return re.findall(r'\d+\.?\d*', text)
        
        key_fields = ['methodology', 'key_findings']
        accuracy_scores = []
        
        for field in key_fields:
            gen_numbers = set(extract_numbers(generated.get(field, '')))
            ref_numbers = set(extract_numbers(reference.get(field, '')))
            
            if len(ref_numbers) > 0:
                # Check if key numbers are present
                overlap = len(ref_numbers & gen_numbers) / len(ref_numbers)
                accuracy_scores.append(overlap)
            else:
                accuracy_scores.append(1.0)  # No numbers to check
        
        return sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 1.0
    
    def evaluate_paper(self, paper_id: str, baseline_summary: Dict, 
                      agent_summary: Dict) -> EvaluationResult:
        """
        Evaluate both baseline and agent summaries for a single paper.
        
        Args:
            paper_id: arXiv ID of the paper
            baseline_summary: Baseline summary dictionary
            agent_summary: Agent summary dictionary
        
        Returns:
            EvaluationResult with all metrics
        """
        expert_summary = self.expert_summaries.get(paper_id, {})
        
        # Calculate ROUGE scores
        baseline_rouge = self.calculate_rouge(
            baseline_summary.get('summary', ''),
            expert_summary.get('summary', baseline_summary.get('summary', ''))
        )
        
        agent_rouge = self.calculate_rouge(
            agent_summary.get('summary', ''),
            expert_summary.get('summary', agent_summary.get('summary', ''))
        )
        
        # Calculate coverage and accuracy
        if expert_summary:
            baseline_coverage = self.calculate_coverage(baseline_summary, expert_summary)
            agent_coverage = self.calculate_coverage(agent_summary, expert_summary)
            baseline_accuracy = self.calculate_accuracy(baseline_summary, expert_summary)
            agent_accuracy = self.calculate_accuracy(agent_summary, expert_summary)
        else:
            # If no expert summary, use heuristic evaluation
            baseline_coverage = len(baseline_summary.get('summary', '')) / 500  # Normalized by expected length
            agent_coverage = len(agent_summary.get('summary', '')) / 500
            baseline_accuracy = 0.5  # Default without ground truth
            agent_accuracy = 0.5
        
        return EvaluationResult(
            paper_id=paper_id,
            paper_title=baseline_summary.get('paper_metadata', {}).get('title', ''),
            baseline_rouge=baseline_rouge,
            agent_rouge=agent_rouge,
            baseline_coverage=baseline_coverage,
            agent_coverage=agent_coverage,
            baseline_accuracy=baseline_accuracy,
            agent_accuracy=agent_accuracy
        )
    
    def evaluate_batch(self, results: List[Tuple[str, Dict, Dict]]) -> List[EvaluationResult]:
        """
        Evaluate multiple papers.
        
        Args:
            results: List of (paper_id, baseline_summary, agent_summary) tuples
        
        Returns:
            List of EvaluationResult objects
        """
        return [
            self.evaluate_paper(paper_id, baseline, agent)
            for paper_id, baseline, agent in results
        ]
    
    def generate_report(self, evaluation_results: List[EvaluationResult]) -> str:
        """
        Generate a comprehensive evaluation report.
        
        Args:
            evaluation_results: List of EvaluationResult objects
        
        Returns:
            Formatted report string
        """
        if not evaluation_results:
            return "No evaluation results to report."
        
        # Calculate aggregate statistics
        avg_baseline_rouge1 = sum(r.baseline_rouge['rouge-1'] for r in evaluation_results) / len(evaluation_results)
        avg_agent_rouge1 = sum(r.agent_rouge['rouge-1'] for r in evaluation_results) / len(evaluation_results)
        
        avg_baseline_coverage = sum(r.baseline_coverage for r in evaluation_results) / len(evaluation_results)
        avg_agent_coverage = sum(r.agent_coverage for r in evaluation_results) / len(evaluation_results)
        
        avg_baseline_accuracy = sum(r.baseline_accuracy for r in evaluation_results) / len(evaluation_results)
        avg_agent_accuracy = sum(r.agent_accuracy for r in evaluation_results) / len(evaluation_results)
        
        report = []
        report.append("=" * 80)
        report.append("RESEARCH PAPER SUMMARIZATION EVALUATION REPORT")
        report.append("=" * 80)
        report.append(f"\nTotal papers evaluated: {len(evaluation_results)}")
        report.append("\n" + "-" * 80)
        report.append("AGGREGATE RESULTS")
        report.append("-" * 80)
        report.append(f"\nROUGE-1 Score:")
        report.append(f"  Baseline: {avg_baseline_rouge1:.4f}")
        report.append(f"  Agent:    {avg_agent_rouge1:.4f}")
        report.append(f"  Improvement: {avg_agent_rouge1 - avg_baseline_rouge1:.4f}")
        
        report.append(f"\nCoverage Score:")
        report.append(f"  Baseline: {avg_baseline_coverage:.4f}")
        report.append(f"  Agent:    {avg_agent_coverage:.4f}")
        report.append(f"  Improvement: {avg_agent_coverage - avg_baseline_coverage:.4f}")
        
        report.append(f"\nAccuracy Score:")
        report.append(f"  Baseline: {avg_baseline_accuracy:.4f}")
        report.append(f"  Agent:    {avg_agent_accuracy:.4f}")
        report.append(f"  Improvement: {avg_agent_accuracy - avg_baseline_accuracy:.4f}")
        
        report.append("\n" + "-" * 80)
        report.append("PER-PAPER RESULTS")
        report.append("-" * 80)
        
        for result in evaluation_results:
            report.append(f"\nPaper: {result.paper_title}")
            report.append(f"ID: {result.paper_id}")
            report.append(f"  Baseline ROUGE-1: {result.baseline_rouge['rouge-1']:.4f}")
            report.append(f"  Agent ROUGE-1:    {result.agent_rouge['rouge-1']:.4f}")
            report.append(f"  Baseline Coverage: {result.baseline_coverage:.4f}")
            report.append(f"  Agent Coverage:    {result.agent_coverage:.4f}")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
    
    def save_results(self, evaluation_results: List[EvaluationResult], output_path: str):
        """
        Save evaluation results to a JSON file.
        
        Args:
            evaluation_results: List of EvaluationResult objects
            output_path: Path to save the results
        """
        results_dict = [
            {
                'paper_id': r.paper_id,
                'paper_title': r.paper_title,
                'baseline_rouge': r.baseline_rouge,
                'agent_rouge': r.agent_rouge,
                'baseline_coverage': r.baseline_coverage,
                'agent_coverage': r.agent_coverage,
                'baseline_accuracy': r.baseline_accuracy,
                'agent_accuracy': r.agent_accuracy,
                'human_preference': r.human_preference
            }
            for r in evaluation_results
        ]
        
        with open(output_path, 'w') as f:
            json.dump(results_dict, f, indent=2)


def main():
    """Example usage of the evaluator."""
    # Create sample data
    sample_baseline = {
        'summary': 'This paper proposes a new method for machine learning.',
        'methodology': 'We use neural networks.',
        'key_findings': 'Our method achieves 95% accuracy.',
        'limitations': 'Not available in abstract-only baseline',
        'related_work': 'Not available in abstract-only baseline',
        'paper_metadata': {'title': 'Sample Paper', 'arxiv_id': '1234.5678'}
    }
    
    sample_agent = {
        'summary': 'This paper proposes a novel transformer-based architecture for machine learning tasks. The method achieves state-of-the-art results on multiple benchmarks.',
        'methodology': 'We propose a transformer architecture with attention mechanisms.',
        'key_findings': 'Our method achieves 95% accuracy on ImageNet and 92% on COCO.',
        'limitations': 'The method requires significant computational resources.',
        'related_work': 'This builds upon previous work in attention mechanisms.',
        'paper_metadata': {'title': 'Sample Paper', 'arxiv_id': '1234.5678'}
    }
    
    evaluator = SummarizationEvaluator()
    result = evaluator.evaluate_paper('1234.5678', sample_baseline, sample_agent)
    
    print("Evaluation Result:")
    print(f"Baseline ROUGE-1: {result.baseline_rouge['rouge-1']:.4f}")
    print(f"Agent ROUGE-1: {result.agent_rouge['rouge-1']:.4f}")
    print(f"Baseline Coverage: {result.baseline_coverage:.4f}")
    print(f"Agent Coverage: {result.agent_coverage:.4f}")


if __name__ == '__main__':
    main()
