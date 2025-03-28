### ⚠️ Data Responsibility Disclaimer

By using this application, you acknowledge and accept that any text or image data submitted for translation or OCR — whether directly typed or captured via screen selection tools — may be transmitted to third-party services including Google Translate.

It is your sole responsibility to ensure that no confidential, sensitive, or personal data is sent to these external services. The developers of this application do not store or process your data and assume no liability for how third-party APIs handle submitted content.

Use of the application constitutes your consent to these terms.
<br><br><br><br>

---

## Live-Translate – Setup and Usage Guide

This early prototype performs basic OCR and translation using **Tesseract OCR** and **Google Translate**. The GUI supports selecting regions on screen and displaying translations with optional text-to-speech.

---

### Dependencies

#### Python Version

Tested with **Python 3.11.9**

#### Required Python Packages

Install the following using `pip`:

```bash
pip install customtkinter pygame pillow gtts googletrans==4.0.0-rc1 pytesseract screeninfo mss
```

---

### Tesseract OCR

This software requires Tesseract OCR to be installed. To ensure compatibility with all supported languages, follow these steps during installation:

1. Download the Tesseract OCR installer from either [UB Mannheim's Tesseract page](https://github.com/UB-Mannheim/tesseract/wiki) or [Tesseract's official GitHub page](https://github.com/tesseract-ocr/tesseract).
2. During installation, select the **Custom** installation option.
3. Enable the following components:
   - **Script Data:** Required for the app, contains non-Latin scripts (e.g., Chinese, Japanese, Arabic).
   - **Language Packs:** Select all available languages to maximise compatibility.
4. Complete the installation.

By default, the application assumes Tesseract OCR is installed at:  
`C:\Program Files\Tesseract-OCR\tesseract.exe`

If Tesseract OCR is installed in a different location, update the following line in `Main.py` to match your installation directory: (replacing the ".........")

```python
pytesseract.pytesseract.tesseract_cmd = r".........\Tesseract-OCR\tesseract.exe"
```

---

### Running the Application

- Launch the application by running `Main.py`:
  ```bash
  python Main.py
  ```

This will launch the GUI window where you can:

- Select a monitor and a region of the screen to capture text from
- Choose the source and target languages
- Display the translation on screen
- Optionally enable **text-to-speech**
- Optionally enable **Region Based Translation** on the OCR tab to display text in the same general layout it was captured in.

---

### OCR Translation (Snip Area Selection)

Use the "OCR Translation" tab to select a region of the screen to translate using **Tesseract OCR** and **Google Translate**. Supports input monitor and output monitor selection.

### Text Translation (Manual Input)

Use the "Text Translation" tab to enter your own text and get instant translations using **Google Translate**.

---

### Feedback

It will help tremendously with my project if you can provide feedback.
To provide feedback, click the **"Click here to give feedback"** link at the bottom of the app where you will be directed to a anonymous google form.
