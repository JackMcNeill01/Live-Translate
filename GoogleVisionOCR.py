import base64
import requests
import io
from Creds import google_vision_api_key  # Import the API key from Creds.py

# Class for handling Google Vision OCR 
class GoogleVisionOCR:
    def __init__(self):
        """
        Initialise the Google Vision OCR using the API key from Creds.py.
        """
        self.api_key = google_vision_api_key

    def perform_ocr(self, image_path):
        """
        Perform OCR using Google Vision API with the API key.
        :param image_path: Path to the image file.
        :return: Dictionary with 'full_text' and 'paragraphs' (bounding boxes and text).
        """
        try:
            print(f"DEBUG: Starting OCR for image: {image_path}")

            # Load the image into memory
            with io.open(image_path, 'rb') as image_file:
                image_content = image_file.read()
            print(f"DEBUG: Image loaded successfully. Size: {len(image_content)} bytes")

            # Encode the image content in base64
            encoded_image_content = base64.b64encode(image_content).decode("utf-8")
            print(f"DEBUG: Image content encoded in base64.")

            # Prepare the request payload
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"
            payload = {
                "requests": [
                    {
                        "image": {"content": encoded_image_content},
                        "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],  # Uses DOCUMENT_TEXT_DETECTION for for better results
                    }
                ]
            }

            # Send the request to the Vision API
            response = requests.post(url, json=payload)
            print(f"DEBUG: Request sent to Google Vision API. Status code: {response.status_code}")
            response.raise_for_status()  # Raise an error for bad responses

            # Parse the response
            result = response.json()

            full_text_annotation = result.get("responses", [{}])[0].get("fullTextAnnotation", {})
            if not full_text_annotation:
                print("DEBUG: No structured text detected by Google Vision OCR.")
                return {"full_text": "", "paragraphs": []}

            # Extract full text
            full_text = full_text_annotation.get("text", "")
            print(f"DEBUG: Extracted full text: {full_text}")

            # Extract paragraphs with bounding boxes
            paragraphs = []
            for page in full_text_annotation.get("pages", []):
                for block in page.get("blocks", []):
                    for paragraph in block.get("paragraphs", []):
                        paragraph_text = ""
                        for word in paragraph.get("words", []):
                            word_text = "".join([symbol.get("text", "") for symbol in word.get("symbols", [])])
                            paragraph_text += word_text + " "
                        bounding_box = paragraph.get("boundingBox", {}).get("vertices", [])

                        # Convert bounding box vertices to x, y, width, height
                        if len(bounding_box) == 4:
                            x = bounding_box[0].get("x", 0)
                            y = bounding_box[0].get("y", 0)
                            width = bounding_box[2].get("x", 0) - x
                            height = bounding_box[2].get("y", 0) - y
                            paragraphs.append({
                                "text": paragraph_text.strip(),
                                "x": x,
                                "y": y,
                                "width": width,
                                "height": height
                            })

            print(f"DEBUG: Extracted {len(paragraphs)} paragraphs with bounding boxes.")
            return {"full_text": full_text, "paragraphs": paragraphs}

        except requests.exceptions.RequestException as req_error:
            print(f"DEBUG: Request error during Google Vision OCR: {req_error}")
            return {"full_text": "", "paragraphs": []}

        except Exception as e:
            print(f"DEBUG: General error during Google Vision OCR: {e}")
            return {"full_text": "", "paragraphs": []}