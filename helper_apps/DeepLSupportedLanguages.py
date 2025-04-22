import sys
import os
import requests
# Adds the parent directory to sys.path since the script is in a subdirectory helper_apps so that it can import modules from the main directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Creds import deepl_api_key  # Import the API key from Creds.py

# DeepL API endpoint for fetching supported languages
deepl_languages_endpoint = "https://api-free.deepl.com/v2/languages"

# The 32 languages that the app currently supports
current_languages = {
    'English': 'en',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Chinese (Simplified)': 'zh-cn',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Russian': 'ru',
    'Italian': 'it',
    'Portuguese': 'pt',
    'Dutch': 'nl',
    'Greek': 'el',
    'Arabic': 'ar',
    'Hindi': 'hi',
    'Bengali': 'bn',
    'Turkish': 'tr',
    'Vietnamese': 'vi',
    'Polish': 'pl',
    'Ukrainian': 'uk',
    'Hebrew': 'he',
    'Swedish': 'sv',
    'Norwegian': 'no',
    'Finnish': 'fi',
    'Danish': 'da',
    'Hungarian': 'hu',
    'Czech': 'cs',
    'Romanian': 'ro',
    'Thai': 'th',
    'Indonesian': 'id',
    'Malay': 'ms',
    'Filipino': 'tl',
    'Swahili': 'sw',
}

def fetch_deepl_supported_languages():
    """
    Fetch the list of supported languages from the DeepL API.
    Returns a dictionary of language names and their corresponding codes.
    """
    try:
        params = {"auth_key": deepl_api_key}
        print("Fetching supported languages from DeepL API...")
        response = requests.get(deepl_languages_endpoint, params=params)

        if response.status_code == 200:
            languages = response.json()
            deepl_languages = {}
            for lang in languages:
                # Handle duplicate names by appending the language code
                name = lang["name"]
                code = lang["language"]
                if name in deepl_languages:
                    # Append the language code to differentiate
                    deepl_languages[f"{name} ({code})"] = code
                else:
                    deepl_languages[name] = code
            print(f"DeepL Supported Languages: {deepl_languages}")
            return deepl_languages
        else:
            print(f"Error: DeepL API returned {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        print(f"Error fetching DeepL supported languages: {e}")
        return {}

def compare_languages(current_languages, deepl_languages):
    """
    Compare the current languages with DeepL's supported languages based on names only.
    :param current_languages: A dictionary of current language names and their codes.
    :param deepl_languages: A dictionary of DeepL-supported language names and their codes.
    """
    print("\nComparing languages...\n")
    matching_languages = []
    unsupported_languages = []

    # Normalise DeepL language names to lowercase for comparison
    normalised_deepl_languages = {name.lower() for name in deepl_languages.keys()}

    for name in current_languages.keys():
        # Simplify names by comparing only the first word (e.g. 'Chinese (Simplified)' -> 'chinese')
        normalised_name = name.split()[0].lower()

        # Check if the language name is supported by DeepL
        if normalised_name in normalised_deepl_languages:
            matching_languages.append(name)
        else:
            unsupported_languages.append(name)

    print("Languages Supported by Both:")
    for name in matching_languages:
        print(f"- {name}")

    print("\nLanguages Not Supported by DeepL:")
    for name in unsupported_languages:
        print(f"- {name}")

def main():
    # Fetch the languages supported by DeepL
    deepl_languages = fetch_deepl_supported_languages()

    # Check if the fetch was successful
    if not deepl_languages:
        print("Failed to fetch DeepL-supported languages. Exiting...")
        return

    # Compare with current languages so the user can see which ones are supported by DeepL and which are not
    compare_languages(current_languages, deepl_languages)

if __name__ == "__main__":
    main()