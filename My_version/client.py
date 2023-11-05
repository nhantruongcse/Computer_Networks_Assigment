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

# region 1: Tao host va connect

HOST = "127.0.0.1"
PORT = 8080
HOST_ip_p2p = "192.168.0.100"
HOST_port_p2p = 51295
ipaddress.ip_address('192.168.0.100')

#connect với server:
CLIENTSOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
CLIENTSOCKET.connect((HOST, PORT))

#Tạo P2P server:
client_ip, client_port = CLIENTSOCKET.getsockname()
# Tạo socket server với địa chỉ IP và cổng từ CLIENTSOCKET

SERVER_P2P = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    SERVER_P2P.bind((client_ip, client_port))
    print(f'* Running on http://{client_ip,}:{client_port}')
    SERVER_P2P.listen() 
except socket.error as e:
    print(f'socket error: {e}')
    print('socket error: %s' %(e))


# endregion

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
    main_window.destroy()
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

    search_button = tk.Button(download_window, text="Search File to Download", command=lambda: searchButtonClicked(entry_filenameDownload, lst_respond))
    bt_download = tk.Button(download_window, text="Download")    
    search_button.pack(pady=10)        
    lst_respond.pack(pady=10)
    bt_download.pack(pady=10)
    back_button = tk.Button(download_window, text="Back", command=lambda:( download_window.destroy(),chooseLayout())  )  
    back_button.pack(side="bottom", anchor="sw", pady=20, padx=20)    

    ip_select = lst_respond.selection_get()[0]
    port_select = lst_respond.selection_get()[1]
    path_select = lst_respond.selection_get()[2]
    bt_download.bind("download",download_file(ip_select, port_select,path_select))
    download_window.mainloop()

def download_file(ip,port,path):
    host_peer = ip
    port_peer = port
    data_download = {
        'method' : 'download',
        'path' : res[0]['path']
    }
    json_data_download = json.dumps(data_download)
    CLIENTSOCKET.close()
    #tạo 1 socket mới để kết nối
    p2p_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    p2p_socket2.connect((host_peer, port_peer))
    p2p_socket2.sendall(json_data_download.encode())

    with open(res[0]['path'].split('/')[-1], 'wb') as file1:
        while True:
            data = p2p_socket2.recv(1024)
            if not data:
                break
            file1.write(data)
    

    p2p_socket2.close()
    return



# endregion

# region 5: Phần Upload info lên server
# Hàm xử lý nút "File to Upload"
def uploadButtonClicked(entry_filenameUpload, entry_file_path, label_file_size):
    filename = entry_filenameUpload.get()
    path = entry_file_path.get()
    file_Size = label_file_size.cget("text")
    sendInformationOfFileToServerToSaveToDatabase(filename,file_Size , path)
def sendInformationOfFileToServerToSaveToDatabase(filename, size, path):
    data = {
        'filename' : filename,
        'size' : size,
        'path' : path,        
        'method' : 'upload',
    }
    json_data = json.dumps(data)
    CLIENTSOCKET.send(json_data.encode())
    receiveUploadResponseFromServer()
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
    main_window.destroy()
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
            file_size_text = f"File Size: {file_size} bytes"
            label_file_size.config(text=file_size_text)

    label_file_path = tk.Label(upload_window, text="File Path:")
    label_file_path.pack(pady=10)

    entry_file_path = tk.Entry(upload_window)
    entry_file_path.pack(pady=10)

    button_browse = tk.Button(upload_window, text="Choose File", command=browse_file)
    button_browse.pack(pady=10)

    label_file_size = tk.Label(upload_window, text="File Size: N/A")
    label_file_size.pack(pady=10)

    upload_button = tk.Button(upload_window, text="File to Upload", command=lambda: uploadButtonClicked(entry_filenameUpload, entry_file_path, label_file_size))
    upload_button.pack(pady=10)
    upload_window.mainloop()

# endregion

# region 6: Mở cửa sổ chọn layout và Ping

def chooseLayout():
    global main_window
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
    download_button = tk.Button(main_window, text="Download", command=openDownloadWindow)
    download_button.pack(pady=10)

    upload_button = tk.Button(main_window, text="Upload", command=openUploadWindow)
    upload_button.pack(pady=10)
    main_window.mainloop()
def ping(host):
    # Gọi lệnh ping từ hệ điều hành Windows
    result = subprocess.run(['ping', '-n', '4', host], capture_output=True, text=True)
    
    # Kiểm tra kết quả trả về
    if result.returncode == 0:
        # Lấy thông tin về độ trễ từ output
        lines = result.stdout.strip().split('\n')
        time_line = lines[-1]  # Dòng cuối cùng chứa thông tin về độ trễ
        time = time_line.split('=')[1].split()[0]  # Lấy giá trị độ trễ
        # Loại bỏ ký tự ',' và 'ms'
        time = time.replace(',', '').replace('ms', '')

        return float(time)
    else:
        return 9999999999

# endregion

# region 7: Tạo giao diện đăng nhập
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



