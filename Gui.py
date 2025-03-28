import customtkinter as ctk
import tkinter as tk
from PIL import Image
from gtts import gTTS
import os
from Translation import TranslationHandling
import pygame
import threading
from screeninfo import get_monitors
import mss
import webbrowser

# Class to handle the GUI for the application
class MainGui(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.tk.call('tk', 'scaling', 1.0)  # Disable DPI scaling for the main window to ensure nothing is scaled
        self.geometry("1280x720")  # Set the initial size before creating widgets
        self.title('Live-Translate')
        self.resizable(False, False)  
        ctk.set_appearance_mode('light')  # Set default theme
        ctk.set_widget_scaling(1.0)

        # Keep a reference to the translation popup so it gets reused
        self.translation_popup = None

        # Create a Tabview widget for two pages
        self.tabview = ctk.CTkTabview(self, width=600, height=600)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabview.add("OCR Translation")  # Renamed Tab 1
        self.tabview.add("Text Translation")  # Renamed Tab 2

        # Add a dropdown menu for theme selection
        self.theme_menu = ctk.CTkOptionMenu(
            self,
            values=self.get_theme_options("Light"),  # Dynamically generate options
            command=lambda theme: self.change_dropdown(self.theme_menu, theme, "theme")
        )
        self.theme_menu.set("Light")  # Set default theme
        self.theme_menu.place(relx=0.95, rely=0.05, anchor="ne")  # Position at top-right

        # Add a size dropdown menu for preset window sizes
        self.size_menu = ctk.CTkOptionMenu(
            self,
            values=self.get_size_options("1280x720"),  # Dynamically generate options
            command=lambda size: self.change_dropdown(self.size_menu, size, "size")
        )
        self.size_menu.set("1280x720")  # Set default size
        self.size_menu.place(relx=0.05, rely=0.05, anchor="nw")

        # -----------------
        # Tab 1: OCR Translation
        # Add a scrollable frame for the OCR Translation tab
        self.ocr_tab_frame = ctk.CTkScrollableFrame(self.tabview.tab("OCR Translation"), width=600, height=600)
        self.ocr_tab_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Available languages list
        self.available_language_names = [
            'English', 'Spanish', 'French', 'German', 'Chinese (Simplified)',
            'Japanese', 'Korean', 'Russian', 'Italian', 'Portuguese',
            'Dutch', 'Greek', 'Arabic', 'Hindi', 'Bengali', 'Turkish',
            'Vietnamese', 'Polish', 'Ukrainian', 'Hebrew', 'Swedish',
            'Norwegian', 'Finnish', 'Danish', 'Hungarian', 'Czech',
            'Romanian', 'Thai', 'Indonesian', 'Malay', 'Filipino', 'Swahili'
        ]

        # Add widgets to the scrollable frame
        self.ocr_from_label = ctk.CTkLabel(self.ocr_tab_frame, text="From Language:")
        self.ocr_from_label.pack(padx=10, pady=(10, 0))
        self.ocr_from_language_combo = ctk.CTkComboBox(
            self.ocr_tab_frame,
            values=self.get_language_options("Chinese (Simplified)"),  # Dynamically generate options
            command=lambda language: self.change_dropdown(self.ocr_from_language_combo, language, "language")
        )
        self.ocr_from_language_combo.set("Chinese (Simplified)")  # Set default to Chinese (Simplified)
        self.ocr_from_language_combo.pack(padx=10, pady=10)

        self.ocr_to_label = ctk.CTkLabel(self.ocr_tab_frame, text="To Language:")
        self.ocr_to_label.pack(padx=10, pady=(10, 0))
        self.ocr_to_language_combo = ctk.CTkComboBox(
            self.ocr_tab_frame,
            values=self.get_language_options("English"),  # Dynamically generate options
            command=lambda language: self.change_dropdown(self.ocr_to_language_combo, language, "language")
        )
        self.ocr_to_language_combo.set("English")  # Set default to English
        self.ocr_to_language_combo.pack(padx=10, pady=10)

        # Select Area button for OCR translation
        self.select_area_btn = ctk.CTkButton(
            self.ocr_tab_frame,
            text="Select Area",
            command=self.start_snip
        )
        self.select_area_btn.pack(padx=20, pady=20)

        # Add "Enable Text To Speech" checkbox to OCR Translation tab
        self.ocr_tts_checkbox = ctk.CTkCheckBox(self.ocr_tab_frame, text="Enable Text To Speech")
        self.ocr_tts_checkbox.pack(padx=10, pady=(10, 0))

        # Add a label for the volume slider with dynamic percentage
        self.ocr_volume_label = ctk.CTkLabel(self.ocr_tab_frame, text="Text To Speech Volume: 20%")
        self.ocr_volume_label.pack(padx=10, pady=(5, 0))
        
        # Add volume slider for OCR Translation tab
        self.ocr_volume_slider = ctk.CTkSlider(self.ocr_tab_frame, from_=0.0, to=1.0, width=150, command=self.update_ocr_volume_label)
        self.ocr_volume_slider.set(0.2)  # Default volume (20%)
        self.ocr_volume_slider.pack(padx=10, pady=(5, 0))

        # Add a monitor selection dropdown to the OCR tab
        self.monitor_label = ctk.CTkLabel(self.ocr_tab_frame, text="Select Monitor:")
        self.monitor_label.pack(padx=10, pady=(10, 0))

        # Get monitor names and resolutions
        self.monitors = get_monitors()
        monitor_options = [f"Monitor {i+1}: {monitor.width}x{monitor.height}" for i, monitor in enumerate(self.monitors)]

        self.monitor_combo = ctk.CTkOptionMenu(
            self.ocr_tab_frame,
            values=self.get_monitor_options(0),  # Dynamically generate options with checkmark
            command=lambda monitor: self.change_monitor(monitor)
        )
        self.monitor_combo.set(monitor_options[0])  # Default to the first monitor
        self.monitor_combo.pack(padx=10, pady=10)

        # Store the selected monitor index
        self.selected_monitor_index = 0

        # Add "Region Based Translation" checkbox to OCR Translation tab
        self.region_based_checkbox = ctk.CTkCheckBox(self.ocr_tab_frame, text="Region Based Translation")
        self.region_based_checkbox.pack(padx=10, pady=(10, 0))

        # Add a dropdown for selecting the translation output monitor
        self.translation_monitor_label = ctk.CTkLabel(self.ocr_tab_frame, text="Select Translation Output Monitor:")
        self.translation_monitor_label.pack(padx=10, pady=(10, 0))

        # Get monitor options without the checkmark for the default value
        monitor_options = self.get_monitor_options(0)  # Dynamically generate options with checkmark
        default_monitor_option = monitor_options[0].replace(" ✓", "")  # Remove the checkmark from the default value

        self.translation_monitor_combo = ctk.CTkOptionMenu(
            self.ocr_tab_frame,
            values=monitor_options,  # Options with checkmarks
            command=lambda monitor: self.change_translation_monitor(monitor)
        )
        self.translation_monitor_combo.set(default_monitor_option)  # Set default value without the checkmark
        self.translation_monitor_combo.pack(padx=10, pady=10)

        
        # Early Prototype Feedback Link
        # Adds a clickable label to the OCR tab for feedback
        self.feedback_label_ocr = tk.Label(
            self.ocr_tab_frame,
            text="Click here to give feedback",
            fg="red",
            font=("Arial", 16, "underline"),
            cursor="hand2"
        )
        self.feedback_label_ocr.pack(pady=(10, 20))
        self.feedback_label_ocr.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://docs.google.com/forms/d/e/1FAIpQLSe37Amony4UaaPBc4rt56xW4ragBvCjR238B7cc4UmmIpvf0Q/viewform")
        )


        # Store the selected translation output monitor index
        self.selected_translation_monitor_index = 0

        # -----------------
        # Tab 2: Text Translation
        # Add a scrollable frame for the Text Translation tab
        self.text_translation_tab_frame = ctk.CTkScrollableFrame(self.tabview.tab("Text Translation"), width=600, height=600)
        self.text_translation_tab_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Add widgets to the scrollable frame
        self.from_label = ctk.CTkLabel(self.text_translation_tab_frame, text="From Language:")
        self.from_label.pack(padx=10, pady=(10, 0))

        self.from_language_combo = ctk.CTkComboBox(
            self.text_translation_tab_frame,
            values=self.get_language_options("English"),
            command=lambda language: self.change_dropdown(self.from_language_combo, language, "language")
        )
        self.from_language_combo.set("English")  # Set default value
        self.from_language_combo.pack(padx=10, pady=10)

        self.to_label = ctk.CTkLabel(self.text_translation_tab_frame, text="To Language:")
        self.to_label.pack(padx=10, pady=(10, 0))

        self.to_language_combo = ctk.CTkComboBox(
            self.text_translation_tab_frame,
            values=self.get_language_options("Spanish"),
            command=lambda language: self.change_dropdown(self.to_language_combo, language, "language")
        )
        self.to_language_combo.set("Spanish")  # Set default value
        self.to_language_combo.pack(padx=10, pady=10)

        # Input textbox for text to translate
        self.input_textbox = ctk.CTkTextbox(self.text_translation_tab_frame, width=500, height=150)
        self.input_textbox.pack(padx=10, pady=10)
        self.input_textbox.insert("0.0", "Enter text to translate here...")

        # Translate button for GUI mode
        self.translate_button = ctk.CTkButton(
            self.text_translation_tab_frame, text="Translate", command=self.translate_action,
        )
        self.translate_button.pack(padx=10, pady=10)

        # Output textbox for translated text
        self.output_textbox = ctk.CTkTextbox(self.text_translation_tab_frame, width=500, height=150)
        self.output_textbox.pack(padx=10, pady=10)
        self.output_textbox.insert("0.0", "Translation will appear here...")

        # Add "Enable Text To Speech" checkbox to Text Translation tab
        self.text_tts_checkbox = ctk.CTkCheckBox(self.text_translation_tab_frame, text="Enable Text To Speech")
        self.text_tts_checkbox.pack(padx=10, pady=(10, 0))

        # Add a label for the volume slider with dynamic percentage
        self.text_volume_label = ctk.CTkLabel(self.text_translation_tab_frame, text="Text To Speech Volume: 20%")
        self.text_volume_label.pack(padx=10, pady=(5, 0))
        
        # Add volume slider for Text Translation tab
        self.text_volume_slider = ctk.CTkSlider(self.text_translation_tab_frame, from_=0.0, to=1.0, width=150, command=self.update_text_volume_label)
        self.text_volume_slider.set(0.2)  # Default volume (20%)
        self.text_volume_slider.pack(padx=10, pady=(5, 0))

        # Early Prototype Feedback Link
        # Adds a clickable label to the text translation tab for feedback
        self.feedback_label_text = tk.Label(
            self.text_translation_tab_frame,
            text="Click here to give feedback",
            fg="red",
            font=("Arial", 16, "underline"),
            cursor="hand2"
        )
        self.feedback_label_text.pack(pady=(10, 20))
        self.feedback_label_text.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://docs.google.com/forms/d/e/1FAIpQLSe37Amony4UaaPBc4rt56xW4ragBvCjR238B7cc4UmmIpvf0Q/viewform")
        )

        # Bind the right Alt key to re-trigger the snip process
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
        sizes = ["640x360", "854x480", "1280x720", "1600x900", "1920x1080"]
        return [f"{size} ✓" if size == selected_size else size for size in sizes]

    def get_monitor_options(self, selected_index):
        """
        Generate a list of monitor options with a checkmark after the currently selected monitor.
        """
        return [
            f"Monitor {i+1}: {monitor.width}x{monitor.height} ✓" if i == selected_index else f"Monitor {i+1}: {monitor.width}x{monitor.height}"
            for i, monitor in enumerate(self.monitors)
        ]

    def change_dropdown(self, dropdown, selected_value: str, option_type: str):
        """
        Update a dropdown's options and reset the selected text.
        :param dropdown: The dropdown widget to update.
        :param selected_value: The selected value with or without a checkmark.
        :param option_type: The type of options to update (e.g., "language", "theme", "size").
        """
        selected_value = selected_value.replace(" ✓", "")  # Remove the checkmark
    
        # Determine which options to use based on the option_type
        if option_type == "language":
            options = self.get_language_options(selected_value)
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
    
    def speak_text(self, text, language_code, volume=0.5):
        """
        Uses gTTS to convert text to speech and play it using pygame in a separate thread.
        Adjusts the volume based on the slider value.
        """
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
        then uses TranslationHandling to perform the translation.
        """
        from Translation import TranslationHandling
        translator = TranslationHandling()
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
        translation_result = translator.translator.translate(
            text, src=languages.get(src_key, ('', None))[1],
            dest=languages.get(dest_key, ('English', 'en'))[1]
        ).text
        self.output_textbox.delete("1.0", "end") # Clear previous output
        self.output_textbox.insert("1.0", translation_result) # Insert the translated text

        # Check if TTS is enabled and speak the translated text
        if self.text_tts_checkbox.get():
            dest_language_code = languages.get(dest_key, ('English', 'en'))[1]
            volume = self.text_volume_slider.get()  # Get volume from slider
            self.speak_text(translation_result, dest_language_code, volume)

    def start_snip(self):
        # Get the selected monitor's resolution and position
        selected_monitor = self.monitors[self.selected_monitor_index]
        screen_width = selected_monitor.width
        screen_height = selected_monitor.height
        screen_x = selected_monitor.x
        screen_y = selected_monitor.y

        # Ensure the user can snip something underneath the main window
        # Send the main application window to the bottom
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

        # Use mss to capture the selected region as an image
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
        import pytesseract
        selected_from_language = self.ocr_from_language_combo.get()
        ocr_language = self.get_ocr_language_code(selected_from_language)

        try:
            # Perform OCR and get bounding boxes
            ocr_data = pytesseract.image_to_data(snip_image, lang=ocr_language, output_type=pytesseract.Output.DICT)
            print(f"DEBUG: OCR data keys: {ocr_data.keys()}")

            # Group lines into paragraphs
            paragraphs = group_lines_into_paragraphs(ocr_data)
            print(f"DEBUG: Grouped paragraphs: {paragraphs}")

            # Combine all paragraph text into a single string for translation
            if ocr_language in ['chi_sim', 'chi_tra']:  # For Chinese, remove spaces
                combined_text = "".join([p["text"] for p in paragraphs])
            else:  # For other languages, keep spaces
                combined_text = " ".join([p["text"] for p in paragraphs])
            print(f"DEBUG: Combined OCR text: {combined_text}")
        except Exception as ocr_error:
            print("DEBUG: OCR error:", ocr_error)
            combined_text = ""
            paragraphs = []

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
        from Translation import TranslationHandling
        translator = TranslationHandling()
        try:
            translated_text = translator.translate_text(text, dest_language)
            print(f"DEBUG: Translated text: {translated_text}")
            self.process_translation_result(translated_text, region, bounding_boxes)
        except Exception as e:
            print(f"DEBUG: Translation error: {e}")
            self.process_translation_result("", region, bounding_boxes)

    def process_translation_result(self, translated_text, region=None, ocr_paragraphs=None):
        """
        Process the translated text and update the GUI.
        """
        if self.region_based_checkbox.get():
            # Use region-based translation
            self.after(0, lambda: self.show_translation_in_region(region, translated_text, ocr_paragraphs))
        else:
            # Use popup-based translation
            self.after(0, lambda: self.show_translation(region, translated_text))

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
            self.translation_textbox = ctk.CTkTextbox(self.translation_popup)
            self.translation_textbox.pack(padx=10, pady=10)
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

        # Enforce minimum size for the textbox
        min_width = 200  # Minimum width in pixels
        min_height = 100  # Minimum height in pixels
        textbox_width = max(textbox_width, min_width)
        textbox_height = max(textbox_height, min_height)

        # Update the textbox size
        self.translation_textbox.configure(width=textbox_width, height=textbox_height)

        # Update the popup window size to fit the textbox
        window_width = textbox_width + 20  # Add padding for the window
        window_height = textbox_height + 20  # Add padding for the window

        # Handle cases where region is None
        if region is None:
            # Center the popup on the screen
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
        else:
            # Position the popup based on the region
            x = region['left']
            y = region['top']

        self.translation_popup.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Check if TTS is enabled for OCR tab and speak the translated text
        if self.ocr_tts_checkbox.get():
            selected_to = self.ocr_to_language_combo.get()
            languages = TranslationHandling().get_available_languages()
            dest_language_code = next(
                (code for name, code in languages.values() if name == selected_to), 'en'
            )
            volume = self.ocr_volume_slider.get()  # Get volume from slider
            self.speak_text(translated_text, dest_language_code, volume)

    def show_translation_in_region(self, region, translated_text, ocr_paragraphs):
        """
        Display the translated text in the same region as the original snip area,
        scaled to the output monitor, using a frameless overlay.
        """
        if not ocr_paragraphs:
            print("DEBUG: No paragraphs provided for region-based translation.")
            return

        # Get monitors
        out_mon = self.monitors[self.selected_translation_monitor_index]
        in_mon = self.monitors[self.selected_monitor_index]
        ow, oh = out_mon.width, out_mon.height
        iw, ih = in_mon.width, in_mon.height

        # Compute scaled region offset & size on output monitor
        x_offset = int(region['left'] * ow / iw)
        y_offset = int(region['top'] * oh / ih)
        reg_w = int(region['width'] * ow / iw)
        reg_h = int(region['height'] * oh / ih)

        # Add padding around the content
        padding = 8
        overlay_w = reg_w + padding * 2
        overlay_h = reg_h + padding * 2
        overlay_x = out_mon.x + x_offset - padding
        overlay_y = out_mon.y + y_offset - padding

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
        lines = translated_text.split("\n")
        for i, para in enumerate(ocr_paragraphs):
            if i >= len(lines):
                break
            text = lines[i]

            # Scale and offset per-paragraph box
            sx = int(para['x'] * ow / iw) + padding
            sy = int(para['y'] * oh / ih) + padding
            sw = int(para['width'] * ow / iw)
            sh = int(para['height'] * oh / ih)

            # Enforce minimum sizes
            sw = max(sw, 100)
            sh = max(sh, 30)

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
                wraplength=sw
            )
            lbl.place(x=sx, y=sy, width=sw, height=sh)

    def get_ocr_language_code(self, selected_language):
        """
        Map the selected language to the corresponding Tesseract OCR language code.
        """
        language_map = {
            'English': 'eng',
            'Spanish': 'spa',
            'French': 'fra',
            'German': 'deu',
            'Chinese (Simplified)': 'chi_sim',
            'Chinese (Traditional)': 'chi_tra',
            'Japanese': 'jpn',
            'Korean': 'kor',
            'Russian': 'rus',
            'Italian': 'ita',
            'Portuguese': 'por',
            'Dutch': 'nld',
            'Greek': 'ell',
            'Arabic': 'ara',
            'Hindi': 'hin',
            'Bengali': 'ben',
            'Turkish': 'tur',
            'Vietnamese': 'vie',
            'Polish': 'pol',
            'Ukrainian': 'ukr',
            'Hebrew': 'heb',
            'Swedish': 'swe',
            'Norwegian': 'nor',
            'Finnish': 'fin',
            'Danish': 'dan',
            'Hungarian': 'hun',
            'Czech': 'ces',
            'Romanian': 'ron',
            'Thai': 'tha',
            'Indonesian': 'ind',
            'Malay': 'msa',
            'Filipino': 'fil',
            'Swahili': 'swa',
        }
        return language_map.get(selected_language, 'eng')  # Default to English if not found

def group_lines_into_paragraphs(ocr_data):
    """
    Group lines of text into paragraphs based on their vertical and horizontal positions.
    """
    paragraphs = []
    current_paragraph = {"x": None, "y": None, "width": 0, "height": 0, "text": ""}

    for i in range(len(ocr_data['text'])):
        if ocr_data['text'][i].strip() and ocr_data['width'][i] > 1 and ocr_data['height'][i] > 1:
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            width = ocr_data['width'][i]
            height = ocr_data['height'][i]
            text = ocr_data['text'][i].strip()

            # If this is the first line in the paragraph
            if current_paragraph["x"] is None:
                current_paragraph["x"] = x
                current_paragraph["y"] = y
                current_paragraph["width"] = width
                current_paragraph["height"] = height
                current_paragraph["text"] = text
            else:
                # Check if the line is close enough vertically or horizontally to be part of the same paragraph
                if (abs(y - (current_paragraph["y"] + current_paragraph["height"])) < 50 or  # Relaxed vertical proximity
                    abs(x - (current_paragraph["x"] + current_paragraph["width"])) < 100):  # Horizontal continuity
                    # Expand the paragraph bounding box
                    current_paragraph["x"] = min(current_paragraph["x"], x)
                    current_paragraph["y"] = min(current_paragraph["y"], y)
                    current_paragraph["width"] = max(current_paragraph["x"] + current_paragraph["width"], x + width) - current_paragraph["x"]
                    current_paragraph["height"] = max(current_paragraph["y"] + current_paragraph["height"], y + height) - current_paragraph["y"]
                    current_paragraph["text"] += " " + text
                else:
                    # Save the current paragraph and start a new one
                    paragraphs.append(current_paragraph)
                    current_paragraph = {"x": x, "y": y, "width": width, "height": height, "text": text}

    # Add the last paragraph
    if current_paragraph["x"] is not None:
        paragraphs.append(current_paragraph)

    return paragraphs
