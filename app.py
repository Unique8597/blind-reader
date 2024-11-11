import streamlit as st
from PIL import Image
import requests
import uuid
import os
import json
import time
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes

# Azure credentials
computervision_key ="fa0dc72138af4601b900910a5005261"
computervision_endpoint = "https://blindreader.cognitiveservices.azure.com/"
translator_key = "73a9eee458ce4ae7bf37761d3eea15f9"
translator_endpoint = "https://api.cognitive.microsofttranslator.com"
translator_location = "eastus"

# Initialize Azure clients
computervision_client = ComputerVisionClient(computervision_endpoint, CognitiveServicesCredentials(computervision_key))

# Set up the page title and layout
st.set_page_config(page_title="OCR Image to Text", layout="centered")

# Title of the app
st.title("Image to Text OCR App")

# Language selection
st.sidebar.header("Select Language")
language = st.sidebar.selectbox(
    "Choose the language for OCR",
    ("English", "Hausa", "Yoruba", "Igbo")
)

# Language mapping for translation
language_map = {
    "English": "en",
    "Hausa": "ha",
    "Yoruba": "yo",
    "Igbo": "ig"
}

# Upload image
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

def perform_ocr_on_image(image_path):
    """Perform OCR on the given image using Azure Computer Vision."""
    
    # Submit the image for OCR processing
    with open(image_path, 'rb') as image_stream:
        read_response = computervision_client.read_in_stream(image_stream, language='en', raw=True, reading_order='natural')
    
    # Extract the operation ID from the response headers
    read_operation_location = read_response.headers["Operation-Location"]
    operation_id = read_operation_location.split("/")[-1]
    
    # Poll the API for the result until it is ready
    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)
    
    # Extract and return the text from the OCR results
    extracted_text = ""
    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                extracted_text += line.text + " "
    return extracted_text.strip()

def translate_text(text, target_lang):
    """Translate text using Microsoft Translator Text API."""
    path = '/translate'
    constructed_url = translator_endpoint + path

    params = {
        'api-version': '3.0',
        'to': target_lang
    }

    headers = {
        'Ocp-Apim-Subscription-Key': translator_key,
        'Ocp-Apim-Subscription-Region': translator_location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{'text': text}]
    
    response = requests.post(constructed_url, params=params, headers=headers, json=body)
    response_json = response.json()
    
    translated_text = response_json[0]['translations'][0]['text']
    return translated_text

if uploaded_file is not None:
    # Save the uploaded image to a temporary file
    save_path = os.path.join(os.getcwd(), "uploaded_image.png")
    
    # Save the uploaded image to the current directory
    with open(save_path, "wb") as f:
        f.write(uploaded_file.read())
    
    # Open the temporary image file
    image = Image.open(save_path)
    
    # Display the uploaded image
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    # Perform OCR
    st.write("Performing OCR...")
    ocr_text = perform_ocr_on_image(save_path)
    
    # Translate the OCR text if not in English
    if language != "English":
        ocr_text = translate_text(ocr_text, language_map[language])
    
    # Display OCR text
    st.subheader("OCR Output:")
    st.text_area("Extracted Text", ocr_text, height=250)
    
    # Clean up temporary file

else:
    st.info("Please upload an image to proceed.")

# Footer
st.write("---")
st.write("Built with Streamlit and Azure Cognitive Services for OCR and translation.")
