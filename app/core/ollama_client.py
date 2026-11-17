# app/core/ollama_client.py
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any

from app.core.config import (
    OLLAMA_BASE_URL,
    OLLAMA_LLM_MODEL,
    OLLAMA_EMBEDDING_MODEL,
    VECTOR_SIZE,
)

# The OllamaEmbeddingClient class is defined below, which is responsible for 
# generating text embeddings using the Ollama API.
class OllamaEmbeddingClient:
    """
    Client for generating text embeddings using Ollama.
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_EMBEDDING_MODEL,
        timeout: int = 60
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the supplied text.
        """

        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        url = f"{self.base_url}/api/embeddings"

        payload = {
            "model": self.model,
            "prompt": text
        }

        request_data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url=url,
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout
            ) as response:

                result = json.loads(
                    response.read().decode("utf-8")
                )

                embedding = result.get("embedding")

                if not embedding:
                    raise RuntimeError(
                        "Ollama returned an empty embedding."
                    )

                if len(embedding) != VECTOR_SIZE:
                    raise RuntimeError(
                        f"Expected {VECTOR_SIZE} dimensions, "
                        f"received {len(embedding)}."
                    )

                return embedding

        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Ollama embedding API error: {exc.code} - "
                f"{exc.read().decode('utf-8', errors='replace')}"
            ) from exc

        except urllib.error.URLError as exc:
            raise ConnectionError(
                f"Unable to connect to Ollama: {exc}"
            ) from exc

# The OllamaLLMClient class is defined below, which is responsible for 
# generating structured JSON responses using the Ollama LLM API. 
# It includes methods for sending prompts to the API and handling responses, 
# including error handling for various scenarios such as HTTP errors, 
# connection issues, and invalid JSON responses.
class OllamaLLMClient:
    """
    Client for generating structured responses using Ollama.
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_LLM_MODEL,
        timeout: int = 180
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a valid JSON response from an LLM.
        """

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2
            }
        }

        request_data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url=url,
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout
            ) as response:

                api_result = json.loads(
                    response.read().decode("utf-8")
                )

                generated_text = api_result.get("response")

                if not generated_text:
                    raise RuntimeError(
                        "Ollama returned an empty LLM response."
                    )

                result = json.loads(generated_text)

                if not isinstance(result, dict):
                    raise ValueError(
                        "LLM response must be a JSON object."
                    )

                return result

        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Ollama LLM API error: {exc.code} - "
                f"{exc.read().decode('utf-8', errors='replace')}"
            ) from exc

        except urllib.error.URLError as exc:
            raise ConnectionError(
                f"Unable to connect to Ollama: {exc}"
            ) from exc

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Ollama returned invalid JSON: {exc}"
            ) from exc


if __name__ == "__main__":

    embedding_client = OllamaEmbeddingClient()
    llm_client = OllamaLLMClient()

    sample_text = (
        "Database connection pool exhaustion "
        "caused production application failures."
    )

    vector = embedding_client.generate_embedding(sample_text)

    print("\nEmbedding generated successfully.")
    print(f"Model: {embedding_client.model}")
    print(f"Dimensions: {len(vector)}")

    test_prompt = """
    Return a JSON object with:
    {
        "status": "success",
        "message": "LLM generation is working"
    }
    """

    result = llm_client.generate_json(test_prompt)

    print("\nLLM generation successful.")
    print(f"Model: {llm_client.model}")
    print(json.dumps(result, indent=4))