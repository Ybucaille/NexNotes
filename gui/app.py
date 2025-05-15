import customtkinter as ctk
from PIL import Image
from tkinterdnd2 import DND_FILES, TkinterDnD
from customtkinter import filedialog
import os
from core.summarizer import summarize_text
from core.audio_to_text import transcribe_audio
import threading

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class NexNotesV2App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        # Wrapper principal CustomTkinter dans la fenêtre TkinterDnD
        self.ctk_container = ctk.CTkFrame(self, fg_color="#121212")
        self.ctk_container.pack(fill="both", expand=True)

        # === Fenêtre principale native ===
        self.geometry("900x470+303+203")
        self.iconbitmap("assets/icon.ico")
        self.title("NexNotes")
        self.resizable(False, False)
        self.bind("<Escape>", lambda e: self.destroy())

        self.default_filenames = {
        "text": "résumé.txt",
        "audio": "transcription.txt"
        }

        # === ASSETS ===
        self.icon_copy = ctk.CTkImage(Image.open("assets/copy.png"), size=(18, 18))
        self.icon_export = ctk.CTkImage(Image.open("assets/export.png"), size=(18, 18))
        self.icon_download = ctk.CTkImage(Image.open("assets/download.png"), size=(16, 16))
        self.active_tab = "Texte"
        self.summary_mode = "Auto (préférer local)"

        # === TABS ===
        self.header = ctk.CTkFrame(self.ctk_container, fg_color="transparent")
        self.header.pack(padx=25, pady=(20, 10), fill="x")

        self.tab_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.tab_frame.pack(side="right")

        self.text_tab = ctk.CTkButton(
            self.tab_frame, text="Texte", width=90, height=32,
            fg_color="#2c2c2c", hover_color="#222222",
            border_color="#3a3a3a", border_width=1,
            text_color="#00cccc", font=("Helvetica", 14, "bold"),
            corner_radius=6, command=lambda: self.set_tab("Texte")
        )
        self.text_tab.grid(row=0, column=0, padx=4)

        self.audio_tab = ctk.CTkButton(
            self.tab_frame, text="Audio", width=90, height=32,
            fg_color="transparent", hover_color="#1a1a1a",
            border_color="#444444", border_width=1,
            text_color="#aaaaaa", font=("Helvetica", 14),
            corner_radius=6, command=lambda: self.set_tab("Audio")
        )
        self.audio_tab.grid(row=0, column=1, padx=4)
        self.audio_mode = "Auto (préférer local)"

        # === CONTENEUR TEXTE ===
        self.text_tab_frame = ctk.CTkFrame(self.ctk_container, fg_color="transparent")
        self.text_tab_frame.pack(fill="both", expand=True)

        # === CONTENEUR AUDIO ===
        self.audio_tab_frame = ctk.CTkFrame(self.ctk_container, fg_color="transparent")
        self.audio_tab_frame.pack_forget()

        # Frame principale avec grid (top + footer)
        self.audio_main_container = ctk.CTkFrame(self.audio_tab_frame, fg_color="transparent")
        self.audio_main_container.pack(fill="both", expand=True)
        self.audio_main_container.grid_rowconfigure(0, weight=1)
        self.audio_main_container.grid_columnconfigure(0, weight=1)

        # Haut : dropzone + champ transcription
        self.audio_top_container = ctk.CTkFrame(self.audio_main_container, fg_color="transparent")
        self.audio_top_container.grid(row=0, column=0, sticky="nsew")

        # Dropzone
        self.dropzone = ctk.CTkFrame(self.audio_top_container, width=300, height=160, corner_radius=10, fg_color="#1e1e1e")
        self.dropzone.pack(pady=(40, 10))
        self.dropzone.drop_target_register(DND_FILES)
        self.dropzone.dnd_bind("<<Drop>>", self.handle_drop)
        self.dropzone.pack_propagate(False)

        self.dropzone_label = ctk.CTkLabel(
            self.dropzone, text="Déposez un fichier audio\nou cliquez ici", justify="center",
            font=("Helvetica", 14), text_color="#cccccc"
        )
        self.dropzone_label.pack(expand=True)

        def on_click(event=None):
            self.import_audio_file()

        self.dropzone.bind("<Button-1>", on_click)
        self.dropzone_label.bind("<Button-1>", on_click)

        # Texte formats
        self.audio_file_label = ctk.CTkLabel(
            self.audio_top_container,
            text="Formats supportés : .mp3, .wav, .m4a",
            text_color="#aaaaaa",
            font=("Helvetica", 12)
        )
        self.audio_file_label.pack(pady=(0, 10))

        # Boîte transcription
        self.transcription_box = ctk.CTkTextbox(
            self.audio_top_container, height=120, font=("JetBrains Mono", 15), wrap="word",
            corner_radius=8, fg_color="#1e1e1e", text_color="#eeeeee"
        )
        self.transcription_box.insert("0.0", "La transcription apparaîtra ici…")
        self.transcription_box.configure(state="disabled")
        self.transcription_box.pack(padx=25, pady=(0, 2), fill="x")

        # === Footer : boutons alignés en bas ===
        self.audio_button_container = ctk.CTkFrame(self.audio_main_container, fg_color="transparent")
        self.audio_button_container.grid(row=1, column=0, sticky="ew", padx=25, pady=12)

        self.audio_button_row_container = ctk.CTkFrame(self.audio_button_container, fg_color="transparent")
        self.audio_button_row_container.pack(fill="x", expand=True)

        self.audio_button_row = ctk.CTkFrame(self.audio_button_row_container, fg_color="transparent")
        self.audio_button_row.pack(side="right")

        # --- Copier ---
        self.copy_container = ctk.CTkFrame(self.audio_button_row, fg_color="transparent")
        self.copy_container.pack(side="left", padx=6)

        self.copy_feedback_label = ctk.CTkLabel(
            self.copy_container, text="", text_color="#00cccc", font=("Helvetica", 12, "bold"), height=18
        )
        self.copy_feedback_label.pack()

        ctk.CTkButton(
            self.copy_container, text="   Copier", image=self.icon_copy, compound="left",
            width=130, height=32, font=("Helvetica", 13),
            fg_color="#2a2a2a", hover_color="#3a3a3a", text_color="#e0e0e0",
            command=lambda: self.copy_textbox_content(self.transcription_box, self.copy_feedback_label)
        ).pack()

        # --- Exporter ---
        self.export_container = ctk.CTkFrame(self.audio_button_row, fg_color="transparent")
        self.export_container.pack(side="left", padx=6)

        self.export_feedback_label = ctk.CTkLabel(
            self.export_container, text="", text_color="#00cc66", font=("Helvetica", 12, "bold"), height=18
        )
        self.export_feedback_label.pack()

        ctk.CTkButton(
            self.export_container, text="   Exporter", image=self.icon_export, compound="left",
            width=130, height=32, font=("Helvetica", 13),
            fg_color="#2a2a2a", hover_color="#3a3a3a", text_color="#e0e0e0",
            command=lambda: self.export_textbox_to_file(self.transcription_box,self.export_feedback_label, self.default_filenames["audio"])
        ).pack()

        # --- Télécharger le modèle ---
        self.download_container = ctk.CTkFrame(self.audio_button_row, fg_color="transparent")
        self.download_container.pack(side="left", padx=10)

        self.download_feedback_label = ctk.CTkLabel(
            self.download_container, text="", text_color="#cccccc", font=("Helvetica", 12), height=18
        )
        self.download_feedback_label.pack()

        self.download_button_audio = ctk.CTkButton(
            self.download_container, text="   Télécharger le modèle (~2.8 Go)",
            image=self.icon_download, compound="left",
            width=230, height=32, font=("Helvetica", 13),
            fg_color="#2a2a2a", hover_color="#3a3a3a", text_color="#e0e0e0",
            command=lambda: self.download_model("audio")
        )
        self.download_button_audio.pack()

        # --- Selecteur de mode ---
        self.selector_container = ctk.CTkFrame(self.audio_button_row_container, fg_color="transparent")
        self.selector_container.pack(side="left", padx=(0, 10))

        self.selector_feedback_label = ctk.CTkLabel(
            self.selector_container, text="", text_color="#cccccc", font=("Helvetica", 12), height=18
        )
        self.selector_feedback_label.pack()

        self.audio_mode_selector = ctk.CTkOptionMenu(
            self.selector_container,
            values=["Auto (préférer local)", "Forcer Whisper local", "Forcer HuggingFace (cache)"],
            command=self.set_audio_mode,
            fg_color="#2a2a2a",
            button_color="#00897B",
            button_hover_color="#00796B",
            text_color="#eeeeee",
            dropdown_fg_color="#1f1f1f",
            dropdown_text_color="#cccccc",
            dropdown_hover_color="#333333",
            font=("Helvetica", 13),
            width=180
        )
        self.audio_mode_selector.pack()
        
        # === INPUT BOX ===
        self.input_box = ctk.CTkTextbox(self.text_tab_frame, height=120, font=("JetBrains Mono", 15), wrap="word", corner_radius=8)
        self.input_box.insert("0.0", "Saisissez ou collez votre texte…")
        self.input_box.configure(text_color="#eeeeee")
        self.input_box.pack(padx=25, pady=(10, 10), fill="x")

        # === BOUTON RÉSUMÉ ===
        self.summarize_button = ctk.CTkButton(
            self.text_tab_frame, text="Résumer", width=240, height=42,
            font=("Helvetica", 15, "bold"), fg_color="#00897B",
            hover_color="#00796B", corner_radius=8,
            command=self.summarize, text_color="white"
        )
        self.summarize_button.pack(pady=(5, 15))

        # === OUTPUT BOX ===
        self.output_box = ctk.CTkTextbox(self.text_tab_frame, height=120, font=("JetBrains Mono", 15), wrap="word",
                                        corner_radius=8, fg_color="#1e1e1e")
        self.output_box.insert("0.0", "La Rome antique était une civilisation italienne qui passa d'une monarchie à une république, puis à un empire,\ndominant la région méditerranéenne pendant des siècles.")
        self.output_box.configure(state="disabled", text_color="#eeeeee")
        self.output_box.pack(padx=25, pady=(0, 2), fill="x")

       # === CONTENEUR DES BOUTONS EN BAS (ONGLET TEXTE) ===
        self.button_container = ctk.CTkFrame(self.text_tab_frame, fg_color="transparent")
        self.button_container.pack(side="bottom", fill="x", padx=25, pady=12)

        # Conteneur horizontal principal
        self.button_row_container = ctk.CTkFrame(self.button_container, fg_color="transparent")
        self.button_row_container.pack(fill="x", expand=True)

        # Row droite
        self.button_row = ctk.CTkFrame(self.button_row_container, fg_color="transparent")
        self.button_row.pack(side="right")

        # --- Copier ---
        self.text_copy_container = ctk.CTkFrame(self.button_row, fg_color="transparent")
        self.text_copy_container.pack(side="left", padx=6)

        self.text_copy_feedback_label = ctk.CTkLabel(
            self.text_copy_container, text="", text_color="#00cccc", font=("Helvetica", 12, "bold"), height=18
        )
        self.text_copy_feedback_label.pack()

        ctk.CTkButton(
            self.text_copy_container, text="   Copier", image=self.icon_copy, compound="left",
            width=130, height=32, font=("Helvetica", 13),
            fg_color="#2a2a2a", hover_color="#3a3a3a", text_color="#e0e0e0",
            command=lambda: self.copy_textbox_content(self.output_box, self.text_copy_feedback_label)
        ).pack()

        # --- Exporter ---
        self.text_export_container = ctk.CTkFrame(self.button_row, fg_color="transparent")
        self.text_export_container.pack(side="left", padx=6)

        self.text_export_feedback_label = ctk.CTkLabel(
            self.text_export_container, text="", text_color="#00cc66", font=("Helvetica", 12, "bold"), height=18
        )
        self.text_export_feedback_label.pack()

        ctk.CTkButton(
            self.text_export_container, text="   Exporter", image=self.icon_export, compound="left",
            width=130, height=32, font=("Helvetica", 13),
            fg_color="#2a2a2a", hover_color="#3a3a3a", text_color="#e0e0e0",
            command=lambda: self.export_textbox_to_file(self.output_box,self.text_export_feedback_label,self.default_filenames["text"])
        ).pack()

        # --- Télécharger le modèle texte ---
        self.text_download_container = ctk.CTkFrame(self.button_row, fg_color="transparent")
        self.text_download_container.pack(side="left", padx=10)

        self.text_download_feedback_label = ctk.CTkLabel(
            self.text_download_container, text="", text_color="#cccccc", font=("Helvetica", 12), height=18
        )
        self.text_download_feedback_label.pack()

        self.download_button_text = ctk.CTkButton(
            self.text_download_container, text="   Télécharger le modèle", image=self.icon_download, compound="left",
            width=230, height=32, font=("Helvetica", 13),
            fg_color="#2a2a2a", hover_color="#3a3a3a", text_color="#e0e0e0",
            command=lambda: self.download_model("text")
        )
        self.download_button_text.pack()

        # --- Sélecteur de mode texte ---
        self.text_mode_selector_container = ctk.CTkFrame(self.button_row_container, fg_color="transparent")
        self.text_mode_selector_container.pack(side="left", padx=(0, 10))

        self.text_mode_feedback_label = ctk.CTkLabel(
            self.text_mode_selector_container, text="", text_color="#cccccc", font=("Helvetica", 12), height=18
        )
        self.text_mode_feedback_label.pack()

        self.mode_selector = ctk.CTkOptionMenu(
            self.text_mode_selector_container,
            values=["Auto (préférer local)", "Forcer online", "Forcer offline"],
            command=self.set_summary_mode,
            fg_color="#2a2a2a",
            button_color="#00897B",
            button_hover_color="#00796B",
            text_color="#eeeeee",
            dropdown_fg_color="#1f1f1f",
            dropdown_text_color="#cccccc",
            dropdown_hover_color="#333333",
            font=("Helvetica", 13),
            width=180
        )
        self.mode_selector.set("Auto (préférer local)")
        self.mode_selector.pack()

        if self.is_local_model_available():
            self._sync_download_buttons()

        self.set_tab("Texte")

        self._start_auto_check()
        self._bind_keyboard_shortcuts()

    def set_tab(self, name):
        self.active_tab = name

        if name == "Texte":
            self.text_tab_frame.pack(fill="both", expand=True)
            self.audio_tab_frame.pack_forget()
            self.text_tab.configure(
                fg_color="#2c2c2c", hover_color="#222222",
                border_color="#3a3a3a", border_width=1,
                text_color="#00cccc", font=("Helvetica", 14, "bold")
            )
            self.audio_tab.configure(
                fg_color="transparent", hover_color="#1a1a1a",
                border_color="#444444", border_width=1,
                text_color="#aaaaaa", font=("Helvetica", 14)
            )
        else:
            self.audio_tab_frame.pack(fill="both", expand=True)
            self.text_tab_frame.pack_forget()
            self.audio_tab.configure(
                fg_color="#2c2c2c", hover_color="#222222",
                border_color="#3a3a3a", border_width=1,
                text_color="#00cccc", font=("Helvetica", 14, "bold")
            )
            self.text_tab.configure(
                fg_color="transparent", hover_color="#1a1a1a",
                border_color="#444444", border_width=1,
                text_color="#aaaaaa", font=("Helvetica", 14)
            )

        self._sync_buttons_state()

    def handle_drop(self, event):
        if self.active_tab != "Audio":
            return  # ignore les drops si on n'est pas sur l'onglet Audio

        file_path = event.data.strip('{}')  # nettoie les accolades autour des chemins
        if file_path.endswith((".mp3", ".wav", ".m4a")):
            filename = os.path.basename(file_path)
            if getattr(self, "_last_dropped_file", None) == filename:
                return  # évite de traiter deux fois le même drop
            self._last_dropped_file = filename

            self.audio_file_label.configure(text=f"Fichier importé : {filename}")
            self.transcription_box.configure(state="normal")
            self.transcription_box.delete("0.0", "end")
            self.transcription_box.insert("0.0", "(la transcription commencera ici…)")
            self.transcription_box.configure(state="disabled")
            self.process_audio_transcription(file_path)
            print(f"🎙️ Fichier glissé : {filename}")
        else:
            print("⛔ Format non supporté.")

    def copy_textbox_content(self, textbox, feedback_label):
        content = textbox.get("0.0", "end").strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            feedback_label.configure(text="📋 Copié !")
            self.after(1500, lambda: feedback_label.configure(text=""))

    def export_textbox_to_file(self, textbox, feedback_label, initial_filename):
        content = textbox.get("0.0", "end").strip()
        if not content:
            print("⛔ Rien à exporter.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichier texte", "*.txt")],
            title="Exporter le fichier",
            initialfile=initial_filename,
            initialdir=os.path.expanduser("~/Desktop")
        )

        if file_path:
            if not file_path.lower().endswith(".txt"):
                file_path += ".txt"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✅ Fichier exporté dans : {file_path}")
            feedback_label.configure(text="✅ Exporté !")
            self.after(1500, lambda: feedback_label.configure(text=""))

    def is_local_model_available(self, target="text"):
        if target == "text":
            return os.path.exists("models/summary_model/")
        elif target == "audio":
            return os.path.exists("models/audio_model/")

    def set_summary_mode(self, value):
        self.summary_mode = value
        print(f"🔁 Mode résumé défini sur : {value}")

    def set_audio_mode(self, value):
        self.audio_mode = value
        print(f"🎧 Mode audio défini sur : {value}")

    def summarize(self):
        text = self.input_box.get("0.0", "end").strip()

        if self.summary_mode == "Forcer offline":
            if not self.is_local_model_available("text"):
                self._handle_missing_model()
                return
            summary = summarize_text(text, mode="offline")

        elif self.summary_mode == "Forcer online":
            summary = summarize_text(text, mode="online")

        else:
            if self.is_local_model_available("text"):
                summary = summarize_text(text, mode="offline")
            else:
                print("📡 Aucun modèle local trouvé, basculement vers le résumé en ligne.")
                summary = summarize_text(text, mode="online")

        self.output_box.configure(state="normal")
        self.output_box.delete("0.0", "end")
        self.output_box.insert("0.0", summary)
        self.output_box.configure(state="disabled")

    def _handle_missing_model(self):
        message = "⛔ Le modèle local est introuvable.\nVeuillez le télécharger à nouveau."
        self.output_box.configure(state="normal")
        self.output_box.delete("0.0", "end")
        self.output_box.insert("0.0", message)
        self.output_box.configure(state="disabled")
        self._enable_download_buttons()

    def _sync_download_buttons(self):
        for btn in [self.download_button_audio, self.download_button_text]:
            btn.configure(text="Modèle installé", state="disabled", fg_color="#1f1f1f")
    
    def _sync_buttons_state(self):
        if self.is_local_model_available("text"):
            self.download_button_text.configure(text="Modèle installé", state="disabled", fg_color="#1f1f1f")
        else:
            self.download_button_text.configure(text="Télécharger le modèle (~220 Mo)", state="normal", fg_color="#2a2a2a")

        if self.is_local_model_available("audio"):
            self.download_button_audio.configure(text="Modèle installé", state="disabled", fg_color="#1f1f1f")
        else:
            self.download_button_audio.configure(text="Télécharger le modèle (~2.8 Go)", state="normal", fg_color="#2a2a2a")

    def _start_auto_check(self):
        self._sync_buttons_state()
        self.after(2000, self._start_auto_check)
        
    def _enable_download_buttons(self):
        for btn in [self.download_button_audio, self.download_button_text]:
            btn.configure(text="Télécharger le modèle", state="normal", fg_color="#2a2a2a")

    def _start_spinner(self):
        self.spinner_running = True
        self._spinner_state = 0
        self._update_spinner()

    def _stop_spinner(self):
        self.spinner_running = False

    def _update_spinner(self):
        if not self.spinner_running:
            return

        dots = "." * (self._spinner_state % 4)
        text = f"Téléchargement{dots}"
        for btn in [self.download_button_audio, self.download_button_text]:
            btn.configure(text=text, state="disabled")

        self._spinner_state += 1
        self.after(500, self._update_spinner)

    def download_model(self, target="text"):
        self._start_spinner()
        threading.Thread(target=lambda: self._download_model_task(target), daemon=True).start()

    def _download_model_task(self, target):
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, WhisperProcessor, WhisperForConditionalGeneration

        if target == "text":
            model_name = "t5-small"
            local_dir = "models/summary_model/"
            print(f"📦 Téléchargement du modèle texte ({model_name})…")

            os.makedirs(local_dir, exist_ok=True)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            tokenizer.save_pretrained(local_dir)
            model.save_pretrained(local_dir)

        elif target == "audio":
            model_name = "openai/whisper-small"
            local_dir = "models/audio_model/"
            print(f"🎙️ Téléchargement du modèle audio ({model_name})…")

            os.makedirs(local_dir, exist_ok=True)
            processor = WhisperProcessor.from_pretrained(model_name)
            model = WhisperForConditionalGeneration.from_pretrained(model_name)
            processor.save_pretrained(local_dir)
            model.save_pretrained(local_dir)

        self.after(0, lambda: [
            self._stop_spinner(),
            self._sync_download_buttons()
        ])
        print(f"✅ Modèle {target} téléchargé et sauvegardé.")

    def process_audio_transcription(self, file_path):
        filename = os.path.basename(file_path)
        self.audio_file_label.configure(text=f"Fichier importé : {filename}")
        self.transcription_box.configure(state="normal")
        self.transcription_box.delete("0.0", "end")
        self.transcription_box.insert("0.0", "(transcription en cours…)")

        threading.Thread(target=lambda: self._transcribe_thread(file_path), daemon=True).start()

    def _transcribe_thread(self, file_path):
        result = transcribe_audio(file_path, mode=self.audio_mode)
        self.after(0, lambda: self._display_transcription(result))

    def _display_transcription(self, result):
        self.transcription_box.delete("0.0", "end")
        self.transcription_box.insert("0.0", result)
        self.transcription_box.configure(state="disabled")


    def import_audio_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Fichiers audio", "*.mp3 *.wav *.m4a")]
        )
        if file_path:
            filename = os.path.basename(file_path)
            if getattr(self, "_last_dropped_file", None) == filename:
                return  # évite de traiter deux fois le même drop
            self.audio_file_label.configure(text=f"Fichier importé : {filename}")
            self.transcription_box.configure(state="normal")
            self.transcription_box.delete("0.0", "end")
            self.transcription_box.insert("0.0", "(la transcription commencera ici…)")
            self.transcription_box.configure(state="disabled")
            self.process_audio_transcription(file_path)
            print(f"🎙️ Fichier sélectionné : {filename}")

    def _bind_keyboard_shortcuts(self):
        self.bind_all("<Control-Key-1>", lambda e: self.set_tab("Texte"))
        self.bind_all("<Control-Key-2>", lambda e: self.set_tab("Audio"))
        self.bind_all("<Control-r>", lambda e: self._on_ctrl_r())
        self.bind_all("<Control-s>", lambda e: self._on_ctrl_s())
        self.bind_all("<Control-S>", lambda e: self._on_ctrl_s())
        self.bind_all("<Control-c>", lambda e: self._on_ctrl_c())
        self.bind_all("<Control-C>", lambda e: self._on_ctrl_c())

    def _on_ctrl_r(self):
        if self.active_tab == "Texte":
            self.summarize()

    def _on_ctrl_s(self):
        if self.active_tab == "Texte":
            self.export_textbox_to_file(self.output_box, self.text_export_feedback_label, self.default_filenames["text"])
        elif self.active_tab == "Audio":
            self.export_textbox_to_file(self.transcription_box, self.export_feedback_label, self.default_filenames["audio"])

    def _on_ctrl_c(self):
        if self.active_tab == "Texte":
            self.copy_textbox_content(self.output_box, self.text_copy_feedback_label)
        elif self.active_tab == "Audio":
            self.copy_textbox_content(self.transcription_box, self.copy_feedback_label)

if __name__ == "__main__":
    app = NexNotesV2App()
    app.mainloop()
