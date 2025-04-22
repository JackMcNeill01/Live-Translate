import requests
from Creds import deepl_api_key  # Import the API key from Creds.py

# Class for handling DeepL translations
# Also includes a check for unsupported languages gotten from a separate helper program DeepLSupportedLanguages.py
class DeepLTranslation:
    def __init__(self):
        self.deepl_api_key = deepl_api_key  # Use the imported API key from Creds.py
        self.endpoint = "https://api-free.deepl.com/v2/translate"
        """
        List of languages that DeepL does not support.
        Gotten from a separate helper program DeepLSupportedLanguages.py I made that checks the DeepL API and
        compares the languages used in the program with the DeepL supported languages.
        """
        self.unsupported_languages = [
            'Hindi', 'Bengali', 'Vietnamese', 'Hebrew',
            'Thai', 'Malay', 'Filipino', 'Swahili'
        ]

    def is_language_supported(self, language_name):
        """
        Check if a language is supported by DeepL.
        :param language_name: The name of the language to check.
        :return: True if the language is supported, False otherwise.
        """
        return language_name not in self.unsupported_languages

    def translate_text(self, text, target_language):
        """
        Sends text to the DeepL API for translation and returns the translated text.
        :param text: The text to be translated.
        :param target_language: The name of the target language (e.g., "English").
        :return: Translated text as a string.
        """
        # Map the target language to the DeepL language code
        language_map = {
            'English': 'EN',
            'Spanish': 'ES',
            'French': 'FR',
            'German': 'DE',
            'Japanese': 'JA',
            'Korean': 'KO',
            'Russian': 'RU',
            'Italian': 'IT',
            'Portuguese': 'PT',
            'Dutch': 'NL',
            'Greek': 'EL',
            'Arabic': 'AR',
            'Turkish': 'TR',
            'Polish': 'PL',
            'Ukrainian': 'UK',
            'Swedish': 'SV',
            'Norwegian': 'NB',
            'Finnish': 'FI',
            'Danish': 'DA',
            'Hungarian': 'HU',
            'Czech': 'CS',
            'Romanian': 'RO',
            'Indonesian': 'ID',
            'Chinese (Simplified)': 'ZH',
        }
    
        # Get the DeepL language code for the target language
        deepl_language_code = language_map.get(target_language)
        if not deepl_language_code:
            print(f"DEBUG: Target language '{target_language}' is not supported by DeepL.")
            return None
    
        try:
            data = {
                "auth_key": self.deepl_api_key,
                "text": text,
                "target_lang": deepl_language_code,
            }
            print(f"DEBUG: Sending text to DeepL API for translation to {deepl_language_code}...")
            response = requests.post(self.endpoint, data=data)
    
            if response.status_code == 200:
                print("DEBUG: Text successfully translated by DeepL.")
                return response.json()["translations"][0]["text"]
            else:
                print(f"DEBUG: DeepL API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"DEBUG: Error during DeepL text translation: {e}")
            return None