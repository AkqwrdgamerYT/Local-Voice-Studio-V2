# How to Use Local Voice Studio

**A step-by-step guide to recording, training, and using a voice model**

Local Voice Studio helps you record voice clips, keep track of voice models, and open other voice tools. **It does not train or convert voices by itself.** RVC WebUI trains a voice model, and a separate live converter is needed for live voice changing.

## Before you start

| Tool | What it does |
| --- | --- |
| Local Voice Studio | Records or imports audio, keeps a list of model file paths, and launches other tools |
| RVC WebUI | Trains a voice model from a dataset of recordings |
| Live voice converter | Uses a trained model to convert microphone audio in real time |

Local Voice Studio currently runs on **Windows**. RVC WebUI can also be used directly on supported Linux systems. For installation instructions, see the [RVC WebUI project](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI).

Use your own voice or a voice you have permission to record and train. Keep recordings and model files private.

## Contents

- [1. Open Local Voice Studio](#1-open-local-voice-studio)
- [2. Record a microphone test](#2-record-a-microphone-test)
- [3. Create a voice dataset](#3-create-a-voice-dataset)
- [4. Train a model in RVC](#4-train-a-model-in-rvc)
- [5. Add the trained model to Local Voice Studio](#5-add-the-trained-model-to-local-voice-studio)
- [6. Set up live voice changing](#6-set-up-live-voice-changing)
- [7. Other tabs and buttons](#7-other-tabs-and-buttons)
- [Troubleshooting](#troubleshooting)
- [Privacy and responsible use](#privacy-and-responsible-use)

## 1. Open Local Voice Studio

On Windows, open the app by double-clicking **Start Local Voice Studio V2.bat**. If it asks to install microphone packages, choose **Y** and press Enter. The app opens with tabs for **My voices**, **Record & import**, **Live changer**, **Train a voice**, and **Privacy & safety**.

Use the **Theme** menu in the top-right corner to switch between Light and Dark. The app saves this preference.

## 2. Record a microphone test

1. Open **Record & import**.
2. Choose your microphone from **Microphone input**. If it is missing, click **Refresh**.
3. Press and hold **Hold to test** while speaking. Release the button to finish.
4. Watch the level meter while you speak. If it moves, the app is receiving microphone audio.
5. If Windows blocks access, click **Open Windows microphone privacy settings** and allow desktop apps to use the microphone.

The microphone test does **not** make a recording or train a model. It only checks the selected input.

## 3. Create a voice dataset

A **dataset** is the collection of audio clips used to train a voice model.

### Record clips

1. In **Record & import**, enter a name in **Dataset name**, such as `My voice`.
2. Select your microphone. Leave **Recording sample rate** on **Device default** unless you have a reason to change it.
3. Click **Start recording** and speak clearly in a quiet room.
4. Click **Stop & save** when you finish.
5. Repeat to make additional clips. Give the clips varied speech; one short sentence, including “The quick brown fox jumps over the lazy dog,” is not enough to train a useful model.
6. Click **Open dataset folder** to find the recordings.

Recordings are saved under:

```text
Documents\LocalVoiceStudio\datasets\<dataset name>
```

If your Windows Documents folder is managed by OneDrive, the app may use the OneDrive Documents folder instead.

### Import existing clips

1. Set the intended **Dataset name**.
2. Click **Import audio files...** and select WAV, FLAC, MP3, M4A, or OGG files.
3. The app copies the files into the dataset folder; it does not move or delete your originals.
4. Click **Open dataset folder** to check the copied clips.

Use clean recordings from one speaker. Avoid music, loud background noise, and other people speaking. Aim for at least **10 minutes** of varied, clear speech; more clean variety is generally better than repeatedly recording the same sentence.

## 4. Train a model in RVC

RVC has its own training controls. The wording and layout can differ between versions, but the general process is:

1. Make sure RVC WebUI is installed and its model-support files are downloaded.
2. In Local Voice Studio, open **Train a voice**.
3. Set **Python executable** to the Python used by your RVC installation. If you created a Windows virtual environment named `.venv` in the RVC project folder, its Python executable is usually:

   ```text
   <RVC project folder>\.venv\Scripts\python.exe
   ```

4. Set **RVC project folder** to the folder containing `webui.py`.
5. Keep **Local RVC page** set to `http://127.0.0.1:7865`, unless your RVC setup uses a different local port.
6. Make sure RVC is configured for local-only access (`127.0.0.1`, not `0.0.0.0`). Check the confirmation box in Local Voice Studio.
7. Click **Launch local RVC training UI**. Keep the RVC terminal open while using the browser page.
8. In RVC, select the dataset folder you made in section 3. Follow the RVC workflow to prepare the audio, extract features, train the model, and export the resulting model. Use the settings and instructions shown by your RVC version.
9. When training finishes, note where RVC saved the exported `.pth` model. If RVC created a matching `.index` file, note that location too.

Training time and quality depend on the audio, training settings, and computer. On a CPU or unsupported graphics card, training can take a long time.

> **If Local Voice Studio rejects a correctly configured local RVC address:** do not change the server to `0.0.0.0`. Start RVC manually from its project folder using the Python executable selected above and `webui.py`, then open `http://127.0.0.1:7865` in your browser. Keep the terminal window open.

## 5. Add the trained model to Local Voice Studio

1. Open **My voices**.
2. Click **Import model...** and choose the exported `.pth` or `.onnx` model.
3. If you selected a `.pth` model, the app asks for an optional RVC `.index` file. Choose the matching index, or cancel if you do not have one.
4. Select the model in the list and click **Open model folder** if you want to see where the file is stored.

The app stores the model's path; it does not copy the model file. Keep the model in place after importing it. **Remove from list** removes only the entry in Local Voice Studio; it does not delete the model from your computer.

## 6. Set up live voice changing

Live voice changing requires a separate compatible converter. Local Voice Studio does not include one.

1. Install a compatible converter. **Get the live converter** opens the converter project's download page; it does not install it.
2. In **Live changer**, click **Browse...** beside **Converter executable** and select the converter's `.exe`.
3. Keep **Local converter page** set to the address required by that converter. The app only permits local addresses such as `http://127.0.0.1:18888`.
4. Click **Save settings**, then **Launch live converter**.
5. In the converter's page, choose the trained model and set the microphone and output devices.
6. To use the converted voice in a game or call, select the converter's output or virtual microphone in that program. The exact audio-routing setup depends on the converter and any virtual audio device you use.

The voice list in Local Voice Studio does not automatically load a model into the converter; select the model in the converter itself.

## 7. Other tabs and buttons

### My voices

- **Import model...** adds a trained model path to the list.
- **Open model folder** opens the folder containing the selected model.
- **Remove from list** removes the selected entry from the app only.

### Record & import

- **Hold to test** checks that the selected microphone is capturing sound. Hold while speaking; release to finish.
- **Start recording** begins a WAV recording.
- **Stop & save** ends and saves the recording.
- **Import audio files...** copies supported audio into the selected dataset.
- **Open dataset folder** opens the folder for the current dataset name.
- **Refresh** reloads available microphone inputs.

### Train a voice

- **Python executable** points to the Python environment used by RVC.
- **RVC project folder** points to the folder containing `webui.py`.
- **Local RVC page** is the browser address for the RVC WebUI.
- The checkbox confirms that the RVC WebUI is local-only before the app attempts to launch it.

### Privacy & safety

This tab explains where the app stores recordings and model paths, and offers reminders about voice permissions and local-only web pages.

## Troubleshooting

- **No microphone appears:** check Windows **Settings → System → Sound → Input**, then click **Refresh**.
- **The meter does not move:** check the selected input, microphone mute switch, and Windows microphone privacy settings.
- **Recording does not save:** wait for the app to finish saving. Check that the dataset folder is writable and that another app is not interfering with the microphone.
- **RVC page cannot be reached:** keep the RVC terminal open, wait for startup to finish, then refresh `http://127.0.0.1:7865`.
- **RVC is reported as not local-only:** check that `webui.py` uses `server_name="127.0.0.1"`. Do not use `0.0.0.0`.
- **A model does not appear in the converter:** select it in the converter itself and verify that its model format is supported.
- **A recording is mistaken for a model:** recordings are training data. Train them in RVC and export a model before importing it into **My voices**.
- **Live conversion does not reach a call or game:** configure the converter's output device or virtual microphone, then select that device in the call or game.

## Privacy and responsible use

Only record or train on your own voice or a voice you have permission to use. Do not use a converted voice to impersonate someone or mislead others. Store recordings and model files somewhere private. Anyone who can access a working model may be able to copy or misuse it; no app can guarantee a model cannot be extracted.

