from PySide6.QtWidgets import (
    QMainWindow, QLabel, QSpinBox, QTimeEdit,
    QDialog, QVBoxLayout, QHBoxLayout, QDoubleSpinBox, QDialogButtonBox, QPushButton, QSlider, QTabWidget, QWidget
)
from PySide6.QtCore import Qt


class DanMuConfig:
    speed_multiplier = 1.0
    font_size_multiplier = 1.0
    display_area_multiplier = 1.0
    max_danmu_count = 300
    

def settings_dialog(window: QMainWindow):
    dialog = QDialog(window)
    dialog.setWindowTitle("Settings")
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.resize(400, 300)
    
    danmu_machine = window.danmu_machine

    # Create tabs
    tabs = QTabWidget()
    general_tab  = QWidget()
    about_tab = QWidget()
    
    general_layout = QVBoxLayout(dialog)
    
    # Maximum Danmu
    max_danmu_label = QLabel("弹幕数量:")
    max_danmu_selector = QSlider(Qt.Horizontal)
    max_danmu_selector.setRange(50, 500)
    max_danmu_selector.setSingleStep(50)
    max_danmu_selector.setValue(danmu_machine.config.max_danmu_count)
    general_layout.addWidget(max_danmu_label)
    general_layout.addWidget(max_danmu_selector)
    
    # Display Area
    display_area_label = QLabel("Display Area:")
    display_area_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
    display_area_SpinBox = QSpinBox()
    display_area_SpinBox.setRange(10, 100)
    display_area_SpinBox.setValue(danmu_machine.config.display_area_multiplier)
    general_layout.addWidget(display_area_label)
    general_layout.addWidget(display_area_SpinBox)

    # Font size
    font_size_label = QLabel("Font Size:")
    font_size_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
    font_size_doubleSpinBox = QDoubleSpinBox()
    font_size_doubleSpinBox.setRange(0.1, 4)
    font_size_doubleSpinBox.setValue(danmu_machine.config.font_size_multiplier)
    font_size_doubleSpinBox.setSingleStep(0.1)
    font_size_doubleSpinBox.setDecimals(1)
    # font_size_doubleSpinBox.valueChanged.connect(lambda value: window.config.font_size_multiplier = value)
    general_layout.addWidget(font_size_label)
    general_layout.addWidget(font_size_doubleSpinBox)
    
    # Speed
    speed_label = QLabel("Speed:")
    speed_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
    speed_doubleSpinBox = QDoubleSpinBox()
    speed_doubleSpinBox.setRange(0.1, 4)
    speed_doubleSpinBox.setValue(danmu_machine.config.speed_multiplier)
    speed_doubleSpinBox.setSingleStep(0.1)
    speed_doubleSpinBox.setDecimals(1)
    # speed_doubleSpinBox.valueChanged.connect(lambda value: window.config.speed_multiplier = value)
    general_layout.addWidget(speed_label)
    general_layout.addWidget(speed_doubleSpinBox)
    
    # playback controls
    playback_label = QLabel("Playback:")
    general_layout.addWidget(playback_label)
    
    # Rewind and fast-forward buttons
    current_time_label = QLabel(f"Current Time: {danmu_machine.get_current_time():.2f}s")
    total_time_label = QLabel(f"Total Time: {danmu_machine.get_total_time():.2f}s")
    
    def playback_action(action):
        if action == "rewind":
            danmu_machine.rewind()
        elif action == "play_pause":
            danmu_machine.play_pause()
        elif action == "fast_forward":
            danmu_machine.fast_forward()
        current_time_label.setText(f"Current Time: {danmu_machine.get_current_time():.2f}s")
    
    
    playback_layout = QHBoxLayout()
    rewind_button = QPushButton("Rewind")
    rewind_button.clicked.connect(lambda: playback_action("rewind"))
    play_pause_button = QPushButton("Play/Pause")
    play_pause_button.clicked.connect(lambda: playback_action("play_pause"))
    fast_forward_button = QPushButton("Fast Forward")
    fast_forward_button.clicked.connect(lambda: playback_action("fast_forward"))
    
    playback_layout.addWidget(rewind_button)
    playback_layout.addWidget(play_pause_button)
    playback_layout.addWidget(fast_forward_button)
    
    playback_layout.addWidget(current_time_label)
    playback_layout.addWidget(total_time_label)
    
    # Progress Slider
    progress_layout = QVBoxLayout()
    progress_label = QLabel("Jump to:")
    progress_input = QSlider(Qt.Horizontal)
    progress_input.setRange(0, 100)
    current_percentage = int((danmu_machine.current_danmu_id / len(danmu_machine.danmu_pool.danmu_list)) * 100)
    progress_input.setValue(current_percentage)
    
    progress_layout.addWidget(progress_label)
    progress_layout.addWidget(progress_input)
    progress_layout.addLayout(playback_layout)
    general_layout.addLayout(progress_layout)

    def on_progress_changed(value):
        danmu_machine.jump_to_percentage(value)
        current_time_label.setText(f"Current Time: {danmu_machine.get_current_time():.2f}s")
    
    progress_input.valueChanged.connect(on_progress_changed)

    general_layout.addStretch()
    general_tab.setLayout(general_layout)
    tabs.addTab(general_tab, "General")
    tabs.addTab(about_tab, "About")
    
    # Main Dialog Layout
    main_layout = QVBoxLayout(dialog)
    main_layout.addWidget(tabs)
    
    # Buttons
    button_box = QDialogButtonBox()
    button_box.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    main_layout.addWidget(button_box)
    dialog.setLayout(main_layout)
    
    if dialog.exec() == QDialog.Accepted:
        danmu_machine.config.font_size_multiplier = font_size_doubleSpinBox.value()
        danmu_machine.config.speed_multiplier = speed_doubleSpinBox.value()
    