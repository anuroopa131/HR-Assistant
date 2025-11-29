import os
import pickle
import faiss
import fitz  # PyMuPDF
import camelot
import tempfile
import time
from sentence_transformers import SentenceTransformer
import django
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 🔧 Normalize folder names to match actual storage format
def normalize_client_folder_name(name):
    return name.strip().replace(" ", "_")

def extract_tables_from_pdf(filepath):
    try:
        tables = camelot.read_pdf(filepath, pages='all', flavor='lattice')
        
        if tables:
            all_tables_text = []
            for table in tables:
                table_text = table.df.to_string(index=False, header=False)
                all_tables_text.append(table_text)
            return "\n\n[Extracted Tables]\n" + "\n\n".join(all_tables_text)
        else:
            return ""
    except Exception as e:
        print(f"[WARN] Table extraction failed for {filepath}: {e}")
        return ""

def load_pdfs(folder_path, skip_files=None):
    skip_files = skip_files or []
    texts = []
    for file in os.listdir(folder_path):
        if file.endswith(".pdf") and file not in skip_files:
            print(f"[INFO] Loading: {file}")
            filepath = os.path.join(folder_path, file)
            try:
                with fitz.open(filepath) as doc:
                    full_text = "\n".join([page.get_text() for page in doc])
            except Exception as e:
                print(f"[ERROR] Failed to read PDF '{file}': {e}")
                continue
            table_text = extract_tables_from_pdf(filepath)
            combined_text = full_text + "\n\n" + table_text
            texts.append((file, combined_text))
    cleanup_camelot_temp_files()
    return texts

def cleanup_camelot_temp_files(retries=3, delay=1):
    temp_dir = tempfile.gettempdir()
    for filename in os.listdir(temp_dir):
        if filename.startswith("page-") and filename.endswith(".pdf"):
            file_path = os.path.join(temp_dir, filename)
            for attempt in range(retries):
                try:
                    os.remove(file_path)
                    break
                except PermissionError:
                    if attempt < retries - 1:
                        time.sleep(delay)
                    else:
                        print(f"[WARN] Could not delete locked file after {retries} attempts: {filename}")

def chunk_text(text, max_length=500):
    import re
    sentences = re.split(r'(?<=[.?!])\s+', text)
    chunks = []
    current_chunk = ''
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += ' ' + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def build_index_incremental(documents_folder, company_name, client_name):
    print(f"[START] Building FAISS index for {company_name} → {client_name}")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # 🔐 Path where index + metadata will be saved
    client_index_dir = os.path.join(BASE_DIR, "media", "faiss_indexes", company_name, client_name)
    os.makedirs(client_index_dir, exist_ok=True)

    index_path = os.path.join(client_index_dir, "index.faiss")
    metadata_path = os.path.join(client_index_dir, "metadata.pkl")

    if os.path.exists(index_path) and os.path.exists(metadata_path):
        print("[INFO] Loading existing index and metadata...")
        index = faiss.read_index(index_path)
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
        indexed_files = set(item['source'] for item in metadata)
    else:
        print("[INFO] Creating new index...")
        index = None
        metadata = []
        indexed_files = set()

    texts = load_pdfs(documents_folder, skip_files=indexed_files)
    if not texts:
        print("[INFO] No new files found to index.")
        return
    else:
        print(f"[INFO] Found {len(texts)} new file(s) to embed.")

    all_chunks = []
    new_metadata = []

    for filename, text in texts:
        print(f"[INFO] Processing file: {filename}")
        contains_table = "[Extracted Tables]" in text
        chunks = chunk_text(text)
        for chunk in chunks:
            all_chunks.append(chunk)
            new_metadata.append({
                "source": filename,
                "text": chunk,
                "contains_table": contains_table
            })

    if not all_chunks:
        print("[WARN] No valid content chunks.")
        return

    print(f"[INFO] Encoding {len(all_chunks)} chunks...")
    embeddings = model.encode(all_chunks, show_progress_bar=True)

    if index is None:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)

    index.add(embeddings)
    metadata.extend(new_metadata)

    faiss.write_index(index, index_path)
    with open(metadata_path, "wb") as f:
        pickle.dump(metadata, f)

    print(f"[DONE] Index ready for {company_name} → {client_name} with {len(metadata)} total chunks.")

if __name__ == "__main__":
    sys.path.append(BASE_DIR)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')  
    django.setup()

    from clients.models import Company, Client

    company_name_input = input("Enter company name: ").strip()
    try:
        company = Company.objects.get(name=company_name_input)
    except Company.DoesNotExist:
        print(f"[ERROR] Company '{company_name_input}' not found.")
        exit()

    clients = Client.objects.filter(company=company)
    if not clients.exists():
        print(f"[INFO] No clients found under company '{company.name}'.")
        exit()

    for client in clients:
        print(f"\n[🔄] Indexing for client: {client.name}")
        normalized_client_folder = normalize_client_folder_name(client.name)
        client_folder = os.path.join(BASE_DIR, "media", "pdfs", company.name, normalized_client_folder)

        if not os.path.exists(client_folder):
            print(f"[SKIP] No PDF folder found at: {client_folder}")
            continue

        build_index_incremental(client_folder, company.name, client.name)
