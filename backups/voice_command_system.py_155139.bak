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
        
        def greet_command():
            """Εντολή χαιρετισμού"""
            responses = [
                "Γεια σου! Πώς μπορώ να βοηθήσω;",
                "Χαίρω πολύ! Είμαι στη διάθεσή σου.",
                "Γεια! Έτοιμος για εντολές."
            ]
            import random
            self.speak(random.choice(responses))
            
        def time_command():
            """Εντολή ώρας"""
            now = datetime.now()
            time_str = now.strftime("%H:%M")
            self.speak(f"Η ώρα είναι {time_str}")
            
        def stop_command():
            """Διακοπή ακρόασης"""
            self.speak("Διακόπτω την ακρόαση")
            self.is_listening = False
            
        def help_command():
            """Βοήθεια για διαθέσιμες εντολές"""
            available_commands = "\n".join([f"- {cmd}" for cmd in self.commands.keys()])
            self.speak(f"Διαθέσιμες εντολές: {available_commands}")
        
        # Εγγραφή εντολών
        self.register_command("γεια", greet_command)
        self.register_command("χαιρετισμός", greet_command)
        self.register_command("ώρα", time_command)
        self.register_command("πόση ώρα είναι", time_command)
        self.register_command("σταμάτα", stop_command)
        self.register_command("διακοπή", stop_command)
        self.register_command("βοήθεια", help_command)
        self.register_command("εντολές", help_command)
        
    def register_command(self, phrase: str, function: Callable):
        """
        Εγγραφή νέας εντολής
        
        Args:
            phrase: Η φράση που ενεργοποιεί την εντολή
            function: Η συνάρτηση που θα εκτελεστεί
        """
        self.commands[phrase.lower()] = function
        print(f"📝 Εγγράφηκε εντολή: '{phrase}'")
        
    def speak(self, text: str):
        """
        Ομιλία κειμένου
        
        Args:
            text: Το κείμενο προς ομιλία
        """
        print(f"🔊: {text}")
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
            print("🎤 Ακούω... (μιλήστε τώρα)")
            
            # Ρύθμιση για περιβαλλοντικό θόρυβο
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                print("🔍 Αναγνώριση...")
                text = self.recognizer.recognize_google(audio, language=self.language)
                text = text.lower()
                print(f"📝 Αναγνωρίστηκε: '{text}'")
                return text
                
            except sr.WaitTimeoutError:
                print("⏰ Δεν ανιχνεύθηκε ομιλία")
                return None
            except sr.UnknownValueError:
                print("❌ Δεν κατάφερα να αναγνωρίσω την ομιλία")
                return None
            except sr.RequestError as e:
                print(f"⚠️ Σφάλμα σύνδεσης: {e}")
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
        for command_phrase, command_func in self.commands.items():
            if command_phrase in text:
                command_func()
                return True
                
        # Αν δεν βρέθηκε εντολή
        self.speak(f"Δεν βρήκα εντολή για: '{text}'. Πες 'βοήθεια' για τις διαθέσιμες εντολές.")
        return False
        
    def start_listening_loop(self):
        """Έναρξη συνεχούς ακρόασης"""
        self.is_listening = True
        self.speak("Έναρξη συστήματος φωνητικών εντολών")
        
        while self.is_listening:
            text = self.listen()
            if text:
                self.process_command(text)
                
    def start_background_listening(self):
        """Έναρξη ακρόασης σε background thread"""
        def listening_thread():
            self.start_listening_loop()
            
        thread = threading.Thread(target=listening_thread, daemon=True)
        thread.start()
        return thread
        
    def add_custom_command(self, phrase: str, action_type: str, **kwargs):
        """
        Προσθήκη προσαρμοσμένης εντολής
        
        Args:
            phrase: Η φράση ενεργοποίησης
            action_type: Τύπος ενέργειας ('speak', 'open_url', 'run_script')
            **kwargs: Παράμετροι για την ενέργεια
        """
        
        def custom_speak():
            """Ενέργεια ομιλίας"""
            message = kwargs.get('message', 'Εκτέλεση εντολής')
            self.speak(message)
            
        def open_url():
            """Ενέργεια άνοιγματος URL"""
            import webbrowser
            url = kwargs.get('url', 'https://www.google.com')
            webbrowser.open(url)
            self.speak(f"Άνοιξα το {url}")
            
        def run_script():
            """Ενέργεια εκτέλεσης script"""
            script_path = kwargs.get('script_path')
            if script_path and os.path.exists(script_path):
                os.system(f"python {script_path}")
                self.speak("Εκτέλεση script ολοκληρώθηκε")
            else:
                self.speak("Το script δεν βρέθηκε")
        
        # Αντιστοίχιση τύπων ενεργειών
        action_map = {
            'speak': custom_speak,
            'open_url': open_url,
            'run_script': run_script
        }
        
        if action_type in action_map:
            self.register_command(phrase, action_map[action_type])
            print(f"✅ Προστέθηκε προσαρμοσμένη εντολή: {phrase}")
        else:
            print(f"❌ Άγνωστος τύπος ενέργειας: {action_type}")
            
    def save_configuration(self, filename: str = "voice_commands_config.json"):
        """Αποθήκευση ρυθμίσεων"""
        config = {
            'language': self.language,
            'registered_commands': list(self.commands.keys()),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
        print(f"💾 Αποθηκεύτηκε η διαμόρφωση στο {filename}")
        
    def load_configuration(self, filename: str = "voice_commands_config.json"):
        """Φόρτωση ρυθμίσεων"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.language = config.get('language', self.language)
            print(f"📂 Φορτώθηκε διαμόρφωση από {filename}")
            
        except FileNotFoundError:
            print(f"⚠️ Το αρχείο {filename} δεν βρέθηκε")


class CommandManager:
    """
    Διαχειριστής εντολών για επέκταση λειτουργιών
    """
    
    def __init__(self, voice_system: VoiceCommandSystem):
        self.voice_system = voice_system
        self.command_history = []
        
    def execute_with_feedback(self, phrase: str, func: Callable, *args, **kwargs):
        """
        Εκτέλεση εντολής με ανατροφοδότηση
        
        Args:
            phrase: Η φράση που ενεργοποίησε την εντολή
            func: Η συνάρτηση προς εκτέλεση
        """
        try:
            # Προσθήκη στο ιστορικό
            self.command_history.append({
                'phrase': phrase,
                'timestamp': datetime.now().isoformat(),
                'status': 'executing'
            })
            
            # Εκτέλεση
            result = func(*args, **kwargs)
            
            # Ενημέρωση ιστορικού
            self.command_history[-1]['status'] = 'completed'
            self.command_history[-1]['result'] = str(result)
            
            return result
            
        except Exception as e:
            # Καταγραφή σφάλματος
            self.command_history[-1]['status'] = 'failed'
            self.command_history[-1]['error'] = str(e)
            self.voice_system.speak(f"Σφάλμα κατά την εκτέλεση: {str(e)}")
            raise


def main():
    """
    Κύρια λειτουργία συστήματος
    """
    print("=" * 50)
    print("ΣΥΣΤΗΜΑ ΦΩΝΗΤΙΚΩΝ ΕΝΤΟΛΩΝ")
    print("Αρχιτεκτονική: Μαστρο-Νεκ")
    print("=" * 50)
    
    # Δημιουργία συστήματος
    system = VoiceCommandSystem(language="el-GR")
    
    # Προσθήκη προσαρμοσμένων εντολών (παράδειγμα)
    system.add_custom_command(
        phrase="άνοιξε το google",
        action_type="open_url",
        url="https://www.google.com"
    )
    
    system.add_custom_command(
        phrase="πες κάτι",
        action_type="speak",
        message="Αυτό είναι ένα προσαρμοσμένο μήνυμα!"
    )
    
    # Εκκίνηση συστήματος
    print("\n🔊 Το σύστημα είναι έτοιμο!")
    print("Διαθέσιμες εντολές:")
    for cmd in system.commands.keys():
        print(f"  • {cmd}")
    
    print("\n🎯 Πες 'βοήθεια' για λίστα εντολών")
    print("🎯 Πες 'σταμάτα' για τερματισμό")
    print("=" * 50)
    
    # Έναρξη ακρόασης
    system.start_listening_loop()


if __name__ == "__main__":
    main()