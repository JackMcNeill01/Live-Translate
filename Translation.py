from googletrans import Translator

# Class to handle Google Translate translations
class TranslationHandling:
    def __init__(self):
        self.translator = Translator()

    def translate_text(self, text, dest_language='en'):
        translation = self.translator.translate(text, dest=dest_language)
        return translation.text

    
    def get_available_languages(self):
        """
        Return a dictionary of supported languages for google translate with their display names and language codes.
        Used for building the selection menus and verifying google translates language support.
        """
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
