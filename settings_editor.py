import os
import sys
import json
import re
import logging
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QCheckBox,
                           QComboBox, QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
                           QDialog, QSpacerItem, QSizePolicy, QDialogButtonBox, QInputDialog)
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QRect, QAbstractAnimation
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('MindcraftSettingsEditor')

class ToolTip(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setWordWrap(True)
        self.setMaximumWidth(300)
        self.setContentsMargins(8, 8, 8, 8)
        self.setVisible(False)
        
        self.light_palette = QPalette()
        self.light_palette.setColor(QPalette.ColorRole.Window, QColor("#FFFFE0"))
        self.light_palette.setColor(QPalette.ColorRole.WindowText, QColor("#000000"))

        self.dark_palette = QPalette()
        self.dark_palette.setColor(QPalette.ColorRole.Window, QColor("#424242"))
        self.dark_palette.setColor(QPalette.ColorRole.WindowText, QColor("#F0F0F0"))
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        
    def set_theme(self, dark_mode):
        if dark_mode:
            self.setPalette(self.dark_palette)
            self.setStyleSheet("border: 1px solid #555555; border-radius: 3px;")
        else:
            self.setPalette(self.light_palette)
            self.setStyleSheet("border: 1px solid #D0D0D0; border-radius: 3px;")
        self.setAutoFillBackground(True)
        
    def show_tooltip(self, text, pos):
        self.setText(text)
        self.adjustSize()
        self.move(pos)
        self.show()
        self.timer.start(5000)
        
    def hide_tooltip(self):
        self.hide()
        self.timer.stop()

class ProfilesManagerWidget(QWidget):
    def __init__(self, current_profiles, available_profiles_from_comments, dark_mode):
        super().__init__()
        self.dark_mode = dark_mode
        self.current_profiles = list(current_profiles) 
        self.available_profiles_from_comments = list(available_profiles_from_comments)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)

        self.profiles_list_widget = QListWidget()
        self.profiles_list_widget.setToolTip("Currently active profiles. Double-click to remove.")
        self.profiles_list_widget.itemDoubleClicked.connect(self.remove_profile)
        self.populate_current_profiles()
        layout.addWidget(self.profiles_list_widget)

        buttons_layout = QHBoxLayout()
        self.add_profile_button = QPushButton("Add Profile...")
        self.add_profile_button.clicked.connect(self.show_add_profile_dialog)
        buttons_layout.addWidget(self.add_profile_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        self.update_theme(dark_mode)

    def populate_current_profiles(self):
        self.profiles_list_widget.clear()
        for profile in self.current_profiles:
            self.profiles_list_widget.addItem(QListWidgetItem(profile))

    def remove_profile(self, item):
        profile_to_remove = item.text()
        if profile_to_remove in self.current_profiles:
            self.current_profiles.remove(profile_to_remove)
            self.populate_current_profiles()
            if profile_to_remove not in self.available_profiles_from_comments:
                 if profile_to_remove not in getattr(MindcraftSettingsEditor, 'SETTINGS_PROFILES_FROM_COMMENTS_CACHE', []):
                    self.available_profiles_from_comments.append(profile_to_remove)
                    self.available_profiles_from_comments.sort()

    def show_add_profile_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Profile")
        dialog_layout = QVBoxLayout(dialog)

        label = QLabel("Select a profile to add or enter a new one:")
        dialog_layout.addWidget(label)

        combo_box = QComboBox()
        combo_box.setEditable(True) 
        combo_box.lineEdit().setPlaceholderText("Type new profile name or select")

        unique_available = sorted(list(set(self.available_profiles_from_comments) - set(self.current_profiles)))
        
        if unique_available:
            combo_box.addItems(unique_available)
        else:
            pass # Dropdown will be empty if no unique_available, lineEdit still active
            
        dialog_layout.addWidget(combo_box)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)
        
        self._apply_dialog_theme(dialog, self.dark_mode)

        if dialog.exec():
            selected_profile = combo_box.currentText().strip()
            if selected_profile and selected_profile not in self.current_profiles:
                self.current_profiles.append(selected_profile)
                self.populate_current_profiles()

    def _apply_dialog_theme(self, dialog, dark_mode):
        dialog_bg = "#2C2C2C" if dark_mode else "#F0F0F0"
        text_color = "#E0E0E0" if dark_mode else "#101010"
        input_bg = "#3C3C3C" if dark_mode else "#FFFFFF"
        input_border = "#555555" if dark_mode else "#B0B0B0"
        button_bg = "#4A4A4A" if dark_mode else "#DCDCDC"
        button_border = "#606060" if dark_mode else "#B0B0B0"
        button_hover_bg = "#5A5A5A" if dark_mode else "#CACACA"

        dialog.setStyleSheet(f"""
            QDialog {{ background-color: {dialog_bg}; }}
            QLabel {{ color: {text_color}; background-color: transparent; }}
            QComboBox {{ 
                background-color: {input_bg}; color: {text_color}; 
                border: 1px solid {input_border}; padding: 3px; border-radius: 3px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {input_bg}; color: {text_color}; border: 1px solid {input_border}; selection-background-color: #0078D7;
            }}
            QLineEdit {{
                 background-color: {input_bg}; color: {text_color}; 
                 border: 1px solid {input_border}; padding: 3px; border-radius: 3px;
            }}
            QPushButton {{ 
                background-color: {button_bg}; color: {text_color}; 
                border: 1px solid {button_border}; padding: 6px 12px; border-radius: 3px;
            }}
            QPushButton:hover {{ background-color: {button_hover_bg}; }}
        """)

    def get_value(self):
        return self.current_profiles

    def update_theme(self, dark_mode):
        self.dark_mode = dark_mode
        text_color = "#E0E0E0" if dark_mode else "#101010"
        input_bg = "#3C3C3C" if dark_mode else "#FFFFFF"
        input_border = "#555555" if dark_mode else "#B0B0B0"
        button_bg = "#4A4A4A" if dark_mode else "#DCDCDC"
        button_border = "#606060" if dark_mode else "#B0B0B0"
        button_hover_bg = "#5A5A5A" if dark_mode else "#CACACA"

        self.profiles_list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {input_border};
                border-radius: 3px;
                padding: 2px;
            }}
            QListWidget::item {{
                padding: 3px;
            }}
            QListWidget::item:selected {{
                background-color: #0078D7;
                color: white;
            }}
        """)
        self.add_profile_button.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {button_bg}; color: {text_color}; 
                border: 1px solid {button_border}; padding: 6px 12px; border-radius: 3px;
            }}
            QPushButton:hover {{ background-color: {button_hover_bg}; }}
        """)

class StringListManagerWidget(QWidget):
    def __init__(self, current_items, item_name_singular, dark_mode):
        super().__init__()
        self.dark_mode = dark_mode
        self.current_items = list(current_items) 
        self.item_name_singular = item_name_singular

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)

        self.list_widget = QListWidget()
        self.list_widget.setToolTip(f"Current {self.item_name_singular.lower()}s. Double-click to remove.")
        self.list_widget.itemDoubleClicked.connect(self.remove_item_from_list_widget)
        self.populate_list_widget()
        layout.addWidget(self.list_widget)

        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton(f"Add {self.item_name_singular}...")
        self.add_button.clicked.connect(self.show_add_item_dialog)
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        self.update_theme(dark_mode)

    def populate_list_widget(self):
        self.list_widget.clear()
        for item_text in self.current_items:
            self.list_widget.addItem(QListWidgetItem(item_text))

    def remove_item_from_list_widget(self, list_widget_item):
        item_to_remove = list_widget_item.text()
        if item_to_remove in self.current_items:
            self.current_items.remove(item_to_remove)
            self.populate_list_widget()

    def show_add_item_dialog(self):
        text, ok = QInputDialog.getText(self, f"Add {self.item_name_singular}", 
                                          f"Enter {self.item_name_singular.lower()}:")
        if ok and text.strip():
            new_item = text.strip()
            if new_item not in self.current_items:
                self.current_items.append(new_item)
                self.populate_list_widget()
            else:
                QMessageBox.information(self, "Item Exists", f"'{new_item}' is already in the list.")

    def get_value(self):
        return self.current_items

    def update_theme(self, dark_mode):
        self.dark_mode = dark_mode
        text_color = "#E0E0E0" if dark_mode else "#101010"
        input_bg = "#3C3C3C" if dark_mode else "#FFFFFF"
        input_border = "#555555" if dark_mode else "#B0B0B0"
        button_bg = "#4A4A4A" if dark_mode else "#DCDCDC"
        button_border = "#606060" if dark_mode else "#B0B0B0"
        button_hover_bg = "#5A5A5A" if dark_mode else "#CACACA"

        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {input_bg}; color: {text_color};
                border: 1px solid {input_border}; border-radius: 3px; padding: 2px;
            }}
            QListWidget::item {{ padding: 3px; }}
            QListWidget::item:selected {{ background-color: #0078D7; color: white; }}
        """)
        self.add_button.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {button_bg}; color: {text_color}; 
                border: 1px solid {button_border}; padding: 6px 12px; border-radius: 3px;
            }}
            QPushButton:hover {{ background-color: {button_hover_bg}; }}
        """)

class SettingsWidget(QWidget):
    def __init__(self, key, value, description, dark_mode, parent=None):
        super().__init__(parent)
        self.key = key
        self.description = description 
        self.original_value_type = type(value)
        self.dark_mode = dark_mode
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)

        self.label = QLabel(key)
        self.label.setMinimumWidth(200)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        layout.addWidget(self.label)
        
        if key == "profiles" and isinstance(value, list):
            available_from_comments = getattr(MindcraftSettingsEditor, 'SETTINGS_PROFILES_FROM_COMMENTS_CACHE', [])
            self.widget = ProfilesManagerWidget(value, available_from_comments, dark_mode)
            layout.addWidget(self.widget, 1)
        elif key == "only_chat_with" and isinstance(value, list):
            self.widget = StringListManagerWidget(value, "Player", dark_mode)
            layout.addWidget(self.widget, 1)
        elif isinstance(value, bool):
            self.widget = QCheckBox()
            self.widget.setChecked(value)
            layout.addWidget(self.widget)
            layout.addStretch(1)
        elif isinstance(value, list):
            self.widget = QLineEdit(json.dumps(value)) 
            self.widget.setMinimumWidth(250)
            layout.addWidget(self.widget, 1) 
            self.helper_label = QLabel("(JSON array)")
            layout.addWidget(self.helper_label)
        elif isinstance(value, int):
            self.widget = QLineEdit(str(value))
            self.widget.setMaximumWidth(120) 
            layout.addWidget(self.widget)
            layout.addStretch(1)
        elif isinstance(value, str):
            if key == "auth":
                self.widget = QComboBox()
                self.widget.addItems(["offline", "microsoft"])
                if value in ["offline", "microsoft"]: self.widget.setCurrentText(value)
                layout.addWidget(self.widget)
                layout.addStretch(1)
            elif key == "language":
                self.widget = QComboBox()
                self.widget.addItems(["en", "fr", "es", "de", "it", "pt", "ru", "zh", "ja", "ko"]) 
                if value in ["en", "fr", "es", "de", "it", "pt", "ru", "zh", "ja", "ko"]: self.widget.setCurrentText(value)
                layout.addWidget(self.widget)
                layout.addStretch(1)
            else:
                self.widget = QLineEdit(value)
                self.widget.setMinimumWidth(250)
                layout.addWidget(self.widget, 1) 
        else: 
            logger.warning(f"SettingsWidget: Unknown value type for key '{key}': {type(value)}. Using QLineEdit.")
            self.widget = QLineEdit(str(value))
            self.widget.setMinimumWidth(250)
            layout.addWidget(self.widget, 1)
        
        self.update_theme(dark_mode)
        
    def update_theme(self, dark_mode):
        self.dark_mode = dark_mode
        text_color = "#E0E0E0" if dark_mode else "#101010"
        input_bg = "#3C3C3C" if dark_mode else "#FFFFFF"
        input_border = "#555555" if dark_mode else "#B0B0B0"
        selected_bg_color = "#0078D7" 
        
        self.label.setStyleSheet(f"color: {text_color}; background-color: transparent;")
        
        if hasattr(self, 'helper_label') and self.helper_label:
            helper_text_color = "#AAAAAA" if dark_mode else "#555555"
            self.helper_label.setStyleSheet(f"font-size: 8pt; color: {helper_text_color}; background-color: transparent;")

        if isinstance(self.widget, (ProfilesManagerWidget, StringListManagerWidget)):
            self.widget.update_theme(dark_mode)
        elif isinstance(self.widget, QLineEdit):
            self.widget.setStyleSheet(
                f"background-color: {input_bg}; "
                f"color: {text_color}; "
                f"border: 1px solid {input_border}; "
                f"padding: 3px; "
                f"border-radius: 3px;"
            )
        elif isinstance(self.widget, QComboBox):
            self.widget.setStyleSheet(f"""
                QComboBox {{ 
                    background-color: {input_bg}; 
                    color: {text_color}; 
                    border: 1px solid {input_border}; 
                    padding: 3px 5px;
                    border-radius: 3px;
                }}
                QComboBox:focus {{
                    border: 1px solid {selected_bg_color}; 
                }}
                QComboBox::drop-down {{
                    border: none; 
                    width: 15px;
                }}
                QComboBox::down-arrow {{
                    /* No image, rely on Fusion style or system default */
                }}
                QComboBox QAbstractItemView {{ 
                    background-color: {input_bg}; 
                    color: {text_color}; 
                    border: 1px solid {input_border}; 
                    selection-background-color: {selected_bg_color};
                    selection-color: white;
                }}
            """)
        elif isinstance(self.widget, QCheckBox):
            indicator_border_unchecked = "#777777" if dark_mode else "#AAAAAA"
            indicator_bg_unchecked = input_bg

            self.widget.setStyleSheet(f"""
                QCheckBox {{ 
                    color: {text_color}; 
                    background-color: transparent; 
                    /* spacing: 5px; --- REMOVED FOR TESTING --- */
                }}
                QCheckBox::indicator {{ 
                    width: 16px; 
                    height: 16px; 
                    /* border-radius: 3px; --- REMOVED FOR TESTING --- */
                    border: 1px solid {indicator_border_unchecked}; 
                    background-color: {indicator_bg_unchecked}; 
                }}
                QCheckBox::indicator:hover {{
                     border: 1px solid {selected_bg_color}; /* Basic hover */
                }}
                QCheckBox::indicator:checked {{ 
                    background-color: {selected_bg_color}; /* Blue background */
                    border: 1px solid {selected_bg_color}; /* Matching border */
                    /* image: none; --- NO IMAGE --- */
                }}
                QCheckBox::indicator:checked:hover {{ /* Basic hover for checked */
                    background-color: {QColor(selected_bg_color).darker(110).name()}; 
                    border: 1px solid {QColor(selected_bg_color).darker(110).name()};
                }}
            """)
    
    def get_value(self):
        if isinstance(self.widget, (ProfilesManagerWidget, StringListManagerWidget)):
            return self.widget.get_value()
        elif self.original_value_type == bool:
            return self.widget.isChecked()
        elif self.original_value_type == int:
            try:
                return int(self.widget.text())
            except ValueError:
                logger.warning(f"Invalid integer for key '{self.key}': '{self.widget.text()}'. Returning 0.")
                return 0
        elif self.original_value_type == list:
            try:
                val = json.loads(self.widget.text())
                if not isinstance(val, list):
                    logger.warning(f"Value for key '{self.key}' is not a list: '{self.widget.text()}'. Returning [].")
                    return []
                return val
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON array for key '{self.key}': '{self.widget.text()}'. Returning [].")
                return []
        elif isinstance(self.widget, QComboBox):
            return self.widget.currentText()
        elif self.original_value_type == str:
            return self.widget.text()
        
        logger.warning(f"Unhandled original type '{self.original_value_type}' for key '{self.key}'. Returning raw text.")
        return self.widget.text()

class CategoryHeader(QWidget):
    def __init__(self, title, dark_mode, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 6)
        layout.setSpacing(4)

        self.label = QLabel(title.upper())
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.label.setFont(font)
        layout.addWidget(self.label)
        
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Plain)
        layout.addWidget(self.separator)
        
        self.update_theme(dark_mode)
        
    def update_theme(self, dark_mode):
        parent_bg_color = "#242424" if dark_mode else "#F5F5F5"
        text_color = "#00AEEF" if dark_mode else "#0078D7"
        separator_color = "#4A4A4A" if dark_mode else "#BDBDBD"
        
        self.setStyleSheet(f"background-color: {parent_bg_color};")
        self.label.setStyleSheet(f"color: {text_color}; background-color: transparent; padding-bottom: 2px;")
        self.separator.setStyleSheet(f"border: none; border-top: 1px solid {separator_color};")

class SelectInstallationDialog(QDialog):
    def __init__(self, paths, dark_mode, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Mindcraft Installation")
        self.setMinimumSize(550, 300)
        self.selected_path = None
        self.dark_mode = dark_mode
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        label = QLabel("Multiple Mindcraft installations found. Please select one:")
        layout.addWidget(label)
        
        self.list_widget = QListWidget()
        for path_str in paths:
            self.list_widget.addItem(path_str)
        if paths:
            self.list_widget.setCurrentRow(0)
        layout.addWidget(self.list_widget)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch(1)
        
        self.select_button = QPushButton("Select")
        self.select_button.setDefault(True)
        self.select_button.clicked.connect(self.accept_selection)
        button_layout.addWidget(self.select_button)
        
        layout.addLayout(button_layout)
        self.apply_theme()
        
    def accept_selection(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_path = current_item.text()
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select an installation path.")
        
    def apply_theme(self):
        dialog_bg = "#2C2C2C" if self.dark_mode else "#F0F0F0"
        text_color = "#E0E0E0" if self.dark_mode else "#101010"
        input_bg = "#3C3C3C" if self.dark_mode else "#FFFFFF"
        input_border = "#555555" if self.dark_mode else "#B0B0B0"
        button_bg = "#4A4A4A" if self.dark_mode else "#DCDCDC"
        button_border = "#606060" if self.dark_mode else "#B0B0B0"
        button_hover_bg = "#5A5A5A" if self.dark_mode else "#CACACA"
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: {dialog_bg}; }}
            QLabel {{ color: {text_color}; background-color: transparent; }}
            QListWidget {{ 
                background-color: {input_bg}; color: {text_color}; 
                border: 1px solid {input_border}; border-radius: 3px; padding: 5px;
            }}
            QListWidget::item:selected {{ background-color: #0078D7; color: white; }}
            QPushButton {{ 
                background-color: {button_bg}; color: {text_color}; 
                border: 1px solid {button_border}; padding: 8px 15px; border-radius: 3px;
            }}
            QPushButton:hover {{ background-color: {button_hover_bg}; }}
            QPushButton:focus {{ border: 1px solid #0078D7; }}
        """)
        self.select_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#0078D7"}; 
                color: white; font-weight: bold;
                border: 1px solid {"#005A9E"}; padding: 8px 15px; border-radius: 3px;
            }}
            QPushButton:hover {{ background-color: {"#005A9E"}; }}
        """)

class MindcraftSettingsEditor(QMainWindow):
    SETTINGS_PROFILES_FROM_COMMENTS_CACHE = []
    SETTINGS_DESCRIPTIONS = {
        "minecraft_version": "The Minecraft version to connect to (e.g., 1.21.4)",
        "host": "The hostname or IP address of the Minecraft server",
        "port": "The port number of the Minecraft server (default: 55916)",
        "auth": "Authentication method ('offline' for local servers, 'microsoft' for online servers)",
        "host_mindserver": "Whether to host the mind server locally",
        "mindserver_host": "The hostname or IP address of the mind server",
        "mindserver_port": "The port number of the mind server",
        "base_profile": "The base profile to use for all agents",
        "profiles": "List of agent profiles to load (JSON array of strings)",
        "load_memory": "Whether to load memory from previous sessions",
        "init_message": "The initial message to send to the agent",
        "only_chat_with": "List of player names the agent will exclusively chat with (JSON array of strings)",
        "speak": "Whether the agent should use text-to-speech",
        "language": "The language code for the agent (e.g., 'en' for English)",
        "show_bot_views": "Whether to show the bot's view in a separate window",
        "allow_insecure_coding": "Whether to allow the agent to write and execute code (CAUTION: security risk)",
        "allow_vision": "Whether to allow the agent to use vision capabilities",
        "blocked_actions": "List of actions that the agent is not allowed to perform (JSON array of strings)",
        "code_timeout_mins": "Timeout for code execution in minutes (-1 for no timeout)",
        "relevant_docs_count": "Number of relevant documents to include in context (-1 for all)",
        "max_messages": "Maximum number of messages to keep in history",
        "num_examples": "Number of examples to include in prompts", 
        "max_commands": "Maximum number of commands the agent can execute (-1 for unlimited)",
        "verbose_commands": "Whether to show detailed command information",
        "narrate_behavior": "Whether the agent should narrate its behavior",
        "chat_bot_messages": "Whether to show bot messages in chat",
        "log_all_prompts": "Whether to log all prompts for debugging"
    }
    
    def __init__(self):
        super().__init__()
        self.settings_path: Path | None = None
        self.settings = {}
        self.settings_widgets = {}
        self.category_headers = []
        self.file_suffix = ""
        
        self.dark_mode = self.is_system_dark_mode()
        logger.info(f"System dark mode detected: {self.dark_mode}")
        
        self.init_ui() 
        self.tooltip = ToolTip(self) 

        logger.info(f"Applying initial theme (Dark mode: {self.dark_mode})")
        self.apply_theme() 

        logger.info("Scanning for Mindcraft installations post-init.")
        QTimer.singleShot(100, self.scan_for_mindcraft)
        
        logger.info("Mindcraft Settings Editor initialized.")
    
    def init_ui(self):
        self.setWindowTitle("Mindcraft Settings Editor")
        self.setMinimumSize(850, 650)
        
        icon_path = self.resource_path("mindcraft_icon.ico")
        if Path(icon_path).exists():
            self.setWindowIcon(QIcon(icon_path))
            logger.info("Application icon loaded successfully.")
        else:
            logger.warning(f"Application icon not found at {icon_path}.")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        path_frame = QFrame()
        path_frame.setObjectName("PathFrame")
        path_layout = QHBoxLayout(path_frame)
        path_layout.setContentsMargins(10, 10, 10, 10)
        path_layout.setSpacing(8)
        
        path_label = QLabel("Settings File:")
        path_layout.addWidget(path_label)
        
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.path_input.setPlaceholderText("No settings file loaded")
        path_layout.addWidget(self.path_input, 1)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_settings_file)
        path_layout.addWidget(self.browse_button)
        
        self.scan_button = QPushButton("Scan Again")
        self.scan_button.clicked.connect(self.scan_for_mindcraft)
        path_layout.addWidget(self.scan_button)
        main_layout.addWidget(path_frame)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.settings_widget_container = QWidget() 
        self.settings_widget_container.setObjectName("SettingsWidgetContainer")
        self.settings_layout = QVBoxLayout(self.settings_widget_container)
        self.settings_layout.setContentsMargins(0, 0, 0, 0) 
        self.settings_layout.setSpacing(0) 
        self.scroll_area.setWidget(self.settings_widget_container)
        main_layout.addWidget(self.scroll_area, 1)
        
        button_frame = QFrame()
        button_frame.setObjectName("ButtonFrame")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(8)
        
        self.theme_button = QPushButton() 
        self.theme_button.clicked.connect(self.toggle_theme)
        button_layout.addWidget(self.theme_button)
        
        button_layout.addStretch(1)
        
        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload_settings)
        button_layout.addWidget(self.reload_button)
        
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        main_layout.addWidget(button_frame)
    
    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError: 
            base_path = Path(__file__).resolve().parent
        return str(Path(base_path) / relative_path)
    
    def is_system_dark_mode(self):
        try:
            if sys.platform == "win32":
                import winreg
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return value == 0
            elif sys.platform == "darwin":
                import subprocess
                cmd = 'defaults read -g AppleInterfaceStyle'
                result = subprocess.run(cmd, shell=True, text=True, capture_output=True, check=False)
                return result.stdout.strip() == "Dark" and result.returncode == 0
        except Exception as e:
            logger.warning(f"Could not detect system theme: {e}")
        return False
    
    def apply_theme(self):
        main_bg = "#242424" if self.dark_mode else "#F5F5F5"
        text_color = "#E0E0E0" if self.dark_mode else "#101010"
        frame_bg = "#2C2C2C" if self.dark_mode else "#FFFFFF"
        frame_border = "#3A3A3A" if self.dark_mode else "#DCDCDC"
        button_bg = "#4A4A4A" if self.dark_mode else "#E0E0E0"
        button_hover_bg = "#5A5A5A" if self.dark_mode else "#D0D0D0"
        button_pressed_bg = "#6A6A6A" if self.dark_mode else "#C0C0C0"
        input_bg = "#3C3C3C" if self.dark_mode else "#FFFFFF"
        input_border = "#555555" if self.dark_mode else "#B0B0B0"
        scrollbar_bg = main_bg
        scrollbar_handle_bg = "#666666" if self.dark_mode else "#BBBBBB"
        save_button_bg = "#0078D7"
        save_button_text = "#FFFFFF"
        save_button_hover_bg = "#005A9E"
        save_button_pressed_bg = "#004C87"

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {main_bg}; }}
            QWidget {{ color: {text_color}; }} 
            QLabel {{ background-color: transparent; }}
            
            QFrame#PathFrame, QFrame#ButtonFrame {{ 
                background-color: {frame_bg}; 
                border: 1px solid {frame_border};
                border-radius: 4px; 
            }}
            
            QPushButton {{ 
                background-color: {button_bg}; color: {text_color};
                border: 1px solid {frame_border}; padding: 6px 12px; 
                border-radius: 3px; min-height: 20px;
            }}
            QPushButton:hover {{ background-color: {button_hover_bg}; }}
            QPushButton:pressed {{ background-color: {button_pressed_bg}; }}
            QPushButton:disabled {{ 
                background-color: {'#404040' if self.dark_mode else '#E0E0E0'}; 
                color: {'#777777' if self.dark_mode else '#A0A0A0'}; 
                border-color: {'#505050' if self.dark_mode else '#C0C0C0'};
            }}
            
            QLineEdit {{ 
                background-color: {input_bg}; color: {text_color}; 
                border: 1px solid {input_border}; padding: 4px; border-radius: 3px;
            }}
            QLineEdit:read-only {{ background-color: {'#333333' if self.dark_mode else '#E9E9E9'}; }}

            QScrollArea {{ border: none; background-color: {main_bg}; }}
            QWidget#SettingsWidgetContainer {{ background-color: {main_bg}; }}

            QScrollBar:vertical {{ 
                background: {scrollbar_bg}; width: 14px; margin: 0px; border-radius: 7px;
            }}
            QScrollBar::handle:vertical {{ 
                background: {scrollbar_handle_bg}; min-height: 25px; border-radius: 6px; margin: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

            QScrollBar:horizontal {{ 
                background: {scrollbar_bg}; height: 14px; margin: 0px; border-radius: 7px;
            }}
            QScrollBar::handle:horizontal {{ 
                background: {scrollbar_handle_bg}; min-width: 25px; border-radius: 6px; margin: 2px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ border: none; background: none; width: 0px; }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}
        """)
        
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {save_button_bg}; color: {save_button_text}; font-weight: bold;
                border: 1px solid {save_button_bg}; padding: 6px 12px; border-radius: 3px;
            }}
            QPushButton:hover {{ background-color: {save_button_hover_bg}; }}
            QPushButton:pressed {{ background-color: {save_button_pressed_bg}; }}
        """)
        self.theme_button.setText("Switch to Light Mode" if self.dark_mode else "Switch to Dark Mode")

        if hasattr(self, 'tooltip'): self.tooltip.set_theme(self.dark_mode)
        
        for widget in self.settings_widgets.values(): widget.update_theme(self.dark_mode)
        for header in self.category_headers: header.update_theme(self.dark_mode)
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        logger.info(f"Theme toggled. Dark mode is now: {self.dark_mode}")
        self.apply_theme()
    
    def eventFilter(self, watched_object, event):
        if event.type() == event.Type.Enter:
            for key, settings_widget_instance in self.settings_widgets.items():
                if watched_object == settings_widget_instance.label:
                    label_global_pos = settings_widget_instance.label.mapToGlobal(QPoint(0,0))
                    tooltip_pos = QPoint(label_global_pos.x(), label_global_pos.y() + settings_widget_instance.label.height() + 3)
                    
                    screen_geometry = QApplication.primaryScreen().availableGeometry()
                    self.tooltip.setText(self.SETTINGS_DESCRIPTIONS.get(key, "No description."))
                    tooltip_size_hint = self.tooltip.sizeHint()

                    if tooltip_pos.x() + tooltip_size_hint.width() > screen_geometry.right() - 10:
                        tooltip_pos.setX(label_global_pos.x() - tooltip_size_hint.width() - 5)
                    if tooltip_pos.y() + tooltip_size_hint.height() > screen_geometry.bottom() - 10:
                        tooltip_pos.setY(label_global_pos.y() - tooltip_size_hint.height() - 3)

                    self.tooltip.show_tooltip(self.SETTINGS_DESCRIPTIONS.get(key, "No description."), tooltip_pos)
                    return True
        elif event.type() == event.Type.Leave:
            is_label_leave = any(watched_object == sw.label for sw in self.settings_widgets.values())
            if is_label_leave and self.tooltip.isVisible():
                self.tooltip.hide_tooltip()
            return True
        return super().eventFilter(watched_object, event)
    
    def scan_for_mindcraft(self):
        logger.info("Starting scan for Mindcraft installations...")
        home_dir = Path.home()
        popular_locations = [
            home_dir / "Desktop", home_dir / "Documents", home_dir / "Downloads", home_dir,
            Path.cwd()
        ]
        if sys.platform == "win32":
            popular_locations.extend([
                Path(os.environ.get("ProgramFiles", "C:/Program Files")),
                Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")),
                Path("C:/")
            ])
        
        try: 
            script_dir = Path(__file__).resolve().parent
            popular_locations.extend([script_dir, script_dir.parent, script_dir.parent.parent])
        except NameError: pass

        valid_locations = sorted(list(set(p for p in popular_locations if p and p.exists() and p.is_dir())))
        logger.info(f"Scanning up to {len(valid_locations)} unique, valid locations.")

        found_files = []
        mindcraft_dirs = ["mindcraft", "mindcraft-main"]
        for loc in valid_locations:
            for dirname in mindcraft_dirs:
                potential_dir = loc / dirname
                if potential_dir.is_dir():
                    settings_file = potential_dir / "settings.js"
                    if settings_file.is_file() and settings_file not in found_files:
                        logger.info(f"Found settings.js at: {settings_file}")
                        found_files.append(settings_file)
            direct_settings_file = loc / "settings.js"
            if direct_settings_file.is_file() and direct_settings_file not in found_files:
                 logger.info(f"Found settings.js directly at: {direct_settings_file}")
                 found_files.append(direct_settings_file)

        if not found_files:
            logger.info("Performing broader search in home subdirectories (level 1)...")
            try:
                for item in home_dir.iterdir():
                    if item.is_dir():
                        for dirname_pattern in mindcraft_dirs:
                            if item.name.lower().startswith(dirname_pattern.lower()):
                                settings_file = item / "settings.js"
                                if settings_file.is_file() and settings_file not in found_files:
                                    logger.info(f"Found settings.js in home subdirectory: {settings_file}")
                                    found_files.append(settings_file)
            except PermissionError:
                logger.warning(f"Permission denied while scanning {home_dir} subdirectories.")

        found_files = sorted(list(set(found_files))) 

        if found_files:
            logger.info(f"Scan complete. Found {len(found_files)} potential Mindcraft settings file(s).")
            if len(found_files) > 1:
                dialog = SelectInstallationDialog([str(p) for p in found_files], self.dark_mode, self)
                if dialog.exec() and dialog.selected_path:
                    self.load_settings_file(Path(dialog.selected_path))
                else:
                    logger.info("User cancelled selection or closed dialog.")
            else:
                self.load_settings_file(found_files[0])
        else:
            logger.warning("No Mindcraft installations found after scan.")
            QMessageBox.information(self, "Scan Complete", "No Mindcraft installations found in common locations. Please use Browse.")
    
    def browse_settings_file(self):
        start_dir = str(self.settings_path.parent if self.settings_path else Path.home())
        file_path_str, _ = QFileDialog.getOpenFileName(self, "Select settings.js", start_dir, "JavaScript files (*.js);;All files (*.*)")
        if file_path_str:
            self.load_settings_file(Path(file_path_str))
    
    def load_settings_file(self, file_path: Path):
        if not file_path or not file_path.is_file():
            logger.error(f"Invalid file path: {file_path}")
            QMessageBox.critical(self, "Error", f"File not found or invalid: {file_path}")
            return

        logger.info(f"Attempting to load settings from: {file_path}")
        try:
            content = file_path.read_text(encoding='utf-8')

            MindcraftSettingsEditor.SETTINGS_PROFILES_FROM_COMMENTS_CACHE = []
            profiles_array_match = re.search(r'("profiles"\s*:\s*\[)([^\]]*)(\])', content, re.DOTALL)
            if profiles_array_match:
                profiles_array_content = profiles_array_match.group(2)
                logger.debug(f"Content of 'profiles' array for comment parsing: '''{profiles_array_content}'''")
                
                commented_profile_matches = re.findall(r'//\s*["\']([^"\']+)["\']', profiles_array_content)
                for cp in commented_profile_matches:
                    normalized_cp = cp.replace("\\", "/") 
                    if normalized_cp not in MindcraftSettingsEditor.SETTINGS_PROFILES_FROM_COMMENTS_CACHE:
                        MindcraftSettingsEditor.SETTINGS_PROFILES_FROM_COMMENTS_CACHE.append(normalized_cp)
                logger.info(f"Found {len(MindcraftSettingsEditor.SETTINGS_PROFILES_FROM_COMMENTS_CACHE)} commented profiles: {MindcraftSettingsEditor.SETTINGS_PROFILES_FROM_COMMENTS_CACHE}")
            else:
                logger.info("No 'profiles' array block found for comment parsing in raw content.")

            settings_match = re.search(r'const\s+settings\s*=\s*(\{[\s\S]*?\n?\})[\s;]*', content, re.DOTALL)
            
            if settings_match:
                settings_str_original = settings_match.group(1)
                logger.debug(f"Extracted active settings block:\n{settings_str_original[:500]}...")

                end_of_settings_block = settings_match.end()
                self.file_suffix = content[end_of_settings_block:].strip()
                
                original_tail_content = content[end_of_settings_block:]
                if "export default settings" not in self.file_suffix.lower() and \
                   "export default settings" not in original_tail_content.lower():
                    logger.info("Appending 'export default settings;' to suffix as it was not found in remaining file content.")
                    newline_prefix = "\n" if self.file_suffix and not self.file_suffix.endswith(("\n", "\r")) else ""
                    self.file_suffix = newline_prefix + self.file_suffix + "\nexport default settings;"

                logger.debug(f"File suffix determined:\n{self.file_suffix[:200]}...")

                try:
                    processed_str = settings_str_original
                    processed_str = re.sub(r"//.*", "", processed_str) 
                    processed_str = re.sub(r"/\*[\s\S]*?\*/", "", processed_str, flags=re.MULTILINE)
                    
                    processed_str = re.sub(r"\bundefined\b", "null", processed_str)
                    processed_str = re.sub(r"\bNaN\b", '"NaN"', processed_str)
                    processed_str = re.sub(r"\bInfinity\b", '"Infinity"', processed_str)
                                        
                    processed_str = re.sub(r'([{,]\s*)([a-zA-Z_]\w*)\s*:', r'\1"\2":', processed_str)
                    
                    processed_str = processed_str.replace("'", '"')
                    
                    processed_str = re.sub(r',(\s*[}\]])', r'\1', processed_str)
                                        
                    self.settings = json.loads(processed_str)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Primary JSON parsing for active settings failed: {e}.")
                    self.settings = {} 
                    key_pattern_orig = r'(?:^|\s)(?:"(\w+)"|\'(\w+)\'|(\w+))\s*:'
                    
                    fallback_str_base_active = re.sub(r"//.*", "", settings_str_original)
                    fallback_str_base_active = re.sub(r"/\*[\s\S]*?\*/", "", fallback_str_base_active, flags=re.MULTILINE)

                    keys_iter = re.finditer(key_pattern_orig, fallback_str_base_active)
                    
                    parsed_pairs = []
                    for key_match in keys_iter:
                        key = next(g for g in key_match.groups() if g is not None)
                        parsed_pairs.append({'key': key, 'start': key_match.end()})
                    
                    for i, pair_info in enumerate(parsed_pairs):
                        key = pair_info['key']
                        val_start_pos = pair_info['start']
                        val_end_pos = len(fallback_str_base_active)
                        
                        next_key_match_obj = None
                        temp_iter = re.finditer(key_pattern_orig, fallback_str_base_active)
                        for idx, m_obj in enumerate(temp_iter):
                            if idx == i + 1:
                                next_key_match_obj = m_obj
                                break
                        if next_key_match_obj:
                            val_end_pos = next_key_match_obj.start()

                        value_str_raw = fallback_str_base_active[val_start_pos:val_end_pos].strip()
                        if value_str_raw.endswith((',', ';')): value_str_raw = value_str_raw[:-1].strip()

                        value = None 
                        if value_str_raw.lower() == 'true': value = True
                        elif value_str_raw.lower() == 'false': value = False
                        elif value_str_raw.lower() == 'null' or value_str_raw.lower() == 'undefined': value = None
                        elif (value_str_raw.startswith('"') and value_str_raw.endswith('"')) or \
                             (value_str_raw.startswith("'") and value_str_raw.endswith("'")):
                            try: value = json.loads(value_str_raw.replace("'", '"')) 
                            except json.JSONDecodeError: value = value_str_raw[1:-1] 
                        elif value_str_raw.startswith('[') and value_str_raw.endswith(']'):
                            try: value = json.loads(value_str_raw.replace("'", '"'))
                            except json.JSONDecodeError: value = [] 
                        elif value_str_raw.isdigit() or (value_str_raw.startswith('-') and value_str_raw[1:].isdigit()):
                            value = int(value_str_raw)
                        else: 
                            value = value_str_raw
                        self.settings[key] = value
                    logger.info(f"Fallback parser loaded {len(self.settings)} active settings.")

                logger.info(f"Successfully processed active settings from {file_path}. Total active settings: {len(self.settings)}")
                self.settings_path = file_path
                self.path_input.setText(str(file_path))
                self.display_settings()
                QMessageBox.information(self, "Settings Loaded", f"Settings loaded from:\n{file_path}")
            else: 
                logger.error(f"Could not find active settings block 'const settings = {{...}}' in {file_path}")
                QMessageBox.critical(self, "Parse Error", f"Could not find active settings block in:\n{file_path}")
                self.settings, self.settings_path = {}, None
                self.path_input.clear()
                self.display_settings()

        except Exception as e:
            logger.error(f"Critical error loading {file_path}: {e}", exc_info=True)
            QMessageBox.critical(self, "Load Error", f"Failed to load settings from:\n{file_path}\n\nError: {e}")
            self.settings, self.settings_path = {}, None
            self.path_input.clear()
            self.display_settings()
    
    def display_settings(self):
        while self.settings_layout.count():
            item = self.settings_layout.takeAt(0)
            if widget := item.widget(): widget.deleteLater()
            elif item.spacerItem(): self.settings_layout.removeItem(item)
        
        self.settings_widgets.clear()
        self.category_headers.clear()
        
        if not self.settings:
            no_settings_label = QLabel("No settings loaded or file is empty.\nUse 'Browse' or 'Scan Again'.")
            no_settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_settings_label.setStyleSheet("font-style: italic; color: gray; padding: 30px;")
            self.settings_layout.addWidget(no_settings_label)
            self.settings_layout.addStretch(1)
            self.reload_button.setEnabled(False) 
            self.save_button.setEnabled(False)
            return

        categories = {
            "Connection": ["minecraft_version", "host", "port", "auth"],
            "Mind Server": ["host_mindserver", "mindserver_host", "mindserver_port"],
            "Agent Configuration": ["base_profile", "profiles", "load_memory", "init_message", "only_chat_with", "speak", "language"],
            "Features": ["show_bot_views", "allow_insecure_coding", "allow_vision", "blocked_actions"],
            "Performance & Limits": ["code_timeout_mins", "relevant_docs_count", "max_messages", "num_examples", "max_commands"],
            "Logging & Behavior": ["verbose_commands", "narrate_behavior", "chat_bot_messages", "log_all_prompts"]
        }
        
        displayed_keys = set()
        for category_title, keys_in_cat in categories.items():
            relevant_keys = [k for k in keys_in_cat if k in self.settings]
            if relevant_keys:
                header = CategoryHeader(category_title, self.dark_mode)
                self.settings_layout.addWidget(header)
                self.category_headers.append(header)
                
                for key in relevant_keys:
                    desc = self.SETTINGS_DESCRIPTIONS.get(key, "No description.")
                    sw = SettingsWidget(key, self.settings[key], desc, self.dark_mode)
                    sw.label.installEventFilter(self)
                    self.settings_layout.addWidget(sw)
                    self.settings_widgets[key] = sw
                    displayed_keys.add(key)
                self.settings_layout.addSpacing(10)

        other_settings_keys = sorted([k for k in self.settings if k not in displayed_keys])
        if other_settings_keys:
            header = CategoryHeader("Other Settings", self.dark_mode)
            self.settings_layout.addWidget(header)
            self.category_headers.append(header)
            for key in other_settings_keys:
                desc = self.SETTINGS_DESCRIPTIONS.get(key, "No description.")
                sw = SettingsWidget(key, self.settings[key], desc, self.dark_mode)
                sw.label.installEventFilter(self)
                self.settings_layout.addWidget(sw)
                self.settings_widgets[key] = sw
            self.settings_layout.addSpacing(10)
        
        self.settings_layout.addStretch(1)
        self.scroll_area.verticalScrollBar().setValue(0)
        self.reload_button.setEnabled(bool(self.settings_path))
        self.save_button.setEnabled(bool(self.settings_path))

    def save_settings(self):
        if not self.settings_path:
            QMessageBox.warning(self, "Save Error", "No settings file loaded. Cannot save.")
            return
        
        logger.info(f"Preparing to save settings to: {self.settings_path}")
        
        current_ui_settings = {}
        for key, widget_instance in self.settings_widgets.items():
            try:
                current_ui_settings[key] = widget_instance.get_value()
            except Exception as e:
                logger.error(f"Error getting value for '{key}': {e}", exc_info=True)
                QMessageBox.critical(self, "Input Error", f"Invalid value for '{key}'. Please correct and try again.\nError: {e}")
                return
        
        try:
            setting_entries = []
            for key, value in sorted(current_ui_settings.items()):
                js_value_str = json.dumps(value, ensure_ascii=False, indent=None)
                setting_entries.append(f'    "{key}": {js_value_str}')
            
            settings_js_object = "{\n" + ",\n".join(setting_entries) + "\n}"
            
            effective_suffix = self.file_suffix
            if effective_suffix and not effective_suffix.startswith(('\n', '\r')):
                effective_suffix = "\n" + effective_suffix
            elif not effective_suffix and not settings_js_object.endswith("\n"): 
                settings_js_object += "\n"

            new_content = f"const settings = {settings_js_object};{effective_suffix}"
            
            self.settings_path.write_text(new_content, encoding='utf-8')
            
            self.settings = current_ui_settings

            original_geom = self.geometry()
            anim = QPropertyAnimation(self, b"geometry", self)
            anim.setDuration(200)
            anim.setStartValue(original_geom)
            anim.setKeyValueAt(0.25, QRect(original_geom).translated(5, 0))
            anim.setKeyValueAt(0.50, QRect(original_geom).translated(-5,0))
            anim.setKeyValueAt(0.75, QRect(original_geom).translated(5, 0))
            anim.setEndValue(original_geom)
            anim.setEasingCurve(QEasingCurve.Type.OutSine)
            anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

            logger.info("Settings saved successfully.")
            QMessageBox.information(self, "Save Successful", f"Settings saved to:\n{self.settings_path}")

        except Exception as e:
            logger.error(f"Failed to save settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Save Error", f"Could not save settings to file:\n{self.settings_path}\n\nError: {e}")
    
    def reload_settings(self):
        if self.settings_path and self.settings_path.is_file():
            logger.info(f"Reloading settings from: {self.settings_path}")
            self.load_settings_file(self.settings_path)
        elif self.settings_path:
            QMessageBox.warning(self, "Reload Error", f"File not found: {self.settings_path}.\nPlease browse again.")
        else:
            QMessageBox.information(self, "Reload Info", "No settings file is currently loaded to reload.")

def main():
    try:
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1" 

        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        default_font = QFont("Segoe UI", 9)
        if sys.platform == "darwin": 
            default_font = QFont(".SF NS Text", 13)
        elif sys.platform.startswith("linux"): 
            default_font = QFont("Noto Sans", 10)
        app.setFont(default_font)
        
        logger.info("Starting Mindcraft Settings Editor application GUI.")
        editor = MindcraftSettingsEditor()
        editor.show()
        
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        print(f"CRITICAL ERROR: {e}", file=sys.stderr)
        
        try:
            if QApplication.instance():
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle("Critical Application Error")
                msg_box.setText(f"A critical error occurred and the application must close:\n\n{type(e).__name__}: {e}")
                msg_box.exec()
            else:
                print("QApplication could not be initialized. Error details logged or printed above.", file=sys.stderr)
        except Exception as q_msg_e:
            print(f"Failed to show critical error QMessageBox: {q_msg_e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    print("Starting Mindcraft Settings Editor...")
    print("Check the console for detailed logs.")
    main()