import socket
import threading #chạy đa luồn
import json
import tkinter as tk
from tkinter import *
import sqlite3
from tkinter import ttk 
from tkinter import messagebox
from pythonping import ping

#region 0 : RUN SERVER
HOST = "127.0.0.1"
PORT = 8080
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def server():
    #nhận dữ liệu khi server chấp nhận kết nối socket
    def _handle(conn, addr): 
        username=""
        while not stop_event.is_set():
                #Dữ liệu nhận được dạng bytes nên decode về string
                data = conn.recv(1024).decode()
                #print(data)
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
                    #print(data_dict)
                    cursor.execute('''
                        SELECT clients.ip_address, clients.port,files.size,files.filepath
                        FROM files LEFT JOIN clients ON files.username = clients.username
                        WHERE files.filename = ? AND clients.status = ? ''', (data_dict['filename'], 1))
                    res = cursor.fetchall() 
                    #print(res)          
                    if (len(res)==0): res = 'NoFile'
                    cursor.close()
                    database.close()
                elif data_dict['method'] == 'getfilelist':
                    database = sqlite3.connect('db_server.db')  
                    cursor = database .cursor()           
                    cursor.execute(''' SELECT filename,size,filepath FROM files WHERE username=?''',(data_dict['username'],))
                    res = cursor.fetchall()
                    #print(res)
                    cursor.close()
                    database.close()
                elif data_dict['method'] == 'remove':
                    database = sqlite3.connect('db_server.db')  
                    cursor = database .cursor()
                    #print(data_dict)            
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
                            #print("khop mat khau")                
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
                elif data_dict['method'] == 'reset':
                    database = sqlite3.connect('db_server.db')  
                    cursor = database .cursor()  
                    try:
                        cursor.execute('UPDATE clients set (ip_address, port, status)= (?,?,?) WHERE username =?',(0,0,0,data_dict['username']))
                        database.commit()
                        res = 'okie'
                    except:
                        res = 'false'                        
                    cursor.close()
                    database.close()
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
    
# endregion

# region 1: tao giao diện cho server
    
def UI():
    # ham refresh UI View
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
    # hàm chuyển lệnh terminal và thực hiện
    def control_terminal(input_entry):
        string_code = input_entry.get()
        spell_code = string_code.split()        
   
        if len(spell_code)==2:
            if spell_code[0]== 'discover': 
                terminal_cursor = database.cursor()
                terminal_cursor.execute(''' SELECT filename,username,size,filepath FROM files WHERE username=?''',(spell_code[1],))
                result = terminal_cursor.fetchall() 
                if result != []:
                    # Tạo một WINDOWS và tree
                    frame_output  = tk.Tk()
                    frame_output .title(f"OUTPUT DISCOVER {spell_code[1]}")
                    frame_output .geometry('400x300')
                    tree = ttk.Treeview(frame_output)          
                    tree.pack(fill='both', expand=True) 
                    tree["columns"] = ("col1", "col2","col3","col4","col5")
                    tree .heading("#0", text="STT")
                    tree .heading("col1", text="Client name")
                    tree .heading("col2", text="file name")
                    tree .heading("col3", text="size")
                    tree .heading("col4", text="Patch")
                    tree.column("#0",anchor="w", width=50)
                    tree.column("col1",anchor="center", width=100)
                    tree.column("col2",anchor="center", width=100) 
                    tree.column("col3",anchor="center", width=75)  
                    tree.column("col4",anchor="center", width=125) 
                    stt = 1
                    for item in result:
                        tree.insert("", tk.END, text=f"{stt}", values=(item[1], item[0], item[2], item[3]))
                        stt = stt + 1
                else:
                    messagebox.showinfo("Thông báo",f"Không tìm thấy file nào của {spell_code[1]}")
                terminal_cursor.close()                
            elif spell_code[0]== 'ping':                
                terminal_cursor = database.cursor()
                terminal_cursor.execute(''' SELECT status, ip_address, port FROM clients WHERE username=?''',(spell_code[1],))
                result = terminal_cursor.fetchone()
                if result[0]==0:
                    messagebox.showinfo("Thông báo",f"Client {spell_code[1]} đang offline")
                else:
                    frame_output  = tk.Tk()
                    frame_output .title(f"OUTPUT PING {spell_code[1]}")
                    frame_output .geometry('500x300')
                    info= ping(result[1])                  
                    tree = tk.Text(frame_output, width=50, height=10)
                    tree.grid(row=1, column=0, columnspan=3, padx=5, pady=5)
                    tree.config(state="disabled") 
                    tree.config(state="normal")  # Cho phép chỉnh sửa nội dung của Text
                    tree.delete(1.0, "end")  # Xóa nội dung hiện tại trong Text
                    tree.insert("end", info)  # Chèn kết quả của ping vào Text
                    tree.config(state="disabled")  # Vô hiệu hóa chỉnh sửa nội dung của Text

                terminal_cursor.close()
        
        else:
            messagebox.showinfo("Thông báo","vui lòng nhập vào terminal đúng định dạng code")
    # ham refresh UI View
    def refresh_lst_respond():
        update_lst_respond()
        lst_respond.pack()
    # các biến, UI view:
    server_windows = tk.Tk()
    server_windows.title(f"SERVER MANAGER")
    server_windows.geometry('500x500')    
    # khu vực hiển thị
    frame = ttk.Frame(server_windows)
    frame.pack(padx=10, pady=10)
    lst_respond = ttk.Treeview(server_windows, columns=("col1", "col2","col3","col4","col5"),selectmode="browse")
    lst_respond .heading("#0", text="STT")
    lst_respond .heading("col1", text="Client name")
    lst_respond .heading("col2", text="status")
    lst_respond .heading("col3", text="IP")
    lst_respond .heading("col4", text="Port")
    lst_respond .heading("col5", text="Number files")
    lst_respond.column("#0",anchor="w", width=50)
    lst_respond.column("col1",anchor="center", width=100,stretch=0)
    lst_respond.column("col2",anchor="center", width=50,stretch=0) 
    lst_respond.column("col3",anchor="center", width=100,stretch=0)  
    lst_respond.column("col4",anchor="center", width=75,stretch=0) 
    lst_respond.column("col5",anchor="center", width=100,stretch=0) 
    database = sqlite3.connect('db_server.db')  
    cursor_server = database .cursor()
    refresh_lst_respond()
    bt_refresh = tk.Button(server_windows, text="Refresh",width=15, command= refresh_lst_respond)  
    bt_refresh.pack(pady=10)
    def close_windows():
        stop_event.set()   
        SERVER.close()
        #print("thay doi stop_even:", stop_event.is_set())
        server_windows.destroy()  
    server_windows.protocol("WM_DELETE_WINDOW", close_windows)
    label_terminal = tk.Label(server_windows, text="Input Terminal here:", bg='#eb85de')
    label_terminal.pack(pady=10)
    #Tạo trường nhập liệu
    entry_terminal = tk.Entry(server_windows,width=70)
    entry_terminal.pack(pady=10)
    # Nút run
    bt_run = tk.Button(server_windows, text="Run Code",width=15, command=lambda:control_terminal(entry_terminal))  
    bt_run.pack(pady=10)
    
    server_windows.protocol("WM_DELETE_WINDOW", close_windows)
    server_windows.mainloop()
    #endregion
    
stop_event = threading.Event()
stop_event.clear()
server_thread = threading.Thread(target=server)
server_thread.start()
ui_thread = threading.Thread(target=UI)
ui_thread.start()