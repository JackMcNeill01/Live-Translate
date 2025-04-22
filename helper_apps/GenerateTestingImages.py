import os
import time
import re
from PIL import Image, ImageDraw, ImageFont
from googletrans import Translator
import arabic_reshaper
from bidi.algorithm import get_display

# Configurations
IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 1200
FONT_SIZE = 35
MARGIN = 50
LINE_SPACING = 20
PARAGRAPH_GAP_LINES = 5
FONT_FOLDER = 'fonts'
IMAGE_OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'benchmark_test_images')
TEXT_OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'benchmark_test_texts')

# Translation setup
translator = Translator()

paragraph1_en = ("The cat jumped over the fence."
                 "It landed softly on the green grass."
                 "The sun was shining brightly overhead."
                 "A small bird flew from a nearby tree.")

paragraph2_en = ("Meanwhile, a dog barked loudly."
                 "Leaves fell from the trees.")

languages = {
    'English': 'en', 'Spanish': 'es', 'French': 'fr', 'German': 'de',
    'Chinese (Simplified)': 'zh-cn', 'Japanese': 'ja', 'Korean': 'ko', 'Russian': 'ru',
    'Italian': 'it', 'Portuguese': 'pt', 'Dutch': 'nl', 'Greek': 'el', 'Arabic': 'ar',
    'Hindi': 'hi', 'Bengali': 'bn', 'Turkish': 'tr', 'Vietnamese': 'vi', 'Polish': 'pl',
    'Ukrainian': 'uk', 'Hebrew': 'he', 'Swedish': 'sv', 'Norwegian': 'no',
    'Finnish': 'fi', 'Danish': 'da', 'Hungarian': 'hu', 'Czech': 'cs',
    'Romanian': 'ro', 'Thai': 'th', 'Indonesian': 'id', 'Malay': 'ms',
    'Filipino': 'tl', 'Swahili': 'sw'
}

# Generating the images requires specific fonts for different languages.
# This have been downloaded from Google Fonts and placed in the 'fonts' directory for this purpose.
language_fonts = {
    'default': 'NotoSans-Regular.ttf',
    'Chinese (Simplified)': 'NotoSansSC-Regular.ttf',
    'Japanese': 'NotoSansJP-Regular.ttf',
    'Korean': 'NotoSansKR-Regular.ttf',
    'Hindi': 'NotoSansDevanagari-Regular.ttf',
    'Bengali': 'NotoSansBengali-Regular.ttf',
    'Thai': 'NotoSansThai-Regular.ttf',
    'Arabic': 'NotoSansArabic-Regular.ttf',
    'Hebrew': 'NotoSansHebrew-Regular.ttf'
}

# Utility Functions
def reshape_for_rtl(text):
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text

def load_font(language_name, size=FONT_SIZE):
    font_file = language_fonts.get(language_name, language_fonts['default'])
    font_path = os.path.join(FONT_FOLDER, font_file)
    try:
        return ImageFont.truetype(font_path, size)
    except Exception as e:
        print(f"Font load failed for {language_name}: {e}. Using fallback.")
        return ImageFont.truetype(os.path.join(FONT_FOLDER, language_fonts['default']), size)

def get_line_height(font):
    ascent, descent = font.getmetrics()
    return ascent + descent

def split_sentences(text):
    return re.findall(r'[^.!?]+[.!?]', text)

# Main logic
os.makedirs(IMAGE_OUTPUT_FOLDER, exist_ok=True)
os.makedirs(TEXT_OUTPUT_FOLDER, exist_ok=True)

success_count = 0
fail_count = 0

MAX_RETRIES = 5

def translate_with_retries(sentence, lang_code):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            result = translator.translate(sentence, dest=lang_code)
            if result and hasattr(result, 'text'):
                return result.text
            else:
                print(f"Translation failed (retry {retries + 1}/{MAX_RETRIES}): '{sentence}' -> Result is None or invalid")
        except Exception as e:
            print(f"Translation failed (retry {retries + 1}/{MAX_RETRIES}): '{sentence}' -> {e}")
        retries += 1
        time.sleep(2)
    return "[Translation failed]"

for idx, (language_name, lang_code) in enumerate(languages.items(), start=1):
    try:
        sentences1 = split_sentences(paragraph1_en)
        sentences2 = split_sentences(paragraph2_en)

        translated1 = [translate_with_retries(s, lang_code) for s in sentences1]
        translated2 = [translate_with_retries(s, lang_code) for s in sentences2]

        font = load_font(language_name)
        line_height = get_line_height(font)

        # Generate Variant 1: white background, black text
        img1 = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), 'white')
        draw1 = ImageDraw.Draw(img1)
        y1 = MARGIN

        # For paragraph 1 apply reshaping for RTL languages to ensure correct display
        for line in (reshape_for_rtl(s) if language_name in ['Arabic', 'Hebrew'] else s for s in translated1):
            draw1.text((MARGIN, y1), line.strip(), fill='black', font=font)
            y1 += line_height + LINE_SPACING

        y1 += PARAGRAPH_GAP_LINES * (line_height + LINE_SPACING)

        # For paragraph 2 apply reshaping for RTL languages to ensure correct display
        for line in (reshape_for_rtl(s) if language_name in ['Arabic', 'Hebrew'] else s for s in translated2):
            draw1.text((MARGIN, y1), line.strip(), fill='black', font=font)
            y1 += line_height + LINE_SPACING

        filename1 = f"paragraph_{language_name.replace(' ', '_')}_1.png"
        img1.save(os.path.join(IMAGE_OUTPUT_FOLDER, filename1))
        print(f"[{idx}/{len(languages)}] Saved: {filename1}")

        # Generate Variant 2: blue background, white text 
        img2 = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), '#3b8ed0')
        draw2 = ImageDraw.Draw(img2)
        y2 = MARGIN

        # For paragraph 1 apply reshaping for RTL languages to ensure correct display
        for line in (reshape_for_rtl(s) if language_name in ['Arabic', 'Hebrew'] else s for s in translated1):
            draw2.text((MARGIN, y2), line.strip(), fill='white', font=font)
            y2 += line_height + LINE_SPACING

        y2 += PARAGRAPH_GAP_LINES * (line_height + LINE_SPACING)

        # For paragraph 2 apply reshaping for RTL languages to ensure correct display
        for line in (reshape_for_rtl(s) if language_name in ['Arabic', 'Hebrew'] else s for s in translated2):
            draw2.text((MARGIN, y2), line.strip(), fill='white', font=font)
            y2 += line_height + LINE_SPACING

        filename2 = f"paragraph_{language_name.replace(' ', '_')}_2.png"
        img2.save(os.path.join(IMAGE_OUTPUT_FOLDER, filename2))
        print(f"[{idx}/{len(languages)}] Saved: {filename2}")

        text_filename = f"paragraph_{language_name.replace(' ', '_')}.txt"
        with open(os.path.join(TEXT_OUTPUT_FOLDER, text_filename), 'w', encoding='utf-8') as text_file:
            text_file.write("\n".join(translated1))
            text_file.write("\n\n\n\n\n")
            text_file.write("\n".join(translated2))
        print(f"[{idx}/{len(languages)}] Saved: {text_filename}")

        success_count += 1
        time.sleep(0.5)

    except Exception as e:
        print(f"[{idx}/{len(languages)}] Error for {language_name}: {e}")
        fail_count += 1

print(f"\nDone: Generated 2 Test Images For {success_count} Languages  | {fail_count} Failed\n")
