import argparse
import re
import sys
from pathlib import Path

from gtts import gTTS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

try:
    import pyttsx3
except Exception:
    pyttsx3 = None


EMOTION_CONFIG = {
    "positive": {
        "base_rate_scale": 1.08,
        "base_volume": 0.95,
        "pitch_shift": 25,  # Hz applied with SAPI XML prosody
    },
    "negative": {
        "base_rate_scale": 0.92,
        "base_volume": 0.85,
        "pitch_shift": -35,
    },
    "neutral": {
        "base_rate_scale": 1.0,
        "base_volume": 0.90,
        "pitch_shift": 0,
    },
}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def detect_emotion_and_intensity(
    text: str, analyzer: SentimentIntensityAnalyzer
) -> tuple[str, float, dict]:
    """
    Returns:
        emotion: one of positive, negative, neutral
        intensity: 0.0 -> 1.0
        scores: raw VADER score dictionary
    """
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]

    # Emotion class
    if compound >= 0.2:
        emotion = "positive"
    elif compound <= -0.2:
        emotion = "negative"
    else:
        emotion = "neutral"

    # Intensity increases with stronger absolute sentiment and punctuation emphasis.
    sentiment_strength = abs(compound)
    emphasis_marks = len(re.findall(r"[!?]{1,}", text))
    emphasis_boost = min(0.25, emphasis_marks * 0.05)
    intensity = clamp(sentiment_strength + emphasis_boost, 0.1, 1.0)
    return emotion, intensity, scores


def build_voice_params(
    emotion: str,
    intensity: float,
    base_rate: int,
    base_volume: float,
) -> dict:
    config = EMOTION_CONFIG[emotion]

    # Scale effect by intensity so stronger emotional text is more expressive.
    rate_multiplier = 1 + (config["base_rate_scale"] - 1) * (0.5 + intensity / 2)
    final_rate = int(round(base_rate * rate_multiplier))

    volume_delta = (config["base_volume"] - base_volume) * (0.5 + intensity / 2)
    final_volume = clamp(base_volume + volume_delta, 0.0, 1.0)

    pitch_shift = int(round(config["pitch_shift"] * (0.4 + intensity * 0.6)))

    return {
        "rate": final_rate,
        "volume": final_volume,
        "pitch_shift_hz": pitch_shift,
    }


def to_sapi_xml(text: str, pitch_shift_hz: int) -> str:
    """
    Wraps text in SAPI XML so Windows voices can apply pitch shifts.
    If the engine/voice ignores XML, plain text still speaks with rate/volume changes.
    """
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
    # SAPI prosody pitch expects an integer in Hz with +/-
    sign = "+" if pitch_shift_hz > 0 else ""
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis">'
        f'<prosody pitch="{sign}{pitch_shift_hz}Hz">{escaped}</prosody>'
        "</speak>"
    )


def synthesize(
    text: str,
    output_path: Path,
    voice_name: str | None = None,
    debug: bool = False,
) -> dict:
    analyzer = SentimentIntensityAnalyzer()
    engine = None
    tts_backend = "pyttsx3"

    if pyttsx3 is not None:
        try:
            engine = pyttsx3.init()
        except Exception:
            engine = None

    if engine is None:
        tts_backend = "gtts"
        # Fallback defaults when local TTS engine is unavailable.
        base_rate = 180
        base_volume = 0.90
    else:
        # Optionally choose a specific voice.
        if voice_name:
            matched = False
            for voice in engine.getProperty("voices"):
                if voice_name.lower() in voice.name.lower():
                    engine.setProperty("voice", voice.id)
                    matched = True
                    break
            if not matched and debug:
                print(f"[warn] Voice containing '{voice_name}' not found. Using default.")

        base_rate = engine.getProperty("rate")
        base_volume = engine.getProperty("volume")

    emotion, intensity, scores = detect_emotion_and_intensity(text, analyzer)
    params = build_voice_params(emotion, intensity, base_rate, base_volume)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if tts_backend == "pyttsx3":
        engine.setProperty("rate", params["rate"])
        engine.setProperty("volume", params["volume"])

        # Use XML prosody for pitch on Windows SAPI voices.
        speak_text = to_sapi_xml(text, params["pitch_shift_hz"])
        engine.save_to_file(speak_text, str(output_path))
        engine.runAndWait()
    else:
        # gTTS creates MP3; switch extension if needed.
        if output_path.suffix.lower() != ".mp3":
            output_path = output_path.with_suffix(".mp3")
        tts = gTTS(text=text, lang="en")
        tts.save(str(output_path))

    return {
        "emotion": emotion,
        "intensity": round(intensity, 3),
        "scores": scores,
        "voice_params": params,
        "output_file": str(output_path),
        "tts_backend": tts_backend,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Empathy Engine: emotion-aware expressive TTS"
    )
    parser.add_argument(
        "--text",
        type=str,
        help="Input text to speak. If omitted, an interactive prompt is shown.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="output/empathy_output.wav",
        help="Output audio path (.wav recommended). Default: output/empathy_output.wav",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default=None,
        help="Optional voice name substring to select a specific installed TTS voice.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print extra debug details.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = args.text

    if not text:
        text = input("Enter text for Empathy Engine: ").strip()

    if not text:
        print("No text provided. Exiting.")
        return 1

    try:
        result = synthesize(
            text=text,
            output_path=Path(args.out),
            voice_name=args.voice,
            debug=args.debug,
        )
    except Exception as exc:
        print(f"Failed to synthesize speech: {exc}")
        return 2

    print("\nEmpathy Engine Result")
    print("-" * 24)
    print(f"Emotion: {result['emotion']}")
    print(f"Intensity: {result['intensity']}")
    print(
        "Voice Params: "
        f"rate={result['voice_params']['rate']}, "
        f"volume={result['voice_params']['volume']:.2f}, "
        f"pitch_shift={result['voice_params']['pitch_shift_hz']}Hz"
    )
    print(f"Audio File: {result['output_file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
