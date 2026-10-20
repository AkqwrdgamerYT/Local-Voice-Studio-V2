import json
import os
import queue
import re
import shutil
import subprocess
import threading
import tkinter as tk
import wave
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from time import monotonic
from urllib.parse import urlparse


APP_NAME = "Local Voice Studio"
LIVE_ENGINE_URL = "https://github.com/w-okada/voice-changer/releases"
TRAINING_PROJECT_URL = "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI"
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
AUDIO_EXTENSIONS = {".wav", ".flac", ".mp3", ".m4a", ".ogg"}
MODEL_EXTENSIONS = {".pth", ".onnx"}
PALETTES = {
	"Light": {
		"background": "#f3f5f9", "surface": "#ffffff", "field": "#ffffff",
		"text": "#202534", "muted": "#596579", "accent": "#4f46e5",
		"accent_hover": "#4338ca", "selection": "#dbeafe", "border": "#d7dce5",
		"disabled": "#a0a8b5",
	},
	"Dark": {
		"background": "#171923", "surface": "#222633", "field": "#1b1f2a",
		"text": "#edf0f7", "muted": "#aab2c3", "accent": "#7568f5",
		"accent_hover": "#8b80ff", "selection": "#39345f", "border": "#383e4d",
		"disabled": "#71798a",
	},
}


def settings_path():
	root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
	return root / "LocalVoiceStudio" / "settings.json"


def load_settings():
	path = settings_path()
	if not path.exists():
		return {"voices": []}
	try:
		with path.open("r", encoding="utf-8") as settings_file:
			settings = json.load(settings_file)
	except (OSError, json.JSONDecodeError) as error:
		raise RuntimeError(f"Could not read settings at {path}:\n{error}") from error
	if not isinstance(settings, dict) or not isinstance(settings.get("voices", []), list):
		raise RuntimeError(f"Settings file has an invalid format:\n{path}")
	return settings


class VoiceStudio:
	def __init__(self, root):
		self.root = root
		self.settings_readonly = False
		try:
			self.settings = load_settings()
		except RuntimeError as error:
			messagebox.showerror(
				"Settings error",
				f"{error}\n\nSettings will not be overwritten during this session.",
				parent=root,
			)
			self.settings_readonly = True
			self.settings = {"voices": []}

		root.title(f"{APP_NAME} V2")
		root.geometry("800x690")
		root.minsize(710, 600)

		self.theme = tk.StringVar(
			value=self.settings.get("theme")
			if self.settings.get("theme") in PALETTES else "Light"
		)
		self.dataset_name = tk.StringVar(value="My voice")
		self.recording_rate = tk.StringVar(value="Device default")
		self.recording_device = None
		self.input_devices = []
		self.recording_stream = None
		self.recording_queue = None
		self.recording_thread = None
		self.recording_path = None
		self.recording_audio = None
		self.recording_started = None
		self.recording_error = None
		self.recording_write_error = None
		self.recording_frames = [0]
		self.recording_lock = threading.Lock()
		self.mic_test_stream = None
		self.mic_test_audio = None
		self.mic_test_peak = 0.0
		self.mic_test_error = None
		self.mic_test_lock = threading.Lock()
		self.mic_test_hold_active = False
		self.mic_test_started = None
		self.mic_test_elapsed = 0.0
		self.converter_process = None
		self.training_process = None

		self.converter_path = tk.StringVar(value=self.settings.get("converter_path", ""))
		self.converter_url = tk.StringVar(
			value=self.settings.get("converter_url", "http://127.0.0.1:18888")
		)
		self.training_python = tk.StringVar(value=self.settings.get("training_python", ""))
		self.training_folder = tk.StringVar(value=self.settings.get("training_folder", ""))
		self.training_url = tk.StringVar(
			value=self.settings.get("training_url", "http://127.0.0.1:7865")
		)
		self.local_training_confirmed = tk.BooleanVar(value=False)

		style = ttk.Style(root)
		style.theme_use("clam")
		style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"))
		style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"))
		style.configure("TButton", padding=(9, 6))
		self.apply_theme()

		header = ttk.Frame(root, padding=(22, 18, 22, 8))
		header.pack(fill="x")
		header_row = ttk.Frame(header)
		header_row.pack(fill="x")
		ttk.Label(header_row, text=f"{APP_NAME} V2", style="Title.TLabel").pack(side="left")
		ttk.Label(header_row, text="Theme").pack(side="right", padx=(0, 8))
		theme_picker = ttk.Combobox(
			header_row, textvariable=self.theme, values=tuple(PALETTES),
			state="readonly", width=9,
		)
		theme_picker.pack(side="right")
		theme_picker.bind("<<ComboboxSelected>>", self.change_theme)
		ttk.Label(
			header,
			text="Record or import voice clips, train a model, and use it with a local converter.",
		).pack(anchor="w", pady=(3, 0))

		self.tabs = ttk.Notebook(root)
		self.tabs.pack(fill="both", expand=True, padx=18, pady=(6, 16))
		self.voices_tab = ttk.Frame(self.tabs, padding=16)
		self.record_tab = ttk.Frame(self.tabs, padding=16)
		self.live_tab = ttk.Frame(self.tabs, padding=16)
		self.train_tab = ttk.Frame(self.tabs, padding=16)
		self.privacy_tab = ttk.Frame(self.tabs, padding=16)
		for tab, title in (
			(self.voices_tab, "My voices"),
			(self.record_tab, "Record & import"),
			(self.live_tab, "Live changer"),
			(self.train_tab, "Train a voice"),
			(self.privacy_tab, "Privacy & safety"),
		):
			self.tabs.add(tab, text=title)

		self.build_voices_tab()
		self.build_record_tab()
		self.build_live_tab()
		self.build_train_tab()
		self.build_privacy_tab()
		self.refresh_voices()
		self.root.after(250, self.poll_audio_levels)
		self.root.after(1000, self.poll_processes)
		self.root.protocol("WM_DELETE_WINDOW", self.close)

	def save_settings(self):
		if self.settings_readonly:
			return
		self.settings.update({
			"theme": self.theme.get(),
			"converter_path": self.converter_path.get().strip(),
			"converter_url": self.converter_url.get().strip(),
			"training_python": self.training_python.get().strip(),
			"training_folder": self.training_folder.get().strip(),
			"training_url": self.training_url.get().strip(),
		})
		try:
			path = settings_path()
			path.parent.mkdir(parents=True, exist_ok=True)
			with path.open("w", encoding="utf-8") as settings_file:
				json.dump(self.settings, settings_file, indent=2)
		except OSError as error:
			messagebox.showerror("Could not save settings", str(error), parent=self.root)

	def apply_theme(self):
		colors = PALETTES[self.theme.get()]
		style = ttk.Style(self.root)
		self.root.configure(background=colors["background"])
		style.configure(".", background=colors["background"], foreground=colors["text"])
		style.configure("TFrame", background=colors["background"])
		style.configure("TLabel", background=colors["background"], foreground=colors["text"])
		style.configure("Title.TLabel", background=colors["background"], foreground=colors["text"])
		style.configure("Section.TLabel", background=colors["background"], foreground=colors["accent"])
		style.configure(
			"TButton", background=colors["surface"], foreground=colors["text"],
			bordercolor=colors["border"], lightcolor=colors["surface"],
			darkcolor=colors["surface"], focuscolor=colors["accent"], padding=(9, 6),
		)
		style.map(
			"TButton",
			background=[("pressed", colors["accent"]), ("active", colors["accent_hover"])],
			foreground=[("pressed", "#ffffff"), ("active", "#ffffff"), ("disabled", colors["disabled"])],
		)
		style.configure(
			"TEntry", fieldbackground=colors["field"], foreground=colors["text"],
			insertcolor=colors["text"], bordercolor=colors["border"],
		)
		style.configure(
			"TCombobox", fieldbackground=colors["field"], background=colors["surface"],
			foreground=colors["text"], bordercolor=colors["border"], arrowcolor=colors["text"],
		)
		style.map(
			"TCombobox",
			fieldbackground=[("readonly", colors["field"])],
			foreground=[("readonly", colors["text"])],
			selectbackground=[("readonly", colors["field"])],
			selectforeground=[("readonly", colors["text"])],
		)
		style.configure(
			"TCheckbutton", background=colors["background"], foreground=colors["text"],
			focuscolor=colors["background"],
		)
		style.configure(
			"TNotebook", background=colors["background"], bordercolor=colors["border"],
			tabmargins=(2, 5, 2, 0),
		)
		style.configure(
			"TNotebook.Tab", background=colors["surface"], foreground=colors["muted"],
			padding=(12, 7),
		)
		style.map(
			"TNotebook.Tab",
			background=[("selected", colors["accent"]), ("active", colors["selection"])],
			foreground=[("selected", "#ffffff"), ("active", colors["text"])],
		)
		style.configure(
			"Treeview", background=colors["field"], fieldbackground=colors["field"],
			foreground=colors["text"], bordercolor=colors["border"], rowheight=28,
		)
		style.configure(
			"Treeview.Heading", background=colors["surface"], foreground=colors["text"],
			bordercolor=colors["border"],
		)
		style.map(
			"Treeview", background=[("selected", colors["accent"])],
			foreground=[("selected", "#ffffff")],
		)
		style.configure("Horizontal.TSeparator", background=colors["border"])
		style.configure(
			"Horizontal.TProgressbar", troughcolor=colors["field"],
			background=colors["accent"], bordercolor=colors["border"],
		)

	def change_theme(self, _event=None):
		self.apply_theme()
		self.save_settings()

	def build_voices_tab(self):
		tab = self.voices_tab
		ttk.Label(tab, text="Voice model library", style="Section.TLabel").pack(anchor="w")
		ttk.Label(
			tab,
			text="Import a trained, compatible voice model. Recordings and audio clips are "
			"training material, not voice models; train them using the RVC WebUI first.",
			wraplength=680,
		).pack(anchor="w", pady=(5, 12))
		self.voice_list = ttk.Treeview(
			tab, columns=("model", "index"), show="headings", height=13, selectmode="browse",
		)
		self.voice_list.heading("model", text="Voice model")
		self.voice_list.heading("index", text="RVC index (optional)")
		self.voice_list.column("model", width=320)
		self.voice_list.column("index", width=260)
		self.voice_list.pack(fill="both", expand=True)
		buttons = ttk.Frame(tab)
		buttons.pack(fill="x", pady=(12, 0))
		ttk.Button(buttons, text="Import model...", command=self.import_model).pack(side="left")
		ttk.Button(buttons, text="Open model folder", command=self.open_selected_voice).pack(
			side="left", padx=8,
		)
		ttk.Button(buttons, text="Remove from list", command=self.remove_voice).pack(side="right")

	def build_record_tab(self):
		tab = self.record_tab
		ttk.Label(tab, text="Record or import voice clips", style="Section.TLabel").pack(anchor="w")
		ttk.Label(
			tab,
			text="Make a local dataset from your own voice, or audio you have permission to "
			"use. This does not automatically create a model: train the saved clips in RVC "
			"before importing its exported .pth model on the My voices tab.",
			wraplength=680,
		).pack(anchor="w", pady=(5, 12))

		name_row = ttk.Frame(tab)
		name_row.pack(fill="x", pady=5)
		ttk.Label(name_row, text="Dataset name", width=22).pack(side="left", anchor="w")
		self.dataset_name = tk.StringVar(value="My voice")
		ttk.Entry(name_row, textvariable=self.dataset_name).pack(side="left", fill="x", expand=True)

		device_row = ttk.Frame(tab)
		device_row.pack(fill="x", pady=5)
		ttk.Label(device_row, text="Microphone input", width=22).pack(side="left", anchor="w")
		self.recording_device = ttk.Combobox(device_row, state="readonly")
		self.recording_device.pack(side="left", fill="x", expand=True)
		self.recording_device.bind("<<ComboboxSelected>>", self.on_device_selected)
		ttk.Button(device_row, text="Refresh", command=self.refresh_devices).pack(side="left", padx=6)

		rate_row = ttk.Frame(tab)
		rate_row.pack(fill="x", pady=5)
		ttk.Label(rate_row, text="Recording sample rate", width=22).pack(side="left", anchor="w")
		self.recording_rate = tk.StringVar(value="Device default")
		ttk.Combobox(
			rate_row, textvariable=self.recording_rate, state="readonly",
			values=("Device default", "48000", "44100", "32000", "22050", "16000"), width=16,
		).pack(side="left")
		ttk.Label(rate_row, text="Hz, mono WAV").pack(side="left", padx=8)

		buttons = ttk.Frame(tab)
		buttons.pack(fill="x", pady=(12, 6))
		self.test_button = ttk.Button(buttons, text="Hold to test")
		self.test_button.pack(side="left")
		self.test_button.bind("<ButtonPress-1>", self.test_microphone)
		self.root.bind_all("<ButtonRelease-1>", self.release_microphone_test, add="+")
		self.start_button = ttk.Button(
			buttons, text="Start recording", command=self.start_recording,
		)
		self.start_button.pack(side="left", padx=8)
		self.stop_button = ttk.Button(
			buttons, text="Stop & save", command=self.stop_recording, state="disabled",
		)
		self.stop_button.pack(side="left")

		self.record_status = ttk.Label(tab, text="Choose a microphone, then test it.", wraplength=680)
		self.record_status.pack(anchor="w", pady=(4, 7))
		self.mic_level = tk.DoubleVar(value=0)
		ttk.Progressbar(tab, variable=self.mic_level, maximum=100).pack(fill="x", pady=(0, 7))
		ttk.Button(
			tab, text="Open Windows microphone privacy settings",
			command=self.open_microphone_settings,
		).pack(anchor="w", pady=(0, 7))

		ttk.Separator(tab).pack(fill="x", pady=9)
		ttk.Label(tab, text="Import existing audio clips", style="Section.TLabel").pack(anchor="w")
		ttk.Label(
			tab,
			text="Supported: WAV, FLAC, MP3, M4A, and OGG. Clips are copied into "
			"Documents\\LocalVoiceStudio\\datasets under your dataset name.",
			wraplength=680,
		).pack(anchor="w", pady=(4, 8))
		import_row = ttk.Frame(tab)
		import_row.pack(fill="x")
		ttk.Button(import_row, text="Import audio files...", command=self.import_audio).pack(side="left")
		ttk.Button(import_row, text="Open dataset folder", command=self.open_dataset_folder).pack(
			side="left", padx=8,
		)
		self.refresh_devices()

	def build_live_tab(self):
		tab = self.live_tab
		ttk.Label(tab, text="Live voice conversion", style="Section.TLabel").pack(anchor="w")
		ttk.Label(
			tab,
			text="A compatible local converter is required for live voice changing. In its "
			"interface, choose an imported model and set microphone/output devices.",
			wraplength=680,
		).pack(anchor="w", pady=(5, 12))
		self.path_row(tab, "Converter executable", self.converter_path, self.browse_converter)
		self.path_row(tab, "Local converter page", self.converter_url, None)
		ttk.Button(tab, text="Save settings", command=self.save_settings).pack(anchor="e", pady=8)
		ttk.Button(tab, text="Launch live converter", command=self.launch_converter).pack(
			fill="x", pady=4,
		)
		self.converter_status = ttk.Label(tab, text="Converter is not running.", wraplength=680)
		self.converter_status.pack(anchor="w", pady=4)
		ttk.Button(
			tab, text="Get the live converter",
			command=lambda: webbrowser.open(LIVE_ENGINE_URL),
		).pack(anchor="w", pady=(10, 0))

	def build_train_tab(self):
		tab = self.train_tab
		ttk.Label(tab, text="Train a model from your dataset", style="Section.TLabel").pack(anchor="w")
		ttk.Label(
			tab,
			text="Use a dataset made from a voice you own or have explicit permission to use. "
			"Select the dataset in RVC, prepare the clips, train, and export a .pth model. "
			"Training can take a long time and works best with a supported GPU.",
			wraplength=680,
		).pack(anchor="w", pady=(5, 12))
		self.path_row(tab, "Python executable", self.training_python, self.browse_python)
		self.path_row(tab, "RVC project folder", self.training_folder, self.browse_training_folder)
		self.path_row(tab, "Local RVC page", self.training_url, None)
		ttk.Checkbutton(
			tab,
			text="I checked that the RVC WebUI is bound to localhost only (not 0.0.0.0).",
			variable=self.local_training_confirmed,
		).pack(anchor="w", pady=(12, 6))
		ttk.Label(
			tab,
			text="The app blocks the current RVC WebUI default that listens on every network interface.",
			wraplength=680,
		).pack(anchor="w")
		ttk.Button(tab, text="Launch local RVC training UI", command=self.launch_training).pack(
			fill="x", pady=5,
		)
		self.training_status = ttk.Label(tab, text="Training UI is not running.", wraplength=680)
		self.training_status.pack(anchor="w", pady=4)
		ttk.Button(
			tab, text="Get RVC training tools",
			command=lambda: webbrowser.open(TRAINING_PROJECT_URL),
		).pack(anchor="w", pady=(10, 0))

	def build_privacy_tab(self):
		tab = self.privacy_tab
		ttk.Label(tab, text="Privacy & responsible use", style="Section.TLabel").pack(anchor="w")
		notes = (
			("Local files", "Recordings and imported clips are copied to your local Documents "
			 "folder. The settings file stores voice-model paths, not model contents."),
			("Protect your voice", "Keep recordings and models in a private Windows account, "
			 "use device encryption, and do not share model files. Anyone who can access a "
			 "working model may copy or misuse it; no app can guarantee it cannot be extracted."),
			("Permission", "Only record or train on voices you own or have permission to use. "
			 "Do not use a converted voice to impersonate someone or mislead people."),
			("Local-only web UIs", "Use localhost URLs and keep converter/training web pages off "
			 "the internet and shared networks."),
		)
		for heading, body in notes:
			ttk.Label(tab, text=heading, style="Section.TLabel").pack(anchor="w", pady=(10, 2))
			ttk.Label(tab, text=body, wraplength=680, justify="left").pack(anchor="w")

	def path_row(self, parent, label, variable, browse_command):
		row = ttk.Frame(parent)
		row.pack(fill="x", pady=6)
		ttk.Label(row, text=label, width=22).pack(side="left", anchor="w")
		ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True)
		if browse_command:
			ttk.Button(row, text="Browse...", command=browse_command).pack(side="left", padx=(6, 0))

	def browse_converter(self):
		path = filedialog.askopenfilename(
			parent=self.root, title="Select the live converter executable",
			filetypes=(("Application", "*.exe"), ("All files", "*.*")),
		)
		if path:
			self.converter_path.set(path)
			self.save_settings()

	def browse_python(self):
		path = filedialog.askopenfilename(
			parent=self.root, title="Select python.exe",
			filetypes=(("Python", "python.exe"), ("Applications", "*.exe"), ("All files", "*.*")),
		)
		if path:
			self.training_python.set(path)
			self.save_settings()

	def browse_training_folder(self):
		path = filedialog.askdirectory(parent=self.root, title="Select the RVC project folder")
		if path:
			self.training_folder.set(path)
			self.save_settings()

	def audio_library(self, show_error=True):
		try:
			import sounddevice
		except (ImportError, OSError) as error:
			message = (
				"Microphone recording needs the sounddevice package. "
				"Install it by running:\n\npython -m pip install -r requirements.txt"
			)
			if isinstance(error, OSError):
				message += f"\n\nThe audio driver could not be loaded: {error}"
			if show_error:
				messagebox.showerror("Recording support is not installed", message, parent=self.root)
			return None
		return sounddevice

	def refresh_devices(self):
		audio = self.audio_library(show_error=False)
		if audio is None:
			self.recording_device.configure(values=())
			self.record_status.configure(
				text="Install recording support: python -m pip install -r requirements.txt"
			)
			return
		try:
			devices = audio.query_devices()
			host_apis = audio.query_hostapis()
		except audio.PortAudioError as error:
			self.input_devices = []
			self.recording_device.configure(values=())
			self.recording_device.set("")
			self.record_status.configure(text=f"Could not list audio devices: {error}")
			return

		self.input_devices = []
		for index, device in enumerate(devices):
			if device["max_input_channels"] < 1:
				continue
			host_name = host_apis[device["hostapi"]]["name"]
			self.input_devices.append({
				"index": index,
				"name": device["name"],
				"host": host_name,
				"rate": int(device["default_samplerate"]),
			})
		labels = [
			f"{device['name']} — {device['host']} (input {device['index']})"
			for device in self.input_devices
		]
		self.recording_device.configure(values=labels)
		if not labels:
			self.recording_device.set("")
			self.record_status.configure(
				text="No microphone input was found. Check Windows Settings > System > Sound > Input."
			)
			return

		default_index = audio.default.device[0]
		selected = next(
			(position for position, device in enumerate(self.input_devices)
			 if device["index"] == default_index),
			0,
		)
		self.recording_device.current(selected)
		self.on_device_selected()

	def selected_device(self):
		position = self.recording_device.current()
		if not 0 <= position < len(self.input_devices):
			raise ValueError("Select a microphone from the dropdown, then press Refresh if it is missing.")
		return self.input_devices[position]

	def on_device_selected(self, _event=None):
		try:
			device = self.selected_device()
		except ValueError as error:
			self.record_status.configure(text=str(error))
			return
		self.record_status.configure(
			text=f"Selected {device['name']} via {device['host']} "
			f"(input {device['index']}, {device['rate']} Hz). "
			"Press and hold Hold to test while speaking; release to see the result."
		)

	def open_microphone_settings(self):
		try:
			os.startfile("ms-settings:privacy-microphone")
		except OSError as error:
			messagebox.showerror(
				"Could not open Windows settings",
				f"Go to Settings > Privacy & security > Microphone.\n\n{error}",
				parent=self.root,
			)

	def dataset_folder(self):
		name = re.sub(r"[^\w -]", "", self.dataset_name.get(), flags=re.UNICODE).strip(" .-_")
		if not name:
			raise ValueError("Enter a dataset name using letters or numbers.")
		self.dataset_name.set(name)
		documents = Path.home() / "Documents"
		if not documents.is_dir():
			documents = Path.home() / "OneDrive" / "Documents"
		folder = documents / "LocalVoiceStudio" / "datasets" / name
		folder.mkdir(parents=True, exist_ok=True)
		return folder

	def unique_destination(self, folder, source_path):
		destination = folder / source_path.name
		counter = 2
		while destination.exists():
			destination = folder / f"{source_path.stem}_{counter}{source_path.suffix}"
			counter += 1
		return destination

	def import_audio(self):
		paths = filedialog.askopenfilenames(
			parent=self.root,
			title="Select audio clips to copy into this voice dataset",
			filetypes=(("Audio files", "*.wav *.flac *.mp3 *.m4a *.ogg"), ("All files", "*.*")),
		)
		if not paths:
			return
		if any(Path(path).suffix.casefold() not in AUDIO_EXTENSIONS for path in paths):
			messagebox.showerror(
				"Unsupported format", "Choose WAV, FLAC, MP3, M4A, or OGG files.", parent=self.root,
			)
			return
		try:
			folder = self.dataset_folder()
			for source in paths:
				shutil.copy2(source, self.unique_destination(folder, Path(source)))
		except (OSError, ValueError) as error:
			messagebox.showerror("Could not import audio", str(error), parent=self.root)
			return
		self.record_status.configure(
			text=f"Imported {len(paths)} audio clip(s) locally into {folder}"
		)

	def open_dataset_folder(self):
		try:
			os.startfile(str(self.dataset_folder()))
		except (OSError, ValueError) as error:
			messagebox.showerror("Could not open dataset folder", str(error), parent=self.root)

	def microphone_stream_options(self, device, audio):
		if device["host"] == "Windows WASAPI":
			return {
				"device": device["index"],
				"extra_settings": audio.WasapiSettings(exclusive=False),
			}
		return {"device": device["index"]}

	def test_microphone(self, _event=None):
		if self.mic_test_stream is not None or self.recording_stream is not None:
			return
		audio = self.audio_library()
		if audio is None:
			return
		try:
			device = self.selected_device()
			options = self.microphone_stream_options(device, audio)
			rate = device["rate"]
			audio.check_input_settings(
				device=device["index"], channels=1, dtype="float32", samplerate=rate,
				extra_settings=options.get("extra_settings"),
			)
		except (ValueError, audio.PortAudioError) as error:
			self.record_status.configure(text=f"Cannot open microphone: {error}")
			messagebox.showerror(
				"Could not test microphone",
				f"{error}\n\nCheck Windows microphone access, select the correct input, and "
				"close other apps using it. Try another device shown for a different audio backend.",
				parent=self.root,
			)
			return

		self.mic_test_audio = audio
		self.mic_test_peak = 0.0
		self.mic_test_rms = 0.0
		self.mic_test_error = None
		self.mic_test_lock = threading.Lock()
		self.mic_test_started = monotonic()
		self.mic_test_hold_active = True

		def capture(indata, _frames, _time_info, status):
			peak = float(abs(indata).max())
			rms = float((indata * indata).mean() ** 0.5)
			with self.mic_test_lock:
				self.mic_test_peak = max(self.mic_test_peak, peak)
				self.mic_test_rms = max(self.mic_test_rms, rms)
				if status:
					self.mic_test_error = str(status)

		try:
			self.mic_test_stream = audio.InputStream(
				**options, channels=1, dtype="float32", samplerate=rate, callback=capture,
			)
			self.mic_test_stream.start()
		except audio.PortAudioError as error:
			self.mic_test_stream = None
			self.mic_test_hold_active = False
			self.record_status.configure(text=f"Could not start microphone test: {error}")
			messagebox.showerror("Microphone test failed", str(error), parent=self.root)
			return
		self.test_button.configure(text="Release to finish")
		self.record_status.configure(
			text=f"Testing {device['name']}... Keep holding the button and speak. Release to finish."
		)
		self.mic_level.set(0)

	def release_microphone_test(self, _event=None):
		if self.mic_test_hold_active:
			self.mic_test_hold_active = False
			self.finish_microphone_test()

	def finish_microphone_test(self):
		stream = self.mic_test_stream
		if stream is None:
			if self.mic_test_started is not None and not self.mic_test_hold_active:
				self.test_button.configure(text="Hold to test")
				self.mic_test_started = None
			return
		self.mic_test_hold_active = False
		try:
			stream.stop()
			stream.close()
		except self.mic_test_audio.PortAudioError as error:
			self.mic_test_stream = None
			self.test_button.configure(text="Hold to test")
			self.mic_test_started = None
			self.record_status.configure(text=f"Microphone test could not close: {error}")
			messagebox.showerror("Microphone test error", str(error), parent=self.root)
			return
		self.mic_test_stream = None
		self.test_button.configure(text="Hold to test")
		with self.mic_test_lock:
			peak, rms, status = self.mic_test_peak, self.mic_test_rms, self.mic_test_error
		elapsed = monotonic() - self.mic_test_started if self.mic_test_started is not None else 0
		self.mic_test_started = None
		self.mic_level.set(min(100, peak * 100))
		if elapsed < 1.0:
			detail = "Test was too short. Hold the button for at least 2 seconds while speaking."
			self.record_status.configure(text=detail)
			messagebox.showinfo("Hold to test", detail, parent=self.root)
			return
		if peak < 0.003 and rms < 0.001:
			detail = "Windows opened this device but it supplied silence."
			if status:
				detail += f" Audio status: {status}"
			self.record_status.configure(text=detail)
			messagebox.showwarning(
				"No microphone signal",
				f"{detail}\n\nCheck Windows Settings > System > Sound > Input. "
				"Make sure the input meter moves there. If it does, press Refresh and try "
				"the same microphone under another audio backend.",
				parent=self.root,
			)
			return
		self.record_status.configure(
			text=f"Microphone works. Peak {peak:.1%}; average {rms:.2%}. Ready to record."
		)
		messagebox.showinfo(
			"Microphone is working",
			f"Audio was received from {self.selected_device()['name']}.\n"
			f"Peak level: {peak:.1%}\nAverage level: {rms:.2%}",
			parent=self.root,
		)

	def poll_audio_levels(self):
		if self.mic_test_stream is not None:
			with self.mic_test_lock:
				peak = self.mic_test_peak
			self.mic_level.set(min(100, peak * 100))
		elif self.recording_stream is not None:
			with self.recording_lock:
				peak = self.recording_peak
			self.mic_level.set(min(100, peak * 100))
		self.root.after(100, self.poll_audio_levels)

	def start_recording(self):
		if self.recording_stream is not None or self.mic_test_stream is not None:
			return
		audio = self.audio_library()
		if audio is None:
			return
		try:
			device = self.selected_device()
			options = self.microphone_stream_options(device, audio)
			if self.recording_rate.get() == "Device default":
				sample_rates = [device["rate"]]
			else:
				requested = int(self.recording_rate.get())
				sample_rates = [requested, device["rate"]]
		except (ValueError, audio.PortAudioError) as error:
			messagebox.showerror("Cannot use microphone", str(error), parent=self.root)
			return

		sample_rate = None
		last_error = None
		for candidate in dict.fromkeys(sample_rates):
			try:
				audio.check_input_settings(
					device=device["index"], channels=1, dtype="int16",
					samplerate=candidate, extra_settings=options.get("extra_settings"),
				)
			except audio.PortAudioError as error:
				last_error = error
				continue
			sample_rate = candidate
			break
		if sample_rate is None:
			messagebox.showerror(
				"Unsupported microphone format",
				f"{last_error}\n\nTry Device default or another microphone.",
				parent=self.root,
			)
			return

		try:
			folder = self.dataset_folder()
		except (OSError, ValueError) as error:
			messagebox.showerror("Could not prepare dataset folder", str(error), parent=self.root)
			return
		path = folder / f"recording_{datetime.now():%Y%m%d_%H%M%S}.wav"
		if path.exists():
			messagebox.showerror("Recording already exists", "Wait a second and try again.", parent=self.root)
			return

		self.recording_queue = queue.Queue(maxsize=256)
		self.recording_path = path
		self.recording_error = None
		self.recording_write_error = None
		self.recording_peak = 0.0
		self.recording_frames = [0]
		self.recording_lock = threading.Lock()
		stream_queue = self.recording_queue
		frames_written = self.recording_frames

		def writer():
			error = None
			try:
				with wave.open(str(path), "wb") as output:
					output.setnchannels(1)
					output.setsampwidth(2)
					output.setframerate(sample_rate)
					while True:
						data = stream_queue.get()
						if data is None:
							break
						output.writeframesraw(data)
				if frames_written[0] == 0:
					error = "No audio frames were captured. Check that the selected microphone is unmuted."
					path.unlink(missing_ok=True)
			except (OSError, wave.Error) as write_error:
				error = str(write_error)
			self.recording_write_error = error

		self.recording_thread = threading.Thread(target=writer, daemon=True)
		self.recording_thread.start()
		self.start_button.configure(state="disabled")

		def capture(indata, frames, _time_info, status):
			peak = max(abs(value) for value in indata)
			with self.recording_lock:
				self.recording_peak = max(self.recording_peak, peak / 32768)
			if status:
				self.recording_error = str(status)
			frames_written[0] += frames
			try:
				stream_queue.put_nowait(indata.tobytes())
			except queue.Full:
				self.recording_error = "The write buffer filled up; stop and save this recording."
				raise audio.CallbackAbort

		try:
			self.recording_stream = audio.InputStream(
				**options, channels=1, dtype="int16", samplerate=sample_rate,
				callback=capture,
			)
			self.recording_stream.start()
		except (audio.PortAudioError, ValueError) as error:
			self.recording_stream = None
			self.recording_audio = None
			self.recording_status.configure(text=f"Could not start recording: {error}")
			self.enqueue_recording_end(stream_queue)
			self.root.after(100, self.poll_recording_writer)
			return

		self.recording_audio = audio
		self.recording_started = monotonic()
		self.stop_button.configure(state="normal")
		self.record_status.configure(
			text=f"Recording {device['name']} at {sample_rate} Hz... Release the button or click Stop & save."
		)

	def enqueue_recording_end(self, stream_queue):
		try:
			stream_queue.put_nowait(None)
		except queue.Full:
			self.root.after(50, lambda: self.enqueue_recording_end(stream_queue))

	def stop_recording(self):
		if self.recording_stream is None:
			return
		stream, audio = self.recording_stream, self.recording_audio
		self.recording_stream = None
		try:
			stream.stop()
			stream.close()
		except audio.PortAudioError as error:
			self.recording_error = f"Microphone stopped with an audio error: {error}"
		self.recording_audio = None
		self.recording_started = None
		self.start_button.configure(state="normal")
		self.stop_button.configure(state="disabled")
		self.record_status.configure(text="Saving recording...")
		self.enqueue_recording_end(self.recording_queue)
		self.root.after(100, self.poll_recording_writer)

	def poll_recording_writer(self):
		if self.recording_thread is not None and self.recording_thread.is_alive():
			self.root.after(100, self.poll_recording_writer)
			return
		self.start_button.configure(state="normal")
		if self.recording_write_error:
			self.record_status.configure(text=f"Recording not saved: {self.recording_write_error}")
			messagebox.showerror("Recording failed", self.recording_write_error, parent=self.root)
			return
		detail = f"Saved recording: {self.recording_path}"
		if self.recording_error:
			detail += f" (audio warning: {self.recording_error})"
		self.record_status.configure(text=detail)
		self.root.after(100, self.poll_audio_levels)

	def import_audio(self):
		paths = filedialog.askopenfilenames(
			parent=self.root, title="Select audio clips for this voice dataset",
			filetypes=(("Audio files", "*.wav *.flac *.mp3 *.m4a *.ogg"), ("All files", "*.*")),
		)
		if not paths:
			return
		if any(Path(path).suffix.casefold() not in AUDIO_EXTENSIONS for path in paths):
			messagebox.showerror(
				"Unsupported format", "Choose WAV, FLAC, MP3, M4A, or OGG audio files.",
				parent=self.root,
			)
			return
		try:
			folder = self.dataset_folder()
			for source in paths:
				shutil.copy2(source, self.unique_destination(folder, Path(source)))
		except (OSError, ValueError) as error:
			messagebox.showerror("Could not import audio", str(error), parent=self.root)
			return
		self.record_status.configure(text=f"Imported {len(paths)} clips into {folder}")

	def import_model(self):
		path = filedialog.askopenfilename(
			parent=self.root, title="Select a compatible trained voice model",
			filetypes=(("Voice models", "*.pth *.onnx"), ("All files", "*.*")),
		)
		if not path:
			return
		index_path = ""
		if Path(path).suffix.casefold() == ".pth":
			index_path = filedialog.askopenfilename(
				parent=self.root, title="Optional RVC index (Cancel to skip)",
				filetypes=(("RVC index", "*.index"), ("All files", "*.*")),
			)
		if any(voice.get("model") == path for voice in self.settings.get("voices", [])):
			messagebox.showinfo("Already imported", "This model is already in your library.", parent=self.root)
			return
		self.settings.setdefault("voices", []).append({
			"name": Path(path).stem, "model": path, "index": index_path,
		})
		self.save_settings()
		self.refresh_voices()

	def refresh_voices(self):
		for item in self.voice_list.get_children():
			self.voice_list.delete(item)
		for position, voice in enumerate(self.settings.get("voices", [])):
			index_path = voice.get("index", "")
			self.voice_list.insert(
				"", "end", iid=str(position),
				values=(
					voice.get("name", "Voice"),
					Path(index_path).name if index_path else "—",
				),
			)

	def selected_voice(self):
		selection = self.voice_list.selection()
		if not selection:
			messagebox.showinfo("Select a voice", "Choose a model first.", parent=self.root)
			return None
		return self.settings["voices"][int(selection[0])]

	def open_selected_voice(self):
		voice = self.selected_voice()
		if voice is None:
			return
		model_path = Path(voice.get("model", ""))
		if not model_path.is_file():
			messagebox.showerror("Model not found", f"Could not find:\n{model_path}", parent=self.root)
			return
		os.startfile(str(model_path.parent))

	def remove_voice(self):
		selection = self.voice_list.selection()
		if not selection:
			messagebox.showinfo("Select a voice", "Choose a voice to remove.", parent=self.root)
			return
		del self.settings["voices"][int(selection[0])]
		self.save_settings()
		self.refresh_voices()

	def local_url(self, value):
		parsed = urlparse(value.strip())
		if parsed.scheme != "http" or parsed.hostname not in LOCAL_HOSTS:
			raise ValueError("Use a local URL such as http://127.0.0.1:18888.")
		return value.strip()

	def launch_converter(self):
		executable = Path(self.converter_path.get().strip())
		if not executable.is_file():
			messagebox.showerror("Converter not found", "Choose the live converter .exe first.", parent=self.root)
			return
		try:
			url = self.local_url(self.converter_url.get())
			self.save_settings()
			self.converter_process = subprocess.Popen([str(executable)], cwd=str(executable.parent))
			webbrowser.open(url)
		except (OSError, ValueError) as error:
			messagebox.showerror("Could not launch converter", str(error), parent=self.root)
			return
		self.converter_status.configure(text="Started. Select your model and audio devices in its page.")

	def launch_training(self):
		python = Path(self.training_python.get().strip())
		project = Path(self.training_folder.get().strip())
		script = next((path for path in (project / "webui.py", project / "infer-web.py") if path.is_file()), None)
		if not self.local_training_confirmed.get():
			messagebox.showwarning(
				"Local access required",
				"Confirm that the RVC WebUI is restricted to localhost before starting it.",
				parent=self.root,
			)
			return
		if not python.is_file():
			messagebox.showerror("Python not found", "Select the Python executable for your RVC setup.", parent=self.root)
			return
		if script is None:
			messagebox.showerror(
				"RVC script not found", f"Could not find webui.py or infer-web.py in:\n{project}",
				parent=self.root,
			)
			return
		try:
			source = script.read_text(encoding="utf-8")
		except (OSError, UnicodeError) as error:
			messagebox.showerror("Could not inspect RVC settings", str(error), parent=self.root)
			return
		if not re.search(r"""server_name\s*=\s*["']0\.0\.0\.0["']""", source):
			messagebox.showerror(
				"RVC is not local-only",
				f"{script.name} listens on every network interface. Change "
				'server_name="0.0.0.0" to server_name="127.0.0.1", then try again.',
				parent=self.root,
			)
			return
		try:
			url = self.local_url(self.training_url.get())
			self.save_settings()
			command = [str(python), str(script)]
			if script.name == "webui.py":
				command.append("--noautoopen")
			self.training_process = subprocess.Popen(
				command, cwd=str(project),
				creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
			)
			self.root.after(5000, lambda: webbrowser.open(url))
		except (OSError, ValueError) as error:
			messagebox.showerror("Could not launch RVC", str(error), parent=self.root)
			return
		self.training_status.configure(text="Started RVC. Check its console window for startup output.")

	def poll_processes(self):
		for process, label, status in (
			(self.converter_process, "Converter", getattr(self, "converter_status", None)),
			(self.training_process, "RVC training UI", getattr(self, "training_status", None)),
		):
			if process is not None and process.poll() is not None and status is not None:
				status.configure(text=f"{label} stopped (exit code {process.returncode}).")
		self.root.after(1000, self.poll_processes)

	def close(self):
		if self.mic_test_stream is not None:
			try:
				self.mic_test_stream.stop()
				self.mic_test_stream.close()
			except self.mic_test_audio.PortAudioError:
				pass
			self.mic_test_stream = None
		if self.recording_stream is not None:
			self.stop_recording()
		if self.recording_thread is not None and self.recording_thread.is_alive():
			self.root.after(100, self.close)
			return
		self.save_settings()
		self.root.destroy()


if __name__ == "__main__":
	window = tk.Tk()
	VoiceStudio(window)
	window.mainloop()
