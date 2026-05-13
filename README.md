# Document Intelligence — Lokale KI-Dokumentenanalyse

Automatically extracts structured information from business documents (invoices, contracts, quotes) using a **local LLM via Ollama**. No cloud, no API keys, no data leaving your network — GDPR-compliant by design.

## What it extracts

From any PDF business document:

| Field | Example |
|---|---|
| Document type | Invoice / Contract / Quote |
| Date | 2026-05-13 |
| Sender | Muster GmbH |
| Recipient | Kunde AG |
| Amounts | Net: 1.200 € / VAT: 228 € |
| Deadlines | Payment due: 30 days |
| Key information | [bullet list of important points] |
| Summary | 1–2 sentence digest |

## Two interfaces

### CLI — `extract.py`

```bash
python extract.py invoice.pdf
python extract.py contract.pdf --model llama3.1:8b
python extract.py document.pdf --json > output.json
```

### Web UI — `app.py`

```bash
streamlit run app.py
```

Upload any PDF → click analyze → get structured results in your browser.

## Tech Stack

| Component | Tool |
|---|---|
| PDF extraction | pdfplumber |
| LLM | Ollama (llama3.2, local) |
| Structured output | JSON via prompt engineering |
| Web UI | Streamlit |

## Setup

### 1. Install Ollama + model

```bash
# Install Ollama: https://ollama.ai
ollama pull llama3.2
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
# CLI
python extract.py your_document.pdf

# Web UI
streamlit run app.py
```

## Why local?

Many business documents contain sensitive data: payment terms, personal information, confidential agreements. This tool processes everything locally — ideal for:

- **SMEs** handling customer contracts and invoices
- **Legal/HR departments** with confidentiality requirements
- **Any GDPR-regulated environment**

## Use cases for SMEs

- Automatic invoice capture (extract amount, date, vendor → bookkeeping)
- Contract overview (parties, deadlines, key clauses at a glance)
- Quote comparison (structured extraction of multiple quotes)
- Document routing (classify incoming mail by type)

## Agentic Extension (Roadmap)

This project lays the foundation for a fully **agentic document workflow**:
- Agent monitors an email inbox or folder
- Classifies and extracts document data automatically  
- Triggers follow-up actions (create task, send confirmation, update spreadsheet)

Technologies on the radar: Claude Computer Use, Browser-based AI agents, Open Interpreter.

## Author

**Robert Legatzki** — Data Scientist & KI-Automatisierer  
[LinkedIn](https://linkedin.com/in/robert-legatzki-19648b13) · [GitHub](https://github.com/robciu22) · contact@ai-processintelligence.com
