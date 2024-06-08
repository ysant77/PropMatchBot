import google.generativeai as genai
import numpy as np
import os

google_api_key = os.environ['GOOGLE_API_KEY']
genai.configure(api_key=google_api_key)

def embed_text(text):
    return genai.embed_content("models/text-embedding-004", content=text)['embedding']
