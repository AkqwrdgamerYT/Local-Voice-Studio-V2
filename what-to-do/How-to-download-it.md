# How to Download and Install Local Voice Studio

**Windows and Ubuntu 24.04 (64-bit) setup guide**

This guide covers two separate programs:

1. **Local Voice Studio** — the desktop app for recording audio, organizing voice models, and opening other tools.
2. **RVC WebUI** — a separate program that trains a voice model from recordings.

Local Voice Studio does **not** train or convert voices by itself. Live voice changing also needs a separate compatible voice converter.

## Platform support

| Program | Windows | Ubuntu 24.04 x86_64 |
| --- | --- | --- |
| Local Voice Studio | Supported | Supported by `voice_changer_linux.py` |
| RVC WebUI | Supported | Supported using the RVC project's CPU instructions |

These steps use the **CPU / AMD / Intel** setup and do not require an NVIDIA graphics card. RVC may run slowly without supported GPU acceleration.

## Contents

- [1. Download this repository](#1-download-this-repository)
- [2. Install Local Voice Studio on Windows](#2-install-local-voice-studio-on-windows)
- [3. Install Local Voice Studio on Ubuntu](#3-install-local-voice-studio-on-ubuntu)
- [4. Download and install RVC WebUI on Windows](#4-download-and-install-rvc-webui-on-windows)
- [5. Download and install RVC WebUI on Ubuntu](#5-download-and-install-rvc-webui-on-ubuntu)
- [6. Download RVC model-support files](#6-download-rvc-model-support-files)
- [7. Start RVC WebUI](#7-start-rvc-webui)
- [Troubleshooting](#troubleshooting)

## 1. Download this repository

On this GitHub repository page:

1. Click **Code_WIN** (for win) or **Code_linux** (for linux).
2. Choose **Download ZIP**.
3. Extract the ZIP to a folder you can find again.
4. Check that the extracted folder contains these files:

   ```text
   voice_changer_v2.py
   voice_changer_linux.py
   requirements.txt
   Start Local Voice Studio V2.bat
   Start Local Voice Studio Linux.sh
   ```

Use the Windows launcher on Windows and the Linux launcher on Ubuntu.

## 2. Install Local Voice Studio on Windows

1. Install **Python 3.12 (64-bit)** from [python.org](https://www.python.org/downloads/windows/).
2. Open the extracted repository folder.
3. Double-click **Start Local Voice Studio V2.bat**.
4. If it asks to install microphone packages, type `Y` and press Enter.

If the launcher does not work, open PowerShell in the repository folder and run:

```powershell
py -3.12 -m pip install -r .\requirements.txt
py -3.12 .\voice_changer_v2.py
```

## 3. Install Local Voice Studio on Ubuntu

These instructions target **Ubuntu 24.04 x86_64**.

1. Install Python 3.12, Tkinter, and the audio library needed by the microphone:

   ```bash
   sudo apt update
   sudo apt install -y python3.12 python3.12-venv python3-tk libportaudio2
   ```

2. Open Terminal in the extracted repository folder.
3. Start the app:

   ```bash
   bash "Start Local Voice Studio Linux.sh"
   ```

The launcher creates a `.venv` folder inside the repository, installs the Python packages listed in `requirements.txt` if needed, and starts `voice_changer_linux.py`. Keep the terminal open while using the app.

## 4. Download and install RVC WebUI on Windows

RVC WebUI is a **separate project**. Download it from the [official RVC GitHub repository](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI):

1. Click **Code → Download ZIP** on the RVC page.
2. Extract the ZIP.
3. Open the project folder containing both `webui.py` and `requirments_cpu_py312.txt`.

The RVC project spells “requirements” as `requirments` in that filename.

Open PowerShell in the folder containing those files, then create an isolated Python environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
```

Install the CPU build of PyTorch and the RVC CPU dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.4.1+cpu torchaudio==2.4.1+cpu torchvision==0.19.1+cpu --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple
.\.venv\Scripts\python.exe -m pip install --timeout 120 --retries 5 -r .\requirments_cpu_py312.txt
```

### If package downloads time out on Windows

The RVC requirements file may list package mirrors that are slow or inaccessible on your network. Open `requirments_cpu_py312.txt` in Notepad and replace the existing `--index-url` and `--extra-index-url` lines near the top with:

```text
--index-url https://pypi.org/simple
--extra-index-url https://download.pytorch.org/whl/cpu
```

Save the file and rerun the second install command. Package downloads can be large. If the network blocks them, ask its administrator or use another network where the downloads are allowed.

## 5. Download and install RVC WebUI on Ubuntu

These commands follow the RVC project's CPU setup for **Ubuntu 24.04 x86_64**. Open Terminal:

1. Install system packages:

   ```bash
   sudo apt update
   sudo apt install -y git python3.12 python3.12-venv python3.12-dev ffmpeg unzip libsndfile1 libportaudio2
   ```

2. Download RVC and enter its project folder:

   ```bash
   git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git
   cd Retrieval-based-Voice-Conversion-WebUI
   ```

3. Create the Python environment and install RVC:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip setuptools wheel
   python -m pip install --timeout 120 --retries 5 -r requirments_cpu_py312.txt
   ```

### If package downloads time out on Ubuntu

Edit `requirments_cpu_py312.txt` and replace its existing package index lines near the top with:

```text
--index-url https://pypi.org/simple
--extra-index-url https://download.pytorch.org/whl/cpu
```

Save the file, then rerun the `python -m pip install ...` command above.

## 6. Download RVC model-support files

RVC needs additional model-support files beyond its source code and Python packages. Download these from inside the RVC project folder.

### Windows PowerShell

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade huggingface_hub
.\.venv\Scripts\hf.exe download lj1995/VoiceConversionWebUI --revision main --include "hubert_base/*" --local-dir assets
.\.venv\Scripts\hf.exe download lj1995/VoiceConversionWebUI rmvpe.pt --revision main --local-dir assets/rmvpe
.\.venv\Scripts\hf.exe download lj1995/VoiceConversionWebUI --revision main --include "pretrained/*" "pretrained_v2/*" --local-dir assets
.\.venv\Scripts\hf.exe download lj1995/VoiceConversionWebUI mute.zip --revision main --local-dir .model-downloads
.\.venv\Scripts\python.exe -m zipfile -e .model-downloads\mute.zip logs
.\.venv\Scripts\hf.exe download lj1995/VoiceConversionWebUI rmvpe.onnx --revision main --local-dir assets/rmvpe
```

For RVC on Windows, also download [ffmpeg.exe](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/ffmpeg.exe?download=true) and [ffprobe.exe](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/ffprobe.exe?download=true). Put both files in the RVC project folder.

### Ubuntu Terminal

First activate the RVC virtual environment if it is not already active:

```bash
source .venv/bin/activate
```

Then download the model-support files:

```bash
python -m pip install --upgrade huggingface_hub
hf download lj1995/VoiceConversionWebUI --revision main --include "hubert_base/*" --local-dir assets
hf download lj1995/VoiceConversionWebUI rmvpe.pt --revision main --local-dir assets/rmvpe
hf download lj1995/VoiceConversionWebUI --revision main --include "pretrained/*" "pretrained_v2/*" --local-dir assets
hf download lj1995/VoiceConversionWebUI mute.zip --revision main --local-dir .model-downloads
python -m zipfile -e .model-downloads/mute.zip logs
```

Ubuntu's system packages provide FFmpeg. The `.onnx` DirectML file is for Windows and is not part of these Ubuntu steps.

## 7. Start RVC WebUI

Before starting RVC, check that its `webui.py` is configured to listen only on your own computer:

```python
server_name="127.0.0.1"
```

Do **not** expose the web UI with `server_name="0.0.0.0"`.

### Start on Windows

From the RVC project folder, run:

```powershell
.\.venv\Scripts\python.exe .\webui.py
```

### Start on Ubuntu

From the RVC project folder, activate its environment if needed, then run:

```bash
source .venv/bin/activate
python webui.py
```

Keep the terminal open. When RVC has finished starting, open **http://127.0.0.1:7865** in your browser.

## Connect RVC to Local Voice Studio

In Local Voice Studio's **Train a voice** tab, set:

- **RVC project folder:** the RVC folder containing `webui.py`.
- **Python executable (Windows):** `<RVC folder>\.venv\Scripts\python.exe`
- **Python executable (Ubuntu):** `<RVC folder>/.venv/bin/python`
- **Local RVC page:** `http://127.0.0.1:7865`

Confirm the local-only checkbox before asking Local Voice Studio to launch RVC. The Linux launcher starts the RVC process in the terminal running the app; keep that terminal open.

## Troubleshooting

- **The launcher says Python is missing:** install Python 3.12 and confirm that the required command is available (`py -3.12` on Windows or `python3.12` on Ubuntu).
- **Ubuntu says Tkinter is missing:** run `sudo apt install python3-tk`.
- **The microphone packages fail to install:** check that package downloads are allowed, then retry the launcher or install command.
- **RVC says the requirements file is missing:** make sure the terminal is in the project folder containing `webui.py`; the ZIP may contain an outer folder and a nested project folder.
- **Pip reports a timeout:** use the official package-index lines above, allow large downloads time to complete, and do not bypass network restrictions.
- **The RVC browser page cannot be reached:** leave the RVC terminal open, wait for startup to finish, then refresh `http://127.0.0.1:7865`.
- **The app says RVC is not local-only:** check `server_name` in `webui.py`. Use `127.0.0.1`, not `0.0.0.0`.

For current RVC instructions and updates, see the [official RVC repository](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI).
