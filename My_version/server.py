import socket
from os import error #xuất ra lỗi
import os
import threading #chạy đa luồn
import json
import tkinter as tk
from tkinter import *
import sqlite3


#đặt host là IP của máy
HOST = "127.0.0.1"
PORT = 8080

#Tạo server socket
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Dùng try-except để bắt sự kiện
    #Cụ thể dùng socket SERVER kết nối (bind) vào HOST, PORT
        #Thành công in ra thông báo...
        #Lỗi in ra mã lỗi
try:
    SERVER.bind((HOST,PORT))
    print(f'* Running on http://{HOST}:{PORT}')
except socket.error as e:
    print(f'socket error: {e}')
    print('socket error: %s' %(e))

def _start():
    SERVER.listen() #lắng nghe yêu cầu từ phía client
    print("listening")
    while True:
        conn, addr = SERVER.accept() #giá trị trả về accept là kết nối và địa chỉ
        if conn:
            print("Địa chi máy sau đang kết nối ", addr)

        #Khai báo thread để nhận dữ liệu đa luồng
        thread = threading.Thread(target=_handle, args=(conn, addr))
        thread.start()

#nhận dữ liệu khi server chấp nhận kết nối socket
def _handle(conn, addr):     
     
    username=""
    while True:
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
        #conn.close() # đóng kết nối
        #break #thoát khỏi vòng lặp để nhận handle khắc
_start()