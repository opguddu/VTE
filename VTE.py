# -*- coding: utf-8 -*-
"""
VTE - Visual Text Extractor & Multilingual Voice Translator
Fully Standalone Desktop application for real-time screen OCR, translation, and text-to-speech.
Zero-configuration: Works without Python or Tesseract pre-installed.
"""

import os
import sys
import time
import json
import shutil
import logging
from difflib import SequenceMatcher

import pytesseract
import pyttsx3
from PIL import ImageGrab, ImageEnhance
from PyQt5.QtCore import Qt, QRect, QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt5.QtGui import QPainter, QPen, QGuiApplication, QFont, QColor, QIcon
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFileDialog, QLabel, QStyle, QStatusBar, QComboBox, QProgressBar
)

# Application Paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller frozen exe."""
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    return os.path.join(APP_DIR, relative_path)

def get_writable_data_dir():
    """
    Returns a safe, writable directory for application logs and user configuration.
    - If running as a frozen app:
        - If installed in Program Files or the exe directory is not writable,
          use %APPDATA%\\VideoTextExtractor.
        - If the exe directory is writable and not in Program Files (portable mode),
          use the exe directory.
    - If running from source (development), use APP_DIR.
    """
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        pf_candidates = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        ]
        is_program_files = any(pf.lower() in exe_dir.lower() for pf in pf_candidates if pf)
        if not is_program_files:
            test_file = os.path.join(exe_dir, ".write_test")
            try:
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write("ok")
                os.remove(test_file)
                return exe_dir
            except Exception:
                pass

        app_data = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "VideoTextExtractor")
        os.makedirs(app_data, exist_ok=True)
        return app_data

    return APP_DIR

DATA_DIR = get_writable_data_dir()
CONFIG_FILE = os.path.join(DATA_DIR, "vte_config.json")
LOG_FILE = os.path.join(DATA_DIR, "text_extractor.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=LOG_FILE
)


def load_saved_tesseract_path():
    """Load previously configured tesseract path from json config."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                path = data.get("tesseract_cmd")
                if path and os.path.isfile(path):
                    return path
        except Exception as e:
            logging.warning(f"Could not read config file: {e}")
    return None


def save_tesseract_path(path):
    """Save valid tesseract path to json config."""
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["tesseract_cmd"] = path
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logging.error(f"Failed to save tesseract path: {e}")


def detect_tesseract():
    """
    Intelligently discover Tesseract OCR on Windows systems:
    1. Bundled Tesseract inside PyInstaller bundle (sys._MEIPASS)
    2. Bundled Tesseract adjacent to VTE.exe or script
    3. User-saved path in vte_config.json
    4. System PATH
    5. Standard Windows Program Files / LocalAppData locations
    """
    # 1. Check frozen PyInstaller _MEIPASS
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        meipass_tess = os.path.join(sys._MEIPASS, "Tesseract-OCR", "tesseract.exe")
        if os.path.isfile(meipass_tess):
            tessdata_dir = os.path.join(sys._MEIPASS, "Tesseract-OCR", "tessdata")
            if os.path.isdir(tessdata_dir):
                os.environ["TESSDATA_PREFIX"] = tessdata_dir
            return meipass_tess

    # 2. Check folder adjacent to executable or script
    base_dirs = []
    if getattr(sys, 'frozen', False):
        base_dirs.append(os.path.dirname(sys.executable))
    base_dirs.append(APP_DIR)

    for b in base_dirs:
        adj_tess = os.path.join(b, "Tesseract-OCR", "tesseract.exe")
        if os.path.isfile(adj_tess):
            tessdata_dir = os.path.join(b, "Tesseract-OCR", "tessdata")
            if os.path.isdir(tessdata_dir):
                os.environ["TESSDATA_PREFIX"] = tessdata_dir
            return adj_tess

    # 3. Check saved config
    saved = load_saved_tesseract_path()
    if saved and os.path.isfile(saved):
        return saved

    # 4. Check system PATH
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path

    # 5. Standard Windows Installation Paths
    candidate_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        r"C:\Tesseract-OCR\tesseract.exe",
        r"D:\Program Files\Tesseract-OCR\tesseract.exe",
        r"D:\Tesseract-OCR\tesseract.exe",
    ]
    for cp in candidate_paths:
        if os.path.isfile(cp):
            return cp
    return None


TESSERACT_EXE = detect_tesseract()
if TESSERACT_EXE:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
    logging.info(f"Tesseract OCR discovered: {TESSERACT_EXE}")
else:
    logging.warning("Tesseract OCR not automatically detected.")


class SafeTranslator:
    """Robust multilingual translator with direct API and multiple fallback tiers."""
    def __init__(self):
        self.session = None

    def translate(self, text, dest='en'):
        if not text or not str(text).strip():
            return type('obj', (object,), {'text': ''})

        text = str(text).strip()

        # Tier 1: Direct Google Translate Single API (Fastest, highly reliable)
        try:
            import requests
            if self.session is None:
                self.session = requests.Session()
                self.session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })
            
            url = 'https://translate.googleapis.com/translate_a/single'
            params = {
                'client': 'gtx',
                'sl': 'auto',
                'tl': dest,
                'dt': 't',
                'q': text
            }
            r = self.session.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                translated = ''.join([part[0] for part in data[0] if part and part[0]])
                if translated:
                    return type('obj', (object,), {'text': translated})
        except Exception as e:
            logging.warning(f"Tier 1 (Direct API) translation failed: {e}")

        # Tier 2: deep_translator GoogleTranslator
        try:
            from deep_translator import GoogleTranslator
            res = GoogleTranslator(source='auto', target=dest).translate(text)
            if res:
                return type('obj', (object,), {'text': res})
        except Exception as e:
            logging.warning(f"Tier 2 (deep-translator) failed: {e}")

        # Tier 3: googletrans
        try:
            from googletrans import Translator
            import asyncio
            tr = Translator()
            res = tr.translate(text, dest=dest)
            if asyncio.iscoroutine(res):
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                res = loop.run_until_complete(res)
            if hasattr(res, 'text'):
                return res
        except Exception as e:
            logging.warning(f"Tier 3 (googletrans) failed: {e}")

        # Tier 4: MyMemoryTranslator
        try:
            from deep_translator import MyMemoryTranslator
            res = MyMemoryTranslator(source='auto', target=dest).translate(text)
            if res:
                return type('obj', (object,), {'text': res})
        except Exception as e:
            logging.error(f"All translation tiers failed: {e}")
            return type('obj', (object,), {'text': f"Translation failed: {str(e)[:60]}"})


class TranslateThread(QThread):
    translation_completed = pyqtSignal(str)
    translation_progress = pyqtSignal(int)
    translation_error = pyqtSignal(str)

    def __init__(self, text, dest_lang, translator):
        super().__init__()
        self.text = text
        self.dest_lang = dest_lang
        self.translator = translator

    def run(self):
        try:
            self.translation_progress.emit(30)
            translated = self.translator.translate(self.text, dest=self.dest_lang)
            self.translation_progress.emit(90)

            if hasattr(translated, 'text'):
                self.translation_completed.emit(translated.text)
            else:
                self.translation_error.emit("Translation failed: Invalid response format")

        except Exception as e:
            logging.error(f"Translation Error: {e}")
            self.translation_error.emit(f"Translation failed: {str(e)[:100]}")
        finally:
            self.translation_progress.emit(100)


class ScreenCapture(QWidget):
    """Transparent overlay allowing the user to drag and select a capture rectangle."""
    area_selected = pyqtSignal(int, int, int, int)

    def __init__(self):
        super().__init__()
        self.start_x = self.start_y = self.end_x = self.end_y = 0
        self.selecting = False
        self.setGeometry(QGuiApplication.primaryScreen().geometry())
        self.setWindowTitle("Select Area for OCR")
        self.setWindowOpacity(0.3)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setCursor(Qt.CrossCursor)
        self.showFullScreen()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_x, self.start_y = event.x(), event.y()
            self.selecting = True

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.end_x, self.end_y = event.x(), event.y()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selecting = False
            x1, x2 = min(self.start_x, self.end_x), max(self.start_x, self.end_x)
            y1, y2 = min(self.start_y, self.end_y), max(self.start_y, self.end_y)

            if x2 - x1 > 10 and y2 - y1 > 10:
                self.hide()
                self.area_selected.emit(x1, y1, x2, y2)
            else:
                QMessageBox.warning(self, "Warning", "Selected area is too small. Please try again.")

    def paintEvent(self, event):
        if self.selecting:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.setBrush(QColor(255, 0, 0, 50))
            painter.drawRect(QRect(self.start_x, self.start_y, self.end_x - self.start_x, self.end_y - self.start_y))


class OCRThread(QThread):
    """Background continuous OCR worker on selected screen bounding box."""
    text_extracted = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, x1, y1, x2, y2):
        super().__init__()
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.running = True
        self.paused = False
        self.previous_text = ""
        self.mutex = QMutex()
        self.consecutive_failures = 0
        self.max_failures = 5

    def run(self):
        while self.running:
            try:
                with QMutexLocker(self.mutex):
                    if not self.running:
                        break
                    if self.paused:
                        time.sleep(0.5)
                        continue

                try:
                    bbox = (self.x1, self.y1, self.x2, self.y2)
                    img = ImageGrab.grab(bbox)

                    if img:
                        img = img.convert('L')
                        img = ImageEnhance.Contrast(img).enhance(2.0)

                        text = pytesseract.image_to_string(img, config='--psm 6').strip()

                        if text and self.is_significant_change(self.previous_text, text):
                            self.previous_text = text
                            self.text_extracted.emit(text)
                            self.consecutive_failures = 0
                    else:
                        logging.warning("Failed to grab screen bounding box")

                except Exception as e:
                    self.consecutive_failures += 1
                    logging.error(f"OCR Error: {e}")
                    if self.consecutive_failures >= self.max_failures:
                        self.error_occurred.emit(f"Multiple OCR failures: {str(e)}")
                        time.sleep(5)

                time.sleep(1)

            except Exception as e:
                logging.error(f"OCR Thread loop error: {e}")
                time.sleep(1)

    def is_significant_change(self, old_text, new_text, threshold=0.85):
        if not old_text or not new_text:
            return True
        return SequenceMatcher(None, old_text, new_text).ratio() < threshold

    def stop(self):
        with QMutexLocker(self.mutex):
            self.running = False
        self.wait(3000)

    def toggle_pause(self):
        with QMutexLocker(self.mutex):
            self.paused = not self.paused
        return self.paused


class TTSThread(QThread):
    """Text to Speech background worker with sentence chunking."""
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, text):
        super().__init__()
        self.text = text
        self.running = True
        self.engine = None

    def run(self):
        try:
            self.progress.emit(10)
            self.engine = pyttsx3.init()
            self.progress.emit(30)

            if self.text and self.running:
                if len(self.text) > 5000:
                    chunks = self.split_text_into_chunks(self.text)
                    total = len(chunks)
                    for i, chunk in enumerate(chunks):
                        if not self.running:
                            break
                        self.engine.say(chunk)
                        self.engine.runAndWait()
                        self.progress.emit(30 + int(60 * (i + 1) / total))
                else:
                    self.engine.say(self.text)
                    self.progress.emit(60)
                    self.engine.runAndWait()
                    self.progress.emit(90)

        except Exception as e:
            logging.error(f"TTS Error: {e}")
            self.error_occurred.emit(f"TTS Error: {str(e)}")
        finally:
            self.progress.emit(100)
            self.finished.emit()

    def split_text_into_chunks(self, text, max_length=1000):
        chunks = []
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        current = ""
        for s in sentences:
            if len(current) + len(s) < max_length:
                current += s + ". "
            else:
                if current:
                    chunks.append(current)
                current = s + ". "
        if current:
            chunks.append(current)
        return chunks

    def stop(self):
        self.running = False
        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass


class TextExtractorApp(QWidget):
    """Main Desktop UI for VTE."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VTE - Visual Text Extractor & Translator")
        self.setGeometry(200, 150, 780, 530)

        icon_path = get_resource_path("app.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.layout = QVBoxLayout()
        self.init_ui()
        self.ocr_thread = None
        self.tts_thread = None
        self.translate_thread = None
        self.reading = False
        self.translating = False
        self.translator = SafeTranslator()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #e0f7fa;
                font-family: Arial, sans-serif;
            }
        """)

        # Header Title
        header = QLabel("VTE - All In One Text Extractor")
        header.setFont(QFont('Arial', 20, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            color: #006064; 
            margin-bottom: 10px;
            background-color: #b2ebf2;
            padding: 8px;
            border-radius: 8px;
        """)
        self.layout.addWidget(header)

        # Dual Column Layout (Extracted & Translated Text)
        text_layout = QHBoxLayout()

        # Left Column: Extracted Text
        ext_col = QVBoxLayout()
        ext_lbl = QLabel("Extracted Text (Screen OCR):")
        ext_lbl.setFont(QFont('Arial', 11, QFont.Bold))
        ext_lbl.setStyleSheet("background-color: #80deea; padding: 4px 8px; border-radius: 4px; color: #004d40;")
        ext_col.addWidget(ext_lbl)
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("Live extracted text will appear here...")
        self.text_edit.setFont(QFont('Courier', 11))
        self.text_edit.setStyleSheet("""
            background-color: #ffffff;
            border: 2px solid #4fc3f7;
            padding: 8px;
            border-radius: 8px;
            color: #212121;
        """)
        ext_col.addWidget(self.text_edit)
        text_layout.addLayout(ext_col)

        # Right Column: Translated Text
        trans_col = QVBoxLayout()
        trans_lbl = QLabel("Translated Text:")
        trans_lbl.setFont(QFont('Arial', 11, QFont.Bold))
        trans_lbl.setStyleSheet("background-color: #80deea; padding: 4px 8px; border-radius: 4px; color: #004d40;")
        trans_col.addWidget(trans_lbl)
        self.translated_text_edit = QTextEdit(self)
        self.translated_text_edit.setPlaceholderText("Translated output will appear here...")
        self.translated_text_edit.setFont(QFont('Courier', 11))
        self.translated_text_edit.setStyleSheet("""
            background-color: #f1f8e9;
            border: 2px solid #81c784;
            padding: 8px;
            border-radius: 8px;
            color: #1b5e20;
        """)
        trans_col.addWidget(self.translated_text_edit)
        text_layout.addLayout(trans_col)

        self.layout.addLayout(text_layout)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #00acc1;
                border-radius: 5px;
                text-align: center;
                background-color: #e0f7fa;
            }
            QProgressBar::chunk {
                background-color: #00acc1;
            }
        """)
        self.layout.addWidget(self.progress_bar)

        # Language Dropdown Row
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Target Language:")
        lang_label.setFont(QFont('Arial', 10, QFont.Bold))
        lang_label.setStyleSheet("background-color: #80deea; padding: 5px; border-radius: 5px; color: #004d40;")
        lang_layout.addWidget(lang_label)

        self.language_combo = QComboBox(self)
        self.language_combo.addItems([
            "mr - Marathi",
            "hi - Hindi",
            "en - English",
            "es - Spanish",
            "fr - French",
            "de - German",
            "zh-cn - Chinese",
            "ja - Japanese",
            "ko - Korean",
            "ru - Russian",
            "it - Italian",
            "pt - Portuguese"
        ])
        self.language_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #4fc3f7;
                padding: 5px;
                border-radius: 5px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                background-color: #4fc3f7;
            }
        """)
        lang_layout.addWidget(self.language_combo)
        self.layout.addLayout(lang_layout)

        # Action Buttons Row
        self.button_layout = QHBoxLayout()

        self.extract_btn = QPushButton("Select Area & Start Extraction", self)
        self.extract_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #26a69a;
                color: white;
                font-weight: bold;
                border: none;
                padding: 9px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #00897b; }
        """)
        self.extract_btn.clicked.connect(self.start_selection)
        self.button_layout.addWidget(self.extract_btn)

        self.pause_btn = QPushButton("Pause", self)
        self.pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef5350;
                color: white;
                font-weight: bold;
                border: none;
                padding: 9px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #e53935; }
            QPushButton:disabled { background-color: #ffcdd2; color: #b71c1c; }
        """)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.button_layout.addWidget(self.pause_btn)

        self.read_btn = QPushButton("Read Aloud", self)
        self.read_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.read_btn.setStyleSheet("""
            QPushButton {
                background-color: #42a5f5;
                color: white;
                font-weight: bold;
                border: none;
                padding: 9px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #1e88e5; }
        """)
        self.read_btn.clicked.connect(self.toggle_read_aloud)
        self.button_layout.addWidget(self.read_btn)

        self.translate_btn = QPushButton("Translate", self)
        self.translate_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffb74d;
                color: #3e2723;
                font-weight: bold;
                border: none;
                padding: 9px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #ff9800; }
        """)
        self.translate_btn.clicked.connect(self.translate_text)
        self.button_layout.addWidget(self.translate_btn)

        self.copy_btn = QPushButton("Copy", self)
        self.copy_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #ab47bc;
                color: white;
                font-weight: bold;
                border: none;
                padding: 9px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #9c27b0; }
        """)
        self.copy_btn.clicked.connect(self.copy_text)
        self.button_layout.addWidget(self.copy_btn)

        self.save_btn = QPushButton("Save", self)
        self.save_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #78909c;
                color: white;
                font-weight: bold;
                border: none;
                padding: 9px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #607d8b; }
        """)
        self.save_btn.clicked.connect(self.save_text)
        self.button_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("Clear", self)
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ec407a;
                color: white;
                font-weight: bold;
                border: none;
                padding: 9px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #d81b60; }
        """)
        self.clear_btn.clicked.connect(self.clear_text)
        self.button_layout.addWidget(self.clear_btn)

        self.layout.addLayout(self.button_layout)

        # Status Bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready | VTE Standalone")
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #b2ebf2;
                border-top: 1px solid #00acc1;
                padding: 3px;
                color: #004d40;
                font-weight: bold;
            }
        """)
        self.layout.addWidget(self.status_bar)

        self.setLayout(self.layout)

    def check_tesseract_available(self):
        """Verify Tesseract OCR is available or provide user option to locate it."""
        global TESSERACT_EXE
        if not TESSERACT_EXE or not os.path.isfile(TESSERACT_EXE):
            TESSERACT_EXE = detect_tesseract()
            if TESSERACT_EXE:
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
                return True

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Tesseract OCR Not Found")
            msg.setText(
                "Tesseract OCR is required for screen text extraction.\n\n"
                "- If already installed, click 'Locate tesseract.exe' to browse to it.\n"
                "- Otherwise, download and install it from:\n"
                "  https://github.com/UB-Mannheim/tesseract/wiki"
            )
            locate_btn = msg.addButton("Locate tesseract.exe", QMessageBox.ActionRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec_()

            if msg.clickedButton() == locate_btn:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Select tesseract.exe", "C:\\", "Executable (tesseract.exe *.exe)"
                )
                if file_path and os.path.isfile(file_path):
                    TESSERACT_EXE = file_path
                    pytesseract.pytesseract.tesseract_cmd = file_path
                    save_tesseract_path(file_path)
                    QMessageBox.information(self, "Success", f"Tesseract OCR configured!\n{file_path}")
                    return True
            return False
        return True

    def start_selection(self):
        if not self.check_tesseract_available():
            return
        try:
            self.capture_window = ScreenCapture()
            self.capture_window.area_selected.connect(self.start_extraction)
            self.status_bar.showMessage("Select an area on the screen (click and drag)...")
        except Exception as e:
            self.show_error(f"Failed to start screen capture: {e}")

    def start_extraction(self, x1, y1, x2, y2):
        try:
            if self.ocr_thread:
                self.ocr_thread.stop()
                self.ocr_thread.wait()

            self.ocr_thread = OCRThread(x1, y1, x2, y2)
            self.ocr_thread.text_extracted.connect(self.append_text)
            self.ocr_thread.error_occurred.connect(self.show_error)
            self.ocr_thread.start()
            self.pause_btn.setEnabled(True)
            self.status_bar.showMessage(f"Extraction running on area ({x1},{y1}) to ({x2},{y2})...")
        except Exception as e:
            self.show_error(f"Failed to start extraction: {e}")

    def append_text(self, text):
        if text:
            self.text_edit.append(text)
            self.status_bar.showMessage(f"Text extracted ({len(text)} chars)")

    def toggle_pause(self):
        if self.ocr_thread:
            paused = self.ocr_thread.toggle_pause()
            self.pause_btn.setText("Resume" if paused else "Pause")
            self.status_bar.showMessage("Extraction paused" if paused else "Extraction resumed")

    def toggle_read_aloud(self):
        if self.reading:
            self.reading = False
            if self.tts_thread:
                self.tts_thread.stop()
                self.tts_thread.wait(1000)
            self.read_btn.setText("Read Aloud")
            self.progress_bar.setVisible(False)
            return

        text = self.text_edit.toPlainText()
        if not text:
            self.status_bar.showMessage("No text to read aloud")
            return

        self.reading = True
        self.read_btn.setText("Stop Reading")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.tts_thread = TTSThread(text)
        self.tts_thread.finished.connect(self.on_tts_finished)
        self.tts_thread.error_occurred.connect(self.show_error)
        self.tts_thread.progress.connect(self.update_progress)
        self.tts_thread.start()

    def on_tts_finished(self):
        self.reading = False
        self.read_btn.setText("Read Aloud")
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Reading completed")

    def translate_text(self):
        if self.translating:
            return

        text = self.text_edit.toPlainText()
        if not text:
            self.status_bar.showMessage("No text to translate")
            return

        try:
            target_lang = self.language_combo.currentText().split(" ")[0]

            self.translating = True
            self.translate_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(10)
            self.status_bar.showMessage(f"Translating to {target_lang}...")

            self.translate_thread = TranslateThread(text, target_lang, self.translator)
            self.translate_thread.translation_completed.connect(self.on_translation_completed)
            self.translate_thread.translation_error.connect(self.show_error)
            self.translate_thread.translation_progress.connect(self.update_progress)
            self.translate_thread.start()

        except Exception as e:
            logging.error(f"Translation Error: {e}")
            self.status_bar.showMessage(f"Translation failed: {str(e)[:100]}")
            self.translating = False
            self.translate_btn.setEnabled(True)
            self.progress_bar.setVisible(False)

    def on_translation_completed(self, translated_text):
        self.translated_text_edit.setPlainText(translated_text)
        self.status_bar.showMessage("Text translated successfully")
        self.translating = False
        self.translate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        self.status_bar.showMessage("Text copied to clipboard")

    def save_text(self):
        try:
            default_dir = os.path.join(os.path.expanduser("~"), "Documents")
            if not os.path.isdir(default_dir):
                default_dir = os.path.expanduser("~")
            default_path = os.path.join(default_dir, "extracted_text.txt")
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save File", default_path, "Text Files (*.txt);;All Files (*)"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(self.text_edit.toPlainText())
                self.status_bar.showMessage(f"Text saved to {filename}")
        except Exception as e:
            self.show_error(f"Failed to save file: {e}")

    def clear_text(self):
        reply = QMessageBox.question(
            self,
            "Clear Text",
            "Are you sure you want to clear both text boxes?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.text_edit.clear()
            self.translated_text_edit.clear()
            self.status_bar.showMessage("Text cleared")

    def show_error(self, message):
        logging.error(message)
        QMessageBox.warning(self, "Error", message)
        self.status_bar.showMessage(f"Error: {message[:50]}...")

    def closeEvent(self, event):
        try:
            if self.ocr_thread:
                self.ocr_thread.stop()
            if self.tts_thread and self.tts_thread.isRunning():
                self.tts_thread.stop()
            if self.translate_thread and self.translate_thread.isRunning():
                self.translate_thread.terminate()

            if self.ocr_thread:
                self.ocr_thread.wait(1000)
            if self.tts_thread:
                self.tts_thread.wait(1000)
            if self.translate_thread:
                self.translate_thread.wait(1000)

            event.accept()
        except Exception as e:
            logging.error(f"Error during application close: {e}")
            event.accept()


def exception_hook(exctype, value, traceback):
    logging.error(f"Uncaught exception: {exctype}, {value}", exc_info=(exctype, value, traceback))
    sys.__excepthook__(exctype, value, traceback)


def main():
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)
    window = TextExtractorApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
