"""
WARNING: This script took 1 hour and 52 minutes to complete on a 14-core CPU despite using multithreading.

TO VIEW THE RESULTS WITHOUT HAVING TO RUN THIS LONG SCRIPT:
Open the ocr_accuracy_parameter_search Completed Example.csv file in the main directory.
This will not be overwritten by the script and is intended to save you time as an examiner.

While this is normally an awfully long time, I wanted to be as thorough as possible in the evaluation of the preprocessing parameters.
Given the 12 weeks of work that went into this project, almost 2 hours is a small price to pay for the best possible performance.

This version was chosen to ensure that the best possible performing parameters are selected for each language.
The script uses the two images and ground truth text file generated in GenerateTestImages.py for each language and compares the OCR results to the real text.
The results are averaged across the two images and the parameters that give the best average performance are selected.

The lengthy time is a result of cycling around 288 variants of preprocessing for each image and language.
Resulting in around 18,432 total OCR operations (288 x 2 x 32).
Google Vision OCR is not considered as it expects no preprocessing. 
"""

import os
import sys
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import csv
import pytesseract
import numpy as np
import cv2
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from Levenshtein import distance as levenshtein_distance
from PipelineForOCR import perform_ocr, get_ocr_language_code
from Translation import TranslationHandling

# Configuration
IMAGE_FOLDER = "benchmark_test_images"
TEXT_FOLDER = "benchmark_test_texts"
OUTPUT_CSV = "ocr_accuracy_parameter_search.csv"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
translator = TranslationHandling()


CONTRAST_VALUES = [1.0, 1.2, 1.4]
DENOISE_VALUES = [None, 1, 3, 9]
INVERT_OPTIONS = [False, True]
BLUR_OPTIONS = ["none", "gaussian", "median"]
THRESHOLD_METHODS = [
    {"method": "none"},
    {"method": "otsu"},
    {"method": "adaptive_gaussian", "blockSize": 15, "C": 4},
    {"method": "adaptive_mean", "blockSize": 11, "C": 2}
]

# Calculate the cost of the preprocessing variant to ensure the simplest of the equally best performing variants is selected
def compute_processing_cost(variant): 
    cost = 0
    if variant["contrast"] != 1.0:
        cost += 1
    if variant["denoise_h"] is not None:
        cost += 1
    if variant["invert"]:
        cost += 1
    if variant["blur"] != "none":
        cost += 1
    if variant["threshold_method"] != "none":
        cost += 1
    return cost


def normalise_display(text):
    return text.replace("\u00A0", " ").replace("\u200E", "").replace("\u200F", "").replace("\n", " ").strip()

def calculate_accuracy_with_levenshtein__distance(ocr_text, ground_truth_text):
    ocr_text = ''.join(ocr_text.split())
    ground_truth_text = ''.join(ground_truth_text.split())
    distance = levenshtein_distance(ocr_text, ground_truth_text)
    total_chars = max(len(ground_truth_text), len(ocr_text))
    return 0.0 if total_chars == 0 else ((total_chars - distance) / total_chars) * 100

def preprocess_for_ocr(pil_img, contrast_values, denoise_values, invert_options, threshold_methods, blur_options):
    img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    results = []

    for contrast in contrast_values:
        for denoise_h in denoise_values:
            for invert in invert_options:
                for threshold_cfg in threshold_methods:
                    for blur_type in blur_options:
                        try:
                            processed_img = gray.copy()

                            if invert:
                                processed_img = cv2.bitwise_not(processed_img)

                            if contrast != 1.0:
                                processed_img = cv2.convertScaleAbs(processed_img, alpha=contrast, beta=0)

                            if denoise_h is not None:
                                processed_img = cv2.fastNlMeansDenoising(processed_img, None, h=denoise_h)

                            if blur_type == "gaussian":
                                processed_img = cv2.GaussianBlur(processed_img, (3, 3), 0)
                            elif blur_type == "median":
                                processed_img = cv2.medianBlur(processed_img, 3)
                            
                            if threshold_cfg["method"] == "none":
                                pass # Skip thresholding step for 'none' method
                            elif threshold_cfg["method"] == "otsu":
                                _, processed_img = cv2.threshold(processed_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                            elif threshold_cfg["method"] == "adaptive_gaussian":
                                processed_img = cv2.adaptiveThreshold(
                                    processed_img, 255,
                                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY,
                                    threshold_cfg["blockSize"], threshold_cfg["C"]
                                )
                            elif threshold_cfg["method"] == "adaptive_mean":
                                processed_img = cv2.adaptiveThreshold(
                                    processed_img, 255,
                                    cv2.ADAPTIVE_THRESH_MEAN_C,
                                    cv2.THRESH_BINARY,
                                    threshold_cfg["blockSize"], threshold_cfg["C"]
                                )

                            result_img = Image.fromarray(processed_img)
                            results.append({
                                "image": result_img,
                                "contrast": contrast,
                                "denoise_h": denoise_h,
                                "invert": invert,
                                "blur": blur_type,
                                "threshold_method": threshold_cfg["method"],
                                "threshold_blockSize": threshold_cfg.get("blockSize", "N/A"),
                                "threshold_C": threshold_cfg.get("C", "N/A")
                            })
                        except Exception as e:
                            print(f"Error during preprocessing: {e}")
    return results

def evaluate_variant(variant, language_name, ground_truth_text):
    try:
        img = variant["image"]
        full_text, _ = perform_ocr(img, lang_name=language_name, use_preprocessing=False, use_google_vision=False)
        accuracy = calculate_accuracy_with_levenshtein__distance(full_text, ground_truth_text)
        return {
            "accuracy": accuracy,
            "full_text": full_text,
            "variant": variant
        }
    except Exception as e:
        return {"accuracy": -1, "error": str(e)}

def compare_ocr_with_ground_truth():
    """
    Compare OCR results with ground truth text files and save the results to a CSV file.
    Evaluate both images for each language and return the parameters that give the best average performance.
    """
    text_files = sorted(f for f in os.listdir(TEXT_FOLDER) if f.endswith(".txt"))
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            "Language",
            "Average Accuracy Before Preprocessing (%)",
            "Accuracy After Preprocessing (Image 1) (%)", 
            "Accuracy After Preprocessing (Image 2) (%)",
            "Average Accuracy After Preprocessing (%)", 
            "Contrast",
            "Denoise",
            "Invert",
            "Blur",
            "Threshold Method",
            "Block Size", "C",
            "OCR Output (Image 1)",
            "OCR Output (Image 2)",
            "Ground Truth"
        ])

        for text_file in text_files:
            language_name = text_file.replace("paragraph_", "").replace(".txt", "").replace("_", " ").strip()
            image_file_1 = f"paragraph_{language_name.replace(' ', '_')}_1.png"
            image_file_2 = f"paragraph_{language_name.replace(' ', '_')}_2.png"
            text_path = os.path.join(TEXT_FOLDER, text_file)
            image_path_1 = os.path.join(IMAGE_FOLDER, image_file_1)
            image_path_2 = os.path.join(IMAGE_FOLDER, image_file_2)

            if not os.path.exists(image_path_1) or not os.path.exists(image_path_2):
                print(f"WARNING: Image files not found for {text_file}. Skipping...")
                continue

            with open(text_path, "r", encoding="utf-8") as file:
                ground_truth_text = file.read()

            image_1 = Image.open(image_path_1)
            image_2 = Image.open(image_path_2)

            # Calculate average accuracy before preprocessing
            try:
                ocr_text_before_1, _ = perform_ocr(image_1, language_name, use_preprocessing=False)
                ocr_text_before_2, _ = perform_ocr(image_2, language_name, use_preprocessing=False)
                accuracy_before_1 = calculate_accuracy_with_levenshtein__distance(ocr_text_before_1, ground_truth_text)
                accuracy_before_2 = calculate_accuracy_with_levenshtein__distance(ocr_text_before_2, ground_truth_text)
                accuracy_before_avg = (accuracy_before_1 + accuracy_before_2) / 2
            except Exception as e:
                print(f"Error in baseline OCR for {language_name}: {e}")
                accuracy_before_avg = -1

            # Generate preprocessing variants
            variants_1 = preprocess_for_ocr(
                image_1,
                CONTRAST_VALUES,
                DENOISE_VALUES,
                INVERT_OPTIONS,
                THRESHOLD_METHODS,
                BLUR_OPTIONS
            )
            variants_2 = preprocess_for_ocr(
                image_2,
                CONTRAST_VALUES,
                DENOISE_VALUES,
                INVERT_OPTIONS,
                THRESHOLD_METHODS,
                BLUR_OPTIONS
            )

            # Evaluate each variant for both images
            best_result = None
            best_avg_accuracy = -1

            with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                results_1 = list(executor.map(
                    lambda v: evaluate_variant(v, language_name, ground_truth_text),
                    variants_1
                ))
                results_2 = list(executor.map(
                    lambda v: evaluate_variant(v, language_name, ground_truth_text),
                    variants_2
                ))


            # Combine results and calculate average accuracy
            for res_1, res_2 in zip(results_1, results_2):
                if res_1["accuracy"] == -1 or res_2["accuracy"] == -1:
                    continue

                avg_accuracy = (res_1["accuracy"] + res_2["accuracy"]) / 2

                if avg_accuracy > best_avg_accuracy:
                    best_avg_accuracy = avg_accuracy
                    best_result = {
                        "variant": res_1["variant"],
                        "ocr_output_1": res_1["full_text"],
                        "ocr_output_2": res_2["full_text"],
                        "accuracy_after_1": res_1["accuracy"],
                        "accuracy_after_2": res_2["accuracy"]
                    }

                elif avg_accuracy == best_avg_accuracy and best_result is not None:
                    current_cost = compute_processing_cost(res_1["variant"])
                    existing_cost = compute_processing_cost(best_result["variant"])
                    if current_cost < existing_cost:
                        best_result = {
                            "variant": res_1["variant"],
                            "ocr_output_1": res_1["full_text"],
                            "ocr_output_2": res_2["full_text"],
                            "accuracy_after_1": res_1["accuracy"],
                            "accuracy_after_2": res_2["accuracy"]
                        }


            v = best_result["variant"]
            # Write the best average result across both images to CSV including all relevant parameters
            csv_writer.writerow([
                language_name,
                f"{accuracy_before_avg:.2f}",  # Average accuracy before preprocessing
                f"{best_result['accuracy_after_1']:.2f}",  # Accuracy after preprocessing for image 1
                f"{best_result['accuracy_after_2']:.2f}",  # Accuracy after preprocessing for image 2
                f"{best_avg_accuracy:.2f}",  # Average accuracy after preprocessing
                v["contrast"],
                "none" if v["denoise_h"] is None else v["denoise_h"],  # Convert None to "none" so csv doesn't leave empty cells
                v["invert"],
                v["blur"],
                v["threshold_method"],
                v.get("threshold_blockSize", "N/A"),
                v.get("threshold_C", "N/A"),
                normalise_display(best_result["ocr_output_1"]),
                normalise_display(best_result["ocr_output_2"]),
                normalise_display(ground_truth_text)
            ])
            print(f"{language_name} Evaluation Complete, Best Average Accuracy: {best_avg_accuracy:.2f}% (Before: {accuracy_before_avg:.2f}%)")

if __name__ == "__main__":
    compare_ocr_with_ground_truth()
