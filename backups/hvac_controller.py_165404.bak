"""
Ελεγκτής HVAC συστήματος (προσομοίωση).
"""

import time
from datetime import datetime

class HVACController:
    def __init__(self):
        """Αρχικοποίηση ελεγκτή HVAC."""
        self.powered_on = False
        self.temperature = 22  # προεπιλεγμένη θερμοκρασία
        self.mode = "cooling"  # cooling, heating, fan_only
        self.fan_speed = "medium"
        
    def turn_on(self):
        """Ενεργοποίηση του HVAC συστήματος."""
        if not self.powered_on:
            self.powered_on = True
            print(f"[{datetime.now()}] HVAC ενεργοποιήθηκε.")
            return True
        return False
    
    def turn_off(self):
        """Απενεργοποίηση του HVAC συστήματος."""
        if self.powered_on:
            self.powered_on = False
            print(f"[{datetime.now()}] HVAC απενεργοποιήθηκε.")
            return True
        return False
    
    def set_temperature(self, temp):
        """
        Ρύθμιση θερμοκρασίας.
        
        Args:
            temp (int): Θερμοκρασία σε βαθμούς Celsius (16-30)
        
        Returns:
            bool: True αν η ρύθμιση ήταν επιτυχής
        """
        if 16 <= temp <= 30:
            self.temperature = temp
            print(f"[{datetime.now()}] Θερμοκρασία ρυθμίστηκε στους {temp}°C.")
            return True
        else:
            print(f"[{datetime.now()}] Μη έγκυρη θερμοκρασία: {temp}°C (επιτρεπτό: 16-30°C).")
            return False
    
    def set_mode(self, mode):
        """
        Ρύθμιση λειτουργίας.
        
        Args:
            mode (str): 'cooling', 'heating', ή 'fan_only'
        """
        valid_modes = ['cooling', 'heating', 'fan_only']
        if mode in valid_modes:
            self.mode = mode
            print(f"[{datetime.now()}] Λειτουργία ρυθμίστηκε σε: {mode}")
            return True
        return False
    
    def set_fan_speed(self, speed):
        """
        Ρύθμιση ταχύτητας ανεμιστήρα.
        
        Args:
            speed (str): 'low', 'medium', 'high', 'auto'
        """
        valid_speeds = ['low', 'medium', 'high', 'auto']
        if speed in valid_speeds:
            self.fan_speed = speed
            print(f"[{datetime.now()}] Ταχύτητα ανεμιστήρα ρυθμίστηκε σε: {speed}")
            return True
        return False
    
    def get_status(self):
        """Επιστρέφει την τρέχουσα κατάσταση του HVAC."""
        status = {
            "powered_on": self.powered_on,
            "temperature": self.temperature,
            "mode": self.mode,
            "fan_speed": self.fan_speed,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if self.powered_on:
            status_str = f"Ενεργό, Θερμοκρασία: {self.temperature}°C, Λειτουργία: {self.mode}"
        else:
            status_str = "Απενεργό"
        
        return status_str
    
    def simulate_operation(self, duration=10):
        """
        Προσομοίωση λειτουργίας HVAC.
        
        Args:
            duration (int): Διάρκεια προσομοίωσης σε δευτερόλεπτα
        """
        if not self.powered_on:
            print("Το HVAC είναι απενεργοποιημένο. Ενεργοποιήστε το πρώτα.")
            return
        
        print(f"Προσομοίωση λειτουργίας HVAC για {duration} δευτερόλεπτα...")
        for i in range(duration):
            print(f"  Λειτουργία... ({i+1}/{duration})")
            time.sleep(1)
        print("Προσομοίωση ολοκληρώθηκε.")

if __name__ == "__main__":
    # Δοκιμή του ελεγκτή HVAC
    hvac = HVACController()
    
    print("=== Δοκιμή HVAC Controller ===")
    print(f"Αρχική κατάσταση: {hvac.get_status()}")
    
    hvac.turn_on()
    hvac.set_temperature(24)
    hvac.set_mode("cooling")
    hvac.set_fan_speed("medium")
    
    print(f"Τελική κατάσταση: {hvac.get_status()}")
    
    # Μικρή προσομοίωση
    hvac.simulate_operation(3)
    
    hvac.turn_off()
    print(f"Κατάσταση μετά από απενεργοποίηση: {hvac.get_status()}")