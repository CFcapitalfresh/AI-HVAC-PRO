import os

def scan_project():
    # Το όνομα του αρχείου που θα δημιουργηθεί
    output_filename = "FULL_PROJECT_CODE.txt"
    
    # Φάκελοι που ΑΓΝΟΟΥΜΕ (για να μην γεμίσει σκουπίδια)
    ignore_dirs = {'.git', '__pycache__', 'venv', 'env', '.venv', '.streamlit'}
    
    # Τύποι αρχείων που θες να διαβάσω
    valid_extensions = {'.py', '.txt', '.md', '.toml'}

    print("🔄 Ξεκινάει η σάρωση του project...")
    
    with open(output_filename, "w", encoding="utf-8") as outfile:
        # Περπατάμε σε όλους τους φακέλους
        for root, dirs, files in os.walk("."):
            # Αφαιρούμε τους φακέλους που δεν θέλουμε
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                # Ελέγχουμε την κατάληξη του αρχείου
                if any(file.endswith(ext) for ext in valid_extensions):
                    # Εξαιρούμε το ίδιο το scanner και το αρχείο εξόδου
                    if file == "scanner.py" or file == output_filename:
                        continue

                    filepath = os.path.join(root, file)
                    print(f"📄 Διάβασμα: {filepath}")
                    
                    # Γράφουμε το όνομα του αρχείου
                    outfile.write(f"\n{'='*50}\n")
                    outfile.write(f"📂 ΑΡΧΕΙΟ: {filepath}\n")
                    outfile.write(f"{'='*50}\n")
                    
                    # Γράφουμε το περιεχόμενο
                    try:
                        with open(filepath, "r", encoding="utf-8") as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"❌ Σφάλμα ανάγνωσης: {str(e)}")
                    
                    outfile.write("\n")

    print(f"\n✅ ΕΤΟΙΜΟ! Όλος ο κώδικας είναι στο αρχείο: {output_filename}")

if __name__ == "__main__":
    scan_project()