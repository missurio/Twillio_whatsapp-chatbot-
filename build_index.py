from rag_engine import load_and_index_docs

# Index all PDFs in the docs folder
result = load_and_index_docs("docs")
print(result)

