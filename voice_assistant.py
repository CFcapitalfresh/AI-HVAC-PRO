#!/usr/bin/env python3
"""
Σύστημα Φωνητικής Εντολής
Senior AI Architect: Μαστρο-Νεκ
"""

import speech_recognition as sr
import pyttsx3
import time
import threading
import queue
import json
import os
from datetime import datetime
from typing import Dict, Callable, Any, List
import logging

# Ρύθμιση logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceCommandSystem:
    """Κύρια κλάση συστήματος φωνητικής εντολής"""
    
    def __init__(self, language: str = "el-GR", rate: int = 150):
        """
        Αρχικοποίηση συστήματος
        
        Args:
            language: Γλώσσα αναγνώρισης ('el-GR' για Ελληνικά, 'en-US' για Αγγλικά)
            rate: Ταχύτητα ομιλίας
        """
        self.language = language
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()
        self.commands: Dict[str, Dict[str, Any]] = {}
        self.is_listening = False
        self.command_queue = queue.Queue()
        self.engine.setProperty('rate', rate)
        
        # Προσθήκη βασικών εντολών
        self._register_default_commands()
        
        logger.info(f"Σύστημα φωνητικής εντολής αρχικοποιήθηκε με γλώσσα: {language}")
    
    def _register_default_commands(self):
        """Εγγραφή προκαθορισμένων εντολών"""
        
        @self.command("γεια", "χαιρετισμός")
        def greet():
            responses = ["Γεια σου!", "Χαίρω πολύ!", "Γεια και από μένα!"]
            return responses
        
        @self.command("ώρα", "πες μου την ώρα")
        def tell_time():
            now = datetime.now()
            return f"Η ώρα είναι {now.hour}:{now.minute}"
        
        @self.command("σταμάτα", "σταμάτησε την ακρόαση")
        def stop_listening():
            self.is_listening = False
            return "Σταματάω την ακρόαση"
        
        @self.command("βοήθεια", "εμφάνισε όλες τις εντολές")
        def show_help():
            help_text = "Διαθέσιμες εντολές:\n"
            for cmd, info in self.commands.items():
                help_text += f"- {cmd}: {info['description']}\n"
            return help_text
        
        @self.command("αλλαγή γλώσσας", "αλλαγή γλώσσας αναγνώρισης")
        def change_language():
            if self.language == "el-GR":
                self.language = "en-US"
                return "Changed to English"
            else:
                self.language = "el-GR"
                return "Αλλαγή σε Ελληνικά"
    
    def command(self, trigger: str, description: str = ""):
        """
        Decorator για εγγραφή νέων εντολών
        
        Args:
            trigger: Φράση που ενεργοποιεί την εντολή
            description: Περιγραφή της εντολής
        """
        def decorator(func: Callable):
            self.commands[trigger.lower()] = {
                'function': func,
                'description': description
            }
            return func
        return decorator
    
    def speak(self, text: str):
        """
        Μετατροπή κειμένου σε ομιλία
        
        Args:
            text: Κείμενο προς ομιλία
        """
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Σφάλμα κατά την ομιλία: {e}")
    
    def listen(self) -> str:
        """
        Ακρόαση και μετατροπή φωνής σε κείμενο
        
        Returns:
            Το αναγνωρισμένο κείμενο ή κενό string σε περίπτωση σφάλματος
        """
        with self.microphone as source:
            logger.info("Ρύθμιση θορύβου περιβάλλοντος...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logger.info("Ακρόαση...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
            except sr.WaitTimeoutError:
                return ""
            
            try:
                logger.info("Αναγνώριση ομιλίας...")
                text = self.recognizer.recognize_google(
                    audio, 
                    language=self.language,
                    show_all=False
                )
                logger.info(f"Αναγνωρίστηκε: {text}")
                return text.lower()
            except sr.UnknownValueError:
                logger.warning("Δεν κατάλαβα τι είπες")
                return ""
            except sr.RequestError as e:
                logger.error(f"Σφάλμα στην υπηρεσία αναγνώρισης: {e}")
                return ""
    
    def process_command(self, text: str) -> bool:
        """
        Επεξεργασία αναγνωρισμένου κειμένου και εκτέλεση εντολής
        
        Args:
            text: Το αναγνωρισμένο κείμενο
            
        Returns:
            True αν βρέθηκε και εκτελέστηκε εντολή, False διαφορετικά
        """
        if not text:
            return False
        
        # Έλεγχος για κάθε εντολή
        for trigger, command_info in self.commands.items():
            if trigger in text:
                try:
                    logger.info(f"Εκτέλεση εντολής: {trigger}")
                    result = command_info['function']()
                    
                    if isinstance(result, list):
                        import random
                        response = random.choice(result)
                    else:
                        response = str(result)
                    
                    self.speak(response)
                    return True
                    
                except Exception as e:
                    logger.error(f"Σφάλμα εκτέλεσης εντολής: {e}")
                    self.speak("Υπήρξε σφάλμα στην εκτέλεση της εντολής")
                    return True
        
        # Αν δεν βρέθηκε εντολή
        logger.info(f"Δεν βρέθηκε εντολή για: {text}")
        return False
    
    def start_listening(self, continuous: bool = True):
        """
        Έναρξη συνεχούς ακρόασης
        
        Args:
            continuous: Αν True, συνεχής ακρόαση μέχρι εντολή διακοπής
        """
        self.is_listening = True
        
        def listening_loop():
            while self.is_listening:
                text = self.listen()
                if text:
                    self.process_command(text)
                
                if not continuous:
                    break
                
                time.sleep(0.1)
        
        # Έναρξη ακρόασης σε ξεχωριστό thread
        thread = threading.Thread(target=listening_loop, daemon=True)
        thread.start()
        
        if continuous:
            logger.info("Σύστημα σε λειτουργία. Πες 'σταμάτα' για διακοπή.")
            self.speak("Σύστημα φωνητικής εντολής ενεργοποιήθηκε")
            
            # Αναμονή για εντολή διακοπής
            try:
                while self.is_listening:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.is_listening = False
                logger.info("Διακοπή από χρήστη")
        
        thread.join()
    
    def add_custom_command(self, trigger: str, function: Callable, description: str = ""):
        """
        Προσθήκη προσαρμοσμένης εντολής
        
        Args:
            trigger: Φράση ενεργοποίησης
            function: Συνάρτηση που θα εκτελεστεί
            description: Περιγραφή εντολής
        """
        self.commands[trigger.lower()] = {
            'function': function,
            'description': description
        }
        logger.info(f"Προστέθηκε νέα εντολή: {trigger}")
    
    def save_commands(self, filename: str = "commands.json"):
        """
        Αποθήκευση εντολών σε αρχείο JSON
        
        Args:
            filename: Όνομα αρχείου
        """
        # Δεν μπορούμε να αποθηκεύσουμε συναρτήσεις, μόνο metadata
        commands_data = {}
        for trigger, info in self.commands.items():
            commands_data[trigger] = {
                'description': info['description'],
                'function_name': info['function'].__name__
            }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(commands_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Εντολές αποθηκεύτηκαν στο {filename}")
    
    def load_commands(self, filename: str = "commands.json"):
        """
        Φόρτωση εντολών από αρχείο JSON
        
        Args:
            filename: Όνομα αρχείου
        """
        if not os.path.exists(filename):
            logger.warning(f"Το αρχείο {filename} δεν βρέθηκε")
            return
        
        with open(filename, 'r', encoding='utf-8') as f:
            commands_data = json.load(f)
        
        logger.info(f"Φορτώθηκαν {len(commands_data)} εντολές από {filename}")


# ΔΕΙΓΜΑ ΧΡΗΣΗΣ
if __name__ == "__main__":
    
    def main():
        """Κύρια συνάρτηση για δοκιμή"""
        
        # Δημιουργία συστήματος
        assistant = VoiceCommandSystem(language="el-GR", rate=160)
        
        # Προσθήκη προσαρμοσμένων εντολών
        @assistant.command("πες το όνομά σου", "πες ποιος είσαι")
        def say_name():
            return "Είμαι ο Μαστρο-Νεκ, ο Senior AI Architect!"
        
        @assistant.command("υπολόγισε", "υπολόγισε μαθηματική παράσταση")
        def calculate():
            assistant.speak("Πες μαθηματική παράσταση για υπολογισμό")
            expression = assistant.listen()
            
            if expression:
                try:
                    # Απλός υπολογισμός (ΠΡΟΣΟΧΗ: μην χρησιμοποιήσετε eval σε production!)
                    result = eval(expression)
                    return f"Το αποτέλεσμα είναι {result}"
                except:
                    return "Δεν μπορώ να υπολογίσω αυτή την παράσταση"
            return ""
        
        # Εκκίνηση συστήματος
        print("=" * 50)
        print("ΣΥΣΤΗΜΑ ΦΩΝΗΤΙΚΗΣ ΕΝΤΟΛΗΣ")
        print("=" * 50)
        print("\nΔιαθέσιμες εντολές:")
        for cmd, info in assistant.commands.items():
            print(f"  • {cmd}: {info['description']}")
        
        print("\nΠαραδείγματα:")
        print("  - 'Γεια' για χαιρετισμό")
        print("  - 'Ώρα' για την τρέχουσα ώρα")
        print("  - 'Βοήθεια' για λίστα εντολών")
        print("  - 'Πες το όνομά σου'")
        print("  - 'Υπολόγισε' για μαθηματικούς υπολογισμούς")
        print("  - 'Αλλαγή γλώσσας' για εναλλαγή Ελληνικά/Αγγλικά")
        print("  - 'Σταμάτα' για τερματισμό")
        print("\n" + "=" * 50)
        
        # Έναρξη συνεχούς ακρόασης
        assistant.start_listening(continuous=True)
        
        print("\nΣύστημα τερματίστηκε. Αντίο!")
    
    # Εκτέλεση
    main()