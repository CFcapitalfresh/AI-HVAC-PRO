"""
Παραδείγματα προσαρμοσμένων εντολών για το σύστημα
"""

from voice_command_system import VoiceCommandSystem
import webbrowser
import os

class CustomVoiceCommands:
    """
    Κλάση με προσαρμοσμένες εντολές
    """
    
    def __init__(self, system: VoiceCommandSystem):
        self.system = system
        self._register_custom_commands()
        
    def _register_custom_commands(self):
        """Εγγραφή προσαρμοσμένων εντολών"""
        
        # Εντολές πλοήγησης ιστού
        def open_google():
            webbrowser.open("https://www.google.com")
            self.system.speak("Άνοιξα τον Google")
            
        def open_youtube():
            webbrowser.open("https://www.youtube.com")
            self.system.speak("Άνοιξα το YouTube")
            
        # Εντολές συστήματος
        def shutdown_command():
            self.system.speak("Απενεργοποίηση συστήματος σε 10 δευτερόλεπτα")
            os.system("shutdown /s /t 10")
            
        def cancel_shutdown():
            os.system("shutdown /a")
            self.system.speak("Ακύρωσα την απενεργοποίηση")
            
        # Εντολές υπολογισμών
        def calculator_command():
            self.system.speak("Εκκίνηση αριθμομηχανής")
            os.system("calc")
            
        # Εγγραφή εντολών
        self.system.register_command("google", open_google)
        self.system.register_command("youtube", open_youtube)
        self.system.register_command("απενεργοποίηση", shutdown_command)
        self.system.register_command("ακύρωση απενεργοποίησης", cancel_shutdown)
        self.system.register_command("αριθμομηχανή", calculator_command)
        self.system.register_command("υπολογιστής", calculator_command)
        
    def add_greeting_command(self, name: str = "φίλε"):
        """Προσθήκη εντολής χαιρετισμού"""
        
        def greeting():
            self.system.speak(f"Γεια σου {name}! Πώς μπορώ να σε βοηθήσω;")
            
        self.system.register_command("γεια", greeting)
        self.system.register_command("χαίρετε", greeting)