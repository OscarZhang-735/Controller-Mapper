# coding: utf-8
import time
import pygame
import pyautogui
import ctypes
import json
import sys
import os
import psutil

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QApplication, QGridLayout, QWidget, QDialog, QMessageBox, QHBoxLayout, QSystemTrayIcon, \
    QPushButton
from qfluentwidgets import (MessageBox, setTheme, Theme, SubtitleLabel, LineEdit, PushButton, BodyLabel,
                            HorizontalSeparator, PrimaryPushButton, MessageBoxBase, SwitchButton, ComboBox,
                            DoubleSpinBox, SystemTrayMenu, Action, CheckBox)
from qfluentwidgets import FluentIcon as FIF

ICON = "icon.png"


class Utils:
    class Data:
        @staticmethod
        def json_read(path):
            with open(path, 'r') as f:
                data = json.load(f)
            return data

        @staticmethod
        def json_write(path, data):
            with open(path, "w") as f:
                json.dump(data, f)

        @staticmethod
        def is_admin():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except Exception:
                return False

        @staticmethod
        def instance_conflict():
            current_process = psutil.Process()
            for process in psutil.process_iter(['pid', 'name']):
                if process.info['name'] == current_process.name() and process.info['pid'] != current_process.pid:
                    return True
            return False

    @staticmethod
    def press_key(keys):
        if "+" in keys and len(keys) > 1:
            # Combo
            key_list = keys.split("+")
            print("Key Combo: ", key_list)
            for key in key_list:
                pyautogui.keyDown(key)
                time.sleep(0.01)
            time.sleep(0.01)
            for key in key_list[::-1]:
                pyautogui.keyUp(key)
                time.sleep(0.01)
        else:
            # Single key
            print("Key Single: ", keys)
            pyautogui.press(keys)


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        QSystemTrayIcon.__init__(self, parent)
        self.parent = parent
        self.setIcon(QIcon("icon.png"))
        self.menu = SystemTrayMenu(parent=parent)
        self.menu.addActions([
            Action("Open", self, triggered=self.show_parent),
            Action("Start Mapping", self, triggered=lambda: parent.mapping_status.setChecked(True)),
            Action("Quit", self, triggered=sys.exit),
            Action("About", self, triggered=parent.about)
        ])
        self.setContextMenu(self.menu)
        self.activated.connect(self.on_click)

    def on_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_parent()
        elif reason == QSystemTrayIcon.Context:
            self.menu.exec_(QCursor.pos())

    def show_parent(self):
        self.parent.show()
        self.parent.setWindowState(self.parent.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)


class TransparentWindow(QWidget):
    # Abandoned func
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Status Bar')
        self.setWindowOpacity(0.25)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet('background-color: rgba(0, 0, 0, 100);')
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setSpacing(10)
        self.statusLabel = BodyLabel("", self)
        self.closeBtn = QPushButton(self)
        self.closeBtn.setStyleSheet('background-color: rgba(255, 255, 255, 0); border: none; color: white;')
        # self.closeBtn.setIcon(QIcon("resources/icons/close.png"))
        self.closeBtn.setFixedWidth(20)
        self.closeBtn.setFixedHeight(20)
        self.mappingSwitch = SwitchButton(self)
        self.mappingSwitch.setOnText("")
        self.mappingSwitch.setOffText("")

        self.mainLayout.addWidget(self.closeBtn, 0)
        self.mainLayout.addWidget(self.mappingSwitch, 1)
        self.mainLayout.addWidget(self.statusLabel, 2)

        self.closeBtn.clicked.connect(self.hide)
        self.mappingSwitch.checkedChanged.connect(self.mapping_ctrl)
        self.setFixedHeight(50)
        self.move(500, 500)
        # self.show()

    def mapping_ctrl(self):
        if self.mappingSwitch.isChecked():
            self.parent.mapping_status.setChecked(True)
        else:
            self.parent.stop_mapping()


class PresetsConfigWidget(QDialog):
    class EditNameMessageBox(MessageBoxBase):
        def __init__(self, parent=None, place_holder="Preset Name", text=None):
            super().__init__(parent=parent)
            self.setWindowTitle("Name")
            self.nameLine = LineEdit(self)
            self.nameLine.setPlaceholderText(place_holder)
            if text:
                self.nameLine.setText(text)
            self.nameLine.setClearButtonEnabled(True)
            self.nameLine.setMinimumWidth(150)
            self.viewLayout.addWidget(self.nameLine)
            self.setFixedWidth(parent.width())

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preset Configuration")
        self.setWhatsThis("Create and manage your own mapping presets.")
        self.setWindowIcon(QIcon(ICON))
        self.config = Utils.Data.json_read("config.json")
        self.current_config_index = 0
        self.mainGridLayout = QGridLayout(self)
        self.mainGridLayout.setContentsMargins(20, 20, 20, 20)
        self.mainGridLayout.setSpacing(10)

        self.titleLabel = SubtitleLabel("Preset Configuration", self)
        self.titleLabel.setFixedHeight(30)
        self.presetsComboBox = ComboBox(self)
        self.addPresetBtn = PrimaryPushButton("New Preset", self)
        self.addPresetBtn.setIcon(FIF.ADD_TO)
        self.seperator1 = HorizontalSeparator(self)
        self.bindingTitle = BodyLabel("Controller-Keyboard Binding", self)
        self.bindingTitle.setFixedHeight(20)
        self.buttonALabel = BodyLabel("A", self)
        self.buttonBLabel = BodyLabel("B", self)
        self.buttonXLabel = BodyLabel("X", self)
        self.buttonYLabel = BodyLabel("Y", self)
        self.buttonLBLabel = BodyLabel("LB", self)
        self.buttonRBLabel = BodyLabel("RB", self)
        self.buttonLSLabel = BodyLabel("LS", self)
        self.buttonRSLabel = BodyLabel("RS", self)
        self.buttonLTLabel = BodyLabel("LT", self)
        self.buttonRTLabel = BodyLabel("RT", self)
        self.buttonWinLabel = BodyLabel("VW", self)
        self.buttonMenuLabel = BodyLabel("MN", self)
        self.buttonALineEdit = LineEdit(self)
        self.buttonBLineEdit = LineEdit(self)
        self.buttonXLineEdit = LineEdit(self)
        self.buttonYLineEdit = LineEdit(self)
        self.buttonLBLineEdit = LineEdit(self)
        self.buttonRBLineEdit = LineEdit(self)
        self.buttonLSLineEdit = LineEdit(self)
        self.buttonRSLineEdit = LineEdit(self)
        self.buttonLTLineEdit = LineEdit(self)
        self.buttonRTLineEdit = LineEdit(self)
        self.buttonVWLineEdit = LineEdit(self)
        self.buttonMNLineEdit = LineEdit(self)

        self.resetBtn = PushButton("Reset", self)
        self.resetBtn.setIcon(FIF.RETURN)
        self.renameBtn = PushButton("Rename", self)
        self.renameBtn.setIcon(FIF.EDIT)
        self.deleteBtn = PushButton("Delete", self)
        self.deleteBtn.setIcon(FIF.DELETE)
        self.seperator2 = HorizontalSeparator(self)
        self.applyBtn = PrimaryPushButton("Apply", self)
        self.cancelBtn = PushButton("Cancel", self)

        self.optionBtnLayout = QHBoxLayout(self)
        self.optionBtnLayout.addWidget(self.applyBtn)
        self.optionBtnLayout.addWidget(self.cancelBtn)

        self.mainGridLayout.addWidget(self.titleLabel, 0, 0, 1, 6)
        self.mainGridLayout.addWidget(self.presetsComboBox, 1, 0, 1, 6)
        self.mainGridLayout.addWidget(self.addPresetBtn, 2, 0, 1, 6)
        self.mainGridLayout.addWidget(self.seperator1, 3, 0, 1, 6)
        self.mainGridLayout.addWidget(self.bindingTitle, 4, 0, 1, 6)

        self.mainGridLayout.addWidget(self.buttonALabel, 5, 0, 1, 1)
        self.mainGridLayout.addWidget(self.buttonALineEdit, 5, 1, 1, 1)
        self.mainGridLayout.addWidget(self.buttonBLabel, 5, 2, 1, 1)
        self.mainGridLayout.addWidget(self.buttonBLineEdit, 5, 3, 1, 1)
        self.mainGridLayout.addWidget(self.buttonXLabel, 5, 4, 1, 1)
        self.mainGridLayout.addWidget(self.buttonXLineEdit, 5, 5, 1, 1)
        self.mainGridLayout.addWidget(self.buttonYLabel, 6, 0, 1, 1)
        self.mainGridLayout.addWidget(self.buttonYLineEdit, 6, 1, 1, 1)
        self.mainGridLayout.addWidget(self.buttonLBLabel, 6, 2, 1, 1)
        self.mainGridLayout.addWidget(self.buttonLBLineEdit, 6, 3, 1, 1)
        self.mainGridLayout.addWidget(self.buttonRBLabel, 6, 4, 1, 1)
        self.mainGridLayout.addWidget(self.buttonRBLineEdit, 6, 5, 1, 1)
        self.mainGridLayout.addWidget(self.buttonLSLabel, 7, 0, 1, 1)
        self.mainGridLayout.addWidget(self.buttonLSLineEdit, 7, 1, 1, 1)
        self.mainGridLayout.addWidget(self.buttonRSLabel, 7, 2, 1, 1)
        self.mainGridLayout.addWidget(self.buttonRSLineEdit, 7, 3, 1, 1)
        self.mainGridLayout.addWidget(self.buttonLTLabel, 7, 4, 1, 1)
        self.mainGridLayout.addWidget(self.buttonLTLineEdit, 7, 5, 1, 1)
        self.mainGridLayout.addWidget(self.buttonRTLabel, 8, 0, 1, 1)
        self.mainGridLayout.addWidget(self.buttonRTLineEdit, 8, 1, 1, 1)
        self.mainGridLayout.addWidget(self.buttonWinLabel, 8, 2, 1, 1)
        self.mainGridLayout.addWidget(self.buttonVWLineEdit, 8, 3, 1, 1)
        self.mainGridLayout.addWidget(self.buttonMenuLabel, 8, 4, 1, 1)
        self.mainGridLayout.addWidget(self.buttonMNLineEdit, 8, 5, 1, 1)

        self.mainGridLayout.addWidget(self.resetBtn, 9, 0, 1, 2)
        self.mainGridLayout.addWidget(self.renameBtn, 9, 2, 1, 2)
        self.mainGridLayout.addWidget(self.deleteBtn, 9, 4, 1, 2)
        self.mainGridLayout.addWidget(self.seperator2, 10, 0, 1, 6)
        self.mainGridLayout.addLayout(self.optionBtnLayout, 11, 0, 1, 6)

        self.presetsComboBox.currentIndexChanged.connect(lambda: self.fill_bindings(self.presetsComboBox.currentText()))
        self.addPresetBtn.clicked.connect(self.new_preset)
        self.resetBtn.clicked.connect(self.reset)
        self.renameBtn.clicked.connect(self.rename_preset)
        self.deleteBtn.clicked.connect(self.delete_preset)
        self.applyBtn.clicked.connect(self.apply)
        self.cancelBtn.clicked.connect(self.close)

        self.setFixedSize(430, 530)

        self.initUI()

    def initUI(self):
        for ps in self.config:
            self.presetsComboBox.addItem(ps)
        self.presetsComboBox.setCurrentIndex(0)
        self.fill_bindings("default")

    def fill_bindings(self, preset):
        self.buttonALineEdit.setText(self.config[preset]["0"])
        self.buttonBLineEdit.setText(self.config[preset]["1"])
        self.buttonXLineEdit.setText(self.config[preset]["2"])
        self.buttonYLineEdit.setText(self.config[preset]["3"])
        self.buttonLBLineEdit.setText(self.config[preset]["4"])
        self.buttonRBLineEdit.setText(self.config[preset]["5"])
        self.buttonVWLineEdit.setText(self.config[preset]['6'])
        self.buttonMNLineEdit.setText(self.config[preset]['7'])
        self.buttonLSLineEdit.setText(self.config[preset]["8"])
        self.buttonRSLineEdit.setText(self.config[preset]["9"])
        self.buttonLTLineEdit.setText(self.config[preset]["-1"])
        self.buttonRTLineEdit.setText(self.config[preset]["-2"])

    def new_preset(self):
        NN = self.EditNameMessageBox(self)
        if NN.exec():
            name = NN.nameLine.text()
            if len(name) == 0:
                w = MessageBox("Warning", "Name cannot be empty", self)
                w.cancelButton.hide()
                if w.exec():
                    pass
                return False
            for n in self.config:
                if name == n:
                    w = MessageBox("Warning", "This name is occupied", self)
                    w.cancelButton.hide()
                    if w.exec():
                        pass
                    return False
        else:
            return False
        print("New name:", name)
        default_dict = {
            "0": "enter",
            "1": "backspace",
            "2": "",
            "3": "",
            "4": "",
            "5": "",
            "8": "",
            "9": ""
        }
        self.config[name] = default_dict
        print(self.config)
        self.fill_bindings("default")
        self.presetsComboBox.addItem(name)
        self.presetsComboBox.setCurrentText(name)

    def delete_preset(self):
        if self.presetsComboBox.currentText() != "default":
            del self.config[self.presetsComboBox.currentText()]
        else:
            w = MessageBox("Warning", "Default preset cannot be deleted.", self)
            w.cancelButton.hide()
            if w.exec():
                pass
            return False

        self.presetsComboBox.removeItem(self.presetsComboBox.currentIndex())
        self.presetsComboBox.setCurrentText("default")
        self.fill_bindings("default")
        w = MessageBox("Notification", "Success.", self)
        w.cancelButton.hide()
        if w.exec():
            pass

    def rename_preset(self):
        rn = self.EditNameMessageBox(self, text=self.presetsComboBox.currentText())
        if rn.exec():
            newName = rn.nameLine.text()
            if len(newName) == 0:
                w = MessageBox("Warning", "Name cannot be empty", self)
                w.cancelButton.hide()
                if w.exec():
                    pass
                return False
            for name in self.config:
                if newName == name:
                    w = MessageBox("Warning", "This name is occupied.", self)
                    w.cancelButton.hide()
                    if w.exec():
                        pass
                    return False
            self.config[newName] = self.config.pop(self.presetsComboBox.currentText())
            self.presetsComboBox.clear()
            for item in self.config:
                self.presetsComboBox.addItem(item)
            self.presetsComboBox.setCurrentText(newName)

    def reset(self):
        self.fill_bindings(self.presetsComboBox.currentText())

    def apply(self):
        name = self.presetsComboBox.currentText()
        self.config[name]["0"] = self.buttonALineEdit.text()
        self.config[name]["1"] = self.buttonBLineEdit.text()
        self.config[name]["2"] = self.buttonXLineEdit.text()
        self.config[name]["3"] = self.buttonYLineEdit.text()
        self.config[name]["4"] = self.buttonLBLineEdit.text()
        self.config[name]["5"] = self.buttonRBLineEdit.text()
        self.config[name]["6"] = self.buttonVWLineEdit.text()
        self.config[name]["7"] = self.buttonMNLineEdit.text()
        self.config[name]["8"] = self.buttonLSLineEdit.text()
        self.config[name]["9"] = self.buttonRSLineEdit.text()
        self.config[name]["-1"] = self.buttonLTLineEdit.text()
        self.config[name]["-2"] = self.buttonRTLineEdit.text()
        Utils.Data.json_write("config.json", self.config)
        self.close()


class MainWidget(QWidget):
    class IntervalSettingMessageBox(MessageBoxBase):
        def __init__(self, curr_value, parent=None):
            super().__init__(parent=parent)
            self.value = curr_value
            self.setWindowTitle("Interval Setting")
            self.titleLabel = SubtitleLabel("Interval Setting", self)
            self.titleLabel.setFixedWidth(200)
            self.intervalBox = DoubleSpinBox(self)
            self.intervalBox.setMinimum(0.01)
            self.intervalBox.setMaximum(0.5)
            self.intervalBox.setSingleStep(0.01)
            self.intervalBox.setValue(self.value)
            self.pollingRateLabel = BodyLabel(self)
            self.viewLayout.addWidget(self.titleLabel)
            self.viewLayout.addWidget(self.intervalBox)
            self.viewLayout.addWidget(self.pollingRateLabel)

            self.intervalBox.valueChanged.connect(self.polling_rate_calculate)

            self.polling_rate_calculate()

        def polling_rate_calculate(self):
            pr = 1 / self.intervalBox.value()
            content = f"Polling Rate: {format(pr, ".2f")} Hz"
            self.pollingRateLabel.setText(content)
            print(content)

    def __init__(self):
        super().__init__()
        self._running = False
        self.interval = 0.05
        self.setWindowTitle("Controller Mapper")
        self.setWindowIcon(QIcon(ICON))
        self.config = Utils.Data.json_read("config.json")
        self.settingWidget = PresetsConfigWidget()
        self.systemTrayIcon = SystemTrayIcon(self)
        self.statusBar = TransparentWindow(self)
        self.main_layout = QGridLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        self.title_label = SubtitleLabel("Controller Mapper", self)
        self.title_label.setFixedHeight(20)
        self.controller_status = BodyLabel(self)
        self.detect_controller_btn = PushButton("Detect Controller", self)
        self.detect_controller_btn.setIcon(FIF.GAME)
        self.mapping_status = SwitchButton(self)
        self.mapping_status.setOnText("Enable Mapping")
        self.mapping_status.setOffText("Disable Mapping")
        self.mapping_action = BodyLabel(self)
        self.preset_box = ComboBox(self)
        self.preset_setting_btn = PushButton("Presets", self)
        self.preset_setting_btn.setIcon(FIF.SETTING)
        self.refresh_btn = PushButton("Refresh", self)
        self.refresh_btn.setIcon(FIF.UPDATE)
        self.rate_btn = PushButton("Interval", self)
        self.rate_btn.setIcon(FIF.SPEED_MEDIUM)
        self.exit_on_close_check = CheckBox("E.O.C.", self)

        self.main_layout.addWidget(self.title_label, 1, 1, 1, 4)
        self.main_layout.addWidget(self.controller_status, 2, 1, 1, 4)
        self.main_layout.addWidget(self.detect_controller_btn, 3, 1, 1, 4)
        self.main_layout.addWidget(self.mapping_status, 4, 1, 1, 2)
        self.main_layout.addWidget(self.preset_box, 4, 3, 1, 2)
        self.main_layout.addWidget(self.mapping_action, 5, 1, 1, 4)
        self.main_layout.addWidget(self.preset_setting_btn, 6, 1, 1, 1)
        self.main_layout.addWidget(self.refresh_btn, 6, 2, 1, 1)
        self.main_layout.addWidget(self.rate_btn, 6, 3, 1, 1)
        self.main_layout.addWidget(self.exit_on_close_check, 6, 4, 1, 1)

        self.detect_controller_btn.clicked.connect(self.detect)
        self.mapping_status.checkedChanged.connect(self.mapping_control)
        self.preset_box.currentIndexChanged.connect(self.change_preset)
        self.refresh_btn.clicked.connect(self.refresh)
        self.preset_setting_btn.clicked.connect(self.presets_config)
        self.rate_btn.clicked.connect(self.interval_settings)
        self.init_ui()

        self.setFixedSize(500, 320)
        self.systemTrayIcon.show()

    def detect(self):
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            print("No Controller Detected")
            self.controller_status.setText("No Controller Detected")
            return False
        else:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            self.controller_status.setText(f"Controller Detected ({joystick.get_name()})")
            return True

    def init_ui(self):
        self.controller_status.setText("Detecting Controller...")
        self.mapping_status.setChecked(False)
        self.preset_box.clear()
        for preset in self.config:
            self.preset_box.addItem(preset)
        self.detect()

    def mapping_control(self):
        if self.mapping_status.isChecked():
            self.tray_action_update(True)
            self.statusBar.mappingSwitch.setChecked(True)
            button_mapping = {int(key): value for key, value in self.config[self.preset_box.currentText()].items()}
            self.start_mapping(button_mapping)
        else:
            self.tray_action_update(False)
            self.statusBar.mappingSwitch.setChecked(False)
            self.stop_mapping()

    def start_mapping(self, button_mapping):
        """

        :param button_mapping: {int: str}
        :return:
        """
        if not self.detect():
            self.mapping_status.setChecked(False)
            return False
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        self._running = True
        print("Mapping Preset:", button_mapping)
        print("Started Controller Mapping")
        self.set_status("Waiting...")
        self.mapping_status.setChecked(True)
        L_TRIGGER = False
        R_TRIGGER = False
        L_STICK_UP = False
        L_STICK_DOWN = False
        L_STICK_LEFT = False
        L_STICK_RIGHT = False

        while self._running:
            time.sleep(self.interval)

            for event in pygame.event.get():
                # Quit event detection
                if event.type == pygame.QUIT:
                    self._running = False

                # Button press input mapper (Customizable)
                elif event.type == pygame.JOYBUTTONDOWN:
                    print(event.button)
                    button = event.button
                    if button in button_mapping:
                        key = button_mapping[button]
                        Utils.press_key(key)
                        self.set_status(f"Pressed: Controller [{button}] ->> Keyboard [{key}]")

                # Button release input mapper
                elif event.type == pygame.JOYBUTTONUP:
                    button = event.button
                    if button in button_mapping:
                        key = button_mapping[button]
                        print(f"Released: Controller [{button}] ->> Keyboard [{key}]")
                        self.set_status(f"Waiting...")

                # D-Pad input mapper (Not customizable)
                elif event.type == pygame.JOYHATMOTION:
                    hat = event.hat
                    value = event.value
                    if hat == 0:
                        if value == (0, 0):
                            print("Released: D-pad")
                            self.set_status("Waiting...")
                        if value == (0, 1):
                            pyautogui.press("up")
                            self.set_status("Pressed: Controller [HAT_UP] ->> Keyboard [UP]")
                        elif value == (0, -1):
                            pyautogui.press("down")
                            self.set_status("Pressed: Controller [HAT_DOWN] ->> Keyboard [DOWN]")
                        elif value == (-1, 0):
                            pyautogui.press("left")
                            self.set_status("Pressed: Controller [HAT_LEFT] ->> Keyboard [LEFT]")
                        elif value == (1, 0):
                            pyautogui.press("right")
                            self.set_status("Pressed: Controller [HAT_RIGHT] ->> Keyboard [RIGHT]")

                # Joystick and Trigger input mapper
                elif event.type == pygame.JOYAXISMOTION:
                    axis = event.axis
                    value = event.value

                    # Left trigger mapping (Customizable)
                    if axis == 4:
                        if value >= 0.9 and not L_TRIGGER:
                            key = button_mapping[-1]
                            self.set_status(f"Controller [Left-Trigger Down] ->> Keyboard [{key}]")
                            Utils.press_key(key)
                            L_TRIGGER = True

                        elif value <= -0.9:
                            print("Left Trigger Released")
                            self.set_status("Waiting...")
                            L_TRIGGER = False

                    # Right trigger mapping (Customizable)
                    if axis == 5:
                        if value >= 0.9 and not R_TRIGGER:
                            key = button_mapping[-2]
                            self.set_status(f"Controller [Right-Trigger Down] ->> Keyboard [{key}]")
                            Utils.press_key(key)
                            R_TRIGGER = True
                        elif value <= -0.9:
                            print("Right Trigger Released")
                            self.set_status("Waiting...")
                            R_TRIGGER = False

                    # Left stick y-axis mapping (Not Customizable)
                    if axis == 1:
                        if value <= -0.8 and not L_STICK_UP:
                            self.set_status("Pressed: Controller [LEFT_STICK_UP] ->> Keyboard [UP]")
                            pyautogui.press("up")
                            L_STICK_UP = True
                        elif value >= 0.8 and not L_STICK_DOWN:
                            self.set_status("Pressed: Controller [LEFT_STICK_DOWN] ->> Keyboard [DOWN]")
                            pyautogui.press("down")
                            L_STICK_DOWN = True
                        elif -0.3 < value < 0.3:
                            L_STICK_UP = False
                            L_STICK_DOWN = False

                    # Left stick x-axis mapping (Not customizable)
                    if axis == 0:
                        if value <= -0.8 and not L_STICK_LEFT:
                            self.set_status("Pressed: Controller [LEFT_STICK_LEFT] ->> Keyboard [LEFT]")
                            pyautogui.press("left")
                            L_STICK_LEFT = True
                        elif value >= 0.8 and not L_STICK_RIGHT:
                            self.set_status("Pressed: Controller [LEFT_STICK_RIGHT] ->> Keyboard [RIGHT]")
                            pyautogui.press("right")
                            L_STICK_RIGHT = True
                        elif -0.3 < value < 0.3:
                            L_STICK_LEFT = False
                            L_STICK_RIGHT = False

    def refresh(self):
        self.config = Utils.Data.json_read("config.json")
        self.stop_mapping()
        self.init_ui()

    def about(self):
        content = f"""
        Controller-Keyboard Mapper
        A convenient tool built with PyQt-Fluent-Widgets
        Author: Rinne
        Version: 1.1.0
        Last-Update: 2024.08.02
        All copyrights reserved.
        """
        abt = MessageBox("About", content, self)
        abt.cancelButton.hide()
        if abt.exec():
            pass

    def set_status(self, text):
        print(text)
        self.statusBar.statusLabel.setText(text)
        self.mapping_action.setText(text)

    def interval_settings(self):
        rs = self.IntervalSettingMessageBox(self.interval, self)
        if rs.exec():
            self.interval = rs.intervalBox.value()
            if self.interval <= 0.03:
                self.rate_btn.setIcon(FIF.SPEED_HIGH)
            elif 0.03 < self.interval <= 0.2:
                self.rate_btn.setIcon(FIF.SPEED_MEDIUM)
            elif self.interval > 0.2:
                self.rate_btn.setIcon(FIF.SPEED_OFF)

    def presets_config(self):
        self.mapping_status.setChecked(False)
        self.settingWidget.exec()

    def stop_mapping(self):
        print("Stopped Controller Mapping")
        self._running = False
        self.mapping_action.setText("Mapper Disabled")
        self.statusBar.statusLabel.setText("Mapper Disabled")
        self.mapping_status.setChecked(False)

    def tray_action_update(self, status):
        self.systemTrayIcon.menu.clear()
        if status:
            self.systemTrayIcon.menu.addActions([
                Action("Open", self, triggered=self.systemTrayIcon.show_parent),
                Action("Stop Mapping", self, triggered=self.stop_mapping),
                Action("About", self, triggered=self.about),
                Action("Quit", self, triggered=sys.exit)

            ])
        else:
            self.systemTrayIcon.menu.addActions([
                Action("Open", self, triggered=self.systemTrayIcon.show_parent),
                Action("Start Mapping", self, triggered=lambda: self.mapping_status.setChecked(True)),
                Action("About", self, triggered=self.about),
                Action("Quit", self, triggered=sys.exit)
            ])

    def change_preset(self):
        # status = self.mapping_status.isChecked()
        self.stop_mapping()
        # time.sleep(0.05)
        # self.mapping_status.setChecked(status)

    def closeEvent(self, event):
        flag = self.exit_on_close_check.isChecked()
        if flag:
            self.stop_mapping()
            self.close()
            event.accept()
            sys.exit()
        else:
            event.ignore()
            self.hide()


def launch_check():
    if not Utils.Data.is_admin():
        if r"Program Files" in os.getcwd():
            QMessageBox.warning(None, "Admin Required",
                                "Admin permission is required for this program since it's located in a system folder")
            sys.exit()

    if Utils.Data.instance_conflict():
        QMessageBox.warning(None, "Multiple Instances", "Another instance is running.")
        sys.exit()


def setup():
    if not os.path.exists("config.json"):
        f = open("config.json", "w")
        f.close()
        init_dict = {
            "default": {
                "0": "enter",
                "1": "esc",
                "2": "space",
                "3": "tab",
                "4": "",
                "5": "",
                "6": "",
                "7": "",
                "8": "",
                "9": "",
                "-1": "",
                "-2": ""
            }
        }
        Utils.Data.json_write("config.json", init_dict)


if __name__ == '__main__':
    setup()
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    setTheme(Theme.LIGHT)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    # Disable Launch-Check when testing in PyCharm

    # launch_check()
    w = MainWidget()
    w.show()
    app.exec_()
