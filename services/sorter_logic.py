"""
SERVICE: AI SORTER LOGIC (DEEP CONTENT ANALYSIS)
------------------------------------------------
Features:
- Reads PDF Content (First 15 pages -> Fallback to Full)
- 4-Level Hierarchy (Category > Brand > Model > Type)
- Quarantine for unknown files (_MANUAL_REVIEW)
"""
import streamlit as st
from core.drive_manager import DriveManager
from core.ai_engine import AIEngine
from core.config_loader import ConfigLoader
import logging
import time
import io
import pypdf

logger = logging.getLogger("Service.Sorter")

# Φάκελοι που αγνοούμε (για να μην ξανα-σκανάρει τα τακτοποιημένα)
IGNORED_FOLDERS = ["Boilers", "AirConditioners", "HeatPumps", "Solar", "Controllers", "WaterHeaters", "_MANUAL_REVIEW"]

class SorterService:
    def __init__(self):
        self.drive = DriveManager()
        self.ai = AIEngine()
        self.root_id = ConfigLoader.get_drive_folder_id()

    def _extract_text_from_pdf(self, file_id, pages_to_read=15):
        """
        Κατεβάζει το PDF στη μνήμη και εξάγει κείμενο.
        Πρώτα δοκιμάζει τις πρώτες X σελίδες.
        """
        try:
            # 1. Λήψη αρχείου στη μνήμη (χωρίς αποθήκευση στο δίσκο)
            file_stream = self.drive.download_file_content(file_id)
            if not file_stream: return None

            # 2. Ανάγνωση PDF
            reader = pypdf.PdfReader(file_stream)
            total_pages = len(reader.pages)
            text = ""
            
            # Διάβασμα των πρώτων X σελίδων
            limit = min(pages_to_read, total_pages)
            for i in range(limit):
                page_text = reader.pages[i].extract_text()
                if page_text: text += page_text + "\n"

            # 3. Fallback: Αν το κείμενο είναι πολύ λίγο (<200 chars), διάβασε ΟΛΟ το αρχείο
            if len(text) < 200 and total_pages > limit:
                # logger.info("Low text detected. Reading full document...")
                for i in range(limit, total_pages):
                    page_text = reader.pages[i].extract_text()
                    if page_text: text += page_text + "\n"

            return text
        except Exception as e:
            logger.error(f"PDF Read Error: {e}")
            return None

    def _find_all_pdfs_recursively(self, folder_id, status_callback, depth=0):
        """Αναδρομική εύρεση PDF, αγνοώντας τους 'Ιερούς' φακέλους."""
        if depth > 4: return [] 
        
        all_pdfs = []
        try:
            items = self.drive.list_files_in_folder(folder_id)
            for item in items:
                if item['mimeType'] == 'application/pdf':
                    all_pdfs.append(item)
                elif item['mimeType'] == 'application/vnd.google-apps.folder':
                    if depth == 0 and item['name'] in IGNORED_FOLDERS:
                        continue
                    status_callback(f"📂 Σάρωση: {item['name']}...", "info")
                    all_pdfs.extend(self._find_all_pdfs_recursively(item['id'], status_callback, depth + 1))
        except: pass
        return all_pdfs

    def process_unsorted_files(self, status_callback):
        """Κύρια διαδικασία Deep Sorting."""
        if not self.root_id:
            status_callback("❌ Σφάλμα: Δεν βρέθηκε Root Folder ID.", "error")
            return

        status_callback("🕵️ Έναρξη Βαθιάς Ανάλυσης Περιεχομένου...", "running")
        
        # 1. Εύρεση όλων των PDF
        pdfs = self._find_all_pdfs_recursively(self.root_id, status_callback)
        if not pdfs:
            status_callback("✅ Δεν βρέθηκαν αρχεία προς ταξινόμηση.", "success")
            return

        status_callback(f"🔎 Βρέθηκαν {len(pdfs)} αρχεία. Ξεκινά η μελέτη...", "info")
        
        count = 0
        manual_review_count = 0

        for pdf in pdfs:
            status_callback(f"📖 Μελέτη αρχείου: {pdf['name']}...", "running")
            
            try:
                # A. Εξαγωγή Κειμένου (Deep Read)
                pdf_text = self._extract_text_from_pdf(pdf['id'], pages_to_read=15)
                
                if not pdf_text or len(pdf_text.strip()) < 50:
                    status_callback(f"⚠️ Μη αναγνώσιμο PDF (Εικόνα;): {pdf['name']}", "warning")
                    # Εδώ θα μπορούσαμε να το στείλουμε στα 'Unsorted'
                    self._move_to_quarantine(pdf, "Unreadable_PDF")
                    manual_review_count += 1
                    continue

                # B. AI Analysis
                ai_result = self.ai.extract_metadata_from_text(pdf_text, pdf['name'])
                
                # C. Λήψη Απόφασης
                if "MANUAL_REVIEW" in ai_result or "|" not in ai_result:
                    self._move_to_quarantine(pdf, "_MANUAL_REVIEW")
                    status_callback(f"⚠️ Άγνωστο αρχείο -> Καραντίνα: {pdf['name']}", "warning")
                    manual_review_count += 1
                    continue

                parts = ai_result.split('|')
                if len(parts) < 4:
                    self._move_to_quarantine(pdf, "_AI_ERROR")
                    continue

                cat, brand, model, doc_type = [p.strip() for p in parts[:4]]

                # D. Δημιουργία Ιεραρχίας 4 Επιπέδων
                # 1. Category (π.χ. Boilers)
                cat_id = self.drive.create_folder(cat, self.root_id)
                if not cat_id: continue
                
                # 2. Brand (π.χ. Ariston)
                brand_id = self.drive.create_folder(brand, cat_id)
                if not brand_id: continue
                
                # 3. Model (π.χ. Clas One)
                model_id = self.drive.create_folder(model, brand_id) or brand_id
                
                # 4. Doc Type (π.χ. Service Manuals)
                type_id = self.drive.create_folder(doc_type, model_id) or model_id

                # E. Μετακίνηση
                if type_id not in pdf.get('parents', []):
                    success = self.drive.move_file(pdf['id'], type_id)
                    if success:
                        status_callback(f"✅ {brand} {model} -> {doc_type}", "success")
                        count += 1
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Processing Error: {e}")
                status_callback(f"❌ Σφάλμα στο αρχείο {pdf['name']}", "error")

        status_callback(f"🏁 Τέλος! Τακτοποιήθηκαν: {count}, Καραντίνα: {manual_review_count}", "success")

    def _move_to_quarantine(self, pdf_item, folder_name):
        """Μετακινεί το αρχείο σε ειδικό φάκελο για έλεγχο από τον άνθρωπο."""
        q_id = self.drive.create_folder(folder_name, self.root_id)
        if q_id:
            self.drive.move_file(pdf_item['id'], q_id)