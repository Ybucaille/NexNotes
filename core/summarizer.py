import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from langdetect import detect

# Chemin vers le modèle local (offline)
LOCAL_MODEL_PATH = "models/summary_model/"
T5_MODEL_NAME = "t5-small"

# Chargement unique du modèle en mémoire
tokenizer = None
model = None

def summarize_text(text, mode="offline"):

    text = text.strip()
    if not text:
        return "⛔ Texte vide, rien à résumer."
    
    try:
        lang = detect(text)
    except Exception:
        lang = "fr"

    if mode == "offline":
        print("🧠 Résumé offline lancé.")
        global tokenizer, model

        if not os.path.exists(LOCAL_MODEL_PATH):
            return "❌ Modèle local introuvable. Télécharge-le d'abord."

        try:
            if tokenizer is None or model is None:
                tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_PATH)
                model = AutoModelForSeq2SeqLM.from_pretrained(LOCAL_MODEL_PATH)

            input_ids = tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=512, truncation=True)
            summary_ids = model.generate(input_ids, max_length=120, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True)
            return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        except Exception as e:
            print(f"⚠️ Erreur résumé offline : {e}")
            if mode != "online":
                return summarize_text(text, mode="online")
            return "❌ Échec du résumé local et en ligne."

    elif mode == "online":
        from dotenv import load_dotenv
        import openai

        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "❌ Clé API manquante. Vérifie ton fichier .env"

        client = openai.OpenAI(api_key=api_key)

        print("🌐 Résumé online lancé.")
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Tu es un assistant qui résume des textes."},
                    {"role": "user", "content": f"Résume ce texte en une phrase claire et complète, sans omettre les informations importantes. Langue du texte : {lang}.\n\n{text}"}
                ],
                temperature=0.7,
                max_tokens=200,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"❌ Erreur résumé online : {str(e)}"
        
    else:
        raise ValueError("❗ Mode de résumé inconnu.")

if __name__ == "__main__":
    test = "La Révolution française a transformé la société, mettant fin à la monarchie et posant les bases de la démocratie moderne..."
    print(summarize_text(test, mode="offline"))