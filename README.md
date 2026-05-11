# FAQ Chatbot

This project implements a local RAG (Retrieval-Augmented Generation) chatbot for answering questions about ZHSF packages and other uploaded documents.

## Documentation

*   **[Git Workflow Guide](GIT_README.md)**: Instructions for the team on how to use Git, manage branches, and contribute to this repository.

## Quick Start

1.  **Clone the repo**:
    ```bash
    git clone <repo_url>
    cd faq
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**:
    ```bash
    streamlit run app.py
    ```

## Project Structure

*   `app.py`: Main Streamlit interface.
*   `rag_engine.py`: Core logic for retrieval and generation.
*   `docs/`: Directory for placing PDF documents.

