# Local Voice Studio & RVC WebUI

**Download and setup guide for Windows and Linux**

This guide explains how to download and set up **Local Voice Studio** and **RVC WebUI**.

> **Important:** Local Voice Studio does not train or convert voices by itself. Use RVC WebUI to train a voice model, and a separate compatible live converter for live voice changing.

## Before you start

| Component | Windows | Linux |
| --- | --- | --- |
| Local Voice Studio app | Supported | Not currently supported |
| RVC WebUI | Supported | Supported on Ubuntu 24.04 x86_64 |

The Windows `.bat` launcher only works on Windows. Local Voice Studio also uses Windows-specific features, so it is not currently supported on Linux. On Linux, you can use RVC WebUI directly.

These instructions cover CPU / AMD / Intel systems and do not require an NVIDIA graphics card. RVC may run more slowly without a supported GPU.

## Contents

- [1. Download Local Voice Studio](#1-download-local-voice-studio)
- [2. Install Local Voice Studio on Windows](#2-install-local-voice-studio-on-windows)
- [3. Download and install RVC WebUI on Windows](#3-download-and-install-rvc-webui-on-windows)
- [4. Install and run RVC WebUI on Linux](#4-install-and-run-rvc-webui-on-linux)
- [5. Record clips and train a voice](#5-record-clips-and-train-a-voice)
- [Troubleshooting](#troubleshooting)
- [Privacy and permissions](#privacy-and-permissions)

## 1. Download Local Voice Studio

1. On this GitHub repository page, click **Code**, then **Download ZIP**.
2. Extract the ZIP file.
3. Open the extracted folder. It should contain `voice_changer_v2.py`, `requirements.txt`, and `Start Local Voice Studio V2.bat`.

## 2. Install Local Voice Studio on Windows

1. Install **Python 3.12 (64-bit)** from [python.org](https://www.python.org/downloads/windows/). During setup, enable **Add Python to PATH** if that option appears.
2. Open the extracted Local Voice Studio folder.
3. Double-click **Start Local Voice Studio V2.bat**. If it asks to install microphone packages, type `Y` and press Enter.

If the launcher does not work, open **PowerShell in the extracted folder** and run:

```powershell
py -3.12 -m pip install -r .\requirements.txt
py -3.12 .\voice_changer_v2.py
```

The app needs NumPy and sounddevice for microphone recording and testing. The launcher checks for these packages and can install them.

## 3. Download and install RVC WebUI on Windows

RVC WebUI is a separate project. Download its ZIP from the [official RVC repository](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI), extract it, and open the **inner project folder** containing both `webui.py` and `requirments_cpu_py312.txt`.

Install Python 3.12 (64-bit) if you have not already. Open PowerShell in that project folder, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
```

For CPU, AMD, or Intel hardware, install the CPU version of PyTorch and then RVC's CPU dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.4.1+cpu torchaudio==2.4.1+cpu torchvision==0.19.1+cpu --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple
.\.venv\Scripts\python.exe -m pip install --timeout 120 --retries 5 -r .\requirments_cpu_py312.txt
```

The filename is spelled `requirments_cpu_py312.txt` in the RVC project.

### If package downloads time out

The RVC requirements file may point to package mirrors that are slow or unavailable on some networks. Open `requirments_cpu_py312.txt` in a text editor and replace its package index lines at the top with:

```text
--index-url https://pypi.org/simple
--extra-index-url https://download.pytorch.org/whl/cpu
```

Save the file and retry the requirements install command. If your network blocks package downloads, ask its administrator or try later on a network you are allowed to use. Do not bypass network restrictions.

### Download RVC's required model-support files

Run these commands from the RVC project folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade huggingface_hub
.\.venv\Scripts\hf.exe download lj1995/VoiceConversionWebUI --revision main --include "hubert_base/*" --local-dir assets
.\.venv\Scripts\hf.exe download lj1995/VoiceConversionWebUI rmvpe.pt --revision main --local-dir assets/rmvpe
.\.venv\Scripts\hf.exe download lj1995/VoiceConversionWebUI --revision main --include "pretrained/*" "pretrained_v2/*" --local-dir assets
.\.venv\Scripts\hf.exe download lj1995/VoiceConversionWebUI mute.zip --revision main --local-dir .model-downloads
.\.venv\Scripts\python.exe -m zipfile -e .model-downloads\mute.zip logs
```

Windows CPU / AMD / Intel setups also need the DirectML RMVPE file:

```powershell
.\.venv\Scripts\hf.exe download lj1995/VoiceConversionWebUI rmvpe.onnx --revision main --local-dir assets/rmvpe
```

RVC also needs FFmpeg on Windows. Download [ffmpeg.exe](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/ffmpeg.exe?download=true) and [ffprobe.exe](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/ffprobe.exe?download=true), then put both files in the RVC project folder.

### Start RVC WebUI on Windows

Before launching, check that RVC's `webui.py` binds to your computer only:

```python
server_name="127.0.0.1"
```

It should **not** be set to `server_name="0.0.0.0"`. The local setting prevents other devices on the network from accessing the RVC page.

Start RVC from its project folder:

```powershell
.\.venv\Scripts\python.exe .\webui.py
```

Keep the terminal window open. Open **http://127.0.0.1:7865** in your browser after the server finishes starting.

## 4. Install and run RVC WebUI on Linux

The RVC project's instructions target **Ubuntu 24.04, 64-bit**. These commands install RVC's CPU version for a CPU / AMD / Intel system.

Open Terminal and install the system packages:

```bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv python3.12-dev ffmpeg unzip libsndfile1 libportaudio2
```

Download the RVC project and install its CPU dependencies:

```bash
git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git
cd Retrieval-based-Voice-Conversion-WebUI
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install --timeout 120 --retries 5 -r requirments_cpu_py312.txt
```

If the package mirrors time out, edit `requirments_cpu_py312.txt` and replace its index lines at the top with:

```text
--index-url https://pypi.org/simple
--extra-index-url https://download.pytorch.org/whl/cpu
```

Then rerun the `pip install -r` command.

Download the model-support files:

```bash
python -m pip install --upgrade huggingface_hub
hf download lj1995/VoiceConversionWebUI --revision main --include "hubert_base/*" --local-dir assets
hf download lj1995/VoiceConversionWebUI rmvpe.pt --revision main --local-dir assets/rmvpe
hf download lj1995/VoiceConversionWebUI --revision main --include "pretrained/*" "pretrained_v2/*" --local-dir assets
hf download lj1995/VoiceConversionWebUI mute.zip --revision main --local-dir .model-downloads
python -m zipfile -e .model-downloads/mute.zip logs
```

Check that `webui.py` uses `server_name="127.0.0.1"` rather than `server_name="0.0.0.0"`, then start RVC:

```bash
python webui.py
```

Keep the terminal open and visit **http://127.0.0.1:7865** in your browser. The Local Voice Studio desktop app is not currently supported on Linux; use RVC directly there.

## 5. Record clips and train a voice

1. In Local Voice Studio on Windows, open **Record & import**.
2. Enter a dataset name, select your microphone, then press and hold **Hold to test** while speaking. Release to finish the test.
3. Click **Start recording**, speak clearly in a quiet room, then click **Stop & save**. You can also import supported audio clips. Use multiple varied recordings; one short sentence is not enough to train a useful model.
4. Recordings are saved under `Documents\LocalVoiceStudio\datasets\<dataset name>`.
5. In RVC WebUI, select that dataset and follow its training steps. The exact controls can vary between RVC versions.
6. Export the trained voice model from RVC. In Local Voice Studio, open **My voices**, click **Import model...**, and select the exported `.pth` or `.onnx` file. If you have the matching RVC `.index`, select it when prompted.

> **Live conversion:** Local Voice Studio does not convert voices or automatically load a model into a live converter. Install a compatible converter separately, set its executable on the **Live changer** tab, launch it, then select the model and audio devices in the converter.

## Troubleshooting

- **The browser says the site cannot be reached:** keep the RVC terminal open, wait for startup to finish, then refresh `http://127.0.0.1:7865`.
- **The app says RVC is not local-only:** change `server_name="0.0.0.0"` to `server_name="127.0.0.1"` in `webui.py`, save, and relaunch RVC.
- **No microphone appears:** check Windows microphone permissions and input settings, then click **Refresh** in the app.
- **Pip reports a timeout:** use the official package index lines above, allow the install to finish, and use only a network where these downloads are permitted.
- **A recording is not a model:** recordings are training data. Train them in RVC and export a model before importing it into **My voices**.

## Privacy and permissions

Record and train only on your own voice or a voice you have permission to use. Keep recordings and model files private. Anyone with access to a working voice model may be able to copy or misuse it; no app can guarantee that a model cannot be extracted.

For the latest RVC requirements, consult the [official RVC repository](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI).
