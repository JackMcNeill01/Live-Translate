import os
import sys
# Adds the parent directory to sys.path since the script is in a subdirectory helper_apps so that it can import modules from the main directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Main import TESSERACT_PATH  # Import the Tesseract path from Main.py
import pytesseract
from PIL import Image
import csv
from Levenshtein import distance as levenshtein_distance
from PipelineForOCR import preprocess_for_ocr, perform_ocr, perform_translation, get_ocr_language_code
from Translation import TranslationHandling
import psutil
import time
import threading

# Paths to the benchmark folders
IMAGE_FOLDER = "benchmark_test_images"
TEXT_FOLDER = "benchmark_test_texts"
OCR_OUTPUT_CSV = "ocr_benchmark_results.csv"
# Ensure Tesseract OCR installation path is set correctly from main.py
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Initialise TranslationHandling to access the language mapping
translator = TranslationHandling()

# Removes special characters for CSV/Excel display later on
def normalise_display(text): 
    """
    Clean up text for consistent display in CSV/Excel.
    Removes special whitespace characters and unwanted markers.
    """
    text = text.replace("\u00A0", " ")   # Non-breaking space -> regular spaces
    text = text.replace("\u200E", "")    # LTR mark
    text = text.replace("\u200F", "")    # RTL mark (we add it explicitly if needed)
    text = text.replace("\n", " ")       # Remove line breaks for single-line display
    return text.strip()

def calculate_accuracy_with_levenshtein__distance(ocr_text, ground_truth_text):
    """
    Calculate OCR accuracy using Levenshtein distance, ignoring spaces and gaps.
    """
    # Normalise the text by removing all whitespace
    ocr_text = ''.join(ocr_text.split())
    ground_truth_text = ''.join(ground_truth_text.split())

    distance = levenshtein_distance(ocr_text, ground_truth_text)
    total_chars = max(len(ground_truth_text), len(ocr_text))

    if total_chars == 0:
        return 0.0

    return ((total_chars - distance) / total_chars) * 100

def monitor_cpu_usage(process, cpu_percentages, stop_event):
    """
    Continuously monitor CPU usage of the current process.
    Normalise CPU usage to a percentage of total system capacity.
    """
    num_cores = psutil.cpu_count(logical=True)  # Get the number of logical CPUs
    while not stop_event.is_set():
        # Normalise CPU usage by dividing by the number of cores
        cpu_percentages.append(process.cpu_percent(interval=0.1) / num_cores)

def compare_ocr_with_ground_truth():
    """
    Compare OCR output of images with ground truth text files and save results to a CSV file.
    Includes timing metrics, CPU usage, and OCR method comparison.
    Evaluates both paragraph image 1 and 2 per language for average accuracy.
    """
    total_files = 0
    skipped_files = 0
    failed_files = 0
    successful_with_preprocessing = 0
    successful_without_preprocessing = 0

    with open(OCR_OUTPUT_CSV, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            "Language", "OCR Method", "Preprocessing", "Average Accuracy (%)", "Average Total Time (s)", "Average Preprocessing Time (s)", "Average OCR Time (s)",
            "Avg CPU (%)", "Peak CPU (%)", "OCR Output Image 1", "OCR Output Image 2", "Ground Truth"
        ])

        for text_file in sorted(os.listdir(TEXT_FOLDER)):
            if text_file.endswith(".txt"):
                # Extract language name from filename
                language_name = text_file.replace("paragraph_", "").replace(".txt", "").replace("_", " ").strip()

                # Build paths for both paragraph image variants
                image_file_1 = f"paragraph_{language_name.replace(' ', '_')}_1.png"
                image_file_2 = f"paragraph_{language_name.replace(' ', '_')}_2.png"
                image_path_1 = os.path.join(IMAGE_FOLDER, image_file_1)
                image_path_2 = os.path.join(IMAGE_FOLDER, image_file_2)
                text_path = os.path.join(TEXT_FOLDER, text_file)

                # Validate that both images exist
                if not os.path.exists(image_path_1) or not os.path.exists(image_path_2):
                    print(f"WARNING: One or both image files not found for {text_file}. Skipping...")
                    skipped_files += 1
                    continue

                # Load ground truth text
                with open(text_path, "r", encoding="utf-8") as file:
                    ground_truth_text = file.read()

                # Load both images
                image_1 = Image.open(image_path_1)
                image_2 = Image.open(image_path_2)

                # Iterate over OCR methods and preprocessing options
                for ocr_method in ["Tesseract", "Google Vision"]:
                    for use_preprocessing in ([False, True] if ocr_method == "Tesseract" else [False]):
                        try:
                            total_files += 1

                            # Initialise CPU monitoring Thread to record average and peak CPU usage
                            process = psutil.Process()
                            cpu_percentages = []
                            stop_event = threading.Event()
                            cpu_thread = threading.Thread(target=monitor_cpu_usage, args=(process, cpu_percentages, stop_event))
                            cpu_thread.start()

                            # Start timing for the entire Preprocessing and OCR process
                            start_time = time.time()

                            # Perform Preprocessing And Measure The Time It Takes For Each Image
                            language_code = get_ocr_language_code(language_name)
                            preprocess_times = []
                            if use_preprocessing:
                                start_p1 = time.time()
                                image_1_proc = preprocess_for_ocr(image_1, language_code)
                                preprocess_times.append(time.time() - start_p1)

                                start_p2 = time.time()
                                image_2_proc = preprocess_for_ocr(image_2, language_code)
                                preprocess_times.append(time.time() - start_p2)
                            else:
                                image_1_proc = image_1
                                image_2_proc = image_2
                                preprocess_times = [0.0, 0.0]

                            avg_preprocess_time = sum(preprocess_times) / 2

                            # Perform OCR And Measure The Time It Takes For Each Image
                            ocr_start_1 = time.time()
                            full_text_1, _ = perform_ocr(image_1_proc, lang_name=language_name, use_preprocessing=False, use_google_vision=(ocr_method == "Google Vision"))
                            ocr_time_1 = time.time() - ocr_start_1

                            ocr_start_2 = time.time()
                            full_text_2, _ = perform_ocr(image_2_proc, lang_name=language_name, use_preprocessing=False, use_google_vision=(ocr_method == "Google Vision"))
                            ocr_time_2 = time.time() - ocr_start_2
                            ocr_time = (ocr_time_1 + ocr_time_2) / 2

                            # Measure Average Total Time For Preprocessing and OCR
                            avg_total_time = (time.time() - start_time) / 2

                            # Stop CPU monitoring
                            stop_event.set()
                            cpu_thread.join()

                            # Calculate average and peak CPU usage
                            avg_cpu = sum(cpu_percentages) / len(cpu_percentages) if cpu_percentages else 0
                            peak_cpu = max(cpu_percentages) if cpu_percentages else 0

                            # Accuracy calculation for both images
                            accuracy_1 = calculate_accuracy_with_levenshtein__distance(full_text_1, ground_truth_text)
                            accuracy_2 = calculate_accuracy_with_levenshtein__distance(full_text_2, ground_truth_text)
                            average_accuracy = (accuracy_1 + accuracy_2) / 2

                            # Normalise text for clean CSV/Excel output
                            full_text_1_display = normalise_display(full_text_1)
                            full_text_2_display = normalise_display(full_text_2)
                            ground_truth_display = normalise_display(ground_truth_text)

                            # Wrap in LTR marker to force direction for RTL languages
                            full_text_1_display = "\u202D" + full_text_1_display.replace('\n', ' ')
                            full_text_2_display = "\u202D" + full_text_2_display.replace('\n', ' ')
                            ground_truth_display = "\u202D" + ground_truth_display.replace('\n', ' ')

                            if language_name in ["Arabic", "Hebrew"]:
                                full_text_1_display = "\u202D" + full_text_1_display
                                full_text_2_display = "\u202D" + full_text_2_display
                                ground_truth_display = "\u202D" + ground_truth_display

                            # Write results to CSV
                            csv_writer.writerow([
                                language_name,
                                ocr_method,
                                "Yes" if use_preprocessing else "No",
                                f"{average_accuracy:.2f}",
                                f"{avg_total_time:.2f}",
                                f"{avg_preprocess_time:.2f}",
                                f"{ocr_time:.2f}",
                                f"{avg_cpu:.2f}",
                                f"{peak_cpu:.2f}",
                                full_text_1_display,
                                full_text_2_display,
                                ground_truth_display
                            ])

                            print(f"Processed {language_name} ({ocr_method}, Preprocessing: {'Yes' if use_preprocessing else 'No'}): Average Accuracy = {average_accuracy:.2f}%")

                            if use_preprocessing:
                                successful_with_preprocessing += 1
                            else:
                                successful_without_preprocessing += 1

                        except Exception as e:
                            print(f"ERROR: Failed to process {language_name} ({ocr_method}, Preprocessing: {'Yes' if use_preprocessing else 'No'}): {e}")
                            failed_files += 1

    # Print final benchmark summary
    print(f"\nSummary:")
    print(f"Total unique files: {total_files}")
    print(f"Successful with preprocessing: {successful_with_preprocessing}")
    print(f"Successful without preprocessing: {successful_without_preprocessing}")
    print(f"Skipped: {skipped_files}")
    print(f"Failed: {failed_files}")

if __name__ == "__main__":
    compare_ocr_with_ground_truth()