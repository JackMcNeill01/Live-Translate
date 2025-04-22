import os
import sys
# Adds the parent directory to sys.path since the script is in a subdirectory helper_apps so that it can import modules from the main directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
import csv
from Translation import TranslationHandling
import time
import threading
from PipelineForOCR import perform_translation
from DeepLTranslation import DeepLTranslation  # Import DeepLTranslation class

# Paths to the benchmark folders
TEXT_FOLDER = "benchmark_test_texts"
TRANSLATION_OUTPUT_CSV = "translation_benchmark_results.csv"

# Initialise TranslationHandling to access the language mapping
translator = TranslationHandling()

# Initialise DeepLTranslation instance to access the translation methods
deepl_translator = DeepLTranslation()

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

def benchmark_translation():
    """
    Benchmark translation times and outputs for each paragraph text file.
    Compares Google Translate and DeepL for translation times and outputs.
    DeepL is expected to be slightly more accurate in most cases but with less supported languages.
    Results are saved to a translation_benchmark_results.csv file.
    Accuracy is not measured or considered in this benchmark, 
    We naively assume that deepL and google translate are 100% accurate as between them they will be accurate enough for the purposes of this application,
    and this accuracy cannot be adequately measured without a human translator for each language.
    There is also no need to measure CPU usage for this benchmark as all translations are done through external APIs and therefore CPU usage will be negligible.
    """
    total_files = 0
    failed_files = 0
    unsupported_deepl = 0

    with open(TRANSLATION_OUTPUT_CSV, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            "From Language", "To Language", "Translation Method", "Translation Time (s)", "Translation Input", "Translation Output"
        ])

        for text_file in sorted(os.listdir(TEXT_FOLDER)):
            if text_file.endswith(".txt"):
                # Extract language name from filename
                language_name = text_file.replace("paragraph_", "").replace(".txt", "").replace("_", " ").strip()
                text_path = os.path.join(TEXT_FOLDER, text_file)

                try:
                    # Load ground truth text
                    with open(text_path, "r", encoding="utf-8") as file:
                        ground_truth_text = file.read()

                    # Determine target language
                    target_language = "English" if language_name != "English" else "Spanish"

                    # Loop through translation methods (Google Translate and DeepL)
                    # If the language is not supported by DeepL, skip it for that method 
                    translation_methods = [("Google Translate", False)]
                    if deepl_translator.is_language_supported(language_name):
                        translation_methods.append(("DeepL", True))
                    else:
                        # Still log the result for unsupported DeepL languages
                        translation_methods.append(("DeepL", "unsupported"))

                    for method, use_deepl in translation_methods:
                        if use_deepl == "unsupported":
                            translation_input_display = "\u202D" + normalise_display(ground_truth_text)
                            translation_output_display = "\u202DLanguage Not Supported By DeepL"
                            if language_name in ["Arabic", "Hebrew"]:
                                translation_input_display = "\u202D" + translation_input_display
                                translation_output_display = "\u202D" + translation_output_display

                            csv_writer.writerow([
                                language_name,
                                target_language,
                                method,
                                "N/A",
                                translation_input_display,
                                translation_output_display
                            ])

                            print(f"Skipped DeepL translation for {language_name}: Language not supported.")
                            unsupported_deepl += 1
                            continue

                        # Retry logic for translation if it fails up to 5 times
                        max_retries = 5
                        translation_successful = False
                        for attempt in range(1, max_retries + 1):
                            try:
                                # Measure translation time and get translation output
                                translation_start = time.time()
                                translation_output_list = perform_translation(
                                    [{"text": ground_truth_text}],
                                    target_lang=target_language,
                                    use_deepl=use_deepl
                                )
                                translation_time = time.time() - translation_start

                                # Extract the translation output (since perform_translation returns a list)
                                translation_output = translation_output_list[0] if translation_output_list else "Translation Failed"

                                translation_input_display = "\u202D" + normalise_display(ground_truth_text)
                                translation_output_display = "\u202D" + normalise_display(translation_output)

                                if language_name in ["Arabic", "Hebrew"]:
                                    translation_input_display = "\u202D" + translation_input_display
                                    translation_output_display = "\u202D" + translation_output_display

                                # Write results to CSV
                                csv_writer.writerow([
                                    language_name,
                                    target_language,
                                    method,  # Translation method (Google Translate or DeepL)
                                    f"{translation_time:.2f}",
                                    translation_input_display,
                                    translation_output_display
                                ])

                                print(f"Translated {language_name} to {target_language} using {method}: Translation Time = {translation_time:.2f}s")

                                total_files += 1
                                translation_successful = True

                                # Add a 0.5-second delay between each translation to avoid overwhelming the API (not included in any benchmark measurements)
                                time.sleep(0.5)

                                # Break out of the retry loop if successful
                                break

                            except Exception as e:
                                print(f"Attempt {attempt} failed for {language_name} using {method}: {e}")
                                if attempt < max_retries:
                                    print(f"Retrying in 2 seconds...")
                                    time.sleep(2)
                                else:
                                    print(f"ERROR: Failed to translate {language_name} using {method} after {max_retries} attempts.")

                        # If translation completely fails, write a placeholder row to the CSV
                        if not translation_successful:
                            translation_input_display = "\u202D" + normalise_display(ground_truth_text)
                            translation_output_display = "\u202DTranslation Failed"
                            if language_name in ["Arabic", "Hebrew"]:
                                translation_input_display = "\u202D" + translation_input_display
                                translation_output_display = "\u202D" + translation_output_display

                            csv_writer.writerow([
                                language_name,
                                target_language,
                                method,
                                "N/A",
                                "N/A",
                                "N/A",
                                translation_input_display,
                                translation_output_display
                            ])

                            failed_files += 1

                except Exception as e:
                    print(f"ERROR: Failed to process {text_file}: {e}")
                    failed_files += 1

    # Print final benchmark summary
    print(f"\nTranslation Benchmark Summary:")
    print(f"Total files processed: {total_files}")
    print(f"DeepL unsupported translations: {unsupported_deepl}")
    print(f"Failed translations: {failed_files}")


if __name__ == "__main__":
    benchmark_translation()