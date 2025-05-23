"""
Script for running the pipeline.

This should:
- Load the data
- Clean the data
- Extract the text from the data and vectorize
- Set up a local vector DB if it doesn't already exist (else connect to it)
- Load the vectorized data into the vector DB (if it doesn't already exist)
- Run the LLM on the data
- Output the results
"""

# Standard imports
import json
import argparse
import shutil
import requests
import subprocess
from pathlib import Path

# Internal imports
from const import PATH_TO_DATA, SYSTEM_PROMPT_TEMPLATE
from config import LLM_MODEL
from data_handler import DataHandler
from chroma import ChromaDB

# Create an argument parser
parser = argparse.ArgumentParser(
    description="Run pipeline with command-line parameters."
)
parser.add_argument(
    "--clean_data",
    type=lambda x: x.lower() == "true",
    default=True,
    help="Whether to setup data (default: True)",
)
parser.add_argument(
    "--vectorize_data",
    type=lambda x: x.lower() == "true",
    default=True,
    help="Whether to vectorize data (default: True)",
)
args = parser.parse_args()

# See if None
if args is None:
    clean_data = True
    vectorize_data = True

# Use the argument
if args.clean_data:
    clean_data = True
else:
    clean_data = False

if args.vectorize_data:
    vectorize_data = True
else:
    vectorize_data = False


def run_LLM(clean_data: bool = True, vectorize_data: bool = True):
    """
    Function that runs the LLM.
    """
    datahandler = __traverse_data_pipeline(
        Path(PATH_TO_DATA), clean_data=clean_data, vectorize_data=vectorize_data
    )

    # Set up the local vector DB and add data to it
    vector_db = __set_up_local_vector_db(datahandler)

    # To verify this works search and print results
    # context = vector_db.search("Teach me about medullary thyroid cancer")
    # print("Context: ", context)

    # Get LLM ready and run it
    __set_up_and_run_LLM(vector_db)


def __traverse_data_pipeline(
    data_path: Path = Path(PATH_TO_DATA),
    clean_data: bool = True,
    vectorize_data: bool = True,
) -> DataHandler:
    """
    Function that traverses the data pipeline.

    Parameters:
    - data_path: str, path to the data

    Returns:
    - data_handler: DataHandler, the data handler object
    """
    # Load the data
    data_handler = DataHandler(data_path=data_path)

    # If we need to clean the data and save it then let's do that
    if clean_data:
        data_handler.load_data()
        data_handler.clean_data()

    # If we need to vectorize the data then let's do that
    if vectorize_data:
        data_handler.vectorize_data()
    else:
        data_handler.load_vectorized_data()

    return data_handler


def __set_up_local_vector_db(datahandler: DataHandler) -> ChromaDB:
    """
    Function that sets up a local vector DB if it doesn't already exist.
    """
    # Set up the local vector DB and add data to it
    vector_db = ChromaDB()
    vector_db.add_data(datahandler)

    return vector_db


def __get_llm():
    """
    Returns a function that sends a prompt to Ollama's local API using the specified model.
    Supports streaming output. Automatically pulls the model if not already downloaded.
    """

    # Check if Ollama is installed
    if shutil.which("ollama") is None:
        raise EnvironmentError(
            r'Ollama is not installed. Please install it from https://ollama.com/download. If installed, ensure it\'s in your PATH. You can do this with: $env:Path += ";C:\Users\<YourUsername>\AppData\Local\Programs\Ollama\" and restarting your computer.'
        )

    def ensure_model(model: str):
        try:
            # Check if model exists
            tags = requests.get("http://localhost:11434/api/tags").json()
            if model not in [m["name"] for m in tags.get("models", [])]:
                print(f"Model '{model}' not found locally. Pulling with ollama CLI...")
                subprocess.run(["ollama", "pull", model], check=True)
        except Exception as e:
            raise RuntimeError(
                f"Error downloading model '{model}': {e}\n\nPlease ensure Ollama is running and the model name is correct."
            )

    def llm(prompt: str, model=LLM_MODEL, host="http://localhost:11434"):
        ensure_model(model)

        try:
            print("LLM is preparing it's response...")
            with requests.post(
                f"{host}/api/generate",
                json={"model": model, "prompt": prompt, "stream": True},
                stream=True,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        data = json.loads(line)
                        yield data.get("response", "")
        except requests.exceptions.RequestException as e:
            print(f"Error contacting Ollama at {host}: {e}")
            yield "[LLM Error: Could not get a response]"

    return llm


def build_system_prompt(prompt: str, sources: list[tuple[str, str]]) -> str:
    formatted_sources = "\n\n".join(
        f"Source {name} says ...{content}..." for name, content in sources
    )
    return SYSTEM_PROMPT_TEMPLATE.format(
        prompt=prompt, formatted_sources=formatted_sources
    )


def __set_up_and_run_LLM(vector_db):
    """
    Function that sets up the LLM and queries a vector DB for context.
    """
    llm = __get_llm()
    response = None

    while True:
        query = input("Enter your question (or type 'q' to quit): ").strip()
        if query.lower() == "q":
            print("Exiting...")
            break

        # Get relevant source context from vector DB
        context_results = vector_db.search(query)

        for title, text in context_results.items():
            print(f"Source Name: {title.split('_', 1)[1]}")
            print(text)
            print("\n")

        # Ensure context is in list-of-tuples format
        if isinstance(context_results, dict):
            sources = [
                (title.split("_", 1)[1], text)
                for title, text in context_results.items()
            ]
        else:
            print("Invalid context format from vector DB. Expected list of dicts.")
            continue

        # Build the prompt
        prompt = build_system_prompt(query, sources)

        print(f"Prompt: {prompt}")

        # Get the LLM response (streaming)
        for chunk in llm(prompt):
            print(chunk, end="", flush=True)

        # Print sources that we pulled from the vector DB
        print("\n\nReferences pulled:")
        reference_list = [title.split("_", 1)[1] for title in context_results.keys()]
        references = list(set(reference_list))
        for ref in references:
            print(f"- {ref}")

        print("\n")  # new line after streaming completes

    return response


run_LLM(clean_data=clean_data, vectorize_data=vectorize_data)
