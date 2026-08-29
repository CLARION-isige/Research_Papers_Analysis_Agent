"""
Generate Agent Trajectories

This script runs the agent on sample papers and saves the trajectories
for submission.
"""

import sys
import os
import json
from datetime import datetime
sys.path.append('src')

from arxiv_fetcher import ArxivFetcher
from agent_summarizer import PaperSummarizerAgent
from baseline_summarizer import BaselineSummarizer
from pdf_processor import PDFProcessor


def generate_agent_trajectories():
    """
    Generate agent trajectories for sample papers and save them.
    
    """
    
    print("=" * 80)
    print("GENERATING AGENT TRAJECTORIES")
    print("=" * 80)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("\nERROR: No API key found!")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
        print("\nExample:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("\nOr create a .env file with the API key")
        return
    
    # Create output directory
    trajectory_dir = 'logs/agent_trajectories'
    os.makedirs(trajectory_dir, exist_ok=True)
    
    # Use sample papers from data
    with open('data/sample_papers.json', 'r') as f:
        sample_papers = json.load(f)
    
    papers = sample_papers['papers']
    print(f"\nProcessing {len(papers)} sample papers...")
    
    # Initialize PDF processor
    pdf_processor = PDFProcessor()
    
    # Check for local PDFs in data/pdfs
    local_pdfs = pdf_processor.get_pdf_files_in_directory("data/pdfs")
    if local_pdfs:
        print(f"\nFound {len(local_pdfs)} local PDF files in data/pdfs/")
        print("Will use local PDFs instead of downloading.")
    
    # Initialize arXiv fetcher for downloading PDFs if needed
    fetcher = ArxivFetcher()
    
    # Initialize agent
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
        print("ERROR: No API key found!")
        print("Please set GROQ_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY environment variable")
        return
    
    print(f"Using {model_provider} with model {model_name}")
    
    agent = PaperSummarizerAgent(model_provider=model_provider, model_name=model_name)
    
    # Process each paper
    for i, paper in enumerate(papers, 1):
        print(f"\n{'='*80}")
        print(f"Paper {i}/{len(papers)}: {paper['title']}")
        print(f"arXiv ID: {paper['arxiv_id']}")
        print(f"{'='*80}")
        
        # Try to get full text from PDF
        paper_text = None
        source = "abstract"
        
        # First, check for local PDF
        pdf_filename = f"{paper['arxiv_id'].replace('/', '_')}.pdf"
        local_pdf_path = f"data/pdfs/{pdf_filename}"
        
        if os.path.exists(local_pdf_path):
            print(f"Found local PDF: {local_pdf_path}")
            result = pdf_processor.process_local_pdf(local_pdf_path)
            if result:
                paper_text = result['extracted_text']
                source = "local PDF"
                print(f"Extracted {len(paper_text)} characters from PDF")
        
        # If no local PDF, try downloading from arXiv
        if not paper_text and paper.get('pdf_url'):
            print(f"Downloading PDF from arXiv...")
            paper_text = fetcher.extract_text_from_pdf_url(paper['pdf_url'], paper['arxiv_id'])
            if paper_text:
                source = "downloaded PDF"
                print(f"Extracted {len(paper_text)} characters from downloaded PDF")
        
        # Fallback to abstract if PDF processing fails
        if not paper_text:
            paper_text = f"""
            Title: {paper['title']}
            Authors: {', '.join(paper['authors'])}
            Abstract: {paper['abstract']}
            
            [Note: Full paper text not available. Using abstract as placeholder.
             Place PDF files in data/pdfs/ for full text processing.]
            """
            source = "abstract (fallback)"
            print(f"Using abstract as fallback (full text not available)")
        else:
            print(f"Using full text from {source}")
        
        try:
            # Run agent
            summary = agent.summarize_paper(paper, paper_text)
            
            # Save trajectory
            trajectory_data = {
                'paper_id': paper['arxiv_id'],
                'paper_title': paper['title'],
                'timestamp': datetime.now().isoformat(),
                'model_provider': model_provider,
                'model_name': model_name,
                'text_source': source,
                'text_length': len(paper_text),
                'trajectory': agent.get_trajectory(),
                'summary': summary['summary'],
                'methodology': summary['methodology'],
                'key_findings': summary['key_findings'],
                'limitations': summary['limitations'],
                'related_work': summary['related_work']
            }
            
            # Save to file
            trajectory_file = os.path.join(trajectory_dir, f"{paper['arxiv_id']}_trajectory.json")
            with open(trajectory_file, 'w') as f:
                json.dump(trajectory_data, f, indent=2)
            
            print(f"\n✓ Trajectory saved to: {trajectory_file}")
            print(f"  Steps executed: {len(agent.trajectory)}")
            
            # Print trajectory summary
            print("\n  Trajectory Steps:")
            for step in agent.trajectory:
                print(f"    {step.step_number}. {step.task}")
                print(f"       Tool: {step.tool_used}")
                print(f"       Reasoning: {step.reasoning}")
            
        except Exception as e:
            print(f"\n✗ Error processing paper: {e}")
            continue
    
    print(f"\n{'='*80}")
    print("TRAJECTORY GENERATION COMPLETE")
    print(f"{'='*80}")
    print(f"\nTrajectories saved to: {trajectory_dir}/")
    print("\nFiles generated:")
    for filename in os.listdir(trajectory_dir):
        if filename.endswith('_trajectory.json'):
            print(f"  - {filename}")
    
    print("\nThese trajectory files are ready")
    print("'Agent trajectories' deliverables ")


def generate_baseline_comparison():
    """
    Generate baseline summaries for comparison with agent trajectories.
    """
    print("\n" + "=" * 80)
    print("GENERATING BASELINE COMPARISON")
    print("=" * 80)
    
    # Load sample papers
    with open('data/sample_papers.json', 'r') as f:
        sample_papers = json.load(f)
    
    papers = sample_papers['papers']
    
    # Initialize baseline
    baseline = BaselineSummarizer()
    
    # Create output directory
    output_dir = 'outputs/baseline_summaries'
    os.makedirs(output_dir, exist_ok=True)
    
    for paper in papers:
        summary = baseline.summarize(paper)
        
        # Save baseline summary
        output_file = os.path.join(output_dir, f"{paper['arxiv_id']}_baseline.json")
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✓ Baseline saved: {output_file}")
    
    print(f"\nBaseline summaries saved to: {output_dir}/")


def main():
    """Main execution function."""
    
    # Generate baseline first (for comparison)
    generate_baseline_comparison()
    
    # Generate agent trajectories
    generate_agent_trajectories()
    
    print("\n" + "=" * 80)
    print("AGENT TRAJECTORY FILES READY")
    print("=" * 80)
    print("Agent trajectories (logs/agent_trajectories/*.json)")
    print("\nThe trajectory files show:")
    print("- Each step the agent took")
    print("- What tool was used")
    print("- Input and output data")
    print("- Reasoning for each decision")
    print("- Timestamps for reproducibility")


if __name__ == '__main__':
    main()
