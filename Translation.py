from googletrans import Translator

# This class handles translation of text using the googletrans library.
class TranslationHandling:
    def __init__(self):
        self.translator = Translator()

    # Translates the provided text into the specified destination language.
    # Uses the googletrans library to perform the translation.
    def translate_text(self, text, dest_language='en'):
        translation = self.translator.translate(text, dest=dest_language)
        return translation.text

    # Provides a dictionary of available languages for translation for google translate and their corresponding language codes.
    # The keys are the language choice numbers, and the values are tuples of (language_name, language_code).
    # The keys are mainly used for user selection in the command-line interface.
    def get_available_languages(self):
        return {
            '1': ('English', 'en'),
            '2': ('Spanish', 'es'),
            '3': ('French', 'fr'),
            '4': ('German', 'de'),
            '5': ('Chinese (Simplified)', 'zh-cn'),
            '6': ('Japanese', 'ja'),
            '7': ('Korean', 'ko'),
            '8': ('Russian', 'ru'),
            '9': ('Italian', 'it'),
            '10': ('Portuguese', 'pt'),
            '11': ('Dutch', 'nl'),
            '12': ('Greek', 'el'),
            '13': ('Arabic', 'ar'),
            '14': ('Hindi', 'hi'),
            '15': ('Bengali', 'bn'),
            '16': ('Turkish', 'tr'),
            '17': ('Vietnamese', 'vi'),
            '18': ('Polish', 'pl'),
            '19': ('Ukrainian', 'uk'),
            '20': ('Hebrew', 'he'),
            '21': ('Swedish', 'sv'),
            '22': ('Norwegian', 'no'),
            '23': ('Finnish', 'fi'),
            '24': ('Danish', 'da'),
            '25': ('Hungarian', 'hu'),
            '26': ('Czech', 'cs'),
            '27': ('Romanian', 'ro'),
            '28': ('Thai', 'th'),
            '29': ('Indonesian', 'id'),
            '30': ('Malay', 'ms'),
            '31': ('Filipino', 'tl'),
            '32': ('Swahili', 'sw'),
        }

    # Translates the provided text using the selected language choice.
    # Returns a tuple of (language_name, translated_text).
    def do_translation(self, language_choice, text):
        """
        Translates the provided text into the language specified by language_choice.
        If the choice is invalid, defaults to English.
        """
        languages = self.get_available_languages()
        language_name, dest_language = languages.get(language_choice, ('English', 'en'))
        result = self.translate_text(text, dest_language)
        return language_name, result

    # Provides a command-line interface for testing and debugging translations.
    # Displays available languages, allows the user to select one, and translates input text.
    def run_translation_cli(self):
        """
        Command-line interface for translation.
        Prompts the user to select a language and enter text to translate.
        Displays the translated text.
        """
        # Display available languages
        languages = self.get_available_languages()
        print("Select the destination language:")
        for key, (name, _) in languages.items():
            print(f"{key}: {name}")
        
        # Get user input for language selection and text
        choice = input("Enter the number corresponding to your choice: ")
        language_name, dest_language = languages.get(choice, ('English', 'en'))
        print(f"You selected: {language_name}")
        user_input = input("Enter the text to translate: ")
        translated = self.translate_text(user_input, dest_language)
        print(f"Translated text: {translated}")
