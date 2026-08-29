"""
Agent-Based Research Paper Summarizer

This module implements an intelligent agent that decomposes the paper summarization
task into sub-tasks, uses tools to analyze full paper content, and iteratively
refines summaries based on evidence.
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime
from dotenv import load_dotenv

# Try to import LLM clients, handle gracefully if not available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class AgentStep:
    """Represents a single step in the agent's reasoning process."""
    step_number: int
    task: str
    tool_used: str
    input_data: str
    output: str
    reasoning: str
    timestamp: str


class PaperSummarizerAgent:
    """
    An intelligent agent for research paper summarization.
    
    This agent decomposes the summarization task into structured sub-tasks:
    1. Paper structure analysis
    2. Methodology extraction
    3. Key findings identification
    4. Limitations and future work extraction
    5. Related work analysis
    6. Cross-paper connection synthesis
    7. Summary refinement
    
    Each step uses appropriate tools and iterates based on evidence.
    """
    
    def __init__(self, model_provider: str = "groq", model_name: str = "openai/gpt-oss-20b"):
        """
        Initialize the agent.
        
        Args:
            model_provider: Either "groq", "openai", or "anthropic"
            model_name: Specific model to use (e.g., "llama3-70b-8192", "gpt-4", "claude-3-opus")
        """
        # Load environment variables
        load_dotenv()
        
        self.model_provider = model_provider
        self.model_name = model_name
        self.trajectory: List[AgentStep] = []
        
        # Initialize the appropriate client
        if model_provider == "groq" and OPENAI_AVAILABLE:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        elif model_provider == "openai" and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.client = openai.OpenAI(api_key=api_key)
        elif model_provider == "anthropic" and ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Model provider {model_provider} not available or API key not set")
    
    def _log_step(self, task: str, tool_used: str, input_data: str, output: str, reasoning: str):
        """Log a step in the agent's trajectory."""
        step = AgentStep(
            step_number=len(self.trajectory) + 1,
            task=task,
            tool_used=tool_used,
            input_data=input_data[:500],  # Truncate for logging
            output=output[:500],
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )
        self.trajectory.append(step)
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """
        Call the LLM with the given prompt.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
        
        Returns:
            LLM response text
        """
        if self.model_provider in ["groq", "openai"]:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            return response.choices[0].message.content
        
        elif self.model_provider == "anthropic":
            response = self.client.messages.create(
                model=self.model_name,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unknown model provider: {self.model_provider}")
    
    def analyze_paper_structure(self, paper_text: str) -> Dict:
        """
        Step 1: Analyze the structure of the paper.
        
        Args:
            paper_text: Full text of the paper
        
        Returns:
            Dictionary with section boundaries and structure
        """
        system_prompt = "You are a research paper analyzer. Identify the main sections of the paper and their approximate locations."
        prompt = f"""Analyze the structure of this research paper. Identify the main sections (Introduction, Methodology, Experiments, Results, Discussion, Conclusion, Related Work, etc.) and their key content.

Paper text:
{paper_text[:4000]}

Return a JSON with this structure:
{{
    "sections": [
        {{"name": "Introduction", "start_approx": "beginning", "key_points": ["..."]}},
        ...
    ],
    "paper_type": "empirical/theoretical/survey",
    "main_contribution": "brief description"
}}"""
        
        response = self._call_llm(prompt, system_prompt)
        self._log_step(
            task="Analyze paper structure",
            tool_used="LLM analysis",
            input_data=paper_text[:500],
            output=response,
            reasoning="Understanding paper structure is essential for targeted extraction of information from specific sections."
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_response": response, "sections": []}
    
    def extract_methodology(self, paper_text: str, structure: Dict) -> str:
        """
        Step 2: Extract the methodology/approach.
        
        Args:
            paper_text: Full text of the paper
            structure: Paper structure from step 1
        
        Returns:
            Detailed methodology description
        """
        system_prompt = "You are an expert at extracting research methodology from academic papers."
        prompt = f"""Extract the methodology/approach from this research paper. Focus on:
1. The core method or framework proposed
2. Key algorithms or techniques used
3. Experimental setup
4. Datasets used
5. Evaluation metrics

Paper text:
{paper_text[:6000]}

Provide a clear, structured methodology description."""
        
        response = self._call_llm(prompt, system_prompt)
        self._log_step(
            task="Extract methodology",
            tool_used="LLM extraction",
            input_data=paper_text[:500],
            output=response,
            reasoning="Methodology extraction requires understanding the technical approach and experimental design."
        )
        
        return response
    
    def extract_key_findings(self, paper_text: str) -> str:
        """
        Step 3: Extract key findings and results.
        
        Args:
            paper_text: Full text of the paper
        
        Returns:
            Key findings description
        """
        system_prompt = "You are an expert at extracting research findings from academic papers."
        prompt = f"""Extract the key findings and results from this research paper. Focus on:
1. Main quantitative results
2. Statistical significance
3. Comparison with baselines or state-of-the-art
4. Ablation study results
5. Key insights from the results

Paper text:
{paper_text[:6000]}

Provide a clear, structured findings description."""
        
        response = self._call_llm(prompt, system_prompt)
        self._log_step(
            task="Extract key findings",
            tool_used="LLM extraction",
            input_data=paper_text[:500],
            output=response,
            reasoning="Key findings extraction requires identifying the most important results and their implications."
        )
        
        return response
    
    def extract_limitations(self, paper_text: str) -> str:
        """
        Step 4: Extract limitations and future work.
        
        Args:
            paper_text: Full text of the paper
        
        Returns:
            Limitations and future work description
        """
        system_prompt = "You are an expert at identifying research limitations."
        prompt = f"""Extract the limitations and future work from this research paper. Focus on:
1. Explicitly stated limitations
2. Assumptions that may not hold
3. Scope of the study
4. Potential biases
5. Suggested future work

Paper text:
{paper_text[:6000]}

Provide a clear, structured limitations description."""
        
        response = self._call_llm(prompt, system_prompt)
        self._log_step(
            task="Extract limitations",
            tool_used="LLM extraction",
            input_data=paper_text[:500],
            output=response,
            reasoning="Limitations are crucial for understanding the boundaries of the research's applicability."
        )
        
        return response
    
    def analyze_related_work(self, paper_text: str) -> str:
        """
        Step 5: Analyze related work and connections.
        
        Args:
            paper_text: Full text of the paper
        
        Returns:
            Related work analysis
        """
        system_prompt = "You are an expert at analyzing research literature and connections."
        prompt = f"""Analyze the related work and connections in this research paper. Focus on:
1. Key papers cited and their relationship
2. How this work differs from previous approaches
3. The research lineage and context
4. Open problems identified

Paper text:
{paper_text[:6000]}

Provide a clear, structured related work analysis."""
        
        response = self._call_llm(prompt, system_prompt)
        self._log_step(
            task="Analyze related work",
            tool_used="LLM analysis",
            input_data=paper_text[:500],
            output=response,
            reasoning="Understanding related work provides context for the paper's contribution and place in the literature."
        )
        
        return response
    
    def synthesize_summary(self, paper_data: Dict, methodology: str, findings: str, 
                          limitations: str, related_work: str) -> Dict:
        """
        Step 6: Synthesize all extracted information into a comprehensive summary.
        
        Args:
            paper_data: Original paper metadata
            methodology: Extracted methodology
            findings: Extracted key findings
            limitations: Extracted limitations
            related_work: Related work analysis
        
        Returns:
            Comprehensive summary dictionary
        """
        system_prompt = "You are an expert at synthesizing research paper summaries for literature reviews."
        prompt = f"""Synthesize a comprehensive summary for a literature review using the following extracted information:

Paper: {paper_data.get('title', '')}
Authors: {', '.join(paper_data.get('authors', []))}
Year: {paper_data.get('year', '')}

Methodology:
{methodology}

Key Findings:
{findings}

Limitations:
{limitations}

Related Work:
{related_work}

Create a structured summary with these sections:
1. One-sentence overview
2. Methodology (2-3 sentences)
3. Key Findings (2-3 sentences)
4. Limitations (1-2 sentences)
5. Relation to other work (1-2 sentences)

Make it concise and suitable for a literature review."""
        
        response = self._call_llm(prompt, system_prompt)
        self._log_step(
            task="Synthesize summary",
            tool_used="LLM synthesis",
            input_data=f"{methodology[:200]} {findings[:200]}",
            output=response,
            reasoning="Synthesis integrates all extracted information into a coherent summary suitable for literature reviews."
        )
        
        return {
            'summary': response,
            'methodology': methodology,
            'key_findings': findings,
            'limitations': limitations,
            'related_work': related_work,
            'paper_metadata': paper_data
        }
    
    def summarize_paper(self, paper_data: Dict, paper_text: str) -> Dict:
        """
        Main orchestration method that runs all agent steps.
        
        Args:
            paper_data: Paper metadata (title, authors, etc.)
            paper_text: Full text of the paper
        
        Returns:
            Comprehensive summary dictionary
        """
        self.trajectory = []  # Reset trajectory for new paper
        
        # Step 1: Analyze structure
        structure = self.analyze_paper_structure(paper_text)
        
        # Step 2: Extract methodology
        methodology = self.extract_methodology(paper_text, structure)
        
        # Step 3: Extract key findings
        findings = self.extract_key_findings(paper_text)
        
        # Step 4: Extract limitations
        limitations = self.extract_limitations(paper_text)
        
        # Step 5: Analyze related work
        related_work = self.analyze_related_work(paper_text)
        
        # Step 6: Synthesize summary
        summary = self.synthesize_summary(paper_data, methodology, findings, limitations, related_work)
        
        # Add trajectory to output
        summary['agent_trajectory'] = [
            {
                'step': step.step_number,
                'task': step.task,
                'tool': step.tool_used,
                'reasoning': step.reasoning
            }
            for step in self.trajectory
        ]
        
        return summary
    
    def get_trajectory(self) -> List[Dict]:
        """
        Get the agent's reasoning trajectory.
        
        Returns:
            List of trajectory steps
        """
        return [
            {
                'step': step.step_number,
                'task': step.task,
                'tool': step.tool_used,
                'input': step.input_data,
                'output': step.output,
                'reasoning': step.reasoning,
                'timestamp': step.timestamp
            }
            for step in self.trajectory
        ]


def main():
    """Example usage of the agent summarizer."""
    # Load environment variables
    load_dotenv()
    
    # Note: This requires API keys to be set
    sample_paper_text = """
    Introduction
    This paper presents a novel approach to machine learning...
    
    Methodology
    We propose a new architecture called Transformer...
    
    Experiments
    We evaluated on WMT translation tasks...
    
    Results
    Our model achieves 28.4 BLEU...
    
    Discussion
    The results show that attention mechanisms are sufficient...
    
    Conclusion
    We presented the Transformer architecture...
    """
    
    sample_paper_data = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani et al.'],
        'year': '2017',
        'arxiv_id': '1706.03762'
    }
    
    try:
        # Read model configuration from environment
        # Default to Groq if available, otherwise Anthropic, then OpenAI
        if os.getenv('GROQ_API_KEY'):
            model_provider = "groq"
            model_name = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')
        elif os.getenv('ANTHROPIC_API_KEY'):
            model_provider = "anthropic"
            model_name = os.getenv('ANTHROPIC_MODEL', 'claude-3-opus-20240229')
        elif os.getenv('OPENAI_API_KEY'):
            model_provider = "openai"
            model_name = os.getenv('OPENAI_MODEL', 'gpt-4')
        else:
            raise ValueError("No API key found in environment variables (GROQ_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY)")
        
        agent = PaperSummarizerAgent(model_provider=model_provider, model_name=model_name)
        summary = agent.summarize_paper(sample_paper_data, sample_paper_text)
        
        print("Agent Summary Generated")
        print(f"Summary: {summary['summary']}")
        print(f"\nTrajectory steps: {len(summary['agent_trajectory'])}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Note: This requires GROQ_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY environment variables")


if __name__ == '__main__':
    main()
