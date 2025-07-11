import speech_recognition as sr
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
import pyaudio
import os
import io

# --- Configuration ---
# Set up Google Cloud credentials (replace with your actual path)
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/your/google-cloud-key.json"

TARGET_LANGUAGE = "es" # Example: Spanish
SOURCE_LANGUAGE = "en" # Example: English (or detect automatically if using advanced STT)

# Initialize clients
r = sr.Recognizer()
translate_client = translate.Client()
tts_client = texttospeech.TextToSpeechClient()

def translate_text(text, target_language):
    """Translates text into the target language."""
    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

def synthesize_speech(text, language_code):
    """Synthesizes speech from the input text."""
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL  # Or MALE/FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16, # Raw audio
        sample_rate_hertz=24000 # Choose a sample rate that matches your speaker
    )
    response = tts_client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
    return response.audio_content

def play_audio(audio_content):
    """Plays raw audio content."""
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=24000, # Must match TTS sample rate
                    output=True)
    stream.write(audio_content)
    stream.stop_stream()
    stream.close()
    p.terminate()

def real_time_translator():
    print("Listening for speech...")
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source) # Optional: Adjust for background noise

        # Consider using a non-blocking approach for real-time
        # For simplicity, this example will process after a pause in speech.
        # A truly real-time system would use a callback for audio chunks.
        try:
            while True:
                print("Say something!")
                audio = r.listen(source, timeout=5, phrase_time_limit=5) # Listen for up to 5 seconds

                try:
                    # Speech Recognition
                    text = r.recognize_google(audio, language=SOURCE_LANGUAGE)
                    print(f"You said: {text}")

                    # Machine Translation
                    translated_text = translate_text(text, TARGET_LANGUAGE)
                    print(f"Translated ({TARGET_LANGUAGE}): {translated_text}")

                    # Text-to-Speech
                    translated_audio = synthesize_speech(translated_text, TARGET_LANGUAGE)

                    # Play Audio
                    play_audio(translated_audio)

                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")
                except Exception as e:
                    print(f"An error occurred: {e}")

        except KeyboardInterrupt:
            print("\nTranslator stopped.")

if __name__ == "__main__":
    # Ensure you have your Google Cloud credentials set up
    # e.g., export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"
    real_time_translator()
