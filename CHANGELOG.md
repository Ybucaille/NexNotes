# Changelog

Toutes les modifications notables du projet NexNotes sont listées ici.

---

## [v1.0] – 2025-05-15

### Ajouté
- Transcription audio offline avec Whisper (`openai/whisper-medium`)
- Résumé de texte local via `t5-small`
- Interface custom sans bordures, drag uniquement depuis la barre
- Navigation par onglet (Texte / Audio)
- Copier / Exporter / Résumer via raccourcis clavier
- Mode online facultatif avec fallback GPT (si API présente)

### Structure
- Organisation en `core/`, `gui/`, `models/`, `assets/`
- Modèles stockés localement dans `models/summary_model/` et `models/audio_model/`
