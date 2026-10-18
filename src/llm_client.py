import json
import os

from dotenv import load_dotenv

# LangChain integration for Google's Gemini models
from langchain_google_genai import ChatGoogleGenerativeAI

# LangChain integration for Groq models
from langchain_groq import ChatGroq


# Load variables from the .env file into the environment
load_dotenv()


def load_config(config_path: str = "config.json") -> dict:
    """
    Read config.json and return its contents as a Python dictionary.

    config_path: Path to the JSON configuration file.
    """
    with open(config_path, "r") as file:
        return json.load(file)


def get_llm():
    """
    Create and return the chat model selected in config.json.

    Supported providers:
        - Gemini
        - Groq
    """

    # Read the configuration file
    config = load_config()

    # Get the provider name and convert it to lowercase
    provider = config["provider"].lower()

    # If Gemini is selected, create a Gemini model
    if provider == "gemini":

        return ChatGoogleGenerativeAI(
            # Get model settings from the "gemini" section
            model=config["gemini"]["model"],
            max_tokens=config["gemini"]["max_tokens"],

            # Read the Gemini API key from .env
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )

    # If Groq is selected, create a Groq model
    elif provider == "groq":

        return ChatGroq(
            # Get model settings from the "groq" section
            model=config["groq"]["model"],
            temperature=config["groq"]["temperature"],
            max_tokens=config["groq"]["max_tokens"],

            # Read the Groq API key from .env
            api_key=os.getenv("GROQ_API_KEY"),
        )

    # If the provider is neither Gemini nor Groq, raise an error
    else:
        raise ValueError(f"Unsupported provider: {provider}")
