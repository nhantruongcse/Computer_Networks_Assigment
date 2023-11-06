import socket
from os import error #xuất ra lỗi
import os
import threading #chạy đa luồn
import json
import tkinter as tk
from tkinter import *
import sqlite3
from pythonping import ping
import socket
import tkinter as tk
from tkinter import *
from tkinter import ttk 
from tkinter import filedialog
import json
from pythonping import ping
import subprocess
import ipaddress
import os # de lay size cua file
from PIL import Image, ImageTk 
from tkinter import messagebox
stop_event=False
print(stop_event)
main_window = None

def chooseLayout():
    global main_window
    def close_windows():
        global stop_event
        stop_event=True
        main_window.destroy()
    if main_window==None:    
        main_window = tk.Tk()
        main_window.title(f"File Upload/Download - Client: ")
        main_window.geometry('500x500')
    # Tạo frame chứa hình ảnh ở giữa góc trên
        # Thay đổi đường dẫn và tên tệp ảnh tương ứng
        canvas = tk.Canvas(main_window, width=400, height=200)
        canvas.pack(pady=50)  # Căn chỉnh để hình ảnh nằm giữa trên cửa sổ
        stop_event = tk.BooleanVar()
        stop_event.set(False)  # Khởi tạo biến stop_event
        # Hình ảnh đặt ở đây
        # Thay đổi đường dẫn và tên tệp ảnh tương ứng
        image_path = "p2p.png"
        image = tk.PhotoImage(file=image_path)
        canvas.create_image(200, 100, image=image)  # Đặt hình ảnh vào giữa của Canvas
        # Tạo nút "Download" và "Upload" và gán cho các hàm tương ứng
        download_button = tk.Button(main_window, text="Download",width=15)
        download_button.pack(pady=10)

        upload_button = tk.Button(main_window, text="Upload",width=15, )
        upload_button.pack(pady=10)
        bt_file_manager = tk.Button(main_window, text="File Manager",width=15,)  
        bt_file_manager.pack(pady=10)       
    else:
        main_window.deiconify()
    main_window.protocol("WM_DELETE_WINDOW", close_windows)
    main_window.mainloop()

chooseLayout()
print(stop_event)