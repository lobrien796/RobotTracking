import sys
try:
    import os
    from ultralytics import YOLO
    import cv2
    from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel, QWidget, QFrame, QPushButton, QLineEdit, QTimeEdit
    from PyQt6.QtGui import QImage, QPixmap, QFont, QResizeEvent
    from PyQt6.QtCore import Qt
    from yt_dlp import YoutubeDL
    import pytesseract
    import numpy as np
    from pathlib import Path
    import tkinter as tk
    from tkinter import filedialog
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install them using 'pip install -r requirements.txt'")
    sys.exit(1)

#Variables and whatnot
root = tk.Tk()
root.withdraw()

model_path = "frc-YOLOv11n.pt"
model_loaded = False

yt_loaded = False
yt_url = ""
video_direct_url = ""
yt_vid_name = ""
yt_is_live = ""

ydl_opts = {
    'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
    'quiet': True,
    'no_warnings': True,
    'logger': None
    }

def load_model():
    global model_loaded, model_path, model
    model_loaded = True
    try:
        model = YOLO(model_path)
        model_loaded = True
    except Exception as e:
        print(f"Tried loading model {model_path} but failed: {e}")
        model_loaded = False
        model_path = ""
load_model()


def load_yt():
    global video_direct_url, cap, yt_vid_name, yt_is_live, yt_loaded
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(yt_url, download=False)
            yt_vid_name = info_dict.get("title",None)
            yt_is_live = info_dict.get("live_status")
            print(f"Name: {yt_vid_name}, Live status: {yt_is_live}")
            
            if 'url' in info_dict:
                video_direct_url = info_dict['url']
            elif 'requested_formats' in info_dict:
                video_direct_url = info_dict['requested_formats'][0]['url']
            else:
                video_direct_url = info_dict['formats'][0]['url']

            cap = cv2.VideoCapture(video_direct_url)
            if not cap.isOpened():
                print("Error: Could not open YouTube video stream in OpenCV.")
                yt_loaded = False
            else:
                window.display_current_frame()
                yt_loaded = True
    except Exception as e:
        print(f'Error: {e}')


def cv_to_pixmap(cv_img):
    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
    return QPixmap.fromImage(q_img)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Tracking")
        self.setMinimumSize(1320, 540)

        #Central Widget setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        #Layouts
        main_layout = QHBoxLayout()
        sidebar_layout = QFormLayout()
        stream_layout = QVBoxLayout()

        central_widget.setLayout(main_layout)

        #Sidebar Widgets
        divider_vline = QFrame()
        divider_vline.setFrameShape(QFrame.Shape.VLine)
        divider_vline.setFrameShadow(QFrame.Shadow.Sunken)
        
        self.model_label = QLabel(f"<b>Model: </b>{model_path}")
        self.model_label.setFont(QFont("Arial", 10))
        change_model_button = QPushButton("Change Model")
        change_model_button.setFixedWidth(100)

        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(change_model_button)

        model_HLine = QFrame()
        model_HLine.setFrameShape(QFrame.Shape.HLine)
        model_HLine.setFrameShadow(QFrame.Shadow.Sunken)

        self.yt_link_input = QLineEdit()
        yt_link_button = QPushButton("Go")
        yt_link_button.setFixedWidth(50)

        yt_link_layout = QHBoxLayout()
        yt_link_layout.addWidget(QLabel("<b>YT Link: </b>"))
        yt_link_layout.addWidget(self.yt_link_input)
        yt_link_layout.addWidget(yt_link_button)

        yt_HLine = QFrame()
        yt_HLine.setFrameShape(QFrame.Shape.HLine)
        yt_HLine.setFrameShadow(QFrame.Shadow.Sunken)

        self.start_time_input = QTimeEdit()
        self.start_time_input.setDisplayFormat("hh:mm:ss")

        self.start_time_go_button = QPushButton("Go")
        self.start_time_go_button.setFixedWidth(50)

        start_time_layout = QHBoxLayout()
        start_time_layout.addWidget(self.start_time_input)
        start_time_layout.addWidget(self.start_time_go_button)

        self.frame_back_button = QPushButton("<")
        self.frame_forward_button = QPushButton(">")
        self.seconds_change = 1
        self.seconds_forward_button = QPushButton(f"↻ {self.seconds_change} sec")
        self.seconds_back_button = QPushButton(f"↺ {self.seconds_change} sec")
        self.seconds_change_increase_button = QPushButton("+")
        self.seconds_change_decrease_button = QPushButton("-")

        for control in[
            self.frame_forward_button, self.frame_back_button, self.seconds_change_increase_button, self.seconds_change_decrease_button
        ]:
            control.setFixedWidth(30)

        #Start disabled until youtube is loaded
        for control in[
                self.start_time_input, self.start_time_go_button, self.seconds_forward_button, self.seconds_back_button, 
                self.seconds_change_increase_button, self.seconds_change_decrease_button, self.frame_forward_button, self.frame_back_button
            ]:
                control.setEnabled(False)
                control.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        seconds_change_layout = QHBoxLayout()
        seconds_change_layout.addWidget(self.frame_back_button)
        seconds_change_layout.addWidget(self.frame_forward_button)
        seconds_change_layout.addWidget(self.seconds_forward_button)
        seconds_change_layout.addWidget(self.seconds_back_button)
        seconds_change_layout.addWidget(self.seconds_change_increase_button)
        seconds_change_layout.addWidget(self.seconds_change_decrease_button)

        #Sidebar addRow
        sidebar_layout.addRow(model_layout)
        sidebar_layout.addRow(model_HLine)
        sidebar_layout.addRow(yt_link_layout)
        sidebar_layout.addRow(yt_HLine)
        sidebar_layout.addRow(start_time_layout)
        sidebar_layout.addRow(seconds_change_layout)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setFixedWidth(360)


        #Stream Canvas Widget
        self.image_label = QLabel("Stream Area - Add a YouTube video")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stream_layout.addWidget(self.image_label)
        
        #Connections
        change_model_button.clicked.connect(self.get_new_model)
        self.yt_link_input.returnPressed.connect(self.get_new_yt)
        yt_link_button.clicked.connect(self.get_new_yt)
        self.start_time_go_button.clicked.connect(self.skip_to_frame_input)
        self.seconds_forward_button.clicked.connect(self.skip_seconds_forward)
        self.seconds_back_button.clicked.connect(self.skip_seconds_back)
        self.seconds_change_decrease_button.clicked.connect(self.seconds_change_decrease)
        self.seconds_change_increase_button.clicked.connect(self.seconds_change_increase)
        self.frame_forward_button.clicked.connect(self.increase_frame)
        self.frame_back_button.clicked.connect(self.decrease_frame)

        #Main Layout
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(divider_vline)
        main_layout.addLayout(stream_layout)

    def display_current_frame(self):
        global cap
        if 'cap' in globals() and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                self.current_raw_frame = frame.copy()
                self.update_canvas_display()

    def display_current_annotation(self):
        global cap
        if 'cap' in globals() and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                self.current_raw_frame = model(frame.copy())[0].plot()
                self.update_canvas_display()

                
    def update_canvas_display(self):
        if hasattr(self, 'current_raw_frame') and self.current_raw_frame is not None:
            pixmap = cv_to_pixmap(self.current_raw_frame)
            self.image_label.setPixmap(
                pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

    def step_frame(self, step_amount, is_seconds = False):
        global cap
        if 'cap' not in globals() or not cap.isOpened():
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <=0:
            fps = 30

        offset = int(step_amount * fps) if is_seconds else int(step_amount)
        current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
        target_pos = max(0, current_pos + offset -1)
        print(f"fps: {fps}, step amount: {step_amount}, is_seconds: {is_seconds}, offset: {offset}, current_pos: {current_pos}, target pos: {target_pos}")
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_pos)
        self.display_current_frame()
    
    def seek_frame(self, target_frame):
        global cap
        if 'cap' not in globals() or not cap.isOpened():
            return

        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, target_frame))
        self.display_current_frame()
    
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.update_canvas_display()
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Comma, Qt.Key.Key_Period) and yt_loaded:
            self.handle_arrow_key(event.key())
            event.accept()
            return
        super().keyPressEvent(event)

    def handle_arrow_key(self, key):
        if key == Qt.Key.Key_Right:
            self.skip_seconds_forward()
        elif key == Qt.Key.Key_Left:
            self.skip_seconds_back()
        elif key == Qt.Key.Key_Down:
            self.seconds_change_decrease()
        elif key == Qt.Key.Key_Up:
            self.seconds_change_increase()
        elif key == Qt.Key.Key_Comma:
            self.decrease_frame()
        elif key == Qt.Key.Key_Period:
            self.increase_frame()

    def mousePressEvent(self, event):
        print(f"({event.position().x()},{event.position().y()})")
        return super().mousePressEvent(event)

    
    def get_new_model(self):
        global model_path
        new_model_path = filedialog.askopenfilename(
            defaultextension="*.pt",
            filetypes=[("PyTorch model file", "*.pt"), ("All Files", "*.*")],
            title="Select model",
        )
        if new_model_path and new_model_path.endswith(".pt"):
            model_path = new_model_path
            load_model()
            if model_loaded:
                self.model_label.setText(f"<b>Model: </b>{Path(model_path).name}")
            else:
                self.model_label.setText(f"<b>Model: </b> Error - Couldn't load {Path(model_path).name}")
    
    def get_new_yt(self):
        global yt_url
        if self.yt_link_input.text() != "":
            yt_url = self.yt_link_input.text()
            self.image_label.setText("Loading...")
            self.image_label.repaint()
            load_yt()

            #Enable Controls
            for control in[
                self.start_time_input, self.start_time_go_button, self.seconds_forward_button, self.seconds_back_button, 
                self.seconds_change_increase_button, self.seconds_change_decrease_button, self.frame_forward_button, self.frame_back_button
            ]:
                control.setEnabled(yt_loaded)

            if yt_loaded:
                self.setWindowTitle(f"Robot Tracking - {yt_vid_name}")
                #Clear focus on the timeedit or youtube link area
                self.yt_link_input.clearFocus()
                self.setFocus()
            else:
                self.image_label.setText("Error Loading YT - Please try again")

    def skip_to_frame_input(self):
        global cap
        if 'cap' not in globals() or not cap.isOpened():
            return
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30

        target_seconds = self.start_time_input.time().hour()*3600 + self.start_time_input.time().minute() * 60 + self.start_time_input.time().second()
        self.seek_frame(target_seconds*fps)
    
    def skip_seconds_forward(self):
        self.step_frame(self.seconds_change, True)
    def skip_seconds_back(self):
        self.step_frame(-self.seconds_change, True)
    def seconds_change_increase(self,):
        self.seconds_change += 1
        self.seconds_forward_button.setText(f"↻ {self.seconds_change} sec")
        self.seconds_back_button.setText(f"↺ {self.seconds_change} sec")
    def seconds_change_decrease(self):
        if self.seconds_change > 0:
            self.seconds_change -= 1
            self.seconds_forward_button.setText(f"↻ {self.seconds_change} sec")
            self.seconds_back_button.setText(f"↺ {self.seconds_change} sec")
    def increase_frame(self):
        self.step_frame(1)
    def decrease_frame(self):
        self.step_frame(-1)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())