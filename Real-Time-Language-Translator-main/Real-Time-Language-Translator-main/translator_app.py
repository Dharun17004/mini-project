import streamlit as st
import speech_recognition as sr
from gtts import gTTS
from googletrans import Translator
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize the translator
translator = Translator()

# List of languages for selection
languages = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Chinese (Simplified)": "zh-CN",
    "Japanese": "ja",
    "Korean": "ko",
    "Russian": "ru",
}

# Streamlit UI
st.title("Real-Time Language Translator")

# Language selection
selected_language = st.selectbox("Select the language you want to translate to:", list(languages.keys()))

# Initialize session state for text input
if 'text_input' not in st.session_state:
    st.session_state.text_input = ""

# Text input for user to enter text
st.session_state.text_input = st.text_area("Enter text to translate:", value=st.session_state.text_input)

# Voice input section
st.subheader("Voice Input")
if st.button("Record Voice"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = recognizer.listen(source)
        st.write("Recording complete.")
        try:
            voice_text = recognizer.recognize_google(audio)
            st.write("You said:", voice_text)
            st.session_state.text_input = voice_text  # Set the text input to the recognized voice text
            st.text_area("Enter text to translate:", value=st.session_state.text_input)  # Update the text area with recognized text
        except sr.UnknownValueError:
            st.error("Could not understand audio. Please try again.")
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Speech Recognition service; {e}")

# Translate button
if st.button("Translate"):
    if st.session_state.text_input:
        try:
            translated_text = translator.translate(st.session_state.text_input, dest=languages[selected_language])
            st.write("Translated Text:", translated_text.text)

            # Text to speech
            tts = gTTS(text=translated_text.text, lang=languages[selected_language])
            tts.save("translated.mp3")
            st.audio("translated.mp3", format="audio/mp3")
        except Exception as e:
            st.error(f"An error occurred during translation: {e}")
    else:
        st.warning("Please enter some text to translate or use voice input.")