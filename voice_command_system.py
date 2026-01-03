"""
Σύστημα φωνητικών εντολών με χρήση speech recognition και text-to-speech.
"""

import sys
import subprocess

def install_package(package_name):
    """Εγκαθιστά μια βιβλιοθήκη Python αν λείπει."""
    try:
        __import__(package_name)
    except ImportError:
        print(f"Βιβλιοθήκη '{package_name}' δεν βρέθηκε. Εγκατάσταση...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"Η βιβλιοθήκη '{package_name}' εγκαταστάθηκε επιτυχώς.")

# Εγκατάσταση απαραίτητων βιβλιοθηκών
install_package('pyttsx3')
install_package('SpeechRecognition')
install_package('pyaudio')

import pyttsx3
import speech_recognition as sr
import time

class VoiceCommandSystem:
    def __init__(self):
        """Αρχικοποίηση του συστήματος φωνητικών εντολών."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = self.init_tts()
        
        print("Φωνητικό σύστημα αρχικοποιήθηκε.")

    def init_tts(self):
        """Αρχικοποιεί τον μηχανισμό text-to-speech."""
        try:
            engine = pyttsx3.init()
            # Ρυθμίσεις ελληνικής φωνής (αν υπάρχει)
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'greek' in voice.name.lower() or 'el' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
            engine.setProperty('rate', 150)  # Ταχύτητα ομιλίας
            return engine
        except Exception as e:
            print(f"Σφάλμα αρχικοποίησης TTS: {e}")
            return None

    def speak(self, text):
        """Μετατρέπει κείμενο σε ομιλία."""
        if self.tts_engine:
            try:
                print(f"Ομιλία: {text}")
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"Σφάλμα ομιλίας: {e}")
        else:
            print(f"(TTS): {text}")

    def listen(self, timeout=5, phrase_time_limit=10):
        """
        Ακούει φωνητική εντολή και την επιστρέφει ως κείμενο.
        
        Args:
            timeout: Μέγιστος χρόνος αναμονής για ομιλία (δευτερόλεπτα)
            phrase_time_limit: Μέγιστος χρόνος ομιλίας (δευτερόλεπτα)
        
        Returns:
            str: Η αναγνωρισμένη φωνητική εντολή ή None αν αποτύχει.
        """
        with self.microphone as source:
            print("Προσαρμογή στο περιβάλλον θορύβου...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Μιλήστε τώρα...")
            
            try:
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                
                print("Αναγνώριση ομιλίας...")
                text = self.recognizer.recognize_google(audio, language="el-GR")
                return text.lower()
                
            except sr.WaitTimeoutError:
                print("Χρονικό όριο αναμονής: Δεν ανιχνεύθηκε ομιλία.")
                return None
            except sr.UnknownValueError:
                print("Δεν μπόρεσα να αναγνωρίσω την ομιλία.")
                return None
            except sr.RequestError as e:
                print(f"Σφάλση σύνδεσης με την υπηρεσία αναγνώρισης: {e}")
                return None
            except Exception as e:
                print(f"Απρόσμενο σφάλμα: {e}")
                return None

    def test_microphone(self):
        """Δοκιμή του μικροφώνου και αναγνώρισης ομιλίας."""
        print("=== Δοκιμή Μικροφώνου ===")
        print("Θα ακούσω για 5 δευτερόλεπτα...")
        
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print("Παρακαλώ μιλήστε...")
            
            try:
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio, language="el-GR")
                print(f"Αναγνώρισα: {text}")
                return text
            except Exception as e:
                print(f"Σφάλμα δοκιμής: {e}")
                return None

if __name__ == "__main__":
    # Δοκιμή του συστήματος φωνητικών εντολών
    vcs = VoiceCommandSystem()
    
    # Δοκιμή μικροφώνου
    test_result = vcs.test_microphone()
    
    if test_result:
        vcs.speak(f"Αναγνώρισα: {test_result}")
    else:
        vcs.speak("Δοκιμή μικροφώνου απέτυχε.")