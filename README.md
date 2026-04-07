# The Empathy Engine

The Empathy Engine is an emotion-aware Text-to-Speech (TTS) application built in Python.  
It takes user text, detects sentiment, maps it to an emotion profile, and generates expressive speech by adjusting voice parameters such as rate, volume, and pitch.

It includes:
- a CLI workflow for quick testing and batch-like usage
- a Flask Web UI for interactive use
- explicit, deterministic emotion-to-voice mapping logic

---

## 1) Project Overview

Core features:
- Accepts text input from CLI and Web UI
- Detects emotion category: `positive`, `negative`, `neutral`
- Computes emotion intensity (weak -> strong)
- Modulates voice using:
  - speaking `rate`
  - `volume`
  - pitch shift (via SAPI XML prosody on Windows)
- Exports playable `.wav` audio output

Tech stack:
- `vaderSentiment` for sentiment analysis
- `pyttsx3` for local offline TTS synthesis
- `Flask` for the browser frontend

---

## 2) Project Structure

- `empathy_engine.py` - core analysis + synthesis logic and CLI entry point
- `web_app.py` - Flask web server and routes
- `templates/index.html` - UI template
- `static/styles.css` - UI styling
- `requirements.txt` - Python dependencies
- `output/` - local generated audio files (CLI usage)

---

## 3) Environment Setup (Step-by-Step)

### Prerequisites
- Python 3.9+ recommended
- Windows (best support for current pitch handling with SAPI prosody)

### Step 1: Clone or open the project

```powershell
cd "path\to\raushan pr1"
```

### Step 2: Create virtual environment

```powershell
python -m venv .venv
```

### Step 3: Activate virtual environment

```powershell
.\.venv\Scripts\activate
```

### Step 4: Install dependencies

```powershell
pip install -r requirements.txt
```

---

## 4) Run the Application

### A) Run via CLI (interactive)

```powershell
python empathy_engine.py
```

### B) Run via CLI (one-line)

```powershell
python empathy_engine.py --text "This is the best news ever!" --out output/happy.wav
```

### C) Run Web UI

```powershell
python web_app.py
```

Open browser:

`http://127.0.0.1:5000`

Web UI supports:
- text input
- emotion-aware audio generation
- embedded playback
- WAV download

---

## 5) Design Choices and Emotion Mapping Logic

This section explains the core design decisions behind the emotional voice behavior.

### Why this design
- **Local-first and simple:** Chose `vaderSentiment` + `pyttsx3` to avoid external paid APIs.
- **Deterministic behavior:** Same input pattern leads to predictable emotion/voice settings.
- **Explainable pipeline:** Sentiment -> emotion label -> intensity -> voice parameter scaling.
- **Practical compatibility:** Pitch is handled through SAPI XML prosody where supported.

### Emotion detection pipeline
1. Analyze text with VADER to get `compound` sentiment score.
2. Map sentiment score to emotion label:
   - `compound >= 0.2` -> `positive`
   - `compound <= -0.2` -> `negative`
   - otherwise -> `neutral`
3. Compute intensity (`0.1` to `1.0`) using:
   - absolute sentiment magnitude
   - punctuation emphasis boost (`!` and `?`)
4. Convert label + intensity into final voice parameters.

### Emotion -> voice parameter strategy

| Emotion | Rate | Volume | Pitch Shift |
|---|---|---|---|
| Positive | Slightly faster | Slightly louder | Up |
| Negative | Slightly slower | Slightly softer | Down |
| Neutral | Baseline | Baseline | Flat |

Notes:
- Rate and volume are always set.
- Pitch shift is applied via SAPI prosody support (Windows voices).
- Intensity scales the size of these adjustments.

---

## 6) Deployment (Render)

Render Web Service configuration:

- **Build Command**
  ```bash
  pip install -r requirements.txt
  ```

- **Start Command**
  ```bash
  gunicorn web_app:app --bind 0.0.0.0:$PORT
  ```

Current code is prepared for Render with temp output directory:
- `web_app.py` uses `/tmp/output/web` and creates it automatically.

---

## 7) Limitations / Notes

- Voice quality depends on installed system voices.
- Pitch/prosody behavior may vary by voice engine.
- `pyttsx3` backend behavior can differ across environments.
- For more realistic speech, you can later replace TTS backend while keeping the same emotion mapping pipeline.
