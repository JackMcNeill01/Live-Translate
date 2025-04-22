> **Note for Examiners**: To view this file in Markdown Preview mode in Visual Studio Code:
>
> - Press `Ctrl+Shift+V` (Windows/Linux) or `Cmd+Shift+V` (Mac).
> - Alternatively, right-click the file tab and select **Open Preview**.

---

<br><br>

### ⚠️ Data Responsibility Disclaimer

By using this application, you acknowledge and accept that any text or image data submitted for translation or OCR — whether directly typed or captured via screen selection tools — may be transmitted to third-party services including Google Translate, Google Vision API, and DeepL API, depending on your selected configuration.

It is your sole responsibility to ensure that no confidential, sensitive, or personal data is sent to these external services. The developers of this application do not store or process your data and assume no liability for how third-party APIs handle submitted content.

Use of the application constitutes your consent to these terms.
<br><br><br><br>

---

### Live-Translate: Setup and Usage Guide

## This project allows you to perform OCR (Optical Character Recognition) and translate text using Google Vision OCR, Tesseract OCR, and translation services like Google Translate and DeepL.

---

### Dependencies

#### Python

This project was run and tested on python version 3.11.9

#### Required Python Packages

Install the following Python packages using `pip`:

```bash
pip install customtkinter pygame pillow gtts googletrans==4.0.0-rc1 pytesseract screeninfo mss opencv-python numpy google-cloud-vision python-Levenshtein psutil arabic-reshaper python-bidi requests
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

### Google Cloud Vision API

To use Google Vision OCR, you need to set up a Google Cloud API key:

1. **Create a Google Cloud Project**:

   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.

2. **Enable the Vision API**:

   - Navigate to **APIs & Services > Library**.
   - Search for "Vision API" and enable it for the project you just created.

3. **Generate an API Key**:

   - Go to **APIs & Services > Credentials**.
   - Click **Create Credentials** and select **API Key**.
   - Copy the generated API key.

4. **Add the API Key to the Project**:

   - Locate the `Creds_template.py` file in the project directory.
   - Make a copy of the file and rename it to `Creds.py`.
   - Open `Creds.py` and replace `YOUR_API_KEY_HERE` with your actual Google Vision API key:
     ```python
     google_vision_api_key = "YOUR_API_KEY_HERE"
     ```
   - Save the file.

5. **Quota and Pricing**:
   - Google Cloud provides **1000 free units per month** for Vision API usage. Each OCR request (image or page) consumes 1 unit, so this should be sufficient for most users.

---

### DeepL Translation

The use of DeepL instead of the default Google Translate can improve translations in most cases. However, the service requires an API key and is only free for the first **500,000 characters** provided you make an account.

#### Setting Up the DeepL API Key

1. Locate the `Creds_template.py` file in the project directory.
2. Make a copy of the file and rename it to `Creds.py`.
3. Open `Creds.py` and replace `YOUR_API_KEY_HERE` with your actual DeepL API key:
   ```python
   deepl_api_key = "YOUR_API_KEY_HERE"
   ```
4. Save the file.

**Important:** Do not share your `Creds.py` file or API key publicly.

---

### First-Time User Guide

1. **Install Dependencies**:

   - Ensure all required Python packages are installed using the `pip` command provided above.

2. **Set Up OCR and Translation Services**:

   - Install Tesseract OCR and configure its path in `Main.py`.
   - Set up the Google Vision API key in `Creds.py` if you plan to use Google Vision OCR.
   - Set up the DeepL API key in `Creds.py` if you plan to use DeepL for translations.

3. **Run the Application**:

   - Launch the application by running `Main.py`:
     ```bash
     python Main.py
     ```

4. **Using the GUI**:

   - **OCR Translation Tab**:
     - Select the input and output monitors.
     - Choose the source and target languages.
     - Use the "Select & Translate" button to capture a region and translate its text.
   - **Text Translation Tab**:
     - Enter text in the input box, select source and target languages, and click "Translate."

5. **Optional Features**:
   - Enable **Text-to-Speech (TTS)** to hear the translated text.
   - Use the **DeepL checkbox** for improved translations (if supported for the selected languages).
   - The pre-processing checkbox can improve translation accuracy in most cases (e.g., greyscaling the image first to improve OCR performance).

**The most common configurations you will have are:**

- **Tesseract OCR** → **Google Translate** → Single Block of Text Output (**Default**)
- **Tesseract OCR** → **Google Translate** → Output Paragraphs Relative to Their Capture Area (**Enable Region-Based Translation**)
- **Tesseract OCR** → **DeepL (Enable DeepL)** → Single Block of Text Output
- **Tesseract OCR** → **DeepL (Enable DeepL)** → Output Paragraphs Relative to Their Capture Area (**Enable Region-Based Translation**)
- **Google Vision (Enable Google Vision)** → **Google Translate** → Single Block of Text Output
- **Google Vision (Enable Google Vision)** → **Google Translate** → Output Paragraphs Relative to Their Capture Area (**Enable Region-Based Translation**)
- **Google Vision (Enable Google Vision)** → **DeepL (Enable DeepL)** → Single Block of Text Output
- **Google Vision (Enable Google Vision)** → **DeepL (Enable DeepL)** → Output Paragraphs Relative to Their Capture Area (**Enable Region-Based Translation**)

All of these also support text-to-speech and the selection of the translation input and output monitors.

## **Note:** Some languages may not be supported for DeepL, and the checkbox will be disabled when such languages are selected, forcing the use of Google Translate.

### Debugging and Logs

- **Debugging OCR**:
  - Debug images are saved to your desktop for inspection. You can try enabling and disabling pre-processing and checking the effect this has on the text you are trying to translate in these debug images.
- **Terminal Logs**:
  - Check the terminal logs for detailed debug information, such as API errors or OCR processing issues.

---

Enjoy using Live-Translate!
