import socket
from os import error #xuất ra lỗi
import os
import threading #chạy đa luồn
from multiprocessing import Process, Manager
import json
import tkinter as tk
from tkinter import *
import sqlite3
from tkinter import ttk 


def server():
    #nhận dữ liệu khi server chấp nhận kết nối socket
    def _handle(conn, addr): 
        username=""
        while not stop_event.is_set():
                #Dữ liệu nhận được dạng bytes nên decode về string
                data = conn.recv(1024).decode()
                print(data)
                #nếu không có data thì thoát khỏi vòng lặp để chạy hàm handle khác
                if not data: 
                    
                    print("Máy sau ngắt kết nối ",addr)
                    if username!="":
                        database = sqlite3.connect('db_server.db')  
                        cursor = database .cursor()
                        cursor.execute('UPDATE clients SET (status, ip_address,port) = (?,?,?) WHERE username = ?', (0,0,0, username))
                        database.commit()
                        cursor.close()
                        database.close()
                        print("da cap nhat trang thai offline")      
                    break
                data_dict = json.loads(data)  # Convert JSON string to dictionary
                res = []        
                if data_dict['method'] == 'download':
                    database = sqlite3.connect('db_server.db')  
                    cursor = database .cursor()
                    print(data_dict)
                    cursor.execute('''
                        SELECT clients.ip_address, clients.port,files.size,files.filepath
                        FROM files LEFT JOIN clients ON files.username = clients.username
                        WHERE files.filename = ? AND clients.status = ? ''', (data_dict['filename'], 1))
                    res = cursor.fetchall() 
                    print(res)          
                    if (len(res)==0): res = 'NoFile'
                    cursor.close()
                    database.close()
                elif data_dict['method'] == 'getfilelist':
                    database = sqlite3.connect('db_server.db')  
                    cursor = database .cursor()           
                    cursor.execute(''' SELECT filename,size,filepath FROM files WHERE username=?''',(data_dict['username'],))
                    res = cursor.fetchall()
                    print(res)
                    cursor.close()
                    database.close()
                elif data_dict['method'] == 'remove':
                    database = sqlite3.connect('db_server.db')  
                    cursor = database .cursor()
                    print(data_dict)            
                    cursor.execute(''' DELETE FROM files WHERE username=? AND filename =?''',(data_dict['username'],data_dict['filename'],))
                    database.commit()
                    res ="success"
                    cursor.close()
                    database.close()
                elif data_dict['method'] == 'upload':
                    database = sqlite3.connect('db_server.db')  
                    cursor = database .cursor()
                    cursor.execute('SELECT count(*) FROM files WHERE username = ? AND filename = ?', (username,data_dict['filename'],))
                    result = cursor.fetchone()[0] 
                    if result>0:
                        try:
                            cursor.execute('UPDATE files set filepath = ? WHERE username =? AND filename =?',(data_dict['path'],username,data_dict['filename']))
                            database.commit()
                            res = 'updated'
                        except:
                            res = 'false'
                    else:
                        try:
                            cursor.execute('INSERT INTO files (filename, username,size,filepath) VALUES (?, ?,?,?)', (data_dict['filename'], username,data_dict['size'],data_dict['path']))
                            database.commit()  
                            res = 'inserted'  
                        except:
                            res = 'false'                     
                    cursor.close()
                    database.close()
                elif data_dict['method'] == 'register':
                    database = sqlite3.connect('db_server.db')  
                    cursor = database .cursor()
                    cursor.execute('SELECT count(*) FROM clients WHERE username = ?', (data_dict['username'],))
                    result = cursor.fetchone()
                    if result[0]>0:
                        res = 'false'
                    else:
                        cursor.execute('INSERT INTO clients (username, password, status, ip_address, port) VALUES (?, ?,?,?,?)', (data_dict['username'], data_dict['password'],0,0,0))
                        database.commit()
                        res = 'success'   
                    cursor.close()
                    database.close()
                elif data_dict['method'] == 'login':
                    database = sqlite3.connect('db_server.db')  
                    username = data_dict['username']
                    cursor = database .cursor()
                    cursor.execute('SELECT password FROM clients WHERE username = ?', (username,))
                    user_pass = cursor.fetchone()
                    cursor.close()
                    if user_pass:
                        if user_pass[0] == data_dict['password']:
                            res = 'OK'
                            print("khop mat khau")                
                            # cập nhật status:
                            cursor = database .cursor()
                            cursor.execute('''UPDATE clients SET (status, ip_address, port) = (?,?,?) WHERE username = ?''', (1, addr[0],addr[1], username))
                            database.commit()  
                            cursor.close()  
                            database.close()
                            print("da cap nhat trang thai online")   
                        else:
                            res = 'Not user'  
                    else:
                        res = 'Not user'      
                else:
                    print('dkuyum')   
                
                if not isinstance(res, str):
                    res_dict = json.dumps(res)
                else:
                    res_dict = res
                #nhận được dữ liệu thì phản hồi về phía client, encode() về lại dạng bytes
                conn.send(res_dict.encode())
                if not stop_event:
                    break
                #conn.close() # đóng kết nối
                #break #thoát khỏi vòng lặp để nhận handle khắc
    HOST = "127.0.0.1"
    PORT = 8080
    SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        SERVER.bind((HOST, PORT))
        print(f'* Running on http://{HOST}:{PORT}')
    except socket.error as e:
        print(f'socket error: {e}')
    SERVER.listen()
    print("listening")

    while not stop_event.is_set():
        conn, addr = SERVER.accept()
        if conn:
            print("Địa chỉ máy sau đang kết nối", addr)
            thread = threading.Thread(target=_handle, args=(conn, addr))
            thread.start()
    print("Close")
    SERVER.close()
# region 0: tao giao diện cho server

def UI():
    def update_lst_respond():
        cursor_server.execute('''
                    SELECT clients.username, clients.status ,clients.ip_address, clients.port, COUNT(files.filename) AS file_count
                    FROM clients
                    LEFT JOIN files ON clients.username = files.username                
                    GROUP BY clients.username''')
        lst_get = cursor_server.fetchall()

        # Xóa tất cả các dòng hiện tại trong lst_respond
        lst_respond.delete(*lst_respond.get_children())

        if lst_get != []:
            stt = 1
            for item in lst_get:
                lst_respond.insert("", tk.END, text=f"{stt}", values=(item[0], item[1], item[2], item[3],item[4]))
                stt = stt + 1

    def refresh_lst_respond():
        update_lst_respond()
        lst_respond.pack()

    file_window = tk.Tk()
    file_window.title(f"SERVER MANAGER")
    file_window.geometry('500x500')    
    # khu vực hiển thị
    lst_respond = ttk.Treeview(file_window, columns=("col1", "col2","col3","col4","col5"),selectmode="browse")
    lst_respond .heading("#0", text="STT")
    lst_respond .heading("col1", text="Client name")
    lst_respond .heading("col2", text="status")
    lst_respond .heading("col3", text="IP")
    lst_respond .heading("col4", text="Port")
    lst_respond .heading("col5", text="Number files")
    lst_respond.column("#0",anchor="w", width=50)
    lst_respond.column("col1",anchor="center", width=100)
    lst_respond.column("col2",anchor="center", width=50) 
    lst_respond.column("col3",anchor="center", width=100)  
    lst_respond.column("col4",anchor="center", width=75) 
    lst_respond.column("col5",anchor="center", width=100) 
    database = sqlite3.connect('db_server.db')  
    cursor_server = database .cursor()
    refresh_lst_respond()
    bt_refresh = tk.Button(file_window, text="Refresh",width=15, command= refresh_lst_respond)  
    bt_refresh.pack(pady=10)
    def close_windows():
        stop_event.set()
        print("thay doi stop_even:", stop_event.is_set())
        file_window.destroy()  
    file_window.protocol("WM_DELETE_WINDOW", close_windows)
    file_window.mainloop()
    #endregion
    

stop_event = threading.Event()
stop_event.clear()
server_thread = threading.Thread(target=server)
server_thread.start()
ui_thread = threading.Thread(target=UI)
ui_thread.start()