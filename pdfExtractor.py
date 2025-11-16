import pypdf
import io
import re
import os
import json
import time
from mistralai import Mistral
from appwrite.client import Client
from appwrite.services.storage import Storage

# Environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
BUCKET_ID = os.getenv("BUCKET_ID")
PROJECT_ID = os.getenv("PROJECT_ID")
APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT")
APPWRITE_API_KEY = os.getenv("API_KEY")

# Initialize Appwrite client and storage service
client = Client()
if APPWRITE_ENDPOINT:
    client.set_endpoint(APPWRITE_ENDPOINT)
if APPWRITE_API_KEY:
    client.set_key(APPWRITE_API_KEY)
if PROJECT_ID:
    client.set_project(PROJECT_ID)
storage = Storage(client)

# Define the prompt template
PROMPT = """Interprete the following text extracted from a pdf invoice and return a json objects with the following structure containing all the informations inside the text i provided you: 
            {{   
                "invoice number": "",
                "date": "",
                "items": [
                    {{
                        "item": "",
                        "unit price": "",
                        "quantity": "",
                        "total": ""
                    }}
                ],
                "subtotal": "",
                "tax (in percentage)": "",
                "amount due": ""
            }}. 
            The content field should contain the informations required in the json with maximum accuracy. Don't include any other text outside of the json object exactly as I described it in your response.
            The text is the following: {}
        """

# Function to extract text from PDF bytes
def extract_text_from_pdf(file_bytes: bytes) -> str:
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise TypeError("extract_text_from_pdf expects raw bytes from Appwrite storage")

    stream = io.BytesIO(file_bytes)
    reader = pypdf.PdfReader(stream)
    text = ''
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + '\n'
    return text

# Function to process PDF text with Mistral API
def process_pdf_text(pdf_stream: str) -> str:
    with Mistral(
        api_key=MISTRAL_API_KEY,
    ) as mistral:
        for i in range(4):
            try:
                res = mistral.chat.complete(
                    model="mistral-small-latest", 
                    messages=[{
                        "content": PROMPT.format(pdf_stream),
                        "role": "user",
                    }], 
                    stream=False)
                break
            except Exception as e:
                time.sleep(0.5 * i)
                if i == 3:
                    raise e
    content = res.choices[0].message.content
    content = re.search(r'\{.*\}', content, flags=re.DOTALL).group(0)
    return content    
    
# Main function to be called
def main(context):
    file_id = context.req.query.get("file_id")
    pdf_bytes = storage.get_file_download(BUCKET_ID,file_id)
    text = extract_text_from_pdf(pdf_bytes)
    result = process_pdf_text(text)
    result_json = json.loads(result)
    return context.res.json(result_json)