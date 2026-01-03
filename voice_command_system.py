"""
Σύστημα Φωνητικών Εντολών
Αρχιτεκτονική: Μαστρο-Νεκ
"""

import speech_recognition as sr
import pyttsx3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable
import threading
import queue

class VoiceCommandSystem:
    """
    Κύρια κλάση για το σύστημα φωνητικών εντολών
    """
    
    def __init__(self, language: str = "el-GR"):
        """
        Αρχικοποίηση συστήματος
        
        Args:
            language: Γλώσσα αναγνώρισης (προεπιλογή: Ελληνικά)
        """
        self.language = language
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.commands: Dict[str, Callable] = {}
        self.is_listening = False
        self.command_queue = queue.Queue()
        
        # Ρυθμίσεις φωνής
        self._setup_voice()
        
        # Βασικές εντολές
        self._register_default_commands()
        
    def _setup_voice(self):
        """Ρύθμιση παραμέτρων φωνής"""
        voices = self.engine.getProperty('voices')
        # Επιλογή ελληνικής φωνής αν υπάρχει
        for voice in voices:
            if 'greek' in voice.name.lower() or 'el' in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        self.engine.setProperty('rate', 150)  # Ταχύτητα ομιλίας
        self.engine.setProperty('volume', 0.9)  # Ένταση
        
    def _register_default_commands(self):
        """Εγγραφή προεπιλεγμένων εντολών"""
        
        def help_command():
            """Εντολή βοήθειας"""
            commands_list = "\n".join([f"- {cmd}" for cmd in self.commands.keys()])
            response = f"Διαθέσιμες εντολές:\n{commands_list}"
            self.speak(response)
            
        def time_command():
            """Εντολή ώρας"""
            current_time = datetime.now().strftime("%H:%M")
            self.speak(f"Η ώρα είναι {current_time}")
            
        def date_command():
            """Εντολή ημερομηνίας"""
            current_date = datetime.now().strftime("%d/%m/%Y")
            self.speak(f"Η ημερομηνία είναι {current_date}")
            
        def stop_command():
            """Εντολή διακοπής"""
            self.speak("Διακόπτω την ακρόαση")
            self.is_listening = False
            
        # Εγγραφή εντολών
        self.register_command("βοήθεια", help_command)
        self.register_command("ώρα", time_command)
        self.register_command("ημερομηνία", date_command)
        self.register_command("σταμάτα", stop_command)
        self.register_command("τερματισμός", stop_command)
        
    def register_command(self, command: str, function: Callable):
        """
        Εγγραφή νέας εντολής
        
        Args:
            command: Η φωνητική εντολή
            function: Συνάρτηση που θα εκτελεστεί
        """
        self.commands[command.lower()] = function
        
    def speak(self, text: str):
        """
        Ομιλία κειμένου
        
        Args:
            text: Κείμενο προς ομιλία
        """
        print(f"Σύστημα: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
        
    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """
        Ακρόαση φωνητικής εντολής
        
        Args:
            timeout: Χρόνος αναμονής για ομιλία (δευτερόλεπτα)
            phrase_time_limit: Μέγιστος χρόνος ομιλίας
            
        Returns:
            Το αναγνωρισμένο κείμενο ή None
        """
        with sr.Microphone() as source:
            print("Ακούω...")
            
            # Προσαρμογή για θόρυβο
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                # Αναγνώριση ομιλίας
                text = self.recognizer.recognize_google(
                    audio, 
                    language=self.language
                )
                
                print(f"Αναγνώρισα: {text}")
                return text.lower()
                
            except sr.WaitTimeoutError:
                print("Χρονικό όριο αναμονής")
                return None
            except sr.UnknownValueError:
                print("Δεν κατάλαβα τι είπες")
                self.speak("Δεν κατάλαβα, παρακαλώ επανάλαβε")
                return None
            except sr.RequestError as e:
                print(f"Σφάλμα σύνδεσης: {e}")
                self.speak("Πρόβλημα σύνδεσης")
                return None
                
    def process_command(self, text: str) -> bool:
        """
        Επεξεργασία αναγνωρισμένης εντολής
        
        Args:
            text: Το αναγνωρισμένο κείμενο
            
        Returns:
            True αν βρέθηκε και εκτελέστηκε εντολή
        """
        if not text:
            return False
            
        # Έλεγχος για ακριβή αντιστοίχιση
        if text in self.commands:
            self.commands[text]()
            return True
            
        # Έλεγχος για μερική αντιστοίχιση
        for command, function in self.commands.items():
            if command in text:
                function()
                return True
                
        # Αν δεν βρέθηκε εντολή
        self.speak(f"Δεν βρήκα εντολή για: {text}")
        return False
        
    def start_listening_loop(self):
        """Έναρξη συνεχούς ακρόασης"""
        self.is_listening = True
        self.speak("Σύστημα φωνητικών εντολών ενεργοποιήθηκε")
        
        while self.is_listening:
            text = self.listen()
            if text:
                self.process_command(text)
                
    def start_background_listening(self):
        """Έναρξη ακρόασης σε background thread"""
        self.is_listening = True
        thread = threading.Thread(target=self.start_listening_loop)
        thread.daemon = True
        thread.start()
        return thread
        
    def save_commands(self, filename: str = "commands.json"):
        """Αποθήκευση εντολών σε αρχείο"""
        commands_data = {
            "language": self.language,
            "registered_commands": list(self.commands.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(commands_data, f, ensure_ascii=False, indent=2)
            
    def load_commands(self, filename: str = "commands.json"):
        """Φόρτωση εντολών από αρχείο"""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Φορτώθηκαν {len(data.get('registered_commands', []))} εντολές")