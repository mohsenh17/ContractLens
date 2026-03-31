# ContractLens

ContractLens is a system for **automated compliance analysis of PDF contracts**.  
It parses PDF contracts, builds a vectorstore of their contents, and evaluates compliance using a language model (Ollama / llama3) with pre-defined rules. The system supports uploading contracts, checking processing status, and querying contract contents via a chat interface.

## Features

- PDF parsing and table extraction
- Vectorstore creation for fast semantic search
- Automated compliance analysis with LLM
- Job status tracking with Redis
- Chat interface to query contracts

## Getting Started

For installation instructions, requirements, API details, and usage examples, please visit the full documentation:

[Read the full documentation on ReadTheDocs](https://contractlens.readthedocs.io/)

## Project Structure
```
backend/ # Core backend modules: parser, analyzer, vectorstore, tasks, app
frontend/ # Web UI for file upload and chat
docs/ # Sphinx documentation
```