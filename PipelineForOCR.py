import pytesseract
from PIL import Image
import cv2
import numpy as np
import os
from GoogleVisionOCR import GoogleVisionOCR
from Translation import TranslationHandling
from DeepLTranslation import DeepLTranslation

def preprocess_for_ocr(pil_img, language_code, debug=False, debug_dir="debug_images"):
    """
    Applies language-specific preprocessing tuned to benchmarked optimal parameters.
    Uses minimal processing for languages that already achieve 100% accuracy across all testing.
    """
    import os
    if debug:
        os.makedirs(debug_dir, exist_ok=True)
        pil_img.save(f"{debug_dir}/original_image.png")

    # Convert to OpenCV format and grayscale
    img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    grey = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    """
    After testing various preprocessing techniques through the OptimisePreProcessing.py helper app I made, the following configurations were found to be optimal for each language.
    The configurations are based on the language code and include parameters for contrast, denoising, inversion, blurring, and thresholding.
    This data can be found in the ocr_accuracy_parameter_search Completed Example.csv that was built using the OptimisePreProcessing.py helper app.
    """
    language_specific_configs = {
        "ara":     {"contrast": 1.2, "denoise": 9,    "invert": False, "blur": "median",   "threshold": "adaptive_gaussian"},
        "ben":     {"contrast": 1.2, "denoise": 1,    "invert": False, "blur": "median",   "threshold": "none"},
        "chi_sim": {"contrast": 1.2, "denoise": None, "invert": False, "blur": "median",   "threshold": "otsu"},
        "ell":     {"contrast": 1.0, "denoise": 3,    "invert": False, "blur": "none",     "threshold": "none"},
        "hin":     {"contrast": 1.4, "denoise": None, "invert": False, "blur": "gaussian", "threshold": "otsu"},
        "jpn":     {"contrast": 1.0, "denoise": None, "invert": False, "blur": "gaussian", "threshold": "none"},
        "kor":     {"contrast": 1.4, "denoise": None, "invert": True,  "blur": "median",   "threshold": "none"},
        "tha":     {"contrast": 1.0, "denoise": None, "invert": False, "blur": "gaussian", "threshold": "otsu"},
    }

    """
    For all other languages, use the default configuration.
    All other languages were found to be 100% accurate without extensive preprocessing,
    At least in the image tests I performed and evaluated.
    Best-performing configurations for most languages.
    This results in the image being just converted to grayscale and saved as a PNG.
    """
    default_config = {
        "contrast": 1.0,
        "denoise": None,
        "invert": False,
        "blur": "none",
        "threshold": "none"
    }
    
    config = language_specific_configs.get(language_code, default_config)

    # Inversion
    if config["invert"]:
        grey = cv2.bitwise_not(grey)
        if debug:
            Image.fromarray(grey).save(f"{debug_dir}/inverted.png")

    # Contrast
    if config["contrast"] != 1.0:
        grey = cv2.convertScaleAbs(grey, alpha=config["contrast"], beta=0)
        if debug:
            Image.fromarray(grey).save(f"{debug_dir}/contrast.png")

    # Denoising
    if config["denoise"] is not None:
        grey = cv2.fastNlMeansDenoising(grey, None, h=config["denoise"])
        if debug:
            Image.fromarray(grey).save(f"{debug_dir}/denoised.png")

    # Blur
    if config["blur"] == "gaussian":
        grey = cv2.GaussianBlur(grey, (3, 3), 0)
        if debug:
            Image.fromarray(grey).save(f"{debug_dir}/blur_gaussian.png")
    elif config["blur"] == "median":
        grey = cv2.medianBlur(grey, 3)
        if debug:
            Image.fromarray(grey).save(f"{debug_dir}/blur_median.png")

    # Thresholding
    if config["threshold"] == "otsu":
        _, grey = cv2.threshold(grey, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if debug:
            Image.fromarray(grey).save(f"{debug_dir}/threshold_otsu.png")
    elif config["threshold"] == "adaptive_gaussian":
        grey = cv2.adaptiveThreshold(grey, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 15, 4)
        if debug:
            Image.fromarray(grey).save(f"{debug_dir}/threshold_adaptive_gaussian.png")
    elif config["threshold"] == "adaptive_mean":
        grey = cv2.adaptiveThreshold(grey, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
        if debug:
            Image.fromarray(grey).save(f"{debug_dir}/threshold_adaptive_mean.png")

    return Image.fromarray(grey)




def get_ocr_language_code(language_name):
    lang_map = {
        'English': 'eng', 'Spanish': 'spa', 'French': 'fra', 'German': 'deu',
        'Chinese (Simplified)': 'chi_sim', 'Japanese': 'jpn', 'Korean': 'kor',
        'Russian': 'rus', 'Italian': 'ita', 'Portuguese': 'por', 'Dutch': 'nld',
        'Greek': 'ell', 'Arabic': 'ara', 'Hindi': 'hin', 'Bengali': 'ben',
        'Turkish': 'tur', 'Vietnamese': 'vie', 'Polish': 'pol', 'Ukrainian': 'ukr',
        'Hebrew': 'heb', 'Swedish': 'swe', 'Norwegian': 'nor', 'Finnish': 'fin',
        'Danish': 'dan', 'Hungarian': 'hun', 'Czech': 'ces', 'Romanian': 'ron',
        'Thai': 'tha', 'Indonesian': 'ind', 'Malay': 'msa', 'Filipino': 'fil',
        'Swahili': 'swa',
    }
    return lang_map.get(language_name, 'eng')


def perform_ocr(image, lang_name, use_preprocessing=True, use_google_vision=False, debug=False):
    temp_path = "temp_ocr_image.png"
    ocr_lang = get_ocr_language_code(lang_name)
    paragraphs = []

    if use_google_vision:
        image.save(temp_path)
        ocr = GoogleVisionOCR()
        result = ocr.perform_ocr(temp_path)
        os.remove(temp_path)
        return result['full_text'], result['paragraphs']

    if use_preprocessing:
        image = preprocess_for_ocr(image, language_code=ocr_lang, debug=debug)

    ocr_data = pytesseract.image_to_data(image, lang=ocr_lang, output_type=pytesseract.Output.DICT)

    current_paragraph = {"x": None, "y": None, "width": 0, "height": 0, "text": ""}
    for i in range(len(ocr_data['text'])):
        if ocr_data['text'][i].strip() and ocr_data['width'][i] > 1 and ocr_data['height'][i] > 1:
            x, y = ocr_data['left'][i], ocr_data['top'][i]
            width, height = ocr_data['width'][i], ocr_data['height'][i]
            text = ocr_data['text'][i].strip()

            if current_paragraph["x"] is None:
                current_paragraph.update({"x": x, "y": y, "width": width, "height": height, "text": text})
            elif abs(y - (current_paragraph["y"] + current_paragraph["height"])) < 50 or abs(x - (current_paragraph["x"] + current_paragraph["width"])) < 100:
                current_paragraph["x"] = min(current_paragraph["x"], x)
                current_paragraph["y"] = min(current_paragraph["y"], y)
                current_paragraph["width"] = max(current_paragraph["x"] + current_paragraph["width"], x + width) - current_paragraph["x"]
                current_paragraph["height"] = max(current_paragraph["y"] + current_paragraph["height"], y + height) - current_paragraph["y"]
                current_paragraph["text"] += " " + text
            else:
                paragraphs.append(current_paragraph)
                current_paragraph = {"x": x, "y": y, "width": width, "height": height, "text": text}
    if current_paragraph["x"] is not None:
        paragraphs.append(current_paragraph)

    if ocr_lang == 'chi_sim':
        full_text = "".join([p['text'] for p in paragraphs])
    else:
        full_text = " ".join([p['text'] for p in paragraphs])

    return full_text, paragraphs

# Route text to the appropriate translation method based on the user's choice.
def perform_translation(paragraphs, target_lang, use_deepl=False):
    if use_deepl:
        deepl = DeepLTranslation()
        return [deepl.translate_text(p['text'], target_lang) for p in paragraphs]
    else:
        translator = TranslationHandling()
        return [translator.translate_text(p['text'], target_lang) for p in paragraphs]
