# The Empathy Engine

An emotion-aware Text-to-Speech service in Python that detects sentiment from input text and modulates synthesized voice to sound more human and expressive.

This implementation satisfies the challenge core requirements:
- Accepts text input from CLI
- Detects emotion (`positive`, `negative`, `neutral`)
- Modulates multiple vocal parameters (`rate`, `volume`, and `pitch` via SAPI XML on Windows)
- Uses explicit emotion-to-voice mapping logic
- Generates a playable audio file (`.wav`)
- Includes a browser frontend where you can type text and play generated audio

## Why this design

- **Fast and local**: Uses `vaderSentiment` + `pyttsx3` for offline prototyping with no paid APIs.
- **Deterministic mapping**: Each emotion maps to a baseline voice profile, then is scaled by intensity.
- **Intensity scaling**: Stronger sentiment and punctuation (`!`, `?`) increase modulation.
- **Windows-friendly pitch control**: Applies pitch with SAPI XML prosody in the spoken text.

## Project structure

- `empathy_engine.py` - main CLI app and synthesis logic
- `web_app.py` - Flask web frontend
- `templates/index.html` - frontend page with input + audio player
- `requirements.txt` - Python dependencies

## Setup

1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run

### Interactive mode

```powershell
python empathy_engine.py
```

### One-liner mode

```powershell
python empathy_engine.py --text "This is the best news ever!" --out output/happy.wav
```

### Optional: pick a specific installed voice

```powershell
python empathy_engine.py --text "I understand your frustration, let me help." --voice "David" --out output/support.wav
```

## Run the frontend (Web UI)

```powershell
python web_app.py
```

Then open `http://127.0.0.1:5000` in your browser.

From the page you can:
- enter any input string
- generate emotion-aware speech
- play the output in an embedded audio player
- download the generated `.wav` file

## Emotion to voice mapping logic

The pipeline:
1. Analyze sentiment with VADER.
2. Classify emotion:
   - `compound >= 0.2` -> `positive`
   - `compound <= -0.2` -> `negative`
   - otherwise -> `neutral`
3. Compute intensity `0.1..1.0` using:
   - absolute compound score
   - punctuation emphasis boost from `!`/`?`
4. Apply emotion profile + intensity scaling to voice parameters:

| Emotion  | Rate             | Volume           | Pitch (Hz) |
|----------|------------------|------------------|------------|
| Positive | Slightly faster  | Slightly louder  | Up         |
| Negative | Slightly slower  | Slightly softer  | Down       |
| Neutral  | Baseline         | Baseline         | Flat       |

Rate and volume are always applied. Pitch is applied through SAPI XML prosody on Windows voices.

## Example output

After running, the script prints:
- detected emotion
- intensity score
- final voice parameters
- output audio file path

## Notes and limitations

- Voice quality depends on installed system voices.
- Some TTS voices may apply pitch/prosody differently.
- For higher realism, you can swap in advanced APIs (Google Cloud TTS, ElevenLabs) while reusing the same emotion mapping logic.

## Stretch-goal ideas

- Add nuanced labels (`concerned`, `excited`, `inquisitive`)
- Add FastAPI endpoint with separate API docs
- Use SSML for richer emphasis and pause control
- Persist logs/metrics for A/B testing voice mappings
