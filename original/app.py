from flask import Flask, render_template, request, jsonify
from googletrans import Translator, LANGUAGES
from gtts import gTTS
import os
import uuid
import time

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/audio'
app.config['SECRET_KEY'] = 'your_strong_unique_secret_key' # IMPORTANT: CHANGE THIS IN PRODUCTION!

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Translator
translator = Translator()

# Helper function for cleaner language name handling
def get_language_name(code):
    """Returns the full language name for a given two-letter code."""
    # Ensure 'zh-cn' and 'zh-tw' are handled as 'zh' for gTTS if it expects it,
    # though googletrans might keep them distinct.
    if code == 'zh-cn' or code == 'zh-tw':
        return LANGUAGES.get(code.lower(), f"Chinese ({code})")
    return LANGUAGES.get(code.lower(), f"Unknown ({code})")

# Function to translate text with retry logic
def translate_text_logic(text, src_lang, dest_lang, max_retries=3, initial_delay=1):
    """
    Translates text with retry mechanism for transient errors.
    Returns translated text and the detected source language code.
    """
    retries = 0
    while retries < max_retries:
        try:
            print(f"Attempting translation (retry {retries + 1}/{max_retries}): '{text}' from {src_lang} to {dest_lang}")
            translated = translator.translate(text, src=src_lang, dest=dest_lang)
            if translated and translated.text:
                return translated.text, translated.src
            else:
                print(f"Translation attempt {retries + 1} returned empty or None for '{text}'.")
                raise Exception("Empty or invalid translation response from Google Translate.")

        except Exception as e:
            retries += 1
            print(f"Translation error (attempt {retries}/{max_retries}): {e}")
            if "too many requests" in str(e).lower() or "timeout" in str(e).lower() or "connection" in str(e).lower() or "bad response from google translate" in str(e).lower():
                delay = initial_delay * (2 ** (retries - 1))
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Non-retryable or unexpected error: {e}. Not retrying.")
                return None, None

    print(f"Failed to translate '{text}' after {max_retries} attempts.")
    return None, None

# Function to synthesize speech and save to a file on the server
def synthesize_speech_to_file(text, lang_code, upload_folder, slow_audio=False):
    """
    Converts text to speech using gTTS, saves it to a temporary file,
    and returns the relative URL. Includes option for slow speech.
    """
    try:
        # gTTS typically uses 2-letter ISO codes, but can sometimes handle 4-letter ones
        # Use only the base language code for gTTS unless specific variations are supported
        gtts_lang_code = lang_code.split('-')[0]
        print(f"Generating speech for text: '{text[:50]}...' in language: {gtts_lang_code}, Slow: {slow_audio}")
        tts = gTTS(text=text, lang=gtts_lang_code, slow=slow_audio)

        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_filepath = os.path.join(upload_folder, audio_filename)

        tts.save(audio_filepath)
        print(f"Audio saved to: {audio_filepath}")
        return f"/static/audio/{audio_filename}"
    except Exception as e:
        print(f"gTTS audio generation error for lang '{lang_code}': {e}")
        return None

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main translation page."""
    # Pass language codes and names for dropdowns
    sorted_languages = sorted(LANGUAGES.items(), key=lambda item: item[1])
    return render_template('index.html', languages=sorted_languages)


@app.route('/translate', methods=['POST'])
def translate():
    """Handles translation requests from the frontend."""
    data = request.json
    input_text = data.get('text', '').strip()
    src_lang_code = data.get('src_lang', 'en').lower()
    dest_lang_code = data.get('dest_lang', 'ta').lower()
    speak_output = data.get('speak_output', False)
    slow_speech = data.get('slow_speech', False) # Boolean from frontend

    src_lang_name = get_language_name(src_lang_code)
    dest_lang_name = get_language_name(dest_lang_code)

    if not input_text:
        return jsonify({
            'original_text': '',
            'translated_text': 'Please enter some text to translate.',
            'audio_url': None,
            'src_lang_name': src_lang_name,
            'dest_lang_name': dest_lang_name,
            'detected_src_lang_code': None,
            'status': 'warning',
            'message': 'Please enter some text to translate.'
        }), 200

    translated_result_text, detected_src_lang_code = translate_text_logic(input_text, src_lang_code, dest_lang_code)

    audio_url = None
    if translated_result_text and speak_output:
        # Pass the slow_speech boolean to the audio generation function
        audio_url = synthesize_speech_to_file(
            translated_result_text,
            dest_lang_code,
            upload_folder=app.config['UPLOAD_FOLDER'],
            slow_audio=slow_speech
        )

    final_src_lang_display_name = src_lang_name
    if src_lang_code == 'auto' and detected_src_lang_code:
        final_src_lang_display_name = f"Auto-detected: {get_language_name(detected_src_lang_code)}"

    if translated_result_text:
        status_message = "Translation successful!"
        status_type = "info"
    else:
        status_message = "Translation failed. Please try again or check server logs."
        status_type = "error"

    response_data = {
        'original_text': input_text,
        'translated_text': translated_result_text if translated_result_text is not None else "Translation failed.",
        'audio_url': audio_url,
        'src_lang_name': final_src_lang_display_name,
        'dest_lang_name': dest_lang_name,
        'detected_src_lang_code': detected_src_lang_code,
        'status': status_type,
        'message': status_message
    }
    return jsonify(response_data)


# --- Main execution ---
if __name__ == '__main__':
    print("Starting Flask web server...")
    print(f"Access the translator at: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
