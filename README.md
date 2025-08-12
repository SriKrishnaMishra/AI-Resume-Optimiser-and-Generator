# AI Resume Optimiser and Generator

Repository: https://github.com/SriKrishnaMishra/AI-Resume-Optimiser-and-Generator

A Streamlit application that parses resumes, scores them against a target Job Description (JD), provides optimization suggestions (rule-based or via an optional LLM), and exports the improved resume to PDF or DOCX.

## Features
- Upload and parse resumes in TXT, PDF, or DOCX formats
- Extract basic fields (name, email, phone) from the resume
- ATS-style scoring against a JD
  - Exact keyword matches (driven by category keyword lists)
  - Semantic similarity via TF‑IDF cosine similarity
  - Category coverage breakdown
- Optimization
  - Rule-based optimization (always available)
  - Optional LLM optimization using Groq API if an API key is provided
- Export optimized resume to PDF or DOCX
- Download score report as JSON
- Sample resume and JD to try the workflow quickly

## Project structure
```
AI Resume Optimiser and Generator/
├─ README.md
├─ resume_optimizer/
│  ├─ app.py                       # Streamlit UI entry point
│  ├─ requirements.txt             # Python dependencies
│  ├─ static/
│  │  └─ style.css                 # Optional styling for the app
│  ├─ data/
│  │  └─ keywords/
│  │     └─ general.txt            # Example keyword list (extendable)
│  └─ utils/
│     ├─ parser.py                 # File parsing + field extraction
│     ├─ scorer.py                 # Keyword scoring + semantic similarity
│     ├─ semantic.py               # TF‑IDF vectorization helpers
│     ├─ optimizer.py              # Rule-based and LLM optimization
│     └─ exporter.py               # PDF/DOCX export utilities
└─ .venv/                          # (optional) local virtual environment
```

## Requirements
- Python 3.9+ (3.10+ recommended)
- pip

## Installation
You can use a virtual environment (recommended).

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r resume_optimizer/requirements.txt
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r resume_optimizer/requirements.txt
```

## Running the app
From the project root:

```bash
streamlit run resume_optimizer/app.py
```

Streamlit will start a local server (typically at http://localhost:8501).

## Optional: Enable LLM optimization (Groq)
LLM optimization is optional. If a Groq API key is set, the app will enable LLM-based resume improvement; otherwise it falls back to a rule-based optimizer.

- Environment variables:
  - `GROQ_API_KEY` (required to enable LLM optimization)
  - `GROQ_MODEL` (optional, defaults to `llama-3.1-8b-instant`)

Set the environment variable before launching the app or enter it in the app sidebar.

Windows (PowerShell):
```powershell
$env:GROQ_API_KEY = "your_api_key_here"
# optional
$env:GROQ_MODEL = "llama-3.1-8b-instant"
```

macOS/Linux:
```bash
export GROQ_API_KEY="your_api_key_here"
# optional
export GROQ_MODEL="llama-3.1-8b-instant"
```

## Usage workflow
1. Start the app and open it in your browser.
2. (Optional) In the sidebar, provide a Groq API key and toggle "Use LLM optimization" to enable LLM-based refinement.
3. Upload a resume (TXT, PDF, or DOCX) and paste the target job description.
4. Click "Score vs Job Description" to compute:
   - Overall score, exact keyword score, semantic similarity
   - Matched/missing keywords
   - Category coverage breakdown
5. Click "Optimise Resume" to produce an optimized resume (rule-based if no API key, or LLM-based if enabled).
6. Download the optimized resume as PDF or DOCX, and/or download the score report as JSON.
7. Use the "Load sample resume + JD" button to try the app quickly.

## Customizing keywords/categories
The scoring uses keyword lists stored under `resume_optimizer/data/keywords/`. Each `.txt` file corresponds to a category; the filename (without extension) becomes the category name (underscores are replaced with spaces and title-cased). Each non-empty line in the file should contain a keyword or phrase.

Example: `resume_optimizer/data/keywords/ml_engineering.txt`
```
python
pandas
numpy
tensorflow
pytorch
mlops
kubernetes
aws
```

The app automatically loads all `*.txt` files from this directory. If the directory is empty or missing, it falls back to a built-in General keyword set.

## Troubleshooting
- Streamlit not found: Ensure dependencies are installed via `pip install -r resume_optimizer/requirements.txt`.
- PDF text extraction issues: Some PDFs have complex layouts; if extraction fails or is incomplete, try uploading a TXT or DOCX version of the resume.
- DOCX parsing error: Ensure the file is a valid `.docx` (not `.doc`) file.
- Semantic similarity = 0: This can happen for very short texts or if TF‑IDF fails to build a vocabulary. Provide a richer JD/resume text.
- LLM optimization not active: Set `GROQ_API_KEY` (in the sidebar or as an environment variable). The app will fall back to rule-based optimization if no key is provided or if the API call fails.
- PDF export glyphs: The built-in PDF export uses a Latin-1 compatible font and will replace unsupported characters.

## Development notes
- The semantic similarity uses scikit-learn TF‑IDF with bigrams and cosine similarity.
- The optimizer prioritizes a concise structure with sections: Professional Summary, Key Skills, Experience (and optionally Education/Projects when present).
- The UI is built with Streamlit and a small custom stylesheet (`static/style.css`).

## License
No license specified.

## Acknowledgments
- Streamlit for the web UI
- scikit-learn for TF‑IDF/cosine similarity
- PyPDF2 and python-docx for file parsing
- fpdf2 and python-docx for export functionality
- Groq (optional) for LLM-based optimization
