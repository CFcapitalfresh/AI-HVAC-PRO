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
        
    def register_command(self, trigger: str, function: Callable):
        """
        Εγγραφή νέας εντολής
        
        Args:
            trigger: Λέξη-κλειδί για ενεργοποίηση
            function: Συνάρτηση που θα εκτελεστεί
        """
        self.commands[trigger.lower()] = function
        
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
                self.speak("Δεν κατάλαβα, παρακαλώ επανέλαβε")
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
            True αν βρέθηκε εντολή, False διαφορετικά
        """
        if not text:
            return False
            
        # Έλεγχος για κάθε εντολή
        for trigger, command_func in self.commands.items():
            if trigger in text:
                print(f"Εκτέλεση εντολής: {trigger}")
                
                # Προσθήκη στην ουρά για ασύγχρονη εκτέλεση
                self.command_queue.put((command_func, text))
                return True
                
        # Αν δεν βρέθηκε εντολή
        self.speak(f"Δεν βρήκα εντολή για: {text}")
        return False
        
    def command_worker(self):
        """Εργαζόμενος για επεξεργασία εντολών από την ουρά"""
        while self.is_listening or not self.command_queue.empty():
            try:
                command_func, text = self.command_queue.get(timeout=1)
                command_func()
                self.command_queue.task_done()
            except queue.Empty:
                continue
                
    def start_listening_loop(self):
        """
        Κύριος βρόχος ακρόασης
        """
        self.is_listening = True
        
        # Εκκίνηση εργαζομένου για εντολές
        worker_thread = threading.Thread(target=self.command_worker)
        worker_thread.daemon = True
        worker_thread.start()
        
        self.speak("Σύστημα φωνητικών εντολών ενεργοποιημένο. Πες 'βοήθεια' για διαθέσιμες εντολές.")
        
        while self.is_listening:
            # Ακρόαση εντολής
            text = self.listen()
            
            # Επεξεργασία αν υπάρχει κείμενο
            if text:
                self.process_command(text)
                
        print("Σύστημα απενεργοποιημένο")
        
    def run_single_command(self):
        """
        Εκτέλεση μίας εντολής
        """
        self.speak("Πες την εντολή σου")
        text = self.listen()
        
        if text:
            if not self.process_command(text):
                self.speak("Δεν βρήκα κατάλληλη εντολή")
                
    def save_commands(self, filename: str = "commands.json"):
        """
        Αποθήκευση εντολών σε αρχείο
        
        Args:
            filename: Όνομα αρχείου
        """
        # Μετατροπή σε λίστα για αποθήκευση
        commands_data = {
            "language": self.language,
            "commands": list(self.commands.keys())
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(commands_data, f, ensure_ascii=False, indent=2)
            
        print(f"Εντολές αποθηκεύτηκαν στο {filename}")
        
    def load_commands(self, filename: str = "commands.json"):
        """
        Φόρτωση εντολών από αρχείο
        
        Args:
            filename: Όνομα αρχείου
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                commands_data = json.load(f)
                
            print(f"Φορτώθηκαν {len(commands_data.get('commands', []))} εντολές")
            
        except FileNotFoundError:
            print(f"Το αρχείο {filename} δεν βρέθηκε")


class AdvancedVoiceAssistant(VoiceCommandSystem):
    """
    Προχωρημένος βοηθός με επιπλέον λειτουργίες
    """
    
    def __init__(self, language: str = "el-GR"):
        super().__init__(language)
        self.conversation_history = []
        self.user_preferences = {}
        
        # Εγγραφή πρόσθετων εντολών
        self._register_advanced_commands()
        
    def _register_advanced_commands(self):
        """Εγγραφή προχωρημένων εντολών"""
        
        def repeat_command():
            """Επανάληψη τελευταίας εντολής"""
            if self.conversation_history:
                last_command = self.conversation_history[-1]
                self.speak(f"Επανάληψη: {last_command}")
            else:
                self.speak("Δεν υπάρχει προηγούμενη εντολή")
                
        def clear_history_command():
            """Εκκαθάριση ιστορικού"""
            self.conversation_history.clear()
            self.speak("Ιστορικό εκκαθαρισμένο")
            
        def list_commands_command():
            """Λίστα όλων των εντολών"""
            commands = ", ".join(self.commands.keys())
            self.speak(f"Όλες οι εντολές: {commands}")
            
        # Εγγραφή νέων εντολών
        self.register_command("επανάλαβε", repeat_command)
        self.register_command("εκκαθάρισε", clear_history_command)
        self.register_command("λίστα", list_commands_command)
        
    def process_command(self, text: str) -> bool:
        """
        Βελτιωμένη επεξεργασία εντολών με ιστορικό
        """
        # Αποθήκευση στο ιστορικό
        self.conversation_history.append(text)
        
        # Κρατάμε μόνο τις τελευταίες 50 εντολές
        if len(self.conversation_history) > 50:
            self.conversation_history.pop(0)
            
        # Κλήση της βασικής μεθόδου
        return super().process_command(text)


def main():
    """
    Κύρια συνάρτηση εκτέλεσης
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Σύστημα Φωνητικών Εντολών")
    parser.add_argument("--mode", choices=["single", "continuous"], 
                       default="continuous", help="Λειτουργία λειτουργίας")
    parser.add_argument("--language", default="el-GR", 
                       help="Γλώσσα αναγνώρισης")
    parser.add_argument("--advanced", action="store_true",
                       help="Χρήση προχωρημένου βοηθού")
    
    args = parser.parse_args()
    
    # Δημιουργία συστήματος
    if args.advanced:
        assistant = AdvancedVoiceAssistant(language=args.language)
    else:
        assistant = VoiceCommandSystem(language=args.language)
    
    # Προσθήκη παραδειγματικής εντολής
    def custom_command():
        assistant.speak("Εκτέλεση προσαρμοσμένης εντολής!")
        
    assistant.register_command("προσαρμοσμένη", custom_command)
    
    print("=" * 50)
    print("ΣΥΣΤΗΜΑ ΦΩΝΗΤΙΚΩΝ ΕΝΤΟΛΩΝ")
    print(f"Γλώσσα: {args.language}")
    print(f"Λειτουργία: {args.mode}")
    print(f"Εντολές: {len(assistant.commands)}")
    print("=" * 50)
    
    # Εκτέλεση
    try:
        if args.mode == "single":
            assistant.run_single_command()
        else:
            assistant.start_listening_loop()
            
    except KeyboardInterrupt:
        print("\nΤερματισμός από χρήστη")
        assistant.is_listening = False
        assistant.speak("Αποσύνδεση")


if __name__ == "__main__":
    main()