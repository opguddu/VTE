# Video Text Extractor (VTE) 🔍🎙️🌐

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011%20(64--bit)-blue.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.12-brightgreen.svg)](#)
[![GUI](https://img.shields.io/badge/GUI-PyQt5-orange.svg)](#)
[![OCR](https://img.shields.io/badge/OCR-Tesseract%205.4-yellow.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

**Video Text Extractor (VTE)** is a high-performance Windows desktop application designed to capture, extract, translate, and speak text from any live video, streaming broadcast, subtitle feed, or screen region in real time.

Built with **PyQt5** and bundled with a fully embedded **Tesseract OCR (v5.x)** engine, VTE runs completely standalone on any Windows PC **without requiring Python, Visual Studio Code, or third-party package installations**.

---

## 📸 Screenshots & Highlights

- **Live Screen / Video Capture**: Drag a translucent selection overlay over any video player (YouTube, VLC, MP4, Teams/Zoom meetings) to extract text frames in real time.
- **Smart Change Detection**: Employs sequence matcher diffing (`SequenceMatcher < 0.85`) to avoid redundant extractions and only capture newly updated text.
- **Multilingual Instant Translation**: Translate extracted text on the fly into 12+ languages including Marathi, Hindi, English, Spanish, French, German, Chinese, Japanese, Korean, Russian, Italian, and Portuguese.
- **Natural Voice Reader (TTS)**: Built-in Text-to-Speech using the native Windows SAPI5 voice engine with sentence chunking for smooth listening without freezing.
- **Zero-Dependency Portable & Setup Installers**: Includes both a full Windows Setup wizard (`.exe`) and an unpack-and-run Portable ZIP archive.

---

## 📥 Downloads & Installation

### Option 1: Official Windows Installer (Recommended)
1. Download **`VideoTextExtractor_Setup.exe`** from the [Releases](https://github.com/opguddu/VTE/releases) page.
2. Run the installer wizard:
   - Select your installation folder (defaults to your user programs folder or `C:\Program Files\Video Text Extractor`).
   - Choose whether to create a **Desktop shortcut**.
   - Start Menu shortcuts and a clean Windows Uninstaller are automatically registered.
3. Launch **Video Text Extractor** from your Desktop or Start Menu!

### Option 2: Portable Edition (Zero Installation)
1. Download **`VideoTextExtractor-Portable-x64.zip`** from [Releases](https://github.com/opguddu/VTE/releases).
2. Extract the ZIP archive to any directory (e.g. Desktop, USB drive).
3. Double-click **`VTE.exe`** to start immediately.
4. *(Optional)* Run `Create Desktop Shortcut.bat` to place a shortcut on your Windows Desktop.

---

## 💻 Running from Source Code (Developers)

If you are developing or customizing the application:

### Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.10, 3.11, or 3.12
- Git

### 1-Click Launch (Recommended)
Simply clone the repository and double-click `run.bat`:
```bash
git clone https://github.com/opguddu/VTE.git
cd VTE
run.bat
```
`run.bat` automatically checks Python, creates an isolated virtual environment (`.venv`), installs required dependencies from `requirements.txt`, and boots the GUI.

### Manual Setup
```powershell
# 1. Clone the repository
git clone https://github.com/opguddu/VTE.git
cd VTE

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
python VTE.py
```

---

## 🛠️ Building Releases & Standalone Binaries

This project includes fully reproducible packaging scripts:

### 1. Build Standalone Folder (`dist\VTE`)
Runs PyInstaller using the dynamic, path-independent `VTE.spec`:
```cmd
build_standalone.bat
```
This bundles Python, PyQt5, pytesseract, Pillow, pyttsx3, and the embedded `Tesseract-OCR` folder into `dist\VTE\`.

### 2. Build Windows Installer & Portable ZIP
Compiles `installer.iss` using Inno Setup 6:
```cmd
build_installer.bat
```
Generates:
- `release_artifacts\VideoTextExtractor_Setup.exe` (78.4 MB)
- `release_artifacts\VideoTextExtractor-Portable-x64.zip` (116.8 MB)

---

## 🏗️ Architecture & Technology Stack

| Layer | Component | Description |
| :--- | :--- | :--- |
| **GUI Framework** | `PyQt5` | Responsive dual-pane editor, asynchronous background threads (`QThread`), transparent capture window (`ScreenCapture`). |
| **OCR Engine** | `pytesseract` + `Tesseract-OCR v5` | Optical character recognition running `--psm 6` with bundled `eng.traineddata` and `osd.traineddata` models. |
| **Video/Screen Grab** | `Pillow (PIL.ImageGrab)` | Real-time pixel buffer capture with contrast enhancement (2.0x) and 8-bit grayscale preprocessing. |
| **Translation** | `deep-translator` & `googletrans` | Asynchronous translation worker with automatic retry and error handling. |
| **Voice Synthesis** | `pyttsx3` | Offline Text-to-Speech using native Windows SAPI5 audio pipeline. |
| **Storage / Settings** | User Data Directory | Stores user configuration and logs in `%APPDATA%\VideoTextExtractor` when installed, avoiding permission errors. |

---

## 📋 System Requirements & Limitations

- **Operating System**: Windows 10 / Windows 11 (64-bit architecture).
- **Target Machine Requirements**: **Zero**. Neither Python nor Tesseract OCR needs to be installed on the user's laptop.
- **Network Access**: 
  - OCR extraction, screen capture, text editing, and voice read-aloud work **100% offline**.
  - Text translation requires an active Internet connection to contact the Google Translate API.

---

## 📄 License & Credits

Created by **Gaurav Mote** ([gauravmote9@gmail.com](mailto:gauravmote9@gmail.com)).  
Released under the MIT License.
