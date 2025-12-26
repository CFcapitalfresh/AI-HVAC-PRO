"""
SERVICE: AI SORTER LOGIC
------------------------
Implements the decision tree for organizing files.
Hierarchy: Category -> Brand -> Model
"""
import streamlit as st
from core.drive_manager import DriveManager
from core.ai_engine import AIEngine
from core.config_loader import ConfigLoader
import logging
import time

logger = logging.getLogger("Service.Sorter")

class SorterService:
    def __init__(self):
        self.drive = DriveManager()
        self.ai = AIEngine()
        self.root_id = ConfigLoader.get_drive_folder_id()

    def process_unsorted_files(self, status_callback):
        """
        Κύρια διαδικασία ταξινόμησης.
        Args:
            status_callback: Συνάρτηση για να στέλνουμε μηνύματα στο UI.
        """
        if not self.root_id:
            status_callback("❌ Σφάλμα: Δεν βρέθηκε Root Folder ID.", "error")
            return

        # 1. Εύρεση PDF στον κεντρικό φάκελο (τα ατακτοποίητα)
        items = self.drive.list_files_in_folder(self.root_id)
        pdfs = [i for i in items if i['mimeType'] == 'application/pdf']
        
        if not pdfs:
            status_callback("✅ Δεν βρέθηκαν ατακτοποίητα αρχεία.", "success")
            return

        status_callback(f"🔎 Βρέθηκαν {len(pdfs)} αρχεία. Ξεκινά η ανάλυση...", "info")
        
        count = 0
        for pdf in pdfs:
            status_callback(f"⚙️ Επεξεργασία: {pdf['name']}...", "running")
            
            # A. Λήψη περιεχομένου (μερικώς)
            # Σημείωση: Εδώ θα χρειαζόμασταν βιβλιοθήκη pypdf για extract text από το stream
            # Για συντομία, στέλνουμε το όνομα αρχείου στο AI αν δεν μπορούμε να διαβάσουμε κείμενο
            text_sample = pdf['name'] 
            
            # B. AI Analysis
            metadata_str = self.ai.extract_metadata_from_text(text_sample, pdf['name'])
            # Αναμένουμε μορφή: CATEGORY|BRAND|MODEL
            
            try:
                parts = metadata_str.split('|')
                if len(parts) < 3: raise ValueError("Invalid AI Format")
                
                cat, brand, model = parts[0].strip(), parts[1].strip(), parts[2].strip()
                
                if cat == "Unknown" or brand == "Unknown":
                    status_callback(f"⚠️ Αγνωστο περιεχόμενο: {pdf['name']}", "warning")
                    continue

                # C. Δημιουργία Ιεραρχίας Φακέλων
                # 1. Category Folder
                cat_id = self.drive.create_folder(cat, self.root_id)
                if not cat_id: continue
                
                # 2. Brand Folder
                brand_id = self.drive.create_folder(brand, cat_id)
                if not brand_id: continue
                
                # 3. Model Folder (Προαιρετικό - αν υπάρχει μοντέλο)
                target_id = brand_id
                if model != "Unknown" and model != "General":
                    target_id = self.drive.create_folder(model, brand_id) or brand_id

                # D. Μετακίνηση
                success = self.drive.move_file(pdf['id'], target_id)
                if success:
                    status_callback(f"✅ Τακτοποιήθηκε: {cat}/{brand}/{model}", "success")
                    count += 1
                
                time.sleep(1) # Rate Limit Protection

            except Exception as e:
                logger.error(f"Sorting Error: {e}")
                status_callback(f"❌ Σφάλμα στο αρχείο {pdf['name']}", "error")

        status_callback(f"🎉 Ολοκληρώθηκε! Τακτοποιήθηκαν {count} αρχεία.", "success")