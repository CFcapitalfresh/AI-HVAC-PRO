"""
Κύριο αρχείο για το σύστημα AI HVAC.
Ενσωματώνει το σύστημα φωνητικών εντολών και τον έλεγχο HVAC.
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
required_packages = ['pyttsx3', 'speech_recognition', 'pyserial']
for package in required_packages:
    install_package(package)

from voice_command_system import VoiceCommandSystem
from hvac_controller import HVACController
import time

class AIHVACSystem:
    def __init__(self):
        """Αρχικοποίηση του συστήματος AI HVAC."""
        self.voice_system = VoiceCommandSystem()
        self.hvac_controller = HVACController()
        self.running = True

    def process_command(self, command):
        """Επεξεργάζεται φωνητικές εντολές και ελέγχει το HVAC."""
        command = command.lower()

        if "ενεργοποίησε" in command and "κλιματισμό" in command:
            self.hvac_controller.turn_on()
            return "Κλιματισμός ενεργοποιήθηκε."
        elif "απενεργοποίησε" in command and "κλιματισμό" in command:
            self.hvac_controller.turn_off()
            return "Κλιματισμός απενεργοποιήθηκε."
        elif "ρύθμισε θερμοκρασία" in command:
            try:
                temp = int(''.join(filter(str.isdigit, command)))
                self.hvac_controller.set_temperature(temp)
                return f"Θερμοκρασία ρυθμίστηκε στους {temp}°C."
            except ValueError:
                return "Δεν μπόρεσα να διαβάσω τη θερμοκρασία."
        elif "κατάσταση" in command:
            status = self.hvac_controller.get_status()
            return f"Κατάσταση HVAC: {status}"
        elif "βγες" in command or "τερμάτισε" in command:
            self.running = False
            return "Τερματισμός συστήματος."
        else:
            return "Δεν κατάλαβα την εντολή. Δοκίμασε ξανά."

    def run(self):
        """Κύριος βρόχος λειτουργίας του συστήματος."""
        print("=== Σύστημα AI HVAC Ενεργοποιήθηκε ===")
        print("Πες 'βγες' ή 'τερμάτισε' για έξοδο.")
        
        while self.running:
            print("\nΑκούω... (Πες 'ενεργοποίησε κλιματισμό', 'ρύθμισε θερμοκρασία 22', κλπ.)")
            command = self.voice_system.listen()
            
            if command:
                print(f"Εντολή: {command}")
                response = self.process_command(command)
                self.voice_system.speak(response)
                print(f"Απόκριση: {response}")
            
            time.sleep(1)

        print("Σύστημα AI HVAC τερματίστηκε.")

if __name__ == "__main__":
    system = AIHVACSystem()
    system.run()