"""
Κύριο πρόγραμμα εκτέλεσης
"""

from voice_command_system import VoiceCommandSystem
from command_examples import CustomVoiceCommands
import argparse

def main():
    """Κύρια λειτουργία"""
    
    parser = argparse.ArgumentParser(description="Σύστημα Φωνητικών Εντολών")
    parser.add_argument("--mode", choices=["interactive", "background"], 
                       default="interactive", help="Λειτουργία λειτουργίας")
    parser.add_argument("--language", default="el-GR", 
                       help="Γλώσσα αναγνώρισης (π.χ. el-GR, en-US)")
    
    args = parser.parse_args()
    
    # Δημιουργία συστήματος
    print("=" * 50)
    print("ΣΥΣΤΗΜΑ ΦΩΝΗΤΙΚΩΝ ΕΝΤΟΛΩΝ")
    print("Αρχιτεκτονική: Μαστρο-Νεκ")
    print("=" * 50)
    
    system = VoiceCommandSystem(language=args.language)
    
    # Προσθήκη προσαρμοσμένων εντολών
    custom_commands = CustomVoiceCommands(system)
    custom_commands.add_greeting_command("χρήστη")
    
    # Εκτύπωση πληροφοριών
    print(f"\nΓλώσσα: {system.language}")
    print(f"Εγγεγραμμένες εντολές: {len(system.commands)}")
    print("\nΔιαθέσιμες εντολές:")
    for cmd in sorted(system.commands.keys()):
        print(f"  • {cmd}")
    
    print("\n" + "=" * 50)
    print("Το σύστημα είναι έτοιμο!")
    print("Πείτε 'βοήθεια' για λίστα εντολών")
    print("Πείτε 'σταμάτα' για τερματισμό")
    print("=" * 50 + "\n")
    
    # Εκκίνηση ανάλογα με τη λειτουργία
    if args.mode == "background":
        print("Εκκίνηση σε λειτουργία παρασκηνίου...")
        thread = system.start_background_listening()
        
        try:
            # Κρατάμε το πρόγραμμα ανοιχτό
            while system.is_listening:
                user_input = input("Πατήστε Enter για τερματισμό: ")
                if user_input == "":
                    system.is_listening = False
                    break
        except KeyboardInterrupt:
            system.is_listening = False
            print("\nΤερματισμός από χρήστη...")
            
    else:  # interactive mode
        system.start_listening_loop()
    
    # Αποθήκευση εντολών
    system.save_commands()
    print("\nΟλοκλήρωση προγράμματος")

if __name__ == "__main__":
    main()