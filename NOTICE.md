# Third-party material

Everything in this repository is our own work under `LICENSE` (all rights reserved), except the items below, which keep their own licences.

| What | Where | Licence |
|---|---|---|
| Inter 4.1 typeface (Rasmus Andersson) | `firmware/tools/fonts/` (rendered into `firmware/mic_display/fonts.h`) | SIL Open Font License 1.1, `firmware/tools/fonts/OFL.txt` |
| Print profile values flattened from Prusa Research's PrusaSlicer vendor bundle (Original Prusa MK4S HF0.4, 0.20mm SPEED, Prusament PETG) | `cad/slicing/mk4s_hf04_petg_SPEED.ini` | PrusaSlicer's licence (AGPL-3.0) |

Used but not included (installed by the setup scripts from their own sources, under their own licences): Arduino ESP32 core, Waveshare's GFX Library for Arduino and SensorLib copies, CadQuery and OCP, PrusaSlicer, Python packages listed in `env/`, three.js. Waveshare's board model and Eino's arm CAD are not in the repository.

Reference only (no code copied): the Windows default-device switch in `pcapp/core_audio.py` follows the public IPolicyConfig interface as documented by EarTrumpet (MIT), credited in the file.
