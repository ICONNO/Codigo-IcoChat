import os
import json
import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from playsound import playsound
import pygame
from NotiWin import mostrar_notificacionWin
import Archi  # Importamos Archi.py
from login import run_login  # Importamos el login que acabas de modificar

# Variables globales
client_socket = None
unread_messages_count = 0
last_sender = None

def play_notification_sound():
    try:
        playsound("notificacion.mp3")
    except Exception as e:
        print(f"Error reproduciendo el sonido de notificación: {e}")

def receive_messages(client_socket):
    global unread_messages_count
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                if message == "NOMBRE_EN_USO":
                    new_name = simpledialog.askstring("Nombre en uso", "El nombre ya está en uso. Ingresa otro nombre:")
                    client_socket.send(new_name.encode('utf-8'))
                elif message.startswith("ARCHIVO"):
                    archivo_nombre = message.split(":", 1)[1]
                    with open(archivo_nombre, 'wb') as f:
                        while True:
                            bytes_read = client_socket.recv(1024)
                            if not bytes_read:
                                break
                            f.write(bytes_read)
                    update_chat(f"Se ha recibido el archivo: {archivo_nombre}", sender="other")
                    save_message(f"Se ha recibido el archivo: {archivo_nombre}", sender="other")
                else:
                    print()
                    update_chat(message, sender="other") 
                    save_message(message, sender="other")

                    if not root.focus_get():  # Si la ventana no está en primer plano
                        unread_messages_count += 1
                        mostrar_notificacionWin("Nuevo mensaje", f"Tienes {unread_messages_count} mensajes nuevos.")
            else:
                break
        except Exception as e:
            print(f"Error recibiendo mensaje: {e}")
            break

def load_user_name():
    if os.path.exists("user_name.json"):
        try:
            with open("user_name.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get("user_name", "")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error cargando el nombre de usuario: {e}")
    return ""

def save_user_name(user_name):
    data = {"user_name": user_name}
    try:
        with open("user_name.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Error guardando el nombre de usuario: {e}")

def connect_to_server():
    global client_socket, user_name

    user_name = load_user_name()
    if not user_name:
        user_name = simpledialog.askstring("Nombre", "¿Cómo te llamas?")
        save_user_name(user_name)

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('190.107.177.156', 12345))  # Cambia al puerto 12346
        client_socket.send(user_name.encode('utf-8'))
    except socket.error as e:
        messagebox.showerror("Error de conexión", f"No se pudo conectar al servidor: {e}")
        return

    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    load_chat_history()

def load_chat_history():
    if os.path.exists("historial_chat.json"):
        try:
            with open("historial_chat.json", "r", encoding="utf-8") as file:
                messages = json.load(file)
                if isinstance(messages, list):
                    for entry in messages:
                        if isinstance(entry, dict) and "message" in entry and "sender" in entry:
                            update_chat(entry["message"], entry["sender"])
        except json.JSONDecodeError:
            print("Error al decodificar el archivo historial_chat.json")

def save_message(message, sender="other"):
    messages = []
    if os.path.exists("historial_chat.json"):
        try:
            with open("historial_chat.json", "r", encoding="utf-8") as file:
                messages = json.load(file)
                if not isinstance(messages, list):
                    messages = []
        except json.JSONDecodeError:
            messages = []
    messages.append({"message": message, "sender": sender})
    try:
        with open("historial_chat.json", "w", encoding="utf-8") as file:
            json.dump(messages, file, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Error guardando el historial de chat: {e}")

def reset_notifications(event=None):
    global unread_messages_count
    unread_messages_count = 0

def show_uploaded_files():
    Archi.mostrar_archivosn 
    def sign_in(self):  # No se elimina, aunque no se use
        pass

def subir_archivo():
    if not client_socket:
        return
    file_path = filedialog.askopenfilename()
    if file_path:
        file_name = os.path.basename(file_path)
        try:
            client_socket.send(f"ARCHIVO:{file_name}".encode('utf-8'))
            with open(file_path, 'rb') as f:
                while (bytes_read := f.read(1024)):
                    client_socket.send(bytes_read)
            mensaje_formateado = f"Tú has subido el archivo: {file_name}"
            update_chat(mensaje_formateado, sender="self")
            save_message(mensaje_formateado, sender="self")
        except Exception as e:
            print(f"Error subiendo archivo: {e}")

def update_chat(message, sender="other"):
    global last_sender
    chat_display.config(state=tk.NORMAL)
    if sender == "self":
        if last_sender != "self":
            chat_display.insert(tk.END, "Tú:\n", "self_name")
            last_sender = "self"
        # Dividimos por ":" si existe
        if ":" in message:
            text_to_show = message.split(":", 1)[1]
        else:
            text_to_show = message
        chat_display.insert(tk.END, text_to_show + "\n", "self")
    else:
        if ":" in message:
            name, text = message.split(":", 1)
        else:
            name, text = ("Desconocido", message)
        if last_sender != name:
            chat_display.insert(tk.END, name + ":\n", "other_name")
            last_sender = name
        chat_display.insert(tk.END, text + "\n", "other_text")
    chat_display.config(state=tk.DISABLED)
    chat_display.see(tk.END)

def send_message(event=None):
    global client_socket
    message = message_entry.get()
    if message:
        try:
            client_socket.send(message.encode('utf-8'))
            update_chat(f"Tú:{message}", sender="self")
            save_message(f"Tú:{message}", sender="self")
            message_entry.delete(0, tk.END)
        except Exception as e:
            print(f"Error enviando mensaje: {e}")

def run_chat():
    """
    Encapsulamos la creación de la ventana y sus widgets para el chat,
    para abrirlo solo si el login tuvo éxito (Resp=1).
    """
    pygame.init()

    global root, chat_display, message_frame, message_entry
    root = tk.Tk()
    root.title("Chat con Notificaciones")
    root.config(bg="#2C2F33")

    global last_sender
    last_sender = None

    # Widgets de la interfaz de chat
    global chat_display
    chat_display = tk.Text(
        root, height=20, width=50, state=tk.DISABLED,
        bg="#FFFFFF", fg="#000000", font=("Arial", 12),
        wrap=tk.WORD, padx=10, pady=10
    )
    chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    chat_display.tag_configure("self", justify='right', background="#FFFFFF",
                               foreground="#000000", font=("Arial", 12),
                               lmargin1=10, lmargin2=10, rmargin=10)
    chat_display.tag_configure("self_name", justify='right', background="#FFFFFF",
                               foreground="#000000", font=("Arial", 12, "bold"),
                               lmargin1=10, lmargin2=10, rmargin=10)
    chat_display.tag_configure("other_name", justify='left', foreground="#FF8C00",
                               font=("Arial", 12, "bold"))
    chat_display.tag_configure("other_text", justify='left', background="#FFFFFF",
                               foreground="#000000", font=("Arial", 12),
                               lmargin1=10, lmargin2=10, rmargin=10)

    global message_frame
    message_frame = tk.Frame(root, bg="#2C2F33")
    message_frame.pack(fill=tk.X, padx=10, pady=10)

    global message_entry
    message_entry = tk.Entry(message_frame, width=40, font=("Arial", 12))
    message_entry.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

    upload_button = tk.Button(
        message_frame, text="Subir archivo", command=subir_archivo,
        bg="#FF8C00", activebackground="#FF8C00", highlightbackground="#FF8C00",
        highlightcolor="#FF8C00", relief="raised", font=("Arial", 12), fg="#FFFFFF"
    )
    upload_button.pack(side=tk.LEFT, padx=5)

    view_files_button = tk.Button(
        message_frame, text="Ver archivos subidos", command=show_uploaded_files,
        bg="#FF8C00", activebackground="#FF8C00", highlightbackground="#FF8C00",
        highlightcolor="#FF8C00", relief="raised", font=("Arial", 12), fg="#FFFFFF"
    )
    view_files_button.pack(side=tk.LEFT, padx=5)

    root.bind("<Return>", send_message)
    root.bind("<Map>", reset_notifications)

    # Conectamos al servidor
    connect_to_server()

    root.mainloop()

def main():
    """
    1) Llamamos run_login().
    2) Si es True => abrimos run_chat().
    3) Si es False => no abrimos nada.
    """
    success = run_login()
    if success:
        run_chat()
    else:
        print("No abrimos el chat, finaliza la app.")

if __name__ == "__main__":
    main()
