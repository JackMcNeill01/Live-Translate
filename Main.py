# Required pip installs:
# pip install customtkinter pygame pillow gtts googletrans==4.0.0-rc1 pytesseract screeninfo mss
import sys
from Gui import MainGui
from Translation import TranslationHandling
import pytesseract
# Replace with the path to your Tesseract-OCR installation
# For example, on Windows, the default installation path should be:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
def run_translation_mode():
    translator = TranslationHandling()
    # Check if parameters for translation have been provided:
    # e.g. python Main.py translate <language_choice> <text>
    if len(sys.argv) >= 4:
        language_choice = sys.argv[2]
        text = sys.argv[3]
        language_name, translated_text = translator.do_translation(language_choice, text)
        print(f"Translated text ({language_name}): {translated_text}")
    else:
        # Otherwise, run the interactive CLI mode
        translator.run_translation_cli()

if __name__ == '__main__':
    # Launch translation mode if the first argument is "translate"
    if len(sys.argv) > 1 and sys.argv[1] == "translate":
        run_translation_mode()
    else:
        app = MainGui()
        app.mainloop()