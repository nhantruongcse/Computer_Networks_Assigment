import socket
import tkinter as tk
from tkinter import *
from tkinter import ttk 
from tkinter import filedialog
import json
from pythonping import ping
import os # de lay size cua file
from PIL import Image, ImageTk 
from tkinter import messagebox
import threading #chạy đa luồng

SERVER_P2P= NONE
stop_event = threading.Event()
stop_event.clear()

# region 0: Tao host va connect server, tạo server p2p

HOST = "127.0.0.1"
PORT = 8080
#connect với server:
CLIENTSOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
CLIENTSOCKET.connect((HOST, PORT))
# Tạo socket server p2p (nhằm gửi nhận file p2p với client khác) với địa chỉ IP và cổng từ CLIENTSOCKET  
client_ip, client_port = CLIENTSOCKET.getsockname()
SERVER_P2P = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_P2P.bind((client_ip, client_port))
print(f'* Running on http://{client_ip,}:{client_port}')
# endregion


#region 1: handle_p2p: xử lý request download P2P từ client khác
def listening_p2p(client_ip,client_port):
    def stop(self):
        print("su dung chuogn tu stop self")
        self.running = False
        socket.socket(socket.AF_INET, 
                    socket.SOCK_STREAM).connect( (self.hostname, self.port))
        self.socket.close()
    # Tạo socket server với địa chỉ IP và cổng từ CLIENTSOCKET  
    try:
        SERVER_P2P.listen() 
        print(f'*{client_ip,}:{client_port} is listening')
        while main_window:
            conn, addr = SERVER_P2P.accept() #giá trị trả về accept là kết nối và địa chỉ
            if conn:
                print("Địa chi máy sau đang kết nối ", addr,' : ',conn)
                #Khai báo thread để nhận dữ liệu đa luồng
                thread_p2p_host = threading.Thread(target=_handle_p2p, args=(conn, addr, SERVER_P2P))
                thread_p2p_host.start()
        stop()
        SERVER_P2P.close()
    except socket.error as e:
        print(f'socket error: {e}')
        print('socket error: %s' %(e))  

def _handle_p2p(conn, addr, SERVER_P2P): # xử lý yêu cầu download của client khác
    BUFFER_SIZE = 1024  # Kích thước của mỗi phần dữ liệu
    while main_window:
        # Chấp nhận kết nối từ client yêu cầu
        data = conn.recv(1024).decode()
        print(data)
        #nếu không có data thì thoát khỏi vòng lặp để chạy hàm handle khác
        if not data: 
            break
        data_dict = json.loads(data)  # Convert JSON string to dictionary
        res = []
        if data_dict['method'] == 'download':
            path = data_dict['path']
            if os.path.exists(path):
            #     if os.path.isfile(path):
            #         print(f"Đường dẫn '{path}' là một tệp.")
            #     else:
            #         print(f"Đường dẫn '{path}' không phải là tệp.")
                BUFFER_SIZE = 1024  # Kích thước của mỗi phần dữ liệu
                while True:
                    # Chấp nhận kết nối từ client yêu cầu                    # Đường dẫn của tệp cần gửi
                    try:
                        with open(path, 'rb') as file:
                            while True:
                                data = file.read(BUFFER_SIZE)
                                if not data:
                                    break
                                conn.sendall(data)
                    finally:
                        # Đóng kết nối với client yêu cầu                        
                        break
                conn.close()
                

#endregion


# region 2: Define a global variable to hold the main window
main_window = None
username_dis = ""
# endregion

# region 3: Đăng nhập, tạo Account

def login(e1, e2):
    username = e1.get()
    password = e2.get()
    data = {
    'username': username,
    'password': password,
    'method': 'login'
    }
    json_data = json.dumps(data)
    CLIENTSOCKET.send(json_data.encode())
    loginResponse(username)

def loginResponse(username):
    res = CLIENTSOCKET.recv(1024).decode()
    #print(res)
    if res == 'OK':
        # Đóng cửa sổ đăng nhập
        global username_dis 
        username_dis = username
        login_window.destroy()
        print("login success")
        # Mở cửa sổ chọn layout
        chooseLayout()
    else:
        messagebox.showinfo("Thông báo","Sai username hoặc password")
        print("Login failed. Please try again.")

def register(e1,e2):
    username = e1.get()
    password = e2.get()
    data = {
    'username': username,
    'password': password,
    'method': 'register'
            }
    json_data = json.dumps(data)
    CLIENTSOCKET.send(json_data.encode())
    register_Response()

def register_Response():
    res = CLIENTSOCKET.recv(1024).decode()
    print(res)
    #print(res)
    if res == 'success':
        # Đóng cửa sổ đăng nhập
        print("Tạo account thành công")
        messagebox.showinfo("Thông báo", "Tạo account thành công, hãy đăng nhập")
    else:
        print("Tạo account thất bại")
        messagebox.showinfo("Thông báo","Tạo account đã tồn tại, tạo account khác hoặc đăng nhập")

# endregion

# region 4: Phần Download
# Hàm xử lý nút "Search File to Download"

def searchButtonClicked(entry_filenameDownload,lst_respond):
    filename = entry_filenameDownload.get()    
    lst_get =  sendFilenameToServerToFind(filename)
    if  lst_get!= 'NoFile':
        stt=1
        lst_respond.delete(*lst_respond.get_children())
        for item in lst_get:          
            response = ping(item[0])
            print(response)
            lst_respond.insert("",tk.END, text=f"Máy {stt}",values=(item[0],item[1],item[2],item[3],response))
            stt=stt+1
        lst_respond.pack()

# Hàm gửi filename lên server để tìm địa chỉ client
def sendFilenameToServerToFind(filename):
    data = {
        'filename' : filename,
        'method' : 'download',
    }
    json_data = json.dumps(data)
    CLIENTSOCKET.send(json_data.encode())
    return receiveAddressFromServer()

# Nhận respon
def receiveAddressFromServer():
    res = CLIENTSOCKET.recv(1024).decode()
    if res == "NoFile":
        print("Cannot find a client having this file")
        return
    else:
        # Thực hiện p2p với client(address) chứa file
        return json.loads(res)

# Mở cửa sổ download
def openDownloadWindow():
    global main_window
    main_window.withdraw()
    download_window = tk.Tk()
    download_window.title("Download")
    download_window.geometry('500x500')
    # Các thành phần và layout cho phần download
    label_name = tk.Label(download_window, text="Filename to download:", bg='#eb85de')
    label_name.pack()
    # Tạo trường nhập liệu
    entry_filenameDownload = tk.Entry(download_window) 
    entry_filenameDownload.pack(pady=10)
    
    # khu vực hiển thị
    lst_respond = ttk.Treeview(download_window, columns=("col1", "col2","col3","col4","col5"),selectmode="browse")
    lst_respond .heading("#0", text="Danh sách: ")
    lst_respond .heading("col1", text="IP address")
    lst_respond .heading("col2", text="Port")
    lst_respond .heading("col3", text="Size")
    lst_respond .heading("col4", text="Path")
    lst_respond .heading("col5", text="Ping")
    lst_respond.column("#0",anchor="w", width=75)
    lst_respond.column("col1",anchor="center", width=100)
    lst_respond.column("col2",anchor="center", width=75) 
    lst_respond.column("col3",anchor="center", width=75)   
    lst_respond.column("col4",anchor="center", width=75)  
    lst_respond.column("col5",anchor="center", width=75)   
     # Tạo nút Search,  tạo nút download

    def download_file():
        item_focus =lst_respond.focus()
        print(lst_respond.item(lst_respond.focus()))
        # if not lst_respond.selection():
        #      tk.messagebox.showerror("Error", "Please select a file to download.")            
        # else:            
        ip_select = lst_respond.item(item_focus)['values'][0]
        port_select = lst_respond.item(item_focus)['values'][1]
        path_select = lst_respond.item(item_focus)['values'][3]
        file_name = entry_filenameDownload.get() 
        print('ip_select ',ip_select )
        print('port_select ',port_select)
        # Đường dẫn để lưu tệp tải về
        save_directory = f"{username_dis}_downloaded"
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        # Tạo yêu cầu để gửi tên tệp cần tải về
        request_download = {'method': 'download','path':path_select}

        try:
            client_request =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_request .connect((ip_select, port_select))
            json_data = json.dumps(request_download)
            client_request.send(json_data.encode())
        
        # Đường dẫn để lưu tệp tải về
            save_path = os.path.join(save_directory, file_name)
            with open(save_path, 'wb') as file:
                while True:
                    data = client_request.recv(1024)  # Nhận dữ liệu theo phần
                    if not data:
                        break
                    file.write(data)
            print("Tải về hoàn thành.")
            messagebox.showinfo("Thông báo","Tải về hoàn thành")
        except Exception as e:
            # Xử lý lỗi khi giải mã JSON hoặc trong quá trình tải về
            tk.messagebox.showerror("Error", f"Download error: {str(e)}")
        finally:
            client_request.close()

    search_button = tk.Button(download_window, text="Search File", width=10,command=lambda: searchButtonClicked(entry_filenameDownload, lst_respond))
    bt_download = tk.Button(download_window,width=10, text="Download", command=download_file)  
    search_button.pack(pady=10)        
    lst_respond.pack(pady=10)
    bt_download.pack(pady=10)
    back_button = tk.Button(download_window, text="Back", command=lambda:( download_window.destroy(),chooseLayout())  )  
    back_button.pack(side="bottom", anchor="sw", pady=20, padx=20)
    download_window.mainloop()
    #threading.Thread(target=download_window.mainloop, args=()).start()   

# endregion

# region 5: Phần Upload info lên server
# Hàm xử lý nút "File to Upload"
def uploadButtonClicked(entry_filenameUpload, entry_file_path, label_file_size):
    filename = entry_filenameUpload.get()
    path = entry_file_path.get()
    file_Size = label_file_size.cget("text")
    print(file_Size)
    sendInformationOfFileToServerToSaveToDatabase(filename,file_Size , path)
def sendInformationOfFileToServerToSaveToDatabase(filename, size, path):
    if path!="" and filename!="":
        data = {
            'filename' : filename,
            'size' : size,
            'path' : path,        
            'method' : 'upload',
        }
        json_data = json.dumps(data)
        CLIENTSOCKET.send(json_data.encode())
        receiveUploadResponseFromServer()
    else:
        messagebox.showinfo("Thông báo","Chọn file để upload trước")
# Nhận và show kết quả
def receiveUploadResponseFromServer():
    res = CLIENTSOCKET.recv(1024).decode()
    if  res=='false':
        messagebox.showinfo("Thông báo","Upload thông tin thất bại")
    elif res== 'updated':
        messagebox.showinfo("Thông báo","Cập nhật thông tin thành công")
    elif res =='inserted':
        messagebox.showinfo("Thông báo","Upload thông tin thành công")
# Mở cửa sổ upload
def openUploadWindow():
    global main_window
    main_window.withdraw()
    upload_window = tk.Tk()
    upload_window.title(f"Upload Client: {username_dis}")
    upload_window.geometry('500x500')

    # # Các thành phần và layout cho phần upload
    label_name_upload = tk.Label(upload_window, text="Filename to upload:", bg='#eb85de')
    label_name_upload.pack(pady=10)
    #Tạo trường nhập liệu
    entry_filenameUpload = tk.Entry(upload_window)
    entry_filenameUpload.pack()
    back_button = tk.Button(upload_window, text="Back", command=lambda: (upload_window.destroy(), chooseLayout()))
    back_button.pack(side="bottom", anchor="sw", pady=20, padx=20)
    # Khung chọn file
    def browse_file():
        file_path = filedialog.askopenfilename()
        entry_file_path.delete(0, tk.END)
        entry_file_path.insert(tk.END, file_path)
        if file_path:
            file_size = os.path.getsize(file_path)
            if file_size <1000:
                file_size_text = f"{round(file_size / 1024, 0)} kb"
            else:
                file_size_text = f"{round(file_size / (1024 * 1024), 2)} Mb"
            label_file_size.config(text=file_size_text)

    label_file_path = tk.Label(upload_window, text="File Path:")
    label_file_path.pack(pady=10)

    entry_file_path = tk.Entry(upload_window)
    entry_file_path.pack(pady=10)

    button_browse = tk.Button(upload_window, text="Choose File", command=browse_file)
    button_browse.pack(pady=10)
    label_size = tk.Label(upload_window, text="File Size:")
    label_size.pack(pady=10)
    label_file_size = tk.Label(upload_window, text="N/A")
    label_file_size.pack(pady=10)

    upload_button = tk.Button(upload_window, text="File to Upload", command=lambda: uploadButtonClicked(entry_filenameUpload, entry_file_path, label_file_size))
    upload_button.pack(pady=10)
    upload_window.mainloop()

# endregion

# region 6: File sharing manager

def file_manager():    
    main_window.withdraw()
    file_window = tk.Tk()
    file_window.title(f"File Manager Client: {username_dis}")
    file_window.geometry('500x500')    
    # khu vực hiển thị
    lst_respond = ttk.Treeview(file_window, columns=("col1", "col2","col3"),selectmode="browse")
    lst_respond .heading("#0", text="STT")
    lst_respond .heading("col1", text="File name")
    lst_respond .heading("col2", text="Size")
    lst_respond .heading("col3", text="File Path")
    lst_respond.column("#0",anchor="w", width=75)
    lst_respond.column("col1",anchor="center", width=100)
    lst_respond.column("col2",anchor="center", width=75) 
    lst_respond.column("col3",anchor="center", width=150)   
    lst_respond.pack()
    # Tạo nút Nhận danh sách file
    data = {
        'method' : 'getfilelist',
        'username': username_dis,
    }
    json_data = json.dumps(data)
    CLIENTSOCKET.send(json_data.encode())
    res = CLIENTSOCKET.recv(1024).decode()
    lst_get = json.loads(res)
    if  lst_get!= []:
        stt=1
        lst_respond.delete(*lst_respond.get_children())
        for item in lst_get: 
            lst_respond.insert("",tk.END, text=f"{stt}",values=(item[0],item[1],item[2]))
            stt=stt+1
        lst_respond.pack()        

    def remove_file():
        selected_items = lst_respond.selection()
        if selected_items:
            file_select = lst_respond.item(selected_items[0])['values'][0]  # Lấy giá trị của cột "File name" của dòng được chọn
            print(file_select)
            data = {
                'filename': file_select,
                'method': 'remove',
                'username': username_dis,
            }
            json_data = json.dumps(data)
            CLIENTSOCKET.send(json_data.encode())
            receive_remove()
        else:
            messagebox.showwarning("Lưu ý", "Hãy chọn một dòng để xóa.")

    def receive_remove():
        response = CLIENTSOCKET.recv(1024).decode()
        if response == "success":
            data = {
                'method' : 'getfilelist',
                'username': username_dis,
                    }
            json_data = json.dumps(data)
            CLIENTSOCKET.send(json_data.encode())
            res = CLIENTSOCKET.recv(1024).decode()
            lst_get = json.loads(res)
            stt = 1
            lst_respond.delete(*lst_respond.get_children())
            for item in lst_get:
                lst_respond.insert("", tk.END, text=f"{stt}", values=(item[0], item[1], item[2]))
                stt += 1
            lst_respond.pack()
            messagebox.showinfo("Thông báo", "Remove thành công")
        else:
            messagebox.showerror("Lỗi", "Xóa không thành công")

    bt_delete = tk.Button(file_window, text="Remove", width=10, command=remove_file)
    bt_delete.pack(pady=10)
    back_button = tk.Button(file_window, text="Back", command=lambda: (file_window .destroy(),chooseLayout()))
    back_button.pack(side="bottom", anchor="sw", pady=20, padx=20)
    file_window.mainloop()




# endregion

# region 7: Mở cửa sổ chọn layout và Ping

def chooseLayout():
    global main_window
    def close_windows():
        stop_event.set()
        print("stop set")
        main_window.destroy()
    if main_window==None:    
        main_window = tk.Tk()
        main_window.title(f"File Upload/Download - Client: {username_dis}")
        main_window.geometry('500x500')
    # Tạo frame chứa hình ảnh ở giữa góc trên
        # Thay đổi đường dẫn và tên tệp ảnh tương ứng
        canvas = tk.Canvas(main_window, width=400, height=200)
        canvas.pack(pady=50)  # Căn chỉnh để hình ảnh nằm giữa trên cửa sổ
        # Hình ảnh đặt ở đây
        # Thay đổi đường dẫn và tên tệp ảnh tương ứng
        image_path = "p2p.png"
        image = tk.PhotoImage(file=image_path)
        canvas.create_image(200, 100, image=image)  # Đặt hình ảnh vào giữa của Canvas
        # Tạo nút "Download" và "Upload" và gán cho các hàm tương ứng
        download_button = tk.Button(main_window, text="Download",width=15, command=openDownloadWindow)
        download_button.pack(pady=10)

        upload_button = tk.Button(main_window, text="Upload",width=15, command=openUploadWindow)
        upload_button.pack(pady=10)
        bt_file_manager = tk.Button(main_window, text="File Manager",width=15, command= file_manager)  
        bt_file_manager.pack(pady=10) 
        
        thread_server_p2p = threading.Thread(target=listening_p2p, args=(client_ip,client_port))
        thread_server_p2p.start()   
    else:
        main_window.deiconify()
    main_window.protocol("WM_DELETE_WINDOW", close_windows)
    main_window.mainloop()
    #threading.Thread(target=download_window.mainloop, args=()).start()
    
# endregion

# region 8: Tạo giao diện đăng nhập
login_window = tk.Tk()
login_window.title("Login Window")
login_window.geometry("500x500")

# Tạo canvas để chứa hình ảnh
canvas = tk.Canvas(login_window, width=400, height=200)
canvas.pack(pady=50)  # Căn chỉnh để hình ảnh nằm giữa trên cửa sổ

# Hình ảnh đặt ở đây
# Thay đổi đường dẫn và tên tệp ảnh tương ứng
image_path = "p2p.png"
image = tk.PhotoImage(file=image_path)
canvas.create_image(200, 100, image=image)  # Đặt hình ảnh vào giữa của Canvas

# Tạo frame chứa các phần tử dưới cùng với nút "Login"
bottom_frame = tk.Frame(login_window)
bottom_frame.pack()

# Label và Entry cho Username
label_username = tk.Label(bottom_frame, text="Username:")
label_username.grid(row=0, column=0, padx=10, pady=10, sticky="e")  # Đặt sticky="e" để căn chỉnh label về phía bên trái (East)
entry_username = tk.Entry(bottom_frame, width=30, justify="center")
entry_username.grid(row=0, column=1, padx=10, pady=10)  # Thêm padx ở đây
entry_username.insert(0, "")

# Label và Entry cho Password
label_password = tk.Label(bottom_frame, text="Password:")
label_password.grid(row=1, column=0, padx=10, pady=10, sticky="e")  # Đặt sticky="e" để căn chỉnh label về phía bên trái (East)
entry_password = tk.Entry(bottom_frame, width=30, show="*", justify="center")
entry_password.grid(row=1, column=1, padx=10, pady=10)  # Thêm padx ở đây
entry_password.insert(0, "")

# Nút "Login" và "Register"
bottom_frame = tk.Frame(login_window)
bottom_frame.pack()
button_frame = tk.Frame(bottom_frame)
button_frame.grid(row=2, column=1, pady=10, padx=20)

# Nút "Login"
login_button = tk.Button(button_frame, text="Login", width=7, command=lambda: login(entry_username, entry_password))
login_button.pack(side="left", padx=82)  # Sử dụng side="left" để nút "Login" nằm bên trái

# Nút "Register"
register_button = tk.Button(button_frame, text="Register", width=7, command=lambda: register(entry_username, entry_password))
register_button.pack(side="right", padx=0)  # Sử dụng side="right" để nút "Register" nằm bên phải
login_window.mainloop()

# endregion
