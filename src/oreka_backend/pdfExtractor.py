import re
import os
import json
import time
import pymupdf as fitz
from mistralai import Mistral


class PDFExtractor:
    # Environment variables
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

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

    # Main function to extract and process PDF
    def extract_pdf_text(self, pdf_bytes: bytes) -> dict:
        """_summary_

        Args:
            pdf_bytes (bytes): pdf file in bytes

        Returns:
            dict: extracted information from the pdf in json format
        """
        text = self.extract_text_from_bytes(pdf_bytes)
        result = self.process_pdf_text(text)
        return json.loads(result)

    # Function to extract text from PDF bytes
    def extract_text_from_bytes(self, file_bytes: bytes) -> str:
        """_summary_

        Args:
            file_bytes (bytes): pdf file in bytes

        Returns:
            str: extracted text from the pdf
        """
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text

    # Function to process PDF text with Mistral API
    def process_pdf_text(self, pdf_stream: str) -> str:
        """_summary_

        Args:
            pdf_stream (str): extracted text from the pdf

        Returns:
            str: processed text in json format
        """
        with Mistral(
            api_key=self.MISTRAL_API_KEY,
        ) as mistral:
            for i in range(4):
                try:
                    res = mistral.chat.complete(
                        model="mistral-large-latest",
                        messages=[
                            {
                                "content": self.PROMPT.format(pdf_stream),
                                "role": "user",
                            }
                        ],
                        stream=False,
                    )
                    break
                except Exception as e:
                    if "capacity" in str(e).lower():
                        time.sleep(2 * (i + 1))  # exponential backoff
                    else:
                        raise
                    if i == 3:
                        raise e
        content = res.choices[0].message.content
        content = re.search(r"\{.*\}", content, flags=re.DOTALL).group(0)
        return content
    