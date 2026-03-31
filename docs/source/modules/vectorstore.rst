Vectorstore Module
=================

`vectorstore.py` handles chunking PDF text and tables, embedding them using Ollama embeddings, and storing in Chroma vectorstore for fast similarity search.

Functions
---------

- **build_vectorstore(job_id, pages)**

  Parses text and tables from PDF pages, splits into chunks, embeds, and stores in Chroma.

- **get_vectorstore(job_id)**

  Retrieves a previously saved Chroma vectorstore.

- **_table_to_text(table)**

  Converts a table (list of lists) into readable text for embedding.