# Seshat Sticky Note 📝

A minimalist desktop task widget built with Python + PyQt6, featuring "Ghost Mode" and smart progress tracking.

## 🔥 Features

* **Ghost Mode:** Semi-transparent window that allows clicks to pass through.
* **Hierarchy:** Infinite task nesting.
* **Smart Progress:**
    * Cancelled tasks are excluded from statistics.
    * **RGB Mode:** Rainbow effect upon 100% completion.
* **History:** Undo/Redo (Ctrl+Z / Ctrl+Y).
* **Soft Delete:** Ability to "strike through" a task without deleting it.
* **Localization:** 20+ languages (EN, RU, KK, KY, UZ, TR, etc.).
* **Timings:** The header displays the exact start and finish dates of the list (`dd.MM.yyyy HH:mm`).

## 🚀 Getting Started

1.  Install dependencies using uv:
    ```bash
    uv sync
    ```

2.  Run the application:
    ```bash
    uv run main.py
    ```

## ⌨️ Hotkeys

| Key | Action |
| :--- | :--- |
| **Ctrl + N** | New Task |
| **Delete** | Delete Task |
| **Ctrl + Arrows** | Move / Nest Tasks |
| **Ctrl + Z / Y** | Undo / Redo |
| **Mouse Wheel** | Transparency (in Lock Mode 🔒) |

## 📂 Files

* `main.py` — Entry point.
* `app.py` — Controller.
* `data_manager.py` — Database (`seshat_db.json`).
* ... (other modules)

---
*Data is saved in `seshat_db.json`.*