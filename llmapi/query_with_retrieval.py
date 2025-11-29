import os
import sys
import json
import pickle
import faiss
import subprocess

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from sentence_transformers import SentenceTransformer

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

EMBED_MODEL_NAME = 'all-MiniLM-L6-v2'
TOP_K = 5

@csrf_exempt
def query_with_retrieval(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get("question", "").strip()
            company_name = data.get("company_name", "").strip()
            client_name = data.get("client_name", "").strip()

            if not question or not company_name or not client_name:
                return JsonResponse(
                    {"error": "Fields 'question', 'company_name', and 'client_name' are required."},
                    status=400
                )

            answer = ask_question(question, company_name, client_name)
            return JsonResponse({"answer": answer})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)


def get_top_chunks(query, company_name, client_name, top_k=TOP_K):
    """
    Search the FAISS index for a specific company and client.
    """
    model = SentenceTransformer(EMBED_MODEL_NAME)

    index_dir = os.path.join(settings.BASE_DIR, "media", "faiss_indexes", company_name, client_name)
    print(f"[DEBUG] Looking for index at: {index_dir}")
    index_path = os.path.join(index_dir, "index.faiss")
    chunks_path = os.path.join(index_dir, "metadata.pkl")  

    if not os.path.exists(index_path) or not os.path.exists(chunks_path):
        print(f"[ERROR] No index found at {index_dir}")
        return []

    index = faiss.read_index(index_path)
    with open(chunks_path, "rb") as f:
        metadata = pickle.load(f)

    query_vector = model.encode([query]).astype("float32")
    D, I = index.search(query_vector, top_k)

    chunks = []
    for dist, i in zip(D[0], I[0]):
        if i < len(metadata):
            chunks.append(metadata[i]['text'])

    return chunks


def format_prompt(chunks, question):
    context = "\n---\n".join(chunks)
    return f"""You are a helpful assistant. Use ONLY the following context to answer the question.

[BEGIN CONTEXT]
{context}
[END CONTEXT]

Question: {question}
Answer:"""


def ask_ollama(prompt):
    try:
        result = subprocess.run(
           ["ollama", "run", "llama3.2:1b"],
            input=prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return result.stdout.decode().strip()
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode().strip()
        print("Ollama Error:", err_msg)
        return f"Error during query processing: {err_msg}"
    except FileNotFoundError:
        return "Ollama not found. Make sure it's installed and in your PATH."


def ask_question(question, company_name, client_name):
    try:
        chunks = get_top_chunks(question, company_name, client_name)
        if not chunks:
            return "No relevant content found in documents."
        prompt = format_prompt(chunks, question)
        return ask_ollama(prompt)
    except Exception as e:
        return f"Error during query processing: {e}"


#  Optional CLI test
if __name__ == "__main__":
    q = input("Ask a question: ")
    company = input("Company name: ")
    client = input("Client name: ").strip()
    print(ask_question(q, company, client))
