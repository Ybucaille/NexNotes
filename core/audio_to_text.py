import os
import re
import torch
import librosa
from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline

MODEL_NAME = "openai/whisper-medium"
MODEL_DIR = "models/audio_model/"

def clean_transcription(text: str) -> str:
    return re.sub(r"[▯■□▪️▫️⬛⬜]+", "", text).strip()

def transcribe_audio(file_path, mode="auto"):
    print(f"⚙️ Transcription Whisper | mode = {mode}")

    audio, _ = librosa.load(file_path, sr=16000)
    if audio is None or max(abs(audio)) < 0.001:
        return "⚠️ Le fichier audio semble vide ou silencieux."

    # === MODE LOCAL ===
    if mode in ["Auto (préférer local)", "Forcer Whisper local"]:
        if not os.path.exists(MODEL_DIR):
            if mode == "Forcer Whisper local":
                return "❌ Le modèle Whisper local est introuvable. Veuillez le télécharger. (~2.8 Go)"
            else:
                print("⏩ Modèle local manquant. Bascule sur transcription online.")
                return transcribe_audio(file_path, mode="Forcer HuggingFace (cache)")

        processor = WhisperProcessor.from_pretrained(MODEL_DIR)
        model = WhisperForConditionalGeneration.from_pretrained(MODEL_DIR)

        inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
        forced_decoder_ids = processor.get_decoder_prompt_ids(language="fr", task="transcribe")

        with torch.no_grad():
            predicted_ids = model.generate(
                inputs["input_features"],
                forced_decoder_ids=forced_decoder_ids
            )

        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        return clean_transcription(transcription)

    # === MODE ONLINE ===
    elif mode == "Forcer HuggingFace (cache)":
        try:
            whisper_pipe = pipeline("automatic-speech-recognition", model=MODEL_NAME)
            result = whisper_pipe(audio, chunk_length_s=30, generate_kwargs={
                "language": "fr",
                "task": "transcribe"
            })
            return clean_transcription(result["text"])
        except Exception as e:
            return f"❌ Échec de la transcription online : {str(e)}"

    return "❓ Mode de transcription inconnu."