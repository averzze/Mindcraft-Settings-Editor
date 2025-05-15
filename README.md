# Mindcraft Settings Editor

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/Qt-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A user-friendly desktop application for editing `settings.js` files for the [MindCraft AI agent](https://github.com/kolbytn/mindcraft) for Minecraft.

<!-- Optional: Add a screenshot or GIF of the application in action here -->
<!-- <p align="center">
  <img src="path/to/your/screenshot.png" alt="Mindcraft Settings Editor Screenshot" width="700"/>
</p> -->

## Features

*   **Automatic Scanning:** Scans common locations for MindCraft installations to quickly find your `settings.js` file.
*   **User-Friendly Interface:** Provides an intuitive GUI to view and modify settings, replacing manual JSON/JavaScript editing.
*   **Categorized Settings:** Organizes settings into logical groups for easier navigation (Connection, Agent Configuration, Features, etc.).
*   **Type-Aware Inputs:** Uses appropriate input fields for different setting types (checkboxes for booleans, dropdowns for predefined choices like `auth` or `language`, text fields for strings/numbers/lists).
*   **Dark/Light Mode:** Automatically detects your system's theme and applies a corresponding dark or light mode to the editor. Manual theme switching is also available.
*   **Tooltips:** Provides descriptions for each setting on hover to explain its purpose.
*   **Enhanced List Management:**
    *   **Profiles:** Manages the list of active profiles and allows adding new profiles from a list of commented-out profiles found in `settings.js` or by typing a new one.
    *   **Player Lists (e.g., `only_chat_with`):** Easy add/remove interface for lists of strings.
*   **Safe Saving:** Edits are applied directly to your `settings.js` file, preserving existing environment variable override logic and other JavaScript code outside the main settings object.
*   **Cross-Platform (Potentially):** Built with Python and PyQt6, aiming for cross-platform compatibility (Windows, macOS, Linux).

## Why this Editor?

Manually editing the `settings.js` file for MindCraft can be error-prone, especially for users less familiar with JavaScript or JSON syntax. This editor aims to:

*   Reduce syntax errors.
*   Provide clarity on what each setting does.
*   Speed up the configuration process.
*   Make MindCraft more accessible to a wider range of users.

## Prerequisites

*   Python 3.8 or higher.
*   An existing [MindCraft installation](https://github.com/kolbytn/mindcraft) (this tool edits its `settings.js` file).

## Installation & Usage

### 1. From Source (Recommended for Developers)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/averzze/Mindcraft-Settings-Editor.git
    cd Mindcraft-Settings-Editor
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install PyQt6
    ```

4.  **Run the application:**
    ```bash
    python settings_editor.py
    ```
    Ensure `mindcraft_icon.ico` is in the same directory as `settings_editor.py` if running from source for the icon to appear.

### 2. Using Pre-built Executable (If Provided)

*   (TODO: Add instructions here if you plan to release pre-built executables, e.g., via GitHub Releases.)
*   Download the executable for your operating system from the [Releases page](https://github.com/averzze/Mindcraft-Settings-Editor/releases).
*   Run the downloaded file. No installation is typically required for a PyInstaller one-file bundle.

### Using the Editor

1.  **Launch the application.**
2.  The editor will attempt to **scan for MindCraft installations**.
    *   If multiple are found, you'll be prompted to select one.
    *   If none are found automatically, use the **"Browse..."** button to manually locate your `settings.js` file.
3.  Once a `settings.js` file is loaded, its settings will be displayed.
4.  Modify the settings as needed using the provided UI elements.
5.  Hover over setting labels to see a **tooltip** with a description.
6.  Click **"Save Settings"** to write your changes back to the `settings.js` file.
7.  Use the **"Reload"** button to discard any unsaved changes and reload the settings from the current file.
8.  Use the **"Switch to Light/Dark Mode"** button to toggle the application's theme.

## Building from Source (for Executable)

If you want to create a standalone executable:

1.  Follow steps 1-3 from "Installation & Usage (From Source)".
2.  Install PyInstaller:
    ```bash
    pip install pyinstaller
    ```
3.  Navigate to the project's root directory in your terminal.
4.  Ensure `mindcraft_icon.ico` is present in this directory.
5.  Run PyInstaller (example for Windows):
    ```bash
    pyinstaller --name "Mindcraft Settings Editor" --onefile --windowed --icon="mindcraft_icon.ico" settings_editor.py
    ```
    *   The executable will be found in the `dist` folder.

    *(Note: For macOS, you might need to use `--onedir` and create an app bundle for proper icon handling, or use tools like `py2app`.)*

## Known Isuues:
1. Light theme setting description not working (✅)
## Contributing

Contributions are welcome! If you'd like to contribute, please:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -am 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Create a new Pull Request.

Please ensure your code follows good practices and includes comments where necessary.

## Issues

If you encounter any bugs or have feature requests, please open an issue on the [GitHub Issues page](https://github.com/averzze/Mindcraft-Settings-Editor/issues).

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file (or [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)) for details.

## Acknowledgements

*   The [MindCraft project](https://github.com/kolbytn/mindcraft) by KolbyTN and contributors, for which this tool is built.
*   The PyQt6 team for the excellent Qt bindings.
