# Research Paper Summarization for Literature Reviews

## Problem Statement

**Who has this problem?**

Researchers, graduate students, and academics conducting literature reviews face the challenge of processing an overwhelming volume of research papers. A single literature review may require analyzing hundreds of papers across multiple domains, with new publications appearing daily.

**What bottleneck makes it worth solving?**

The current bottleneck is the manual effort required to:
- Read and comprehend full research papers
- Extract key methodologies, findings, and limitations
- Identify connections between related work
- Synthesize information into coherent literature review summaries

Researchers spend approximately 80% of their time reading and processing papers, leaving only 20% for actual analysis and synthesis. This manual process is:
- **Time-consuming**: Reading a single technical paper can take 1-3 hours
- **Inconsistent**: Different researchers extract different information from the same paper
- **Error-prone**: Important details may be missed or misinterpreted
- **Unscalable**: Cannot keep up with the rate of new publications

**Why is solving this valuable?**

Automating research paper summarization would:
- **Accelerate research**: Reduce literature review time from weeks to days
- **Improve consistency**: Ensure systematic extraction of key information
- **Enhance coverage**: Enable processing of more papers in less time
- **Facilitate discovery**: Help identify connections and patterns across papers
- **Democratize access**: Make literature reviews feasible for researchers with limited time

## Solution Overview

This project implements an **agent-based research paper summarization system** that:

1. **Decomposes the summarization task** into structured sub-tasks:
   - Paper structure analysis
   - Methodology extraction
   - Key findings identification
   - Limitations and future work extraction
   - Related work analysis
   - Summary synthesis

2. **Uses appropriate tools** for each sub-task:
   - LLM-based analysis for text understanding
   - Structured extraction for specific information
   - Iterative refinement based on evidence

3. **Compares against a baseline**:
   - Baseline: Abstract-only summarization (current common practice)
   - Agent: Full paper analysis with structured extraction

4. **Provides measurable improvements**:
   - ROUGE scores for automatic evaluation
   - Coverage metrics for key information
   - Accuracy metrics for factual correctness
   - Human evaluation for quality assessment

## Project Structure

```
research_paper_summarizer/
├── README.md                          # This file
├── REPRODUCTION_GUIDE.md              # Step-by-step reproduction instructions
├── IMPROVEMENT_CHANGELOG.md           # Iteration history and evidence
├── generate_traces.py                 # Script to generate agent trajectories for submission
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
├── src/
│   ├── __init__.py
│   ├── baseline_summarizer.py         # Abstract-only baseline
│   ├── agent_summarizer.py            # Agent-based summarizer
│   ├── arxiv_fetcher.py               # arXiv paper fetching and PDF download
│   ├── pdf_processor.py               # PDF text extraction
│   └── evaluator.py                   # Evaluation framework
├── data/
│   ├── sample_papers.json             # Sample paper metadata
│   ├── pdfs/                          # Downloaded PDF files
│   └── expert_summaries.json          # Expert-generated summaries (optional)
├── outputs/
│   ├── baseline_summaries/            # Baseline output
│   └── agent_summaries/               # Agent output
├── logs/
│   └── agent_trajectories/            # Agent reasoning trajectories (for submission)
└── evaluations/
    └── results.json                   # Evaluation results
```

## Key Features

### Agent-Based Summarization

The agent follows a structured workflow:
1. **Analyze paper structure** - Identify sections and organization
2. **Extract methodology** - Understand the technical approach
3. **Extract key findings** - Identify main results and contributions
4. **Extract limitations** - Document constraints and future work
5. **Analyze related work** - Understand context and connections
6. **Synthesize summary** - Combine extracted information into coherent summary

Each step is logged with:
- Task description
- Tool used
- Input data
- Output
- Reasoning
- Timestamp

### Baseline Comparison

The baseline represents current common practice:
- Uses only the paper's abstract
- Simple pattern matching for methodology and findings
- No analysis of full paper content
- No related work or limitations extraction

### Evaluation Framework

Multiple evaluation metrics:
- **ROUGE scores**: Automatic text similarity with expert summaries
- **Coverage**: How well key information is captured
- **Accuracy**: Factual correctness of extracted information
- **Human preference**: Qualitative assessment by domain experts

## Intended User

**Primary users**: Researchers conducting literature reviews in computer science, machine learning, and related fields.

**Secondary users**: 
- Graduate students writing thesis literature reviews
- Research analysts tracking industry developments
- Academic librarians assisting researchers

**User's current bottleneck**: The user must manually read and process dozens to hundreds of papers, extracting and synthesizing information without systematic tools, leading to inconsistent coverage and significant time investment.

## Data Sources

- **Primary source**: arXiv.org preprint server (public, freely accessible)
- **Paper domains**: Computer science (cs.AI, cs.LG, cs.CL, cs.CV, etc.)
- **Data types**: Paper metadata, abstracts, and full PDF text
- **Sample size**: 10-50 papers for initial evaluation

All data is publicly available and does not require special permissions.

## PDF Processing

The system now supports full PDF text extraction:

### Automatic PDF Download
```python
from src.arxiv_fetcher import ArxivFetcher

fetcher = ArxivFetcher()
paper = fetcher.fetch_paper_with_full_text('1706.03762')
# PDF is downloaded to data/pdfs/ and text extracted automatically
```

### Local PDF Processing
```python
from src.pdf_processor import PDFProcessor

processor = PDFProcessor()
result = processor.process_local_pdf('data/pdfs/my_paper.pdf')
text = result['extracted_text']
```

### Priority Order for Text Sources
1. Local PDF in `data/pdfs/` (highest priority)
2. Download from arXiv URL
3. Abstract fallback (if PDF unavailable)

PDFs are automatically downloaded to `data/pdfs/` and cached for reuse.

## Ethical Considerations

- **Data usage**: Only public arXiv papers are used; no private or restricted content
- **Attribution**: All papers are properly cited with arXiv IDs and author information
- **Human oversight**: Final summaries should be reviewed by human researchers for critical applications
- **Limitations**: System may not capture all nuances; intended as an aid, not replacement for human analysis

## Dependencies

- Python 3.9+
- **Groq API (FREE - Recommended)** or OpenAI API or Anthropic API (for LLM-based analysis)
- Standard libraries: requests, beautifulsoup4, pandas, numpy
- Evaluation: rouge, nltk
- PDF processing: PyPDF2, pdfplumber

See `requirements.txt` for complete list.

## API Configuration

The system supports three LLM providers (priority order):

1. **Groq (FREE - Recommended)**
   - Get API key: https://console.groq.com/keys
   - Default model: openai/gpt-oss-20b
   - Set in `.env`: `GROQ_API_KEY=your_key`

2. **Anthropic (Paid)**
   - Get API key: https://console.anthropic.com/
   - Default model: claude-3-opus-20240229
   - Set in `.env`: `ANTHROPIC_API_KEY=your_key`

3. **OpenAI (Paid)**
   - Get API key: https://platform.openai.com/api-keys
   - Default model: gpt-4
   - Set in `.env`: `OPENAI_API_KEY=your_key`

The system automatically selects the first available API key in the order above.

## Expected Performance

Based on initial testing:
- **Speed**: ~2-5 minutes per paper (vs 1-3 hours manual)
- **Coverage**: 60-80% of key information (vs 40-60% for baseline)
- **Accuracy**: 70-85% factual correctness (vs 50-65% for baseline)
- **ROUGE-1**: 0.45-0.55 (vs 0.30-0.40 for baseline)

## Limitations and Failure Modes

**Known limitations**:
1. **PDF parsing**: Complex layouts (multi-column, equations) may not parse correctly
2. **Domain specificity**: Performance may vary across different research domains
3. **Recent papers**: Limited context for very recent work without citations
4. **Nuance**: May miss subtle contributions or novel insights

**Main failure mode**: The agent may hallucinate information not present in the paper, particularly when the paper structure is non-standard or when technical terminology is ambiguous.

**Mitigation**: 
- Human review of summaries before use
- Confidence scores for extracted information
- Clear indication when information is uncertain

## Future Work

- **Multi-paper synthesis**: Analyze connections across multiple papers
- **Citation graph analysis**: Understand influence and relationships
- **Domain adaptation**: Specialize for specific research areas
- **Interactive refinement**: Allow human feedback to improve summaries
- **Visualization**: Generate literature review graphs and timelines

## Citation

If you use this work, please cite:
```
Research Paper Summarization for Literature Reviews
Agentic Workflows Hackathon Submission
2024
```

## License

MIT License - See LICENSE file for details

## Contact

For questions or issues, please open an issue on the project repository.
