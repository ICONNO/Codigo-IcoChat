import os
import socket
import tkinter as tk
from tkinter import simpledialog
import threading
import json
from noti3 import mostrar_notificacion  # Importar desde notificaciones.py
from login import run_login  # Importar la función de login

# Configuración global para la fuente y el tamaño
FONT_NAME = "Times New Roman"
FONT_SIZE = 19  # Aumentar el tamaño de la fuente
FONT_BOLD = (FONT_NAME, FONT_SIZE, "bold")
FONT_NORMAL = (FONT_NAME, FONT_SIZE)

# Función para recibir mensajes
def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                if message == "NOMBRE_EN_USO":
                    new_name = simpledialog.askstring("Nombre en uso", "El nombre ya está en uso. Ingresa otro nombre:")
                    client_socket.send(new_name.encode('utf-8'))
                elif message.startswith("LLAMADA"):  # Si el mensaje indica una llamada
                    update_chat("Recibiendo llamada...", "left")
                    mostrar_notificacion("Tienes una llamada entrante.")
                elif message == "FIN_LLAMADA":  # Si la llamada ha terminado
                    update_chat("Llamada finalizada.", "left")
                else:
                    update_chat(message, "left")  # Actualiza el chat
                    save_message(message)  # Guardar mensaje recibido en historial
                    mostrar_notificacion(message)  # Muestra notificación visual
            else:
                break
        except Exception as e:
            print(f"Error al recibir mensaje: {e}")
            break

# Función para enviar un mensaje al servidor
def send_message(event=None):
    message = message_entry.get()
    if message:
        client_socket.send(message.encode('utf-8'))
        update_chat(f"Tú: {message}", "right")
        save_message(f"Tú: {message}")  # Guardar mensaje enviado en historial
        message_entry.delete(0, tk.END)

# Función para actualizar la ventana de chat
def update_chat(message, align):
    if isinstance(message, str):  # Verificar que 'message' sea una cadena
        chat_display.config(state=tk.NORMAL)
        chat_display.insert(tk.END, message + "\n")
        chat_display.config(state=tk.DISABLED)
        chat_display.see(tk.END)  # Desplazar hacia abajo automáticamente

# Función para cargar el nombre del usuario desde un archivo
def load_user_name():
    if os.path.exists("user_name.json"):
        with open("user_name.json", "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                return data.get("user_name", "")
            except json.JSONDecodeError:
                return ""
    return ""

# Función para guardar el nombre del usuario en un archivo
def save_user_name(user_name):
    data = {"user_name": user_name}
    with open("user_name.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Conectar al servidor
def connect_to_server():
    global client_socket, user_name

    # Verificar si hay un nombre guardado en el archivo
    user_name = load_user_name()

    if not user_name:
        # Si no existe, pedir el nombre al usuario
        user_name = simpledialog.askstring("Nombre", "¿Cómo te llamas?")
        if not user_name:
            user_name = "Anónimo"  # Nombre por defecto si no se ingresa uno

        # Guardar el nombre en el archivo para futuras sesiones
        save_user_name(user_name)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('190.107.177.156', 12345))  # Cambia la IP al servidor

    # Enviar el nombre al servidor
    client_socket.send(user_name.encode('utf-8'))

    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

    load_chat_history()  # Cargar historial de chat al iniciar

# Función para cargar el historial de chat desde el archivo JSON
def load_chat_history():
    if os.path.exists("historial_chat.json"):
        with open("historial_chat.json", "r", encoding="utf-8") as file:
            try:
                messages = json.load(file)
                for message in messages:
                    if isinstance(message, str):  # Verificar que el mensaje sea una cadena
                        update_chat(message, "left" if message.startswith("Tú:") else "right")
            except json.JSONDecodeError:
                pass  # Si el archivo está vacío o corrupto, lo ignoramos

# Función para guardar el historial de chat en un archivo JSON
def save_message(message):
    if os.path.exists("historial_chat.json"):
        with open("historial_chat.json", "r", encoding="utf-8") as file:
            try:
                messages = json.load(file)
            except json.JSONDecodeError:
                messages = []  # Si el archivo está vacío o corrupto, iniciamos una lista vacía
    else:
        messages = []

    if isinstance(message, str):  # Verificar que 'message' sea una cadena
        messages.append(message)

    with open("historial_chat.json", "w", encoding="utf-8") as file:
        json.dump(messages, file, ensure_ascii=False, indent=4)

# Crear la ventana principal
if __name__ == "__main__":
    # Ejecutar el login
    if not run_login():
        exit()  # Salir si el login no es exitoso

    root = tk.Tk()
    root.title("Chat con Notificaciones")
    root.config(bg="grey")

    # Configurar la ventana para que se abra casi en pantalla completa
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = int(screen_width * 0.9)
    window_height = int(screen_height * 0.9)
    x_position = (screen_width // 2) - (window_width // 2)
    y_position = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # Crear un marco para organizar los widgets
    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    # Crear los widgets de la interfaz de chat
    chat_display = tk.Text(frame, height=20, width=50, state=tk.DISABLED, bg="white", fg="black", font=FONT_NORMAL)
    chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)  # Ajuste al tamaño de la ventana

    # Crear una barra de desplazamiento
    scrollbar = tk.Scrollbar(frame, command=chat_display.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    chat_display.config(yscrollcommand=scrollbar.set)

    message_label = tk.Label(root, text="Escribe tu mensaje:", bg="grey", font=FONT_NORMAL)
    message_label.pack()

    message_entry = tk.Entry(root, width=50, font=("Arial", 20))  # Aumentar el tamaño de la fuente
    message_entry.pack(pady=10)

    # Vincular la tecla "Enter" para enviar mensaje
    root.bind('<Return>', send_message)

    # Vincular la rueda del ratón para desplazarse
    def on_mouse_wheel(event):
        chat_display.yview_scroll(int(-1*(event.delta/120)), "units")

    chat_display.bind_all("<MouseWheel>", on_mouse_wheel)

    # Conectar al servidor
    connect_to_server()

    # Iniciar la interfaz gráfica
    root.mainloop()
