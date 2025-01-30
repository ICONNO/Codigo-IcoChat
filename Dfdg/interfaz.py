import os
import socket
import tkinter as tk
from tkinter import simpledialog
import threading
import json
from noti3 import mostrar_notificacion  # Importar desde notificaciones.py
from pathlib import Path

# Configuración global para la fuente y el tamaño
FONT_NAME = "Times New Roman"
FONT_SIZE = 19
FONT_BOLD = (FONT_NAME, FONT_SIZE, "bold")
FONT_NORMAL = (FONT_NAME, FONT_SIZE)

# Archivos de configuración
USER_NAME_FILE = Path("user_name.json")
CHAT_HISTORY_FILE = Path("historial_chat.json")
SERVER_ADDRESS = ('190.107.177.156', 12345)


def receive_messages(client_socket):
    """Recibe mensajes del servidor y actualiza la interfaz."""
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                if message == "NOMBRE_EN_USO":
                    handle_name_in_use(client_socket)
                elif message.startswith("LLAMADA"):
                    handle_incoming_call()
                elif message == "FIN_LLAMADA":
                    update_chat("Llamada finalizada.", "left")
                else:
                    update_chat(message, "left")
                    save_message(message)
                    mostrar_notificacion(message)
            else:
                break
        except Exception as e:
            print(f"Error al recibir mensaje: {e}")
            break


def handle_name_in_use(client_socket):
    """Maneja la situación cuando el nombre de usuario ya está en uso."""
    new_name = simpledialog.askstring("Nombre en uso", "El nombre ya está en uso. Ingresa otro nombre:")
    if new_name:
        client_socket.send(new_name.encode('utf-8'))


def handle_incoming_call():
    """Maneja una llamada entrante."""
    update_chat("Recibiendo llamada...", "left")
    mostrar_notificacion("Tienes una llamada entrante.")


def send_message(event=None):
    """Envía un mensaje al servidor."""
    message = message_entry.get().strip()
    if message:
        client_socket.send(message.encode('utf-8'))
        update_chat(f"Tú: {message}", "right")
        save_message(f"Tú: {message}")
        message_entry.delete(0, tk.END)


def update_chat(message, align):
    """Actualiza el área de chat con el nuevo mensaje."""
    if isinstance(message, str):
        chat_display.config(state=tk.NORMAL)
        chat_display.insert(tk.END, message + "\n")
        chat_display.config(state=tk.DISABLED)
        chat_display.see(tk.END)


def load_user_name():
    """Carga el nombre de usuario desde un archivo JSON."""
    if USER_NAME_FILE.exists():
        try:
            with USER_NAME_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get("user_name", "")
        except json.JSONDecodeError:
            return ""
    return ""


def save_user_name(user_name):
    """Guarda el nombre de usuario en un archivo JSON."""
    data = {"user_name": user_name}
    with USER_NAME_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def connect_to_server():
    """Establece la conexión con el servidor y comienza a recibir mensajes."""
    global client_socket, user_name

    user_name = load_user_name()
    if not user_name:
        user_name = simpledialog.askstring("Nombre", "¿Cómo te llamas?") or "Anónimo"
        save_user_name(user_name)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(SERVER_ADDRESS)
        client_socket.send(user_name.encode('utf-8'))
    except Exception as e:
        mostrar_notificacion("No se pudo conectar al servidor.")
        print(f"Error al conectar al servidor: {e}")
        return

    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    load_chat_history()


def load_chat_history():
    """Carga el historial de chat desde un archivo JSON."""
    if CHAT_HISTORY_FILE.exists():
        try:
            with CHAT_HISTORY_FILE.open("r", encoding="utf-8") as file:
                messages = json.load(file)
                for message in messages:
                    if isinstance(message, str):
                        align = "left" if message.startswith("Tú:") else "right"
                        update_chat(message, align)
        except json.JSONDecodeError:
            pass


def save_message(message):
    """Guarda un mensaje en el historial de chat."""
    messages = []
    if CHAT_HISTORY_FILE.exists():
        try:
            with CHAT_HISTORY_FILE.open("r", encoding="utf-8") as file:
                messages = json.load(file)
        except json.JSONDecodeError:
            pass

    if isinstance(message, str):
        messages.append(message)

    with CHAT_HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(messages, file, ensure_ascii=False, indent=4)


def on_mouse_wheel(event):
    """Permite el desplazamiento del chat con la rueda del ratón."""
    chat_display.yview_scroll(int(-1 * (event.delta / 120)), "units")


# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("Chat con Notificaciones")
root.config(bg="grey")

# Configuración de la ventana
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = int(screen_width * 0.9)
window_height = int(screen_height * 0.9)
x_position = (screen_width // 2) - (window_width // 2)
y_position = (screen_height // 2) - (window_height // 2)
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

# Marco principal
frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

# Área de chat
chat_display = tk.Text(
    frame,
    height=20,
    width=50,
    state=tk.DISABLED,
    bg="white",
    fg="black",
    font=FONT_NORMAL
)
chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Barra de desplazamiento
scrollbar = tk.Scrollbar(frame, command=chat_display.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
chat_display.config(yscrollcommand=scrollbar.set)

# Etiqueta y entrada de mensaje
message_label = tk.Label(root, text="Escribe tu mensaje:", bg="grey", font=FONT_NORMAL)
message_label.pack()

message_entry = tk.Entry(root, width=50, font=("Arial", 20))
message_entry.pack(pady=10)
message_entry.bind('<Return>', send_message)

# Eventos de la rueda del ratón
chat_display.bind_all("<MouseWheel>", on_mouse_wheel)

# Conexión al servidor y ejecución de la interfaz
connect_to_server()
root.mainloop()
