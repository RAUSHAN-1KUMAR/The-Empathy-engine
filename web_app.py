from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, send_from_directory, url_for

from empathy_engine import synthesize


app = Flask(__name__)
GENERATED_DIR = Path("output/web")


@app.route("/", methods=["GET", "POST"])
def index():
    context = {
        "audio_url": None,
        "error": None,
        "emotion": None,
        "intensity": None,
        "voice_params": None,
        "input_text": "",
    }

    if request.method == "POST":
        text = (request.form.get("text") or "").strip()
        context["input_text"] = text

        if not text:
            context["error"] = "Please enter some text."
            return render_template("index.html", **context)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out_file = GENERATED_DIR / f"speech_{timestamp}.wav"

        try:
            result = synthesize(text=text, output_path=out_file)
            context["emotion"] = result["emotion"]
            context["intensity"] = result["intensity"]
            context["voice_params"] = result["voice_params"]
            context["audio_url"] = url_for(
                "serve_audio", filename=out_file.name, _external=False
            )
        except Exception as exc:
            context["error"] = f"Failed to synthesize audio: {exc}"

    return render_template("index.html", **context)


@app.route("/audio/<path:filename>")
def serve_audio(filename: str):
    return send_from_directory(GENERATED_DIR.resolve(), filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
