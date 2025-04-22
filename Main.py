"""
Below are the required pip installs for the project to run correctly:
pip install customtkinter pygame pillow gtts googletrans==4.0.0-rc1 pytesseract screeninfo mss opencv-python numpy google-cloud-vision python-Levenshtein psutil arabic-reshaper python-bidi requests
"""
from Gui import MainGui
import pytesseract

# This is the path to the Tesseract-OCR installation on your system. Make sure to adjust it if necessary.
# This is the default path for Windows installations. If you are using a different OS, you may need to adjust this path accordingly.
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Entry point of the entire application.
if __name__ == '__main__':
        app = MainGui()
        app.mainloop()