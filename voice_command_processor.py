"""
Σύστημα επεξεργασίας φωνητικών εντολών - Mastronek AI Architecture
Κύρια αρχιτεκτονική για real-time φωνητική κατανόηση και εκτέλεση εντολών
"""

import speech_recognition as sr
import pyttsx3
import numpy as np
from datetime import datetime
import json
import threading
import queue
import re
from typing import Dict, List, Optional, Callable
import logging

class VoiceCommandProcessor:
    """
    Βασική κλάση επεξεργασίας φωνητικών εντολών με modular αρχιτεκτονική
    """
    
    def __init__(self, language="el-GR", energy_threshold=300):
        """
        Αρχικοποίηση επεξεργαστή φωνητικών εντολών
        
        Args:
            language: Γλώσσα αναγνώρισης (προεπιλογή Ελληνικά)
            energy_threshold: Κατώφλι ενέργειας για ανίχνευση ομιλίας
        """
        self.logger = self._setup_logger()
        self.language = language
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.dynamic_energy_threshold = True
        
        self.command_registry = {}
        self.context_memory = {}
        self.is_listening = False
        self.command_queue = queue.Queue()
        
        # Αρχικοποίηση text-to-speech engine
        self.tts_engine = self._init_tts()
        
        self.logger.info("✅ Αρχικοποιήθηκε ο Voice Command Processor")
    
    def _setup_logger(self) -> logging.Logger:
        """Ρύθμιση συστήματος καταγραφής"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _init_tts(self):
        """Αρχικοποίηση συστήματος text-to-speech"""
        try:
            engine = pyttsx3.init()
            # Ρυθμίσεις για Ελληνική ομιλία
            engine.setProperty('rate', 150)  # Ταχύτητα ομιλίας
            engine.setProperty('volume', 0.9)  # Ένταση
            return engine
        except Exception as e:
            self.logger.error(f"Σφάλμα αρχικοποίησης TTS: {e}")
            return None
    
    def register_command(self, command_pattern: str, handler: Callable, 
                        description: str = ""):
        """
        Εγγραφή νέας φωνητικής εντολής
        
        Args:
            command_pattern: Regex pattern για την εντολή
            handler: Συνάρτηση που θα εκτελεστεί
            description: Περιγραφή της εντολής
        """
        self.command_registry[command_pattern] = {
            'handler': handler,
            'description': description,
            'pattern': re.compile(command_pattern, re.IGNORECASE)
        }
        self.logger.info(f"📝 Εγγράφηκε εντολή: {command_pattern}")
    
    def speak(self, text: str):
        """Μετατροπή κειμένου σε ομιλία"""
        if self.tts_engine:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            self.logger.info(f"🗣️  Ομιλία: {text}")
    
    def process_audio(self, audio_data) -> Optional[str]:
        """
        Επεξεργασία ήχου και εξαγωγή κειμένου
        
        Args:
            audio_data: Δεδομένα ήχου από το microphone
            
        Returns:
            Το αναγνωρισμένο κείμενο ή None
        """
        try:
            # Χρήση Google Speech Recognition
            text = self.recognizer.recognize_google(
                audio_data, 
                language=self.language
            )
            self.logger.info(f"🎤 Αναγνωρίστηκε: {text}")
            return text.lower()
            
        except sr.UnknownValueError:
            self.logger.warning("Δεν κατάλαβα τι είπες")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Σφάλμα στην αναγνώριση: {e}")
            return None
    
    def match_command(self, text: str) -> Optional[Dict]:
        """
        Αντιστοίχιση κειμένου με καταχωρημένες εντολές
        
        Args:
            text: Το αναγνωρισμένο κείμενο
            
        Returns:
            Πληροφορίες εντολής ή None
        """
        for pattern, command_info in self.command_registry.items():
            match = command_info['pattern'].match(text)
            if match:
                return {
                    'handler': command_info['handler'],
                    'matches': match.groups(),
                    'pattern': pattern,
                    'text': text
                }
        return None
    
    def execute_command(self, command_info: Dict):
        """Εκτέλεση της εντολής"""
        try:
            result = command_info['handler'](
                *command_info['matches'], 
                context=self.context_memory
            )
            self.logger.info(f"⚡ Εκτελέστηκε εντολή: {command_info['pattern']}")
            return result
        except Exception as e:
            self.logger.error(f"Σφάλμα εκτέλεσης εντολής: {e}")
            self.speak("Υπήρξε ένα σφάλμα στην εκτέλεση της εντολής")
    
    def listen_continuously(self, timeout: int = 5, phrase_time_limit: int = 10):
        """
        Συνεχής ακρόαση για εντολές
        
        Args:
            timeout: Χρόνος αναμονής για ομιλία
            phrase_time_limit: Μέγιστος χρόνος φράσης
        """
        self.is_listening = True
        
        def listening_thread():
            with sr.Microphone() as source:
                self.logger.info("🔊 Αρχίζει η ακρόαση...")
                self.speak("Είμαι έτοιμος να ακούσω εντολές")
                
                # Προσαρμογή για θόρυβο περιβάλλοντος
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                while self.is_listening:
                    try:
                        audio = self.recognizer.listen(
                            source, 
                            timeout=timeout,
                            phrase_time_limit=phrase_time_limit
                        )
                        
                        text = self.process_audio(audio)
                        if text:
                            command_info = self.match_command(text)
                            if command_info:
                                self.command_queue.put(command_info)
                            else:
                                self.logger.warning(f"Δεν βρέθηκε εντολή για: {text}")
                                self.speak("Δεν κατάλαβα αυτή την εντολή")
                                
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        self.logger.error(f"Σφάλμα ακρόασης: {e}")
        
        # Εκκίνηση thread ακρόασης
        thread = threading.Thread(target=listening_thread, daemon=True)
        thread.start()
        
        # Επεξεργασία εντολών από την ουρά
        self.process_command_queue()
    
    def process_command_queue(self):
        """Επεξεργασία ουράς εντολών"""
        def queue_processor():
            while self.is_listening:
                try:
                    command_info = self.command_queue.get(timeout=1)
                    self.execute_command(command_info)
                except queue.Empty:
                    continue
        
        processor_thread = threading.Thread(target=queue_processor, daemon=True)
        processor_thread.start()
    
    def stop_listening(self):
        """Διακοπή ακρόασης"""
        self.is_listening = False
        self.logger.info("⏹️  Διακόπηκε η ακρόαση")
        self.speak("Διακόπτω την ακρόαση")

# ============================================================================
# ΠΡΟΚΑΤΑΣΚΕΥΑΣΜΕΝΕΣ ΕΝΤΟΛΕΣ
# ============================================================================

class DefaultCommands:
    """
    Βιβλιοθήκη προκατασκευασμένων εντολών
    """
    
    @staticmethod
    def greet(*args, **kwargs):
        """Εντολή χαιρετισμού"""
        greetings = [
            "Γεια σου! Πώς μπορώ να βοηθήσω;",
            "Χαίρομαι που σε βλέπω!",
            "Γεια! Είμαι έτοιμος για εντολές."
        ]
        import random
        return random.choice(greetings)
    
    @staticmethod
    def get_time(*args, **kwargs):
        """Εντολή λήψης ώρας"""
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        return f"Η ώρα είναι {time_str}"
    
    @staticmethod
    def get_date(*args, **kwargs):
        """Εντολή λήψης ημερομηνίας"""
        now = datetime.now()
        date_str = now.strftime("%d %B %Y")
        return f"Σήμερα είναι {date_str}"
    
    @staticmethod
    def calculate(expression, *args, **kwargs):
        """Εντολή υπολογισμού"""
        try:
            # Ασφαλής υπολογισμός
            expression = expression.replace('x', '*').replace('^', '**')
            result = eval(expression, {"__builtins__": {}}, {})
            return f"Το αποτέλεσμα είναι {result}"
        except:
            return "Δεν μπορώ να εκτελέσω αυτόν τον υπολογισμό"
    
    @staticmethod
    def set_reminder(text, *args, **kwargs):
        """Εντολή ρύθμισης υπενθύμισης"""
        context = kwargs.get('context', {})
        reminders = context.get('reminders', [])
        reminders.append({
            'text': text,
            'time': datetime.now().isoformat()
        })
        context['reminders'] = reminders
        return f"Ορίστηκε υπενθύμιση: {text}"
    
    @staticmethod
    def list_reminders(*args, **kwargs):
        """Εντολή λίστας υπενθυμίσεων"""
        context = kwargs.get('context', {})
        reminders = context.get('reminders', [])
        
        if not reminders:
            return "Δεν υπάρχουν υπενθυμίσεις"
        
        response = "Οι υπενθυμίσεις σου:\n"
        for i, reminder in enumerate(reminders, 1):
            response += f"{i}. {reminder['text']}\n"
        
        return response

# ============================================================================
# ΚΥΡΙΟ ΣΥΣΤΗΜΑ
# ============================================================================

def main():
    """
    Κύριο πρόγραμμα επίδειξης του συστήματος
    """
    print("=" * 50)
    print("🎤 ΣΥΣΤΗΜΑ ΦΩΝΗΤΙΚΩΝ ΕΝΤΟΛΩΝ - MASTRONEK AI")
    print("=" * 50)
    
    # Δημιουργία επεξεργαστή
    processor = VoiceCommandProcessor(language="el-GR")
    
    # Εγγραφή προκατασκευασμένων εντολών
    processor.register_command(
        r'^(γεια|χαίρετε|hello|hey).*',
        DefaultCommands.greet,
        "Χαιρετισμός"
    )
    
    processor.register_command(
        r'^(πες μου )?την ώρα$',
        DefaultCommands.get_time,
        "Προβολή ώρας"
    )
    
    processor.register_command(
        r'^(πες μου )?την ημερομηνία$',
        DefaultCommands.get_date,
        "Προβολή ημερομηνίας"
    )
    
    processor.register_command(
        r'^υπολόγισε (.+)$',
        DefaultCommands.calculate,
        "Υπολογισμός μαθηματικών παραστάσεων"
    )
    
    processor.register_command(
        r'^όρισε υπενθύμιση (.+)$',
        DefaultCommands.set_reminder,
        "Ορισμός νέας υπενθύμισης"
    )
    
    processor.register_command(
        r'^(δείξε μου )?τις υπενθυμίσεις$',
        DefaultCommands.list_reminders,
        "Προβολή όλων των υπενθυμίσεων"
    )
    
    processor.register_command(
        r'^(σταμάτα|τερμάτισε|stop)$',
        lambda *args, **kwargs: processor.stop_listening(),
        "Διακοπή λειτουργίας"
    )
    
    # Εκκίνηση συστήματος
    print("\n📋 Διαθέσιμες εντολές:")
    for pattern, info in processor.command_registry.items():
        print(f"  • {pattern} - {info['description']}")
    
    print("\n🎧 Αρχίζει η ακρόαση... (πες 'σταμάτα' για έξοδο)")
    print("=" * 50)
    
    # Εκκίνηση συνεχούς ακρόασης
    processor.listen_continuously()
    
    # Κύριο loop
    try:
        while processor.is_listening:
            # Μπορείς να προσθέσεις άλλες εργασίες εδώ
            pass
    except KeyboardInterrupt:
        processor.stop_listening()
        print("\n\n👋 Έξοδος από το σύστημα")
    
    print("=" * 50)

if __name__ == "__main__":
    main()