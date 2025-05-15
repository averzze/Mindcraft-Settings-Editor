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
            self.setStyleSheet("border: 1px solid #555555; border-radius: 3px; background-color: #424242;")
        else:
            self.setPalette(self.light_palette)
            self.setStyleSheet("border: 1px solid #D0D0D0; border-radius: 3px; background-color: #FFFFE0;")
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

        all_available = sorted(list(set(self.available_profiles_from_comments) | set(getattr(MindcraftSettingsEditor, 'SETTINGS_PROFILES_FROM_COMMENTS_CACHE', []))))
        unique_available_for_adding = sorted(list(set(all_available) - set(self.current_profiles)))
        
        if unique_available_for_adding:
            combo_box.addItems(unique_available_for_adding)
        
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
                if selected_profile in self.available_profiles_from_comments:
                    self.available_profiles_from_comments.remove(selected_profile)

    def _apply_dialog_theme(self, dialog, dark_mode):
        dialog_bg = "#2C2C2C" if dark_mode else "#F0F0F0"
        text_color = "#E0E0E0" if dark_mode else "#101010" 
        label_bg_color = "transparent" if dark_mode else "#FFFFFF"
        input_bg = "#3C3C3C" if dark_mode else "#FFFFFF" 
        input_border = "#555555" if dark_mode else "#B0B0B0" 
        button_bg = "#4A4A4A" if dark_mode else "#DCDCDC" 
        button_border = "#606060" if dark_mode else "#B0B0B0" 
        button_hover_bg = "#5A5A5A" if dark_mode else "#CACACA"

        dialog.setStyleSheet(f"""
            QDialog {{ background-color: {dialog_bg}; }}
            QDialog QLabel {{ color: {text_color}; background-color: {label_bg_color}; padding: 2px; }}
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
        list_item_selected_bg = "#0078D7" 

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
                background-color: {list_item_selected_bg};
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
        # *** THIS WAS THE MISSING LINE ***
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

    def remove_item_from_list_widget(self, list_widget_item): # Renamed parameter for clarity
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
        list_item_selected_bg = "#0078D7"

        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {input_bg}; color: {text_color};
                border: 1px solid {input_border}; border-radius: 3px; padding: 2px;
            }}
            QListWidget::item {{ padding: 3px; }}
            QListWidget::item:selected {{ background-color: {list_item_selected_bg}; color: white; }}
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
                else: self.widget.setCurrentIndex(0) 
                layout.addWidget(self.widget)
                layout.addStretch(1)
            elif key == "language":
                self.widget = QComboBox()
                langs = ["en", "fr", "es", "de", "it", "pt", "ru", "zh", "ja", "ko"]
                self.widget.addItems(langs) 
                if value in langs: self.widget.setCurrentText(value)
                else: self.widget.setCurrentIndex(0) if "en" in langs else self.widget.setCurrentIndex(-1)
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
        label_bg_color = "transparent" if dark_mode else "#FFFFFF" 
        input_bg = "#3C3C3C" if dark_mode else "#FFFFFF"
        input_border = "#555555" if dark_mode else "#B0B0B0" 
        selected_bg_color = "#0078D7" 
        
        self.label.setStyleSheet(f"color: {text_color}; background-color: {label_bg_color}; padding: 2px;") 
        
        if hasattr(self, 'helper_label') and self.helper_label:
            helper_text_color = "#AAAAAA" if dark_mode else "#555555" 
            self.helper_label.setStyleSheet(f"font-size: 8pt; color: {helper_text_color}; background-color: {label_bg_color}; padding: 1px;") 

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
                    spacing: 5px; 
                }}
                QCheckBox::indicator {{ 
                    width: 16px; 
                    height: 16px; 
                    border: 1px solid {indicator_border_unchecked}; 
                    background-color: {indicator_bg_unchecked}; 
                    border-radius: 3px; 
                }}
                QCheckBox::indicator:hover {{
                     border: 1px solid {selected_bg_color}; 
                }}
                QCheckBox::indicator:checked {{ 
                    background-color: {selected_bg_color}; 
                    border: 1px solid {selected_bg_color}; 
                }}
                QCheckBox::indicator:checked:hover {{ 
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
        
        logger.warning(f"Unhandled original type '{self.original_value_type}' for key '{self.key}'. Returning raw text from widget.")
        if hasattr(self.widget, 'text'):
            return self.widget.text()
        return str(self.widget) 

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
        label_bg_color = "transparent" if dark_mode else "#FFFFFF" 
        separator_color = "#4A4A4A" if dark_mode else "#BDBDBD" 
        
        self.setStyleSheet(f"background-color: {parent_bg_color};") 
        self.label.setStyleSheet(f"color: {text_color}; background-color: {label_bg_color}; padding: 3px 0px 2px 0px;") 
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
        label_bg_color = "transparent" if self.dark_mode else "#FFFFFF" 
        input_bg = "#3C3C3C" if self.dark_mode else "#FFFFFF"
        input_border = "#555555" if self.dark_mode else "#B0B0B0" 
        button_bg = "#4A4A4A" if self.dark_mode else "#DCDCDC" 
        button_border = "#606060" if self.dark_mode else "#B0B0B0" 
        button_hover_bg = "#5A5A5A" if self.dark_mode else "#CACACA"
        list_item_selected_bg = "#0078D7"
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: {dialog_bg}; }}
            QDialog QLabel {{ color: {text_color}; background-color: {label_bg_color}; padding: 2px; }}
            QListWidget {{ 
                background-color: {input_bg}; color: {text_color}; 
                border: 1px solid {input_border}; border-radius: 3px; padding: 5px;
            }}
            QListWidget::item:selected {{ background-color: {list_item_selected_bg}; color: white; }}
            QPushButton {{ 
                background-color: {button_bg}; color: {text_color}; 
                border: 1px solid {button_border}; padding: 8px 15px; border-radius: 3px;
            }}
            QPushButton:hover {{ background-color: {button_hover_bg}; }}
            QPushButton:focus {{ border: 1px solid {list_item_selected_bg}; }} 
        """)
        
        select_button_bg = "#0078D7" 
        select_button_text_color = "white"
        select_button_border_color = "#005A9E" if self.dark_mode else "#006ABC" 
        select_button_hover_bg = "#005A9E"

        self.select_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {select_button_bg}; 
                color: {select_button_text_color}; font-weight: bold;
                border: 1px solid {select_button_border_color}; padding: 8px 15px; border-radius: 3px;
            }}
            QPushButton:hover {{ background-color: {select_button_hover_bg}; }}
        """)

class MindcraftSettingsEditor(QMainWindow):
    SETTINGS_PROFILES_FROM_COMMENTS_CACHE = []
    SETTINGS_DESCRIPTIONS = {
        "minecraft_version": "The Minecraft version to connect to (e.g., 1.20.4)",
        "host": "The hostname or IP address of the Minecraft server",
        "port": "The port number of the Minecraft server (default: 25565 or from server.properties)",
        "auth": "Authentication method ('offline' for local/cracked servers, 'microsoft' for online-mode servers)",
        "host_mindserver": "Whether this instance should host the MindServer (for multi-agent or external control)",
        "mindserver_host": "Hostname/IP for the MindServer if hosting or connecting to one",
        "mindserver_port": "Port for the MindServer",
        "base_profile": "The base agent profile defining core behaviors and personality",
        "profiles": "List of additional agent profiles to load, layering capabilities or behaviors",
        "load_memory": "Whether the agent should load its long-term memory from previous sessions",
        "init_message": "An initial message or instruction to give the agent upon connection",
        "only_chat_with": "A list of player usernames. If not empty, the agent will only respond to these players.",
        "speak": "Enable text-to-speech for the agent's messages",
        "language": "Language code for agent's speech and understanding (e.g., 'en', 'es')",
        "show_bot_views": "Display a window showing what the agent 'sees' (if vision is enabled)",
        "allow_insecure_coding": "CRITICAL: Allow agent to write/execute code. Major security risk if agent is compromised or misbehaves.",
        "allow_vision": "Enable visual processing capabilities for the agent (requires appropriate model setup)",
        "blocked_actions": "A list of game actions the agent is forbidden to perform",
        "code_timeout_mins": "Timeout in minutes for agent-generated code execution (-1 for no timeout)",
        "relevant_docs_count": "How many relevant documents from memory/knowledge to fetch for context (-1 for all)",
        "max_messages": "Maximum number of recent chat messages to keep in the agent's short-term context",
        "num_examples": "Number of few-shot examples to include in prompts to guide agent behavior",
        "max_commands": "Maximum number of commands the agent can issue in a short time frame (-1 for unlimited)",
        "verbose_commands": "Log detailed information about commands being executed by the agent",
        "narrate_behavior": "Agent will 'think out loud' or narrate its actions/intentions in chat",
        "chat_bot_messages": "Whether the bot's own messages are processed as part of chat history for itself",
        "log_all_prompts": "Log all full prompts sent to the LLM (can be very verbose; for debugging)"
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
        
        self.central_widget_ref = QWidget() 
        self.setCentralWidget(self.central_widget_ref)

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
        
        icon_path = MindcraftSettingsEditor.resource_path("mindcraft_icon.ico")
        if Path(icon_path).exists():
            self.setWindowIcon(QIcon(icon_path))
            logger.info("Application icon loaded successfully.")
        else:
            logger.warning(f"Application icon not found at {icon_path}.")
        
        main_layout = QVBoxLayout(self.central_widget_ref) 
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        path_frame = QFrame()
        path_frame.setObjectName("PathFrame") 
        path_layout = QHBoxLayout(path_frame)
        path_layout.setContentsMargins(10, 10, 10, 10) 
        path_layout.setSpacing(8)
        
        self.path_label_ref = QLabel("Settings File:") 
        path_layout.addWidget(self.path_label_ref)
        
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
        self.reload_button.setEnabled(False) 
        button_layout.addWidget(self.reload_button)
        
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setEnabled(False) 
        button_layout.addWidget(self.save_button)
        main_layout.addWidget(button_frame)
    
    @staticmethod
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError: 
            base_path = Path(__file__).resolve().parent
        return str(Path(base_path) / "resources" / relative_path) 
    
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
        label_bg_global = "transparent" if self.dark_mode else "#FFFFFF" 
        
        frame_bg = "#2C2C2C" if self.dark_mode else "#FFFFFF"
        frame_border = "#3A3A3A" if self.dark_mode else "#E0E0E0" 

        button_bg = "#4A4A4A" if self.dark_mode else "#E0E0E0"
        button_text_color = text_color
        button_border = frame_border 
        button_hover_bg = "#5A5A5A" if self.dark_mode else "#D0D0D0"
        button_pressed_bg = "#6A6A6A" if self.dark_mode else "#C0C0C0"
        
        button_disabled_bg = "#404040" if self.dark_mode else "#E0E0E0"
        button_disabled_text_color = "#777777" if self.dark_mode else "#A0A0A0"
        button_disabled_border_color = "#505050" if self.dark_mode else "#C0C0C0"

        input_bg_global = "#3C3C3C" if self.dark_mode else "#FFFFFF"
        input_text_global = text_color 
        input_border_global = "#555555" if self.dark_mode else "#B0B0B0"
        input_readonly_bg_global = "#333333" if self.dark_mode else "#E9E9E9"

        scrollbar_bg = main_bg 
        scrollbar_handle_bg = "#666666" if self.dark_mode else "#BBBBBB"
        
        save_button_bg = "#0078D7"
        save_button_text_color = "#FFFFFF"
        save_button_border_color = "#006ABC" 
        save_button_hover_bg = "#005A9E"
        save_button_pressed_bg = "#004C87"

        self.central_widget_ref.setStyleSheet(f"background-color: {main_bg};")
        if hasattr(self, 'path_label_ref'): 
            self.path_label_ref.setStyleSheet(f"color: {text_color}; background-color: {label_bg_global}; padding: 1px;")


        self.setStyleSheet(f"""
            QMainWindow {{ 
                background-color: {main_bg}; 
            }}
            QWidget {{ 
                color: {text_color}; 
            }} 
            QLabel {{ 
                color: {text_color}; 
                background-color: {label_bg_global}; 
                padding: 1px; 
            }}
            
            QFrame#PathFrame, QFrame#ButtonFrame {{ 
                background-color: {frame_bg}; 
                border: 1px solid {frame_border};
                border-radius: 4px; 
            }}
            
            QPushButton {{ 
                background-color: {button_bg}; 
                color: {button_text_color};
                border: 1px solid {button_border}; 
                padding: 6px 12px; 
                border-radius: 3px; 
                min-height: 20px;
            }}
            QPushButton:hover {{ 
                background-color: {button_hover_bg}; 
            }}
            QPushButton:pressed {{ 
                background-color: {button_pressed_bg}; 
            }}
            QPushButton:disabled {{ 
                background-color: {button_disabled_bg}; 
                color: {button_disabled_text_color}; 
                border-color: {button_disabled_border_color};
            }}
            
            QLineEdit {{ 
                background-color: {input_bg_global}; 
                color: {input_text_global}; 
                border: 1px solid {input_border_global}; 
                padding: 4px; 
                border-radius: 3px;
            }}
            QLineEdit:read-only {{ 
                background-color: {input_readonly_bg_global}; 
            }}

            QScrollArea {{ 
                border: none; 
                background-color: {main_bg}; 
            }}
            QWidget#SettingsWidgetContainer {{ 
                background-color: {main_bg}; 
            }}

            QScrollBar:vertical {{ 
                background: {scrollbar_bg}; 
                width: 14px; 
                margin: 0px; 
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical {{ 
                background: {scrollbar_handle_bg}; 
                min-height: 25px; 
                border-radius: 6px; 
                margin: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ 
                border: none; 
                background: none; 
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ 
                background: none;
            }}

            QScrollBar:horizontal {{ 
                background: {scrollbar_bg}; 
                height: 14px; 
                margin: 0px; 
                border-radius: 7px;
            }}
            QScrollBar::handle:horizontal {{ 
                background: {scrollbar_handle_bg}; 
                min-width: 25px; 
                border-radius: 6px; 
                margin: 2px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ 
                border: none; 
                background: none; 
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ 
                background: none;
            }}
        """)
        
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {save_button_bg}; 
                color: {save_button_text_color}; 
                font-weight: bold;
                border: 1px solid {save_button_border_color}; 
                padding: 6px 12px; 
                border-radius: 3px;
            }}
            QPushButton:hover {{ 
                background-color: {save_button_hover_bg}; 
            }}
            QPushButton:pressed {{ 
                background-color: {save_button_pressed_bg}; 
            }}
        """)
        
        self.theme_button.setText("Switch to Light Mode" if self.dark_mode else "Switch to Dark Mode")

        if hasattr(self, 'tooltip') and self.tooltip: 
            self.tooltip.set_theme(self.dark_mode)
        
        for settings_key_widget in self.settings_widgets.values(): 
            settings_key_widget.update_theme(self.dark_mode)
        
        for header_widget in self.category_headers: 
            header_widget.update_theme(self.dark_mode)
    
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
                    self.tooltip.setText(self.SETTINGS_DESCRIPTIONS.get(key, "No description available.")) 
                    tooltip_size_hint = self.tooltip.sizeHint()

                    if tooltip_pos.x() + tooltip_size_hint.width() > screen_geometry.right() - 10: 
                        tooltip_pos.setX(label_global_pos.x() + settings_widget_instance.label.width() - tooltip_size_hint.width()) 
                    if tooltip_pos.y() + tooltip_size_hint.height() > screen_geometry.bottom() - 10: 
                        tooltip_pos.setY(label_global_pos.y() - tooltip_size_hint.height() - 3) 

                    self.tooltip.show_tooltip(self.SETTINGS_DESCRIPTIONS.get(key, "No description available."), tooltip_pos)
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
            home_dir / "Desktop", home_dir / "Documents", home_dir / "Downloads", 
            home_dir / "Projects", home_dir / "dev", home_dir / "workspace", home_dir,
            Path.cwd() 
        ]
        if sys.platform == "win32":
            onedrive_docs = Path(os.environ.get("OneDrive", "")) / "Documents"
            if onedrive_docs.exists(): popular_locations.append(onedrive_docs)
            popular_locations.extend([
                Path(os.environ.get("ProgramFiles", "C:/Program Files")),
                Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")),
                Path("C:/"), Path("D:/") 
            ])
        elif sys.platform == "darwin":
             popular_locations.append(home_dir / "Developer")
        
        try: 
            script_dir = Path(__file__).resolve().parent
            popular_locations.extend([script_dir, script_dir.parent, script_dir.parent.parent])
        except NameError: pass 

        valid_locations = sorted(list(set(p for p in popular_locations if p and p.exists() and p.is_dir())))
        logger.info(f"Scanning up to {len(valid_locations)} unique, valid base locations.")

        found_files = []
        mindcraft_dirs_patterns = ["mindcraft", "MindCraft", "Voyager", "voyager"] 
        
        for loc in valid_locations:
            try:
                for item in loc.iterdir(): 
                    if item.is_dir() and any(pattern in item.name for pattern in mindcraft_dirs_patterns):
                        settings_file = item / "settings.js"
                        if settings_file.is_file() and settings_file not in found_files:
                            logger.info(f"Found settings.js at: {settings_file}")
                            found_files.append(settings_file)
                if any(pattern in loc.name for pattern in mindcraft_dirs_patterns):
                    direct_settings_file = loc / "settings.js"
                    if direct_settings_file.is_file() and direct_settings_file not in found_files:
                        logger.info(f"Found settings.js directly at: {direct_settings_file}")
                        found_files.append(direct_settings_file)
            except PermissionError:
                logger.warning(f"Permission denied while scanning {loc}.")
            except Exception as e:
                logger.error(f"Error scanning {loc}: {e}")


        if not found_files: 
            logger.info("Performing broader search in home subdirectories (level 1)...")
            try:
                for item in home_dir.iterdir():
                    if item.is_dir():
                        if any(pattern in item.name for pattern in mindcraft_dirs_patterns):
                            settings_file = item / "settings.js"
                            if settings_file.is_file() and settings_file not in found_files:
                                logger.info(f"Found settings.js in home subdirectory: {settings_file}")
                                found_files.append(settings_file)
            except PermissionError:
                logger.warning(f"Permission denied while scanning {home_dir} subdirectories.")
            except Exception as e:
                logger.error(f"Error scanning home subdirectories: {e}")


        found_files = sorted(list(set(found_files))) 

        if found_files:
            logger.info(f"Scan complete. Found {len(found_files)} potential Mindcraft settings file(s).")
            if len(found_files) > 1:
                dialog = SelectInstallationDialog([str(p.resolve()) for p in found_files], self.dark_mode, self)
                if dialog.exec() and dialog.selected_path:
                    self.load_settings_file(Path(dialog.selected_path))
                else:
                    logger.info("User cancelled selection or closed dialog.")
                    QMessageBox.information(self, "Scan Results", "Multiple settings files found. No file selected.")
            else:
                self.load_settings_file(found_files[0])
        else:
            logger.warning("No Mindcraft installations found after scan.")
            QMessageBox.information(self, "Scan Complete", "No Mindcraft 'settings.js' found in common locations. Please use 'Browse' to locate it manually.")
    
    def browse_settings_file(self):
        start_dir = str(self.settings_path.parent if self.settings_path and self.settings_path.parent.exists() else Path.home())
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
                logger.debug(f"Content of 'profiles' array for comment parsing: '''{profiles_array_content[:200]}...'''")
                
                commented_profile_matches = re.findall(r'//\s*["\']([^"\']+)["\']', profiles_array_content)
                for cp in commented_profile_matches:
                    normalized_cp = cp.replace("\\\\", "\\").replace("\\/", "/") 
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
                    logger.info("Appending 'export default settings;' to suffix as it was not found.")
                    newline_prefix = "\n" if self.file_suffix and not self.file_suffix.endswith(("\n", "\r")) else ""
                    self.file_suffix = newline_prefix + self.file_suffix + "\nexport default settings;"
                elif "export default settings" not in self.file_suffix.lower() and \
                     "export default settings" in original_tail_content.lower():
                     if not self.file_suffix.strip():
                         self.file_suffix = "\nexport default settings;"


                logger.debug(f"File suffix determined:\n{self.file_suffix[:200]}...")

                try:
                    processed_str = settings_str_original
                    processed_str = re.sub(r"//.*", "", processed_str) 
                    processed_str = re.sub(r"/\*[\s\S]*?\*/", "", processed_str, flags=re.MULTILINE)
                    
                    processed_str = re.sub(r"\bundefined\b", "null", processed_str)
                    processed_str = re.sub(r"\bNaN\b", '"NaN"', processed_str) 
                    processed_str = re.sub(r"\bInfinity\b", '"Infinity"', processed_str) 
                                        
                    processed_str = re.sub(r'([{,]\s*)([a-zA-Z_]\w*)\s*:', r'\1"\2":', processed_str)
                    processed_str = re.sub(r'(\{\s*)([a-zA-Z_]\w*)\s*:', r'\1"\2":', processed_str) 
                    
                    processed_str = processed_str.replace("'", '"')
                    
                    processed_str = re.sub(r',(\s*[}\]])', r'\1', processed_str)
                                        
                    self.settings = json.loads(processed_str)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Primary JSON parsing for active settings failed: {e}. Attempting fallback parser.")
                    self.settings = {} 
                    key_pattern_orig = r'(?:^|\s|,)(?:"([\w\-$]+)"|\'([\w\-$]+)\'|([\w\-$]+))\s*:'
                    
                    fallback_str_base_active = re.sub(r"//.*", "", settings_str_original)
                    fallback_str_base_active = re.sub(r"/\*[\s\S]*?\*/", "", fallback_str_base_active, flags=re.MULTILINE)

                    matches = list(re.finditer(key_pattern_orig, fallback_str_base_active))
                    
                    for i, key_match_obj in enumerate(matches):
                        key = next(g for g in key_match_obj.groups() if g is not None)
                        val_start_pos = key_match_obj.end() 

                        val_end_pos = len(fallback_str_base_active)
                        if i + 1 < len(matches):
                            next_key_match_obj = matches[i+1]
                            val_end_pos = next_key_match_obj.start() 
                        else: 
                            pass


                        value_str_raw = fallback_str_base_active[val_start_pos:val_end_pos].strip()
                        
                        if value_str_raw.endswith((',', ';')): value_str_raw = value_str_raw[:-1].strip()
                        if value_str_raw.endswith(','):
                             temp_strip = value_str_raw[:-1].strip()
                             if fallback_str_base_active[val_start_pos + len(temp_strip) + 1:].strip().startswith('}'):
                                 value_str_raw = temp_strip


                        value = None 
                        if value_str_raw.lower() == 'true': value = True
                        elif value_str_raw.lower() == 'false': value = False
                        elif value_str_raw.lower() == 'null' or value_str_raw.lower() == 'undefined': value = None
                        elif (value_str_raw.startswith('"') and value_str_raw.endswith('"')) or \
                             (value_str_raw.startswith("'") and value_str_raw.endswith("'")):
                            try: 
                                value = json.loads(value_str_raw.replace("'", '"')) 
                            except json.JSONDecodeError: value = value_str_raw[1:-1] 
                        elif value_str_raw.startswith('[') and value_str_raw.endswith(']'):
                            try: 
                                value = json.loads(value_str_raw.replace("'", '"'))
                            except json.JSONDecodeError: 
                                logger.warning(f"Fallback couldn't parse list for key '{key}': {value_str_raw}")
                                value = [] 
                        elif value_str_raw.isdigit() or (value_str_raw.startswith('-') and value_str_raw[1:].isdigit()):
                            value = int(value_str_raw)
                        else: 
                            value = value_str_raw
                        self.settings[key] = value
                    logger.info(f"Fallback parser loaded {len(self.settings)} active settings.")

                logger.info(f"Successfully processed active settings from {file_path}. Total active settings: {len(self.settings)}")
                self.settings_path = file_path
                self.path_input.setText(str(file_path.resolve())) 
                self.display_settings()
                self.reload_button.setEnabled(True)
                self.save_button.setEnabled(True)

            else: 
                logger.error(f"Could not find active settings block 'const settings = {{...}}' in {file_path}")
                QMessageBox.critical(self, "Parse Error", f"Could not find the main settings block (e.g., 'const settings = {{...}}') in:\n{file_path}.\n\nThe file might be corrupted or not a Mindcraft settings file.")
                self.settings, self.settings_path = {}, None
                self.path_input.clear()
                self.display_settings() 
                self.reload_button.setEnabled(False)
                self.save_button.setEnabled(False)


        except Exception as e:
            logger.error(f"Critical error loading {file_path}: {e}", exc_info=True)
            QMessageBox.critical(self, "Load Error", f"Failed to load settings from:\n{file_path}\n\nError: {e}")
            self.settings, self.settings_path = {}, None
            self.path_input.clear()
            self.display_settings() 
            self.reload_button.setEnabled(False)
            self.save_button.setEnabled(False)
    
    def display_settings(self):
        while self.settings_layout.count():
            item = self.settings_layout.takeAt(0)
            if widget := item.widget(): widget.deleteLater()
            elif isinstance(item, QSpacerItem): self.settings_layout.removeItem(item) 
        
        self.settings_widgets.clear()
        self.category_headers.clear() 
        
        if not self.settings:
            no_settings_label = QLabel("No settings loaded or file is empty.\nUse 'Browse' or 'Scan Again'.")
            no_settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.settings_layout.addWidget(no_settings_label)
            self.settings_layout.addStretch(1) 
            return

        categories = {
            "Connection": ["minecraft_version", "host", "port", "auth"],
            "Mind Server": ["host_mindserver", "mindserver_host", "mindserver_port"],
            "Agent Configuration": ["base_profile", "profiles", "load_memory", "init_message", "only_chat_with", "speak", "language"],
            "Features & Safety": ["show_bot_views", "allow_insecure_coding", "allow_vision", "blocked_actions"],
            "Performance & Limits": ["code_timeout_mins", "relevant_docs_count", "max_messages", "num_examples", "max_commands"],
            "Logging & Behavior": ["verbose_commands", "narrate_behavior", "chat_bot_messages", "log_all_prompts"]
        }
        
        displayed_keys = set()
        for category_title, keys_in_cat in categories.items():
            relevant_keys_in_category = [k for k in keys_in_cat if k in self.settings]
            if relevant_keys_in_category:
                header = CategoryHeader(category_title, self.dark_mode)
                self.settings_layout.addWidget(header)
                self.category_headers.append(header)
                
                for key in relevant_keys_in_category: 
                    desc = self.SETTINGS_DESCRIPTIONS.get(key, "No description available.")
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
                desc = self.SETTINGS_DESCRIPTIONS.get(key, "No description available.")
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
                logger.error(f"Error getting value for setting '{key}': {e}", exc_info=True)
                QMessageBox.critical(self, "Input Error", f"Invalid value for setting '{key}'. Please correct and try again.\nError: {e}")
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

        except Exception as e:
            logger.error(f"Failed to save settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Save Error", f"Could not save settings to file:\n{self.settings_path}\n\nError: {e}")
    
    def reload_settings(self):
        if self.settings_path and self.settings_path.is_file():
            logger.info(f"Reloading settings from: {self.settings_path}")
            self.load_settings_file(self.settings_path) 
        elif self.settings_path: 
            QMessageBox.warning(self, "Reload Error", f"File not found: {self.settings_path}.\nPlease browse for the file again or use 'Scan Again'.")
            self.path_input.clear()
            self.settings = {}
            self.settings_path = None
            self.display_settings()
            self.reload_button.setEnabled(False)
            self.save_button.setEnabled(False)
        else: 
            QMessageBox.information(self, "Reload Info", "No settings file is currently loaded to reload.")

def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion") 
        
        try:
            app_icon_path = MindcraftSettingsEditor.resource_path("mindcraft_icon.ico")
            if Path(app_icon_path).exists():
                app.setWindowIcon(QIcon(app_icon_path))
                logger.info("Application-level icon set.")
            else:
                logger.warning(f"Application-level icon file not found: {app_icon_path}")
        except Exception as e:
            logger.warning(f"Could not set application-level icon: {e}")

        default_font = QFont()
        if sys.platform == "win32": 
            default_font = QFont("Segoe UI", 9)
        elif sys.platform == "darwin": 
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
        error_message = f"A critical error occurred and the application must close:\n\n{type(e).__name__}: {e}"
        print(error_message, file=sys.stderr) 
        
        try:
            if QApplication.instance():
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle("Critical Application Error")
                msg_box.setText(error_message)
                msg_box.exec()
            else:
                print("QApplication could not be initialized. Error details logged or printed above.", file=sys.stderr)
        except Exception as q_msg_e: 
            print(f"Failed to show critical error QMessageBox: {q_msg_e}", file=sys.stderr)
        sys.exit(1) 

if __name__ == "__main__":
    print("Starting Mindcraft Settings Editor...")
    print("Check the console output or application logs for detailed information and diagnostics.")
    main()
