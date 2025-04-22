import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image
from gtts import gTTS
import os
from Translation import TranslationHandling
from DeepLTranslation import DeepLTranslation
import pygame
import threading
from screeninfo import get_monitors
import mss
import cv2
import numpy as np
import pytesseract
from GoogleVisionOCR import GoogleVisionOCR
import webbrowser
from PipelineForOCR import perform_ocr, perform_translation

# Import the API keys to check if they are set correctly
# If they are not the related options will be disabled in the GUI
from Creds import deepl_api_key, google_vision_api_key

# Class that handles the GUI for the Live-Translate application along with the related functionality
class MainGui(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.tk.call('tk', 'scaling', 1.0)  # Disable DPI scaling
        self.geometry("1280x720")  # Set the initial size before creating widgets
        self.title('Live-Translate')
        self.resizable(False, False)
        ctk.set_appearance_mode('light')  # Set default theme
        ctk.set_widget_scaling(1.0)

        # Keep a reference to the translation popup so it gets reused
        self.translation_popup = None

        # Configure the main window to expand
        self.grid_rowconfigure(0, weight=1)  # Allow row 0 to expand
        self.grid_columnconfigure(0, weight=1)  # Allow column 0 to expand

        # Create a main container frame that that fills the entire window
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10,0))

        # Let main_frame stretch to fill the window
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # Two rows: one for theme and size dropdowns, one for tabs
        self.main_frame.grid_rowconfigure(0, weight=0)  # dropdowns
        self.main_frame.grid_rowconfigure(1, weight=1)  # tabview

        # Create header_frame to hold theme and size dropdowns in a single row
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 0))
        # Three equal-width columns: [theme] [tabs placeholder] [size]
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=1)
        self.header_frame.grid_columnconfigure(2, weight=1)

        # Create a Tabview widget for two pages inside main_frame
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=(5,0))

        # Add the tabs to the Tabview
        self.tabview.add("OCR Translation")  # First tab
        self.tabview.add("Text Translation")  # Second tab

        # Make the Tabview itself expandable
        self.tabview.grid_rowconfigure(0, weight=1)
        self.tabview.grid_columnconfigure(0, weight=1)

        # Make each individual tab’s layout expandable
        self.tabview.tab("OCR Translation").grid_rowconfigure(0, weight=1)
        self.tabview.tab("OCR Translation").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Text Translation").grid_rowconfigure(0, weight=1)
        self.tabview.tab("Text Translation").grid_columnconfigure(0, weight=1)

        # Add a dropdown menu for theme selection
        self.theme_menu = ctk.CTkOptionMenu(
            self.header_frame,
            values=self.get_theme_options("Light"),
            command=lambda theme: self.change_dropdown(self.theme_menu, theme, "theme")
        )
        self.theme_menu.set("Light")
        self.theme_menu.grid(row=0, column=0, padx=(10,0), sticky="w")
        
        # Add a feedback hyperlink in the header_frame
        self.feedback_button = ctk.CTkButton(
            self.header_frame,
            text="Provide App Feedback / Report Issues",
            text_color="white",
            command=lambda: webbrowser.open("https://docs.google.com/forms/d/e/1FAIpQLSczHCVuwtJaZmq3rffNkqExhQlxThHChYxxayv6rpNhtjHTnw/viewform"),
            font=("Arial", 12, "bold"),
        )
        self.feedback_button.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="n")  # Centre it in the middle column
        
        # Add a size dropdown menu for preset window sizes
        self.size_menu = ctk.CTkOptionMenu(
            self.header_frame,
            values=self.get_size_options("1280x720"),  # Dynamically generate options
            command=lambda size: self.change_dropdown(self.size_menu, size, "size")
        )
        self.size_menu.set("1280x720")  # Set default size
        self.size_menu.grid(row=0, column=2, padx=(10,0), sticky="e")

        # Check if the API keys for DeepL and Google Vision are set up correctly
        # If not, later disable their use through the checkboxes in the GUI
        self.deepl_enabled = self.is_deepl_enabled()
        self.google_vision_enabled = self.is_google_vision_enabled()

        # Show an error message if either API key is invalid so the user knows why the features are disabled
        # Delay showing the error so the GUI loads onto the screen first
        self.after(1500, self.show_api_key_error)  # Delay by 1.5 seconds

        # -----------------
        # Tab 1: OCR Translation
        # Add a scrollable frame for the OCR Translation tab
        self.ocr_tab_frame = ctk.CTkScrollableFrame(self.tabview.tab("OCR Translation"), width=2000, height=2000)
        self.ocr_tab_frame.grid(row=0, column=0, padx=10, pady=0, sticky="nsew")

        # Configure the OCR tab frame to expand with 7 columns for precise layout
        self.ocr_tab_frame.grid_columnconfigure(0, weight=1)  # Left spacer
        self.ocr_tab_frame.grid_columnconfigure(1, weight=0)  # From Label
        self.ocr_tab_frame.grid_columnconfigure(2, weight=0)  # From Dropdown
        self.ocr_tab_frame.grid_columnconfigure(3, weight=1)  # Centre dynamic gap
        self.ocr_tab_frame.grid_columnconfigure(4, weight=0)  # To Label
        self.ocr_tab_frame.grid_columnconfigure(5, weight=0)  # To Dropdown
        self.ocr_tab_frame.grid_columnconfigure(6, weight=1)  # Right spacer

        # Available languages list
        self.available_language_names = [
            'English', 'Spanish', 'French', 'German', 'Chinese (Simplified)',
            'Japanese', 'Korean', 'Russian', 'Italian', 'Portuguese',
            'Dutch', 'Greek', 'Arabic', 'Hindi', 'Bengali', 'Turkish',
            'Vietnamese', 'Polish', 'Ukrainian', 'Hebrew', 'Swedish',
            'Norwegian', 'Finnish', 'Danish', 'Hungarian', 'Czech',
            'Romanian', 'Thai', 'Indonesian', 'Malay', 'Filipino', 'Swahili'
        ]

        # Add From Language Label
        self.ocr_from_label = ctk.CTkLabel(self.ocr_tab_frame, text="From Language:")
        self.ocr_from_label.grid(row=0, column=1, padx=(10,5), pady=(30,30), sticky="e")

        # Add From Language ComboBox
        self.ocr_from_language_combo = ctk.CTkComboBox(
            self.ocr_tab_frame,
            width=160,
            values=self.get_language_options("Chinese (Simplified)"),
            command=lambda language: self.change_dropdown(self.ocr_from_language_combo, language, "language")
        )
        self.ocr_from_language_combo.set("Chinese (Simplified)")
        self.ocr_from_language_combo.grid(row=0, column=2, padx=(5,10), pady=(30,30), sticky="w")

        # Add To Language Label
        self.ocr_to_label = ctk.CTkLabel(self.ocr_tab_frame, text="To Language:")
        self.ocr_to_label.grid(row=0, column=4, padx=(10,5), pady=(30,30), sticky="e")

        # Add To Language ComboBox
        self.ocr_to_language_combo = ctk.CTkComboBox(
            self.ocr_tab_frame,
            width=160,
            values=self.get_language_options("English"),
            command=lambda language: self.change_dropdown(self.ocr_to_language_combo, language, "language")
        )
        self.ocr_to_language_combo.set("English")
        self.ocr_to_language_combo.grid(row=0, column=5, padx=(5,10), pady=(30,30), sticky="w")

        # Add A Checkbox To Use DeepL Instead Of Google Translate (Disabled if DeepL API key is not set up correctly) 
        self.ocr_deepl_checkbox = ctk.CTkCheckBox(
            self.ocr_tab_frame,
            text="Use DeepL Instead Of Google Translate",
            state="normal" if self.deepl_enabled else "disabled"
        )
        self.ocr_deepl_checkbox.grid(row=1, column=1, columnspan=2, padx=(10, 5), pady=(30, 30), sticky="w")


        # Add Translation Input Monitor Label
        self.monitor_label = ctk.CTkLabel(self.ocr_tab_frame, text="Select Translation Input Monitor:")
        self.monitor_label.grid(row=1, column=4, padx=(20,5), pady=(30,30), sticky="e")

        # Add Translation Input Monitor ComboBox
        self.monitors = get_monitors()
        monitor_options = [f"Monitor {i+1}: {monitor.width}x{monitor.height}" for i, monitor in enumerate(self.monitors)]
        self.monitor_combo = ctk.CTkOptionMenu(
            self.ocr_tab_frame,
            values=self.get_monitor_options(0),
            command=lambda monitor: self.change_monitor(monitor)
        )
        self.monitor_combo.set(monitor_options[0].replace(" ✓", ""))
        self.monitor_combo.grid(row=1, column=5, padx=(0,10), pady=(30,30), sticky="w")

        self.selected_monitor_index = 0

        # Add Region Based Translation checkbox
        self.region_based_checkbox = ctk.CTkCheckBox(self.ocr_tab_frame, text="Region Based Translation")
        self.region_based_checkbox.grid(row=4, column=1, columnspan=2, padx=(10,5), pady=(30,30), sticky="w")

        # Add Translation Output Monitor Label
        self.translation_monitor_label = ctk.CTkLabel(self.ocr_tab_frame, text="Select Translation Output Monitor:")
        self.translation_monitor_label.grid(row=2, column=4, padx=(20,5), pady=(30,30), sticky="e")

        # Add Translation Output Monitor ComboBox
        monitor_options = self.get_monitor_options(0)
        default_monitor_option = monitor_options[0].replace(" ✓", "")

        self.translation_monitor_combo = ctk.CTkOptionMenu(
            self.ocr_tab_frame,
            values=monitor_options,
            command=lambda monitor: self.change_translation_monitor(monitor)
        )
        self.translation_monitor_combo.set(default_monitor_option)
        self.translation_monitor_combo.grid(row=2, column=5, padx=(0,10), pady=(30,30), sticky="w")

        self.selected_translation_monitor_index = 0

        # Add Enable Text To Speech checkbox
        self.ocr_tts_checkbox = ctk.CTkCheckBox(self.ocr_tab_frame, text="Enable Text To Speech")
        self.ocr_tts_checkbox.grid(row=3, column=1, padx=(10,5), pady=(30,30), sticky="w")

        # Add Text To Speech Volume label
        self.ocr_volume_label = ctk.CTkLabel(self.ocr_tab_frame, text="Text To Speech Volume: 20%")
        self.ocr_volume_label.grid(row=3, column=4, padx=(20,5), pady=(30,30), sticky="e")

        # Add volume slider for text to speech
        self.ocr_volume_slider = ctk.CTkSlider(
            self.ocr_tab_frame,
            from_=0.0,
            to=1.0,
            width=150,
            command=self.update_ocr_volume_label
        )
        self.ocr_volume_slider.set(0.2)
        self.ocr_volume_slider.grid(row=3, column=5, columnspan=2, padx=(0,10), pady=(30,30), sticky="w")

        # Add Enable Preprocessing checkbox
        self.enable_preprocessing = tk.BooleanVar(value=True)
        self.preprocessing_checkbox = ctk.CTkCheckBox(
            self.ocr_tab_frame,
            text="Enable Preprocessing",
            variable=self.enable_preprocessing
        )
        self.preprocessing_checkbox.grid(row=4, column=0, columnspan=7, pady=(30,30))

        # Add Select & Translate button
        self.select_area_btn = ctk.CTkButton(
            self.ocr_tab_frame,
            text="Select & Translate",
            command=self.start_snip
        )
        self.select_area_btn.grid(row=5, column=0, columnspan=7, pady=(30,30))

        # Add A Checkbox to Use Google Vision OCR Instead Of Tesseract OCR (Disabled if Google Vision API key is not set up correctly)
        self.use_google_vision_checkbox = ctk.CTkCheckBox(
            self.ocr_tab_frame,
            text="Use Google Vision OCR Instead Of Tesseract",
            state="normal" if self.google_vision_enabled else "disabled"
        )
        self.use_google_vision_checkbox.grid(row=2, column=1, columnspan=2, padx=(10, 5), pady=(30, 30), sticky="w")


        # -----------------
        # Tab 2: Text Translation
        # Add a scrollable frame for the Text Translation tab
        self.text_translation_tab_frame = ctk.CTkScrollableFrame(self.tabview.tab("Text Translation"), width=2000, height=2000)
        self.text_translation_tab_frame.grid(row=0, column=0, padx=10, pady=0, sticky="nsew")

        # Configure the Text Translation tab frame to expand
        self.text_translation_tab_frame.grid_rowconfigure(0, weight=1)
        self.text_translation_tab_frame.grid_columnconfigure(1, weight=1)  # Right column

        # 2 Equal columns inside the scrollable frame to hold the widgets
        self.text_translation_tab_frame.grid_columnconfigure(0, weight=1)
        self.text_translation_tab_frame.grid_columnconfigure(1, weight=1)

        # Helper frame to hold From/To in one line, centred
        lang_frame = ctk.CTkFrame(self.text_translation_tab_frame, fg_color="transparent")
        lang_frame.grid(row=0, column=0, columnspan=2, pady=(10,10), sticky="ew")

        # 7 equal columns inside helper
        for c in range(7):
            lang_frame.grid_columnconfigure(c, weight=1)

        # Add widgets to the scrollable frame
        # Add From Language Label
        self.from_label = ctk.CTkLabel(lang_frame, text="From Language:")
        self.from_label.grid(in_=lang_frame, row=0, column=1, padx=5, sticky="e")

        # Add From Language ComboBox
        self.from_language_combo = ctk.CTkComboBox(
            lang_frame,
            values=self.get_language_options("English"),
            width=160,
            command=lambda language: self.change_dropdown(self.from_language_combo, language, "language")
        )
        self.from_language_combo.set("English")  # Set default value
        self.from_language_combo.grid(in_=lang_frame, row=0, column=2, padx=5, sticky="w")

        # Add To Language Label
        self.to_label = ctk.CTkLabel(lang_frame, text="To Language:")
        self.to_label.grid(in_=lang_frame, row=0, column=4, padx=5, sticky="e")

        # Add To Language ComboBox
        self.to_language_combo = ctk.CTkComboBox(
            lang_frame,
            values=self.get_language_options("Spanish"),
            width=160,
            command=lambda language: self.change_dropdown(self.to_language_combo, language, "language")
        )
        self.to_language_combo.set("Spanish")  # Set default value
        self.to_language_combo.grid(in_=lang_frame, row=0, column=5, padx=5, sticky="w")

        # Input textbox for text to translate
        self.input_textbox = ctk.CTkTextbox(self.text_translation_tab_frame, width=500, height=150)
        self.input_textbox.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
        self.input_textbox.insert("0.0", "Enter text to translate here...")

        # Translate button for GUI mode
        self.translate_button = ctk.CTkButton(
            self.text_translation_tab_frame, text="Translate", command=self.translate_action,
        )
        self.translate_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        # Output textbox for translated text
        self.output_textbox = ctk.CTkTextbox(self.text_translation_tab_frame, width=500, height=150)
        self.output_textbox.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
        self.output_textbox.insert("0.0", "Translation will appear here...")

        # Add a Checkbox To Use DeepL Instead Of Google Translate (Disabled if DeepL API key is not set up correctly) 
        self.text_deepl_checkbox = ctk.CTkCheckBox(
            self.text_translation_tab_frame,
            text="Use DeepL Instead Of Google Translate",
            state="normal" if self.deepl_enabled else "disabled"
        )
        self.text_deepl_checkbox.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

        # Add "Enable Text To Speech" checkbox to Text Translation tab
        self.text_tts_checkbox = ctk.CTkCheckBox(self.text_translation_tab_frame, text="Enable Text To Speech")
        self.text_tts_checkbox.grid(row=6, column=0, columnspan=2, padx=10, pady=(10, 0))

        # Add a label for the volume slider with dynamic percentage to Text Translation tab
        self.text_volume_label = ctk.CTkLabel(self.text_translation_tab_frame, text="Text To Speech Volume: 20%")
        self.text_volume_label.grid(row=7, column=0, columnspan=2, padx=10, pady=(5, 0))
        
        # Add volume slider for Text Translation tab
        self.text_volume_slider = ctk.CTkSlider(self.text_translation_tab_frame, from_=0.0, to=1.0, width=150, command=self.update_text_volume_label)
        self.text_volume_slider.set(0.2)  # Default volume (20%)
        self.text_volume_slider.grid(row=8, column=0, columnspan=2, padx=10, pady=(5, 0))

        # Bind the right Alt key as a hotkey to re-trigger the snip process
        self.bind("<Alt_R>", lambda event: self.start_snip())

    def get_language_options(self, selected_language):
        """
        Generate a list of language options with a checkmark after the currently selected language.
        """
        return [f"{language} ✓" if language == selected_language else language for language in self.available_language_names]

    def get_theme_options(self, selected_theme):
        """
        Generate a list of theme options with a checkmark after the currently selected theme.
        """
        themes = ["Light", "Dark", "System"]
        return [f"{theme} ✓" if theme == selected_theme else theme for theme in themes]

    def get_size_options(self, selected_size):
        """
        Generate a list of size options with a checkmark after the currently selected size.
        """
        sizes = ["960x540", "1280x720", "1600x900"]
        return [f"{size} ✓" if size == selected_size else size for size in sizes]

    def get_monitor_options(self, selected_index):
        """
        Generate a list of monitor options with a checkmark after the currently selected monitor.
        """
        return [
            f"Monitor {i+1}: {monitor.width}x{monitor.height} ✓" if i == selected_index else f"Monitor {i+1}: {monitor.width}x{monitor.height}"
            for i, monitor in enumerate(self.monitors)
        ]

    def is_deepl_enabled(self):
        """
        Check if DeepL API key is valid.
        :return: True if valid, False otherwise.
        """
        if not os.path.exists("Creds.py"):
            return False
        # Check if the API key not null, an empty string, or the default placeholder
        return deepl_api_key and deepl_api_key != "YOUR_DEEPL_API_KEY_HERE"
    
    def is_google_vision_enabled(self):
        """
        Check if Google Vision API key is valid.
        :return: True if valid, False otherwise.
        """
        if not os.path.exists("Creds.py"):
            return False
        # Check if the API key not null, an empty string, or the default placeholder
        return google_vision_api_key and google_vision_api_key != "YOUR_GOOGLE_VISION_API_KEY_HERE"
    
    def show_api_key_error(self):
        """
        Display an error message if either DeepL or Google Vision API key is invalid.
        """
        if not self.deepl_enabled or not self.google_vision_enabled:
            invalid_keys = []
            if not self.deepl_enabled:
                invalid_keys.append("DeepL")
            if not self.google_vision_enabled:
                invalid_keys.append("Google Vision OCR")
    
            # Dynamically construct the error message depending on if one or both keys are invalid
            keys_text = " and ".join(invalid_keys)
            plural_features = "features" if len(invalid_keys) > 1 else "feature"
            plural_keys = "keys" if len(invalid_keys) > 1 else "key"
            plural_these = "these" if len(invalid_keys) > 1 else "this"
            article = "a " if len(invalid_keys) == 1 else ""  # Use "a" for singular, nothing for plural
            message = (
                f"Invalid API Keys or Creds.py\n"
                f"({keys_text}) will be disabled until you provide {article}valid API {plural_keys}.\n"
                f"Please follow the README.md instructions in order to enable {plural_these} {plural_features}."
            )
            # Show the error message in a popup
            messagebox.showerror("Live-Translate - DeepL/Google Vision OCR API Key Error", message)

    def change_dropdown(self, dropdown, selected_value: str, option_type: str):
        """
        Update a dropdown's options and reset the selected text.
        Automatically disable or enable the DeepL checkbox if an unsupported language is selected.
        :param dropdown: The dropdown widget to update.
        :param selected_value: The selected value with or without a checkmark so that it updates when it is changed and only shows when the dropdown is open
        :param option_type: The type of options to update (e.g., "language", "theme", "size").
        """

        selected_value = selected_value.replace(" ✓", "")  # Remove the checkmark 

        # Determine which options to use based on the option_type
        if option_type == "language":
            options = self.get_language_options(selected_value)
            deepl = DeepLTranslation()

            # Determine which tab the dropdown belongs to
            if dropdown in [self.ocr_from_language_combo, self.ocr_to_language_combo]:
                # OCR Translation tab
                from_language = self.ocr_from_language_combo.get().replace(" ✓", "")
                to_language = self.ocr_to_language_combo.get().replace(" ✓", "")

                # Check if the selected language is unsupported by DeepL if so disable the use DeepL checkbox
                if not deepl.is_language_supported(from_language) or not deepl.is_language_supported(to_language):
                    if not deepl.is_language_supported(from_language):
                        print(f"DEBUG: Disabled DeepL checkbox for OCR tab due to unsupported language: {from_language}")
                    if not deepl.is_language_supported(to_language):
                        print(f"DEBUG: Disabled DeepL checkbox for OCR tab due to unsupported language: {to_language}")
                    self.ocr_deepl_checkbox.deselect()
                    self.ocr_deepl_checkbox.configure(state="disabled")  # Disable the checkbox
                else:
                    # Only Re-enable the checkbox if the deepl_enabled flag is True (Valid API key in Creds.py)
                    if self.deepl_enabled:
                        self.ocr_deepl_checkbox.configure(state="normal")  # Re-enable the checkbox
                        print(f"DEBUG: Enabled DeepL checkbox for OCR tab with supported languages: {from_language}, {to_language}")
            elif dropdown in [self.from_language_combo, self.to_language_combo]:
                # Text Translation tab
                from_language = self.from_language_combo.get().replace(" ✓", "")
                to_language = self.to_language_combo.get().replace(" ✓", "")

                if not deepl.is_language_supported(from_language) or not deepl.is_language_supported(to_language):
                    if not deepl.is_language_supported(from_language):
                        print(f"DEBUG: Disabled DeepL checkbox for Text Translation tab due to unsupported language: {from_language}")
                    if not deepl.is_language_supported(to_language):
                        print(f"DEBUG: Disabled DeepL checkbox for Text Translation tab due to unsupported language: {to_language}")
                    self.text_deepl_checkbox.deselect()
                    self.text_deepl_checkbox.configure(state="disabled")  # Disable the checkbox
                else:
                    # Only Re-enable the checkbox if the deepl_enabled flag is True (Valid API key in Creds.py)
                    if self.deepl_enabled:
                        self.text_deepl_checkbox.configure(state="normal")  # Re-enable the checkbox
                        print(f"DEBUG: Enabled DeepL checkbox for Text Translation tab with supported languages: {from_language}, {to_language}")
        elif option_type == "theme":
            options = self.get_theme_options(selected_value)
            # Apply the selected theme
            theme_map = {"Light": "light", "Dark": "dark", "System": "system"}
            ctk.set_appearance_mode(theme_map[selected_value])
        elif option_type == "size":
            options = self.get_size_options(selected_value)
            # Apply the selected size
            desired_width, desired_height = map(int, selected_value.split('x'))
            self.geometry(f"{desired_width}x{desired_height}")
        else:
            raise ValueError(f"Unknown option_type: {option_type}")

        # Update the dropdown with the correct options
        dropdown.configure(values=options)
        dropdown.set(selected_value)  # Reset to plain text after selection

    def change_monitor(self, selected_monitor: str):
        """
        Update the selected monitor index based on the dropdown selection.
        """
        # Remove the checkmark from the selected monitor
        selected_monitor = selected_monitor.replace(" ✓", "")

        # Find the index of the selected monitor
        self.selected_monitor_index = next(
            (i for i, monitor in enumerate(self.monitors) if f"Monitor {i+1}: {monitor.width}x{monitor.height}" == selected_monitor),
            0
        )

        # Update the dropdown options with the selected monitor highlighted
        self.monitor_combo.configure(values=self.get_monitor_options(self.selected_monitor_index))
        # Set the selected value without the checkmark
        self.monitor_combo.set(f"Monitor {self.selected_monitor_index + 1}: {self.monitors[self.selected_monitor_index].width}x{self.monitors[self.selected_monitor_index].height}")

        print(f"DEBUG: Selected monitor index: {self.selected_monitor_index}")

    def change_translation_monitor(self, selected_monitor: str):
        """
        Update the selected translation output monitor index based on the dropdown selection.
        """
        # Remove the checkmark from the selected monitor
        selected_monitor = selected_monitor.replace(" ✓", "")

        # Find the index of the selected monitor
        self.selected_translation_monitor_index = next(
            (i for i, monitor in enumerate(self.monitors) if f"Monitor {i+1}: {monitor.width}x{monitor.height}" == selected_monitor),
            0
        )

        # Update the dropdown options with the selected monitor highlighted
        self.translation_monitor_combo.configure(values=self.get_monitor_options(self.selected_translation_monitor_index))
        # Set the selected value without the checkmark
        self.translation_monitor_combo.set(f"Monitor {self.selected_translation_monitor_index + 1}: {self.monitors[self.selected_translation_monitor_index].width}x{self.monitors[self.selected_translation_monitor_index].height}")

        print(f"DEBUG: Selected translation output monitor index: {self.selected_translation_monitor_index}")

    def update_ocr_volume_label(self, value):
        """
        Update the OCR volume percentage in the label above the slider.
        """
        percentage = int(float(value) * 100)  # Convert to percentage
        self.ocr_volume_label.configure(text=f"Text To Speech Volume: {percentage}%")
    
    def update_text_volume_label(self, value):
        """
        Update the Text Translation volume percentage in the label above the slider.
        """
        percentage = int(float(value) * 100)  # Convert to percentage
        self.text_volume_label.configure(text=f"Text To Speech Volume: {percentage}%")
    
    def speak_text(self, text, language_name, volume=0.5):
        """
        Uses gTTS to convert text to speech and play it using pygame in a separate thread.
        Adjusts the volume based on the slider value.
        """
        # Correct mapping of language names to gTTS language codes as they are not the same as the Google Translate or OCR ones
        tts_language_map = {
            'English': 'en',
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Chinese (Simplified)': 'zh-CN',
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
            'Hebrew': 'iw',
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
    
        # Get the correct gTTS language code
        language_code = tts_language_map.get(language_name, 'en')  # Default to English if not found
    
        def play_audio():
            try:
                tts = gTTS(text=text, lang=language_code)
                audio_file = "output.mp3"
                tts.save(audio_file)
    
                # Initialise pygame mixer and set volume
                pygame.mixer.init()
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.set_volume(volume)  # Set volume
                pygame.mixer.music.play()
                print(f"DEBUG: Audio playback started for text: {text} at volume: {volume}")
    
                # Wait for the audio to finish playing
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(1000)  # Wait for 1s to avoid busy-waiting
    
                # Stop the music and clean up the audio file
                print(f"DEBUG: Audio playback ended for text: {text}")
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                os.remove(audio_file)
            except Exception as e:
                print(f"Error in TTS: {e}")
    
        # Run the audio playback in a separate thread
        threading.Thread(target=play_audio, daemon=True).start()
    def translate_action(self):
        """
        Called when user clicks the Translate button.
        It reads the input text and selected source/target languages,
        then uses the appropriate translation service to perform the translation.
        """

        translator = TranslationHandling()
        deepl = DeepLTranslation()
        languages = translator.get_available_languages()
        selected_from = self.from_language_combo.get()
        selected_to = self.to_language_combo.get()
        src_key = next((k for k, (name, code) in languages.items() if name == selected_from), None)
        dest_key = next((k for k, (name, code) in languages.items() if name == selected_to), None)
        if src_key is None:
            src_key = '1'
        if dest_key is None:
            dest_key = '1'
        text = self.input_textbox.get("1.0", "end").strip()

        # Check if DeepL is enabled
        if self.text_deepl_checkbox.get():
            translation_result = deepl.translate_text(text, target_language=selected_to)
            print(f"DEBUG: Translated text using DeepL: {translation_result}")
        else:
            translation_result = translator.translator.translate(
                text, src=languages.get(src_key, ('', None))[1],
                dest=languages.get(dest_key, ('English', 'en'))[1]
            ).text
            print(f"DEBUG: Translated text using Google Translate: {translation_result}")

        self.output_textbox.delete("1.0", "end")
        self.output_textbox.insert("1.0", translation_result)

        # Check if TTS is enabled and speak the translated text
        if self.text_tts_checkbox.get():
            dest_language_name = languages.get(dest_key, ('English', 'en'))[0]
            volume = self.text_volume_slider.get()  # Get volume from slider
            self.speak_text(translation_result, dest_language_name, volume)

    def start_snip(self):
        # Get the selected monitor's resolution and position
        selected_monitor = self.monitors[self.selected_monitor_index]
        screen_width = selected_monitor.width
        screen_height = selected_monitor.height
        screen_x = selected_monitor.x
        screen_y = selected_monitor.y

        # Send the main application window to the bottom so the user can snip the screen without the app blocking it
        self.attributes("-topmost", False)  # Remove "always on top" attribute
        self.lower()  # Send the main application window to the bottom of the stacking order

        # Create a full-screen overlay using a Toplevel window
        self.snip_overlay = tk.Toplevel(self)
        self.snip_overlay.overrideredirect(True)         # Remove window decorations
        self.snip_overlay.attributes("-topmost", True)  # Ensure the overlay is on top
        self.snip_overlay.geometry(f"{screen_width}x{screen_height}+{screen_x}+{screen_y}")
        self.snip_overlay.attributes("-alpha", 0.3)     # Semi-transparent overlay
        self.snip_overlay.config(bg="black")

        # Explicitly set focus to the snip overlay
        self.snip_overlay.focus_force()

        # Create a canvas on the overlay for selection
        self.canvas = tk.Canvas(self.snip_overlay, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)
        self.start_x = None
        self.start_y = None
        self.rect = None

        # Bind mouse events for snip selection
        self.canvas.bind("<ButtonPress-1>", self.on_snip_press)
        self.canvas.bind("<B1-Motion>", self.on_snip_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_snip_release)

        # If the user presses either the Esc key or right mouse button the snip process will be canceled
        self.snip_overlay.bind("<Escape>", lambda event: self.cancel_snip())
        self.snip_overlay.bind("<Button-3>", lambda event: self.cancel_snip())

    def on_snip_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        # Create rectangle
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2)

    def on_snip_drag(self, event):
        curX, curY = event.x, event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_snip_release(self, event):
        # Finalise the selection
        end_x, end_y = event.x, event.y
        overlay_rootx = self.snip_overlay.winfo_rootx()
        overlay_rooty = self.snip_overlay.winfo_rooty()
        left = overlay_rootx + min(self.start_x, end_x)
        top = overlay_rooty + min(self.start_y, end_y)
        right = overlay_rootx + max(self.start_x, end_x)
        bottom = overlay_rooty + max(self.start_y, end_y)
        region = {"top": int(top), "left": int(left), "width": int(right - left), "height": int(bottom - top)}
        print(f"DEBUG: Selected region {region}")

        # Use mss to capture the selected region
        with mss.mss() as sct:
            try:
                snip_image = sct.grab(region)
                snip_image = Image.frombytes("RGB", snip_image.size, snip_image.rgb)
            except Exception as e:
                print(f"DEBUG: Error capturing region with mss: {e}")
                return

        # Validate dimensions
        w, h = snip_image.size
        print(f"DEBUG: Captured image size: {w}x{h}")
        if w == 0 or h == 0:
            print("DEBUG: Invalid capture region.")
            return

        # Close the snip overlay
        self.snip_overlay.destroy()

        # Perform OCR in a separate thread
        threading.Thread(target=self.perform_ocr_in_thread, args=(snip_image, region), daemon=True).start()

    def perform_ocr_in_thread(self, snip_image, region):
        """
        Perform OCR processing in a separate thread.
        """
        try:
            combined_text, paragraphs = perform_ocr(
                snip_image,
                lang_name=self.ocr_from_language_combo.get(),
                use_preprocessing=self.enable_preprocessing.get(),
                use_google_vision=self.use_google_vision_checkbox.get(),
                debug=True
            )
            print(f"DEBUG: Combined OCR text: {combined_text}")
        except Exception as ocr_error:
            print(f"DEBUG: OCR error: {ocr_error}")
            combined_text, paragraphs = "", []

        # Process the OCR result
        self.process_ocr_result(combined_text, region, paragraphs)

    def process_ocr_result(self, text, region, bounding_boxes):
        """
        Process the OCR result and initiate translation.
        """
        if not text:
            print("DEBUG: No text detected.")
            return

        # Perform translation in a separate thread
        selected_to_language = self.ocr_to_language_combo.get()
        threading.Thread(target=self.perform_translation_in_thread, args=(text, selected_to_language, region, bounding_boxes), daemon=True).start()

    def perform_translation_in_thread(self, text, dest_language, region, bounding_boxes):
        """
        Perform translation in a separate thread.
        """
        try:
            translated_paragraphs = perform_translation(
                bounding_boxes,
                target_lang=dest_language,
                use_deepl=self.ocr_deepl_checkbox.get()
            )
            print(f"DEBUG: Translated paragraphs: {translated_paragraphs}")
        except Exception as translation_error:
            print(f"DEBUG: Translation error: {translation_error}")
            translated_paragraphs = []

        # Process the translation result
        self.process_translation_result(translated_paragraphs, region, bounding_boxes)

    def process_translation_result(self, translated_paragraphs, region=None, ocr_paragraphs=None):
        """
        Process the translated text and update the GUI.
        """
        if self.region_based_checkbox.get():
            # Use region-based translation
            self.after(0, lambda: self.show_translation_in_region(region, translated_paragraphs, ocr_paragraphs))
        else:
            # Use popup-based translation
            combined_text = "\n".join(translated_paragraphs)
            self.after(0, lambda: self.show_translation(region, combined_text))

    def cancel_snip(self):
        """
        Cancels the snip selection process and closes the snip overlay.
        """
        print("DEBUG: Snip selection canceled by user.")
        if self.snip_overlay:
            # Destroy the overlay window
            self.snip_overlay.destroy()
            self.snip_overlay = None

    def show_translation(self, region, translated_text):
        """
        Display the translated text in a popup window.
        """
        # Reuse translation_popup if it exists, otherwise create it
        if self.translation_popup is None or not self.translation_popup.winfo_exists():
            self.translation_popup = ctk.CTkToplevel(self)
            self.translation_popup.title("Translation")
            
            # Create a textbox for displaying the translation
            self.translation_textbox = ctk.CTkTextbox(self.translation_popup, wrap="word")  # Enable word wrapping
            self.translation_textbox.pack(fill="both", expand=True, padx=10, pady=10)

            # Bind resizing of the popup window to adjust the textbox size
            self.translation_popup.bind("<Configure>", self.resize_textbox)
        else:
            # Update the text in the existing textbox
            self.translation_textbox.configure(state="normal")  # Temporarily enable editing
            self.translation_textbox.delete("1.0", "end")
        
        # Insert the translated text
        self.translation_textbox.insert("1.0", translated_text)
        self.translation_textbox.configure(state="disabled")  # Disable editing

        # Calculate the required size for the textbox
        lines = translated_text.split("\n")
        max_line_length = max(len(line) for line in lines)
        char_width = 8  # Approximate width of a character in pixels
        line_height = 20  # Approximate height of a line in pixels
        textbox_width = max_line_length * char_width
        textbox_height = len(lines) * line_height

        # Enforce minimum and maximum sizes for the textbox
        min_width = 200  # Minimum width in pixels
        max_width = 800  # Maximum width in pixels
        min_height = 100  # Minimum height in pixels
        max_height = int(self.winfo_screenheight() * 0.75)  # 75% of screen height
        textbox_width = max(min_width, min(textbox_width, max_width))
        textbox_height = max(min_height, min(textbox_height, max_height))

        # Update the popup window size to fit the textbox
        window_width = textbox_width + 20  # Add padding for the window
        window_height = textbox_height + 20  # Add padding for the window

        # Handle cases where region is None
        if region is None:
            # Centre the popup on the screen
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
        else:
            # Map region position from input monitor to output monitor
            in_mon = self.monitors[self.selected_monitor_index]
            out_mon = self.monitors[self.selected_translation_monitor_index]

            iw, ih = in_mon.width, in_mon.height
            ix, iy = in_mon.x, in_mon.y

            ow, oh = out_mon.width, out_mon.height
            ox, oy = out_mon.x, out_mon.y

            # Calculate relative position inside input monitor
            x_relative = (region['left'] - ix) / iw
            y_relative = (region['top'] - iy) / ih

            # Map relative position to output monitor
            x = int(x_relative * ow) + ox
            y = int(y_relative * oh) + oy

        self.translation_popup.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Set the initial size of the textbox
        self.translation_textbox.configure(width=textbox_width, height=textbox_height)

        # Check if TTS is enabled for OCR tab and speak the translated text
        if self.ocr_tts_checkbox.get():
            selected_to = self.ocr_to_language_combo.get()  # Get the selected language name
            volume = self.ocr_volume_slider.get()  # Get volume from slider
            self.speak_text(translated_text, selected_to, volume)  # Pass the language name

    def resize_textbox(self, event):
        """
        Adjust the width of the textbox when the popup window is resized.
        """
        if self.translation_popup is not None and self.translation_textbox is not None:
            # Get the current width of the popup window
            window_width = self.translation_popup.winfo_width()
    
            # Calculate the new width in characters (approximate character width is 8 pixels)
            new_width = max(20, (window_width - 40) // 8)  # Ensure a minimum width of 20 characters
            self.translation_textbox.configure(width=new_width)

    def show_translation_in_region(self, region, translated_paragraphs, ocr_paragraphs):
        """
        Display the translated text in the same region as the original snip area,
        scaled to the output monitor, using a frameless overlay.
        """
        if not ocr_paragraphs:
            print("DEBUG: No paragraphs provided for region-based translation.")
            return

        # Debug: Print the number of paragraphs and their content
        print(f"DEBUG: Total paragraphs to display: {len(ocr_paragraphs)}")
        for i, para in enumerate(ocr_paragraphs):
            print(f"DEBUG: Paragraph {i}: {para['text']}")

        # Get input and output monitors
        in_mon = self.monitors[self.selected_monitor_index]
        out_mon = self.monitors[self.selected_translation_monitor_index]

        # Input monitor dimensions
        iw, ih = in_mon.width, in_mon.height
        ix, iy = in_mon.x, in_mon.y

        # Output monitor dimensions
        ow, oh = out_mon.width, out_mon.height
        ox, oy = out_mon.x, out_mon.y

        # Compute scaled region offset & size on output monitor
        x_offset = int((region['left'] - ix) * ow / iw) + ox
        y_offset = int((region['top'] - iy) * oh / ih) + oy
        reg_w = int(region['width'] * ow / iw)
        reg_h = int(region['height'] * oh / ih)

        # Add padding around the content
        padding = 8
        overlay_w = reg_w + padding * 2
        overlay_h = reg_h + padding * 2
        overlay_x = x_offset - padding
        overlay_y = y_offset - padding

        # Ensure the overlay is within the bounds of the output monitor
        overlay_x = max(ox, min(overlay_x, ox + ow - overlay_w))
        overlay_y = max(oy, min(overlay_y, oy + oh - overlay_h))

        # Destroy any existing overlay
        if hasattr(self, 'translation_overlay') and self.translation_overlay.winfo_exists():
            self.translation_overlay.destroy()

        # Create frameless overlay
        self.translation_overlay = tk.Toplevel(self)
        self.translation_overlay.overrideredirect(True)        # No frame
        self.translation_overlay.attributes("-topmost", True)  # Always on top
        self.translation_overlay.config(bg="white")
        self.translation_overlay.geometry(f"{overlay_w}x{overlay_h}+{overlay_x}+{overlay_y}")

        # Custom close “✕” button
        btn = tk.Button(
            self.translation_overlay,
            text="✕",
            bd=0,  # no border
            highlightthickness=0,
            font=("Arial", 12, "bold"),
            bg="white",
            activebackground="lightgrey",
            command=self.translation_overlay.destroy
        )
        btn.place(x=overlay_w - 20, y=4, width=16, height=16)

        # Place each paragraph
        for i, para in enumerate(ocr_paragraphs):
            # Use the corresponding translated paragraph if available
            text = translated_paragraphs[i] if i < len(translated_paragraphs) else para['text']

            # Scale and offset per-paragraph box
            sx = int(para['x'] * ow / iw) + padding
            sy = int(para['y'] * oh / ih) + padding
            sw = int(para['width'] * ow / iw)
            sh = int(para['height'] * oh / ih)

            # Add spacing between paragraphs
            spacing = 10  # Add 10 pixels of spacing between paragraphs
            sy += i * spacing

            # Enforce minimum sizes
            sw = max(sw, 100)
            sh = max(sh, 30)

            # Debug: Print the size and position of each label
            print(f"DEBUG: Label {i} - x: {sx}, y: {sy}, width: {sw}, height: {sh}")

            # Choose a font size
            font_size = max(10, min(20, sh // 2))

            lbl = tk.Label(
                self.translation_overlay,
                text=text,
                bg="white",
                fg="black",
                font=("Arial", font_size),
                anchor="nw",
                justify="left",
                wraplength=sw  # Wrap text to fit within the width of the label
            )
            lbl.place(x=sx, y=sy, width=sw, height=sh)

            # Trigger TTS for each paragraph if enabled
            if self.ocr_tts_checkbox.get():
                selected_to = self.ocr_to_language_combo.get()  # Get the selected language name
                volume = self.ocr_volume_slider.get()  # Get volume from slider
                self.speak_text(text, selected_to, volume)  # Pass the language name