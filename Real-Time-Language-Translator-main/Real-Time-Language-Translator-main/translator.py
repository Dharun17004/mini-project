import speech_recognition as sr
from gtts import gTTS
import os
from googletrans import Translator
from tkinter import *

# Initialize the recognizer and translator
recognizer = sr.Recognizer()
translator = Translator()

# Function to translate text
def translate_text():
    input_text = text_input.get()
    translated_text = translator.translate(input_text, dest='es')  # Change 'es' to desired language code
    output_text.delete(1.0, END)
    output_text.insert(END, translated_text.text)

    # Convert translated text to speech
    tts = gTTS(translated_text.text, lang='es')  # Change 'es' to match the translation language
    tts.save("translated.mp3")
    os.system("mpg123 translated.mp3")

# Function to listen for voice input and translate
def voice_translate():
    with sr.Microphone() as source:
        print("Listening for your voice...")
        audio = recognizer.listen(source)

        try:
            user_input = recognizer.recognize_google(audio)
            print(f"You said: {user_input}")
            text_input.delete(0, END)
            text_input.insert(0, user_input)
            translate_text()
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

# Create the main window
root = Tk()
root.geometry('400x300')
root.title('Voice and Text Translator')

# Create input field for text
text_input = Entry(root, width=50)
text_input.pack(pady=20)

# Create button for text translation
translate_btn = Button(root, text='Translate Text', command=translate_text)
translate_btn.pack(pady=10)

# Create button for voice translation
voice_btn = Button(root, text='Translate Voice', command=voice_translate)
voice_btn.pack(pady=10)

# Create output field for translated text
output_text = Text(root, height=5, width=50)
output_text.pack(pady=20)

# Start the Tkinter event loop
root.mainloop()