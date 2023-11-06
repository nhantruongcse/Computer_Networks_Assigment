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

def update_lst_respond():
    cursor_server.execute('''
                SELECT clients.username, clients.ip_address, clients.port, COUNT(files.filename) AS file_count
                FROM clients
                LEFT JOIN files ON clients.username = files.username
                WHERE clients.status = ?
                GROUP BY clients.username''', (1,))
    lst_get = cursor_server.fetchall()

    # Xóa tất cả các dòng hiện tại trong lst_respond
    lst_respond.delete(*lst_respond.get_children())

    if lst_get != []:
        stt = 1
        for item in lst_get:
            lst_respond.insert("", tk.END, text=f"{stt}", values=(item[0], item[1], item[2], item[3]))
            stt = stt + 1

def refresh_lst_respond():
    update_lst_respond()
    lst_respond.pack()

file_window = tk.Tk()
file_window.title(f"SERVER MANAGER")
file_window.geometry('500x500')    
# khu vực hiển thị
lst_respond = ttk.Treeview(file_window, columns=("col1", "col2","col3","col4"),selectmode="browse")
lst_respond .heading("#0", text="STT")
lst_respond .heading("col1", text="Client name")
lst_respond .heading("col2", text="IP")
lst_respond .heading("col3", text="Port")
lst_respond .heading("col4", text="Number file shared")
lst_respond.column("#0",anchor="w", width=50)
lst_respond.column("col1",anchor="center", width=75)
lst_respond.column("col2",anchor="center", width=75) 
lst_respond.column("col3",anchor="center", width=75)  
lst_respond.column("col4",anchor="center", width=120) 
database = sqlite3.connect('db_server.db')  
cursor_server = database .cursor()
refresh_lst_respond()
bt_file_manager = tk.Button(file_window, text="Refresh",width=15, command= refresh_lst_respond)  
bt_file_manager.pack(pady=10)   


def close_windows():
    global stop_event
    stop_event=True
    file_window.destroy()

file_window.protocol("WM_DELETE_WINDOW", close_windows)
file_window.mainloop()

print(stop_event)