import json
import logging
import socket
import threading
from pathlib import Path
from typing import Optional, Dict, Any

import pygame
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk

from playsound import playsound

import Archi  # Importamos Archi.py
from NotiWin import mostrar_notificacionWin
from login import run_login  # Importamos el login que acabas de modificar

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("icocchat.log"),
        logging.StreamHandler()
    ]
)

# Configuración de servidor
SERVER_CONFIG_FILE = Path("server_config.json")


def load_server_config() -> Dict[str, Any]:
    """
    Carga la configuración del servidor desde un archivo JSON.

    Returns:
        Dict[str, Any]: Diccionario con la configuración del servidor.
    """
    default_config = {
        "server_ip": "190.107.177.156",
        "server_port": 12345
    }
    if SERVER_CONFIG_FILE.exists():
        try:
            with SERVER_CONFIG_FILE.open("r", encoding="utf-8") as file:
                config = json.load(file)
                logging.info("Configuración del servidor cargada desde server_config.json.")
                return config
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error cargando la configuración del servidor: {e}")
    else:
        # Crear archivo de configuración por defecto
        try:
            with SERVER_CONFIG_FILE.open("w", encoding="utf-8") as file:
                json.dump(default_config, file, ensure_ascii=False, indent=4)
            logging.info("Archivo server_config.json creado con configuración por defecto.")
        except IOError as e:
            logging.error(f"Error creando server_config.json: {e}")
    return default_config


SERVER_CONFIG = load_server_config()

# Variables globales
client_socket: Optional[socket.socket] = None
unread_messages_count: int = 0
last_sender: Optional[str] = None
root: Optional[tk.Tk] = None
chat_display: Optional[tk.Text] = None
message_entry: Optional[tk.Entry] = None


def play_notification_sound() -> None:
    """Reproduce el sonido de notificación."""
    try:
        playsound("notificacion.mp3")
    except Exception as e:
        logging.error(f"Error reproduciendo el sonido de notificación: {e}")


def receive_messages(client_socket: socket.socket) -> None:
    """
    Recibe mensajes del servidor y actualiza la interfaz de chat.

    Args:
        client_socket (socket.socket): El socket del cliente conectado al servidor.
    """
    global unread_messages_count
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                if message == "NOMBRE_EN_USO":
                    new_name = simpledialog.askstring(
                        "Nombre en uso",
                        "El nombre ya está en uso. Ingresa otro nombre:"
                    )
                    if new_name:
                        client_socket.sendall(new_name.encode('utf-8'))
                elif message.startswith("ARCHIVO"):
                    archivo_nombre = message.split(":", 1)[1]
                    recibir_archivo(archivo_nombre, client_socket)
                else:
                    logging.info(f"Mensaje recibido: {message}")
                    update_chat(message, sender="other")
                    save_message(message, sender="other")

                    if not root.focus_get():  # Si la ventana no está en primer plano
                        unread_messages_count += 1
                        mostrar_notificacionWin("Nuevo mensaje", f"Tienes {unread_messages_count} mensajes nuevos.")
                        play_notification_sound()
            else:
                logging.warning("Servidor desconectado.")
                break
        except Exception as e:
            logging.error(f"Error recibiendo mensaje: {e}")
            break


def recibir_archivo(archivo_nombre: str, client_socket: socket.socket) -> None:
    """
    Recibe un archivo del servidor y actualiza el chat.

    Args:
        archivo_nombre (str): Nombre del archivo a recibir.
        client_socket (socket.socket): El socket del cliente conectado al servidor.
    """
    try:
        save_path = filedialog.asksaveasfilename(
            initialfile=archivo_nombre,
            title="Guardar archivo como"
        )
        if save_path:
            with open(save_path, 'wb') as f:
                while True:
                    bytes_read = client_socket.recv(1024)
                    if not bytes_read:
                        break
                    f.write(bytes_read)
            update_chat(f"Se ha recibido el archivo: {archivo_nombre}", sender="other")
            save_message(f"Se ha recibido el archivo: {archivo_nombre}", sender="other")
            messagebox.showinfo("Éxito", f"Archivo '{archivo_nombre}' descargado exitosamente!")
    except Exception as e:
        logging.error(f"Error recibiendo archivo: {e}")
        messagebox.showerror("Error", f"No se pudo descargar el archivo: {e}")


def load_user_name() -> str:
    """
    Carga el nombre de usuario desde el archivo de configuración.

    Returns:
        str: Nombre de usuario.
    """
    user_file = Path("user_name.json")
    if user_file.exists():
        try:
            with user_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get("user_name", "")
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error cargando el nombre de usuario: {e}")
    return ""


def save_user_name(user_name: str) -> None:
    """
    Guarda el nombre de usuario en el archivo de configuración.

    Args:
        user_name (str): Nombre de usuario a guardar.
    """
    data = {"user_name": user_name}
    try:
        with Path("user_name.json").open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logging.info("Nombre de usuario guardado en user_name.json.")
    except IOError as e:
        logging.error(f"Error guardando el nombre de usuario: {e}")


def connect_to_server() -> None:
    """Establece la conexión con el servidor y comienza a recibir mensajes."""
    global client_socket, user_name

    user_name = load_user_name()
    if not user_name:
        user_name = simpledialog.askstring("Nombre", "¿Cómo te llamas?")
        if user_name:
            save_user_name(user_name)
        else:
            messagebox.showwarning("Nombre requerido", "Debes ingresar un nombre para conectarte.")
            return

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_CONFIG["server_ip"], SERVER_CONFIG["server_port"]))
        client_socket.sendall(user_name.encode('utf-8'))
        logging.info("Conectado al servidor.")
    except socket.error as e:
        messagebox.showerror("Error de conexión", f"No se pudo conectar al servidor: {e}")
        logging.error(f"Error de conexión: {e}")
        return

    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    load_chat_history()


def load_chat_history() -> None:
    """Carga el historial de chat desde un archivo local."""
    historial_file = Path("historial_chat.json")
    if historial_file.exists():
        try:
            with historial_file.open("r", encoding="utf-8") as file:
                messages = json.load(file)
                if isinstance(messages, list):
                    for entry in messages:
                        if isinstance(entry, dict) and "message" in entry and "sender" in entry:
                            update_chat(entry["message"], entry["sender"])
            logging.info("Historial de chat cargado desde historial_chat.json.")
        except json.JSONDecodeError:
            logging.error("Error al decodificar el archivo historial_chat.json")


def save_message(message: str, sender: str = "other") -> None:
    """
    Guarda un mensaje en el historial de chat.

    Args:
        message (str): Mensaje a guardar.
        sender (str, optional): Remitente del mensaje. Defaults to "other".
    """
    messages = []
    historial_file = Path("historial_chat.json")
    if historial_file.exists():
        try:
            with historial_file.open("r", encoding="utf-8") as file:
                messages = json.load(file)
                if not isinstance(messages, list):
                    messages = []
        except json.JSONDecodeError:
            messages = []
    messages.append({"message": message, "sender": sender})
    try:
        with historial_file.open("w", encoding="utf-8") as file:
            json.dump(messages, file, ensure_ascii=False, indent=4)
        logging.info("Mensaje guardado en historial_chat.json.")
    except IOError as e:
        logging.error(f"Error guardando el historial de chat: {e}")


def reset_notifications(event: Optional[tk.Event] = None) -> None:
    """Resetea el contador de mensajes no leídos."""
    global unread_messages_count
    unread_messages_count = 0
    logging.info("Contador de mensajes no leídos reseteado.")


def show_uploaded_files() -> None:
    """Muestra la ventana de archivos subidos."""
    Archi.mostrar_archivos(client_socket)


def subir_archivo() -> None:
    """Permite al usuario seleccionar y subir un archivo al servidor."""
    if not client_socket:
        messagebox.showwarning("No conectado", "Debes estar conectado al servidor para subir archivos.")
        return
    file_path = filedialog.askopenfilename(
        title="Seleccionar archivo",
        filetypes=[("Todos los archivos", "*.*")]
    )
    if file_path:
        file_path = Path(file_path)
        file_name = file_path.name
        try:
            client_socket.sendall(f"ARCHIVO:{file_name}".encode('utf-8'))
            with file_path.open('rb') as f:
                for bytes_read in iter(lambda: f.read(1024), b''):
                    client_socket.sendall(bytes_read)
            mensaje_formateado = f"Tú has subido el archivo: {file_name}"
            update_chat(mensaje_formateado, sender="self")
            save_message(mensaje_formateado, sender="self")
            messagebox.showinfo("Éxito", f"Archivo '{file_name}' subido exitosamente!")
            logging.info(f"Archivo '{file_name}' subido al servidor.")
        except Exception as e:
            logging.error(f"Error subiendo archivo: {e}")
            messagebox.showerror("Error", f"No se pudo subir el archivo: {e}")


def update_chat(message: str, sender: str = "other") -> None:
    """
    Actualiza la interfaz de chat con un nuevo mensaje.

    Args:
        message (str): Mensaje a mostrar.
        sender (str, optional): Remitente del mensaje. Defaults to "other".
    """
    global last_sender
    if not chat_display:
        logging.error("chat_display no está inicializado.")
        return

    chat_display.config(state=tk.NORMAL)
    if sender == "self":
        if last_sender != "self":
            chat_display.insert(tk.END, "Tú:\n", "self_name")
            last_sender = "self"
        text_to_show = message.split(":", 1)[1] if ":" in message else message
        chat_display.insert(tk.END, text_to_show + "\n", "self")
    else:
        name, text = (message.split(":", 1) if ":" in message else ("Desconocido", message))
        if last_sender != name:
            chat_display.insert(tk.END, f"{name}:\n", "other_name")
            last_sender = name
        chat_display.insert(tk.END, text + "\n", "other_text")
    chat_display.config(state=tk.DISABLED)
    chat_display.see(tk.END)
    logging.info(f"Mensaje actualizado en el chat: {message}")


def send_message(event: Optional[tk.Event] = None) -> None:
    """
    Envía el mensaje escrito por el usuario al servidor.

    Args:
        event (tk.Event, optional): Evento de teclado. Defaults to None.
    """
    global client_socket
    if not client_socket:
        messagebox.showwarning("No conectado", "Debes estar conectado al servidor para enviar mensajes.")
        return

    message = message_entry.get().strip()
    if message:
        try:
            client_socket.sendall(message.encode('utf-8'))
            update_chat(f"Tú:{message}", sender="self")
            save_message(f"Tú:{message}", sender="self")
            message_entry.delete(0, tk.END)
            logging.info(f"Mensaje enviado al servidor: {message}")
        except Exception as e:
            logging.error(f"Error enviando mensaje: {e}")
            messagebox.showerror("Error", f"No se pudo enviar el mensaje: {e}")


def run_chat() -> None:
    """Inicializa y ejecuta la interfaz de chat."""
    pygame.init()

    global root, chat_display, message_entry
    root = tk.Tk()
    root.title("Chat con Notificaciones")
    root.geometry("600x600")
    root.configure(bg="#2C2F33")

    # Configuración de estilos con ttk
    style = ttk.Style()
    style.theme_use('default')
    style.configure("TButton", padding=6, relief="flat",
                    background="#FF8C00", foreground="#FFFFFF")
    style.map("TButton",
              background=[('active', '#FFA500')])

    global last_sender
    last_sender = None

    # Widgets de la interfaz de chat
    chat_display = tk.Text(
        root, height=20, width=50, state=tk.DISABLED,
        bg="#FFFFFF", fg="#000000", font=("Arial", 12),
        wrap=tk.WORD, padx=10, pady=10
    )
    chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Configuración de etiquetas de texto
    chat_display.tag_configure("self", justify='right', background="#DCF8C6",
                               foreground="#000000", font=("Arial", 12),
                               lmargin1=10, lmargin2=10, rmargin=10)
    chat_display.tag_configure("self_name", justify='right', background="#DCF8C6",
                               foreground="#000000", font=("Arial", 12, "bold"),
                               lmargin1=10, lmargin2=10, rmargin=10)
    chat_display.tag_configure("other_name", justify='left', foreground="#FF8C00",
                                font=("Arial", 12, "bold"))
    chat_display.tag_configure("other_text", justify='left', background="#FFFFFF",
                                foreground="#000000", font=("Arial", 12),
                                lmargin1=10, lmargin2=10, rmargin=10)

    # Frame para el campo de entrada y botones
    message_frame = tk.Frame(root, bg="#2C2F33")
    message_frame.pack(fill=tk.X, padx=10, pady=10)

    message_entry = tk.Entry(message_frame, width=40, font=("Arial", 12))
    message_entry.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)
    message_entry.bind("<Return>", send_message)

    upload_button = ttk.Button(
        message_frame, text="Subir archivo", command=subir_archivo
    )
    upload_button.pack(side=tk.LEFT, padx=5)

    view_files_button = ttk.Button(
        message_frame, text="Ver archivos subidos", command=show_uploaded_files
    )
    view_files_button.pack(side=tk.LEFT, padx=5)

    root.bind("<Map>", reset_notifications)

    # Conectamos al servidor
    connect_to_server()

    root.mainloop()


def main() -> None:
    """
    Punto de entrada principal de la aplicación.
    Ejecuta el proceso de login y, si es exitoso, inicia el chat.
    """
    success = run_login()
    if success:
        run_chat()
    else:
        logging.info("No se abrió el chat, finaliza la app.")

if __name__ == "__main__":  
    main()
