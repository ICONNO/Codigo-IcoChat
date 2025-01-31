# icoappchat.py

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

import Archi
from login import run_login
from config import DATA_DIR, ASSETS_DIR

import platform
from PIL import Image, ImageTk
import customtkinter as ctk

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# -------------------------
# IMPORTACIONES CONDICIONALES DE NOTIFICACIONES
# -------------------------
from tkinter import messagebox

mostrar_notificacion = None

def seleccionar_notificacion_funcion():
    """
    Selecciona y asigna la función de notificación adecuada según el sistema operativo.
    """
    global mostrar_notificacion
    sistema_operativo = platform.system()
    
    if sistema_operativo == 'Windows':
        try:
            from NotiWin import mostrar_notificacionWin
            mostrar_notificacion = mostrar_notificacionWin
            logging.info("Usando NotiWin para notificaciones en Windows.")
        except ImportError as e:
            logging.error(f"No se pudo importar NotiWin: {e}")
            # Fallback a una función genérica
            mostrar_notificacion = lambda titulo, mensaje, duracion=5, icon_path=None: messagebox.showinfo(titulo, mensaje)
    elif sistema_operativo == 'Linux':
        try:
            from noti3 import mostrar_notificacion as mostrar_notificacion_linux
            mostrar_notificacion = mostrar_notificacion_linux
            logging.info("Usando noti3 para notificaciones en Linux.")
        except ImportError as e:
            logging.error(f"No se pudo importar noti3: {e}")
            # Fallback a una función genérica
            mostrar_notificacion = lambda titulo, mensaje, duracion=5, icon_path=None: messagebox.showinfo(titulo, mensaje)
    else:
        # Función genérica para otros sistemas operativos
        mostrar_notificacion = lambda titulo, mensaje, duracion=5, icon_path=None: messagebox.showinfo(titulo, mensaje)
        logging.info("Usando función de notificación genérica para el sistema operativo actual.")

# Llama a la función para seleccionar la función de notificación adecuada al inicio
seleccionar_notificacion_funcion()

# -------------------------
# CONFIGURACIÓN DE SERVIDOR
# -------------------------
SERVER_CONFIG_FILE = DATA_DIR / "server_config.json"

def load_server_config() -> Dict[str, Any]:
    """Carga la configuración del servidor desde un archivo JSON."""
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

# -------------------------
# VARIABLES GLOBALES (CHAT)
# -------------------------
client_socket: Optional[socket.socket] = None
unread_messages_count: int = 0
last_sender: Optional[str] = None
username: str = ""  # Variable para almacenar el nombre de usuario

# Guardamos la instancia de la interfaz para poder llamarla
app = None  
root: Optional[tk.Tk] = None

# -------------------------
# FUNCIONES DE AUDIO/LOGIN
# -------------------------
def play_notification_sound() -> None:
    """Reproduce el sonido de notificación."""
    try:
        sound_path = ASSETS_DIR / "notificacion.mp3"
        playsound(str(sound_path))
    except Exception as e:
        logging.error(f"Error reproduciendo el sonido de notificación: {e}")

# -------------------------
# MANEJO DE MENSAJES
# -------------------------
def receive_messages(client_socket: socket.socket) -> None:
    """
    Recibe mensajes del servidor y actualiza la interfaz de chat
    usando app.actualizar_chat(...).
    """
    global unread_messages_count, username
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
                        username = new_name  # Actualizar el nombre de usuario
                elif message.startswith("ARCHIVO"):
                    archivo_nombre = message.split(":", 1)[1]
                    recibir_archivo(archivo_nombre, client_socket)
                else:
                    logging.info(f"Mensaje recibido: {message}")

                    # Parsear remitente y contenido
                    if ": " in message:
                        remitente, contenido = message.split(": ", 1)
                    else:
                        remitente, contenido = "Desconocido", message

                    # Ignorar mensajes propios ecoados
                    if remitente == username:
                        continue

                    # Guardar y mostrar mensajes de otros usuarios
                    save_message(message, sender="other")
                    
                    if app:
                        app.actualizar_chat(message)
                    else:
                        logging.warning("No hay instancia de app para actualizar el chat.")

                    # Notificación si la ventana no está en foco
                    if root and not root.focus_get():
                        unread_messages_count += 1
                        mostrar_notificacion("Nuevo mensaje", f"Tienes {unread_messages_count} mensajes nuevos.")
                        play_notification_sound()
            else:
                logging.warning("Servidor desconectado.")
                break
        except Exception as e:
            logging.error(f"Error recibiendo mensaje: {e}")
            break

def recibir_archivo(archivo_nombre: str, client_socket: socket.socket) -> None:
    """
    Recibe un archivo del servidor y actualiza el chat con app.actualizar_chat().
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
            if app:
                app.actualizar_chat(f"Se ha recibido el archivo: {archivo_nombre}")
            messagebox.showinfo("Éxito", f"Archivo '{archivo_nombre}' descargado exitosamente!")
            # Usar la función de notificación adecuada
            mostrar_notificacion("Archivo recibido", f"Archivo '{archivo_nombre}' descargado exitosamente.")
    except Exception as e:
        logging.error(f"Error recibiendo archivo: {e}")
        messagebox.showerror("Error", f"No se pudo descargar el archivo: {e}")
        # Usar la función de notificación adecuada
        mostrar_notificacion("Error", f"No se pudo descargar el archivo: {e}.")

# -------------------------
# USUARIO Y LOGIN
# -------------------------
def load_user_name() -> str:
    """Carga el nombre de usuario desde un archivo JSON."""
    user_file = DATA_DIR / "user_name.json"
    if user_file.exists():
        try:
            with user_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get("user_name", "")
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error cargando el nombre de usuario: {e}")
    return ""

def save_user_name(user_name: str) -> None:
    """Guarda el nombre de usuario en un archivo JSON."""
    data = {"user_name": user_name}
    try:
        with (DATA_DIR / "user_name.json").open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logging.info("Nombre de usuario guardado en user_name.json.")
    except IOError as e:
        logging.error(f"Error guardando el nombre de usuario: {e}")

# -------------------------
# CONEXIÓN AL SERVIDOR
# -------------------------
def connect_to_server() -> None:
    """Establece la conexión con el servidor y comienza a recibir mensajes."""
    global client_socket, username

    # Carga/solicita el nombre de usuario
    user_name = load_user_name()
    if not user_name:
        user_name = simpledialog.askstring("Nombre", "¿Cómo te llamas?")
        if user_name:
            save_user_name(user_name)
            username = user_name  # Asignar el nombre de usuario
        else:
            messagebox.showwarning("Nombre requerido", "Debes ingresar un nombre para conectarte.")
            return
    else:
        username = user_name  # Asignar el nombre de usuario

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_CONFIG["server_ip"], SERVER_CONFIG["server_port"]))
        client_socket.sendall(user_name.encode('utf-8'))
        logging.info("Conectado al servidor.")
    except socket.error as e:
        messagebox.showerror("Error de conexión", f"No se pudo conectar al servidor: {e}")
        logging.error(f"Error de conexión: {e}")
        return

    # Hilo para recibir mensajes
    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    load_chat_history()

# -------------------------
# HISTORIAL DE CHAT
# -------------------------
def load_chat_history() -> None:
    """Carga el historial de chat desde un archivo local."""
    historial_file = DATA_DIR / "historial_chat.json"
    if historial_file.exists():
        try:
            with historial_file.open("r", encoding="utf-8") as file:
                messages = json.load(file)
                if isinstance(messages, list):
                    # Recupera y muestra mensajes usando app.actualizar_chat(...)
                    for entry in messages:
                        if isinstance(entry, dict) and "message" in entry and "sender" in entry:
                            if app:
                                if entry["sender"] == "self":
                                    # El mensaje es tuyo, dirección=right
                                    remitente = "Tú"
                                    contenido = entry["message"]
                                    app.actualizar_chat(f"{remitente}: {contenido}")
                                else:
                                    app.actualizar_chat(entry["message"])
            logging.info("Historial de chat cargado desde historial_chat.json.")
        except json.JSONDecodeError:
            logging.error("Error al decodificar el archivo historial_chat.json")

def save_message(message: str, sender: str = "other") -> None:
    """Guarda un mensaje en el historial de chat."""
    messages = []
    historial_file = DATA_DIR / "historial_chat.json"
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

# -------------------------
# ACCIONES
# -------------------------
def reset_notifications(event: Optional[tk.Event] = None) -> None:
    """Resetea el contador de mensajes no leídos."""
    global unread_messages_count
    unread_messages_count = 0
    logging.info("Contador de mensajes no leídos reseteado.")

def show_uploaded_files() -> None:
    """Muestra la ventana de archivos subidos."""
    if client_socket:
        Archi.mostrar_archivos(client_socket)
    else:
        messagebox.showwarning("No conectado", "Debes estar conectado para ver archivos subidos.")

def subir_archivo() -> None:
    """Permite al usuario seleccionar y subir un archivo al servidor."""
    global client_socket
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
            if app:
                # Insertar mensaje en la interfaz
                app.actualizar_chat(f"Tú: has subido el archivo: {file_name}")
            save_message(f"Tú: has subido el archivo: {file_name}", sender="self")
            messagebox.showinfo("Éxito", f"Archivo '{file_name}' subido exitosamente!")
            # Usar la función de notificación adecuada
            mostrar_notificacion("Archivo Subido", f"Archivo '{file_name}' subido exitosamente.")
            logging.info(f"Archivo '{file_name}' subido al servidor.")
        except Exception as e:
            logging.error(f"Error subiendo archivo: {e}")
            messagebox.showerror("Error", f"No se pudo subir el archivo: {e}")
            # Usar la función de notificación adecuada
            mostrar_notificacion("Error", f"No se pudo subir el archivo: {e}.")

# -------------------------
# ENVÍO DE MENSAJES
# -------------------------
def send_message(event: Optional[tk.Event] = None) -> None:
    """
    Envía el mensaje escrito por el usuario al servidor,
    y muestra el mensaje con app.actualizar_chat(...).
    """
    global client_socket, username
    if not client_socket:
        messagebox.showwarning("No conectado", "Debes estar conectado al servidor para enviar mensajes.")
        return

    texto = app.entrada_mensaje.get().strip()  # Obtenemos el texto del Entry en la interfaz
    if texto:
        try:
            client_socket.sendall(texto.encode('utf-8'))
            # Insertar en la interfaz
            app.actualizar_chat(f"Tú: {texto}")
            # Guardar en el historial
            save_message(texto, sender="self")  # Guardar solo el mensaje sin "Tú: "
            # Limpiar el campo
            app.entrada_mensaje.delete(0, tk.END)
            logging.info(f"Mensaje enviado al servidor: {texto}")
        except Exception as e:
            logging.error(f"Error enviando mensaje: {e}")
            messagebox.showerror("Error", f"No se pudo enviar el mensaje: {e}")
            # Usar la función de notificación adecuada
            mostrar_notificacion("Error", f"No se pudo enviar el mensaje: {e}.")
    else:
        messagebox.showwarning("Mensaje vacío", "No puedes enviar un mensaje vacío.")

# -------------------------
# CLASE ChatUI (Interfaz)
# -------------------------
class ChatUI:
    """
    Clase para manejar la interfaz gráfica del chat
    con estilo oscuro y acentos en naranja.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Chat")

        # Tamaño de la ventana: 80% del tamaño de la pantalla
        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()
        self.root.geometry(f"{int(ancho_pantalla * 0.8)}x{int(alto_pantalla * 0.8)}")  # Tamaño más manejable

        # Tamaños de fuente e iconos ajustados
        self.tamano_fuente = max(10, int(alto_pantalla * 0.015))  # Fuente más pequeña
        self.tamano_icono = (int(alto_pantalla * 0.03), int(alto_pantalla * 0.03))  # Iconos más pequeños
        self.fuente_dinamica = ("Arial", self.tamano_fuente)

        self.imagenes = {}
        self.ruta_assets = Path(__file__).resolve().parent.parent / 'assets'

        self.cargar_imagenes()
        self.configurar_estilos()
        self.configurar_lista_chats()
        self.configurar_titulo()
        self.configurar_area_mensajes()
        self.configurar_barra_acciones()

        self.configurar_fondo()

        self.root.bind('<Return>', self.enviar_mensaje_evento)
        self.vincular_eventos_mouse()

    def configurar_estilos(self):
        """Configura los estilos de los widgets."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Vertical.TScrollbar",
            background="#808080",
            troughcolor="#2D2D2D",
            bordercolor="#2D2D2D"
        )
        style.map(
            "Custom.Vertical.TScrollbar",
            background=[('active', '#2D2D2D')]
        )
        logger.info("Estilos de ttk configurados.")

    def cargar_imagenes(self):
        """Carga y redimensiona las imágenes utilizadas en los botones."""
        rutas_imagenes = {
            'send': self.ruta_assets / 'iconos' / 'send.png',
            'photo': self.ruta_assets / 'iconos' / 'photo.png',
            'mention': self.ruta_assets / 'iconos' / 'mention.png',
            'file': self.ruta_assets / 'iconos' / 'file.png',               
        }
        for clave, ruta in rutas_imagenes.items():
            imagen = self.redimensionar_imagen(ruta, self.tamano_icono)
            if imagen:
                self.imagenes[clave] = imagen
                logger.info(f"Imagen cargada: {clave} desde {ruta}")
            else:
                logger.error(f"Fallo al cargar la imagen: {ruta}")

    def redimensionar_imagen(self, ruta_imagen: Path, tamaño: tuple[int, int]) -> Optional[ImageTk.PhotoImage]:
        """Redimensiona una imagen y la convierte a PhotoImage."""
        try:
            with Image.open(ruta_imagen) as imagen:
                imagen = imagen.convert("RGBA")
                imagen_redimensionada = imagen.resize(tamaño, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(imagen_redimensionada)
        except FileNotFoundError:
            logger.error(f"No se encontró la imagen: {ruta_imagen}")
        except Exception as e:
            logger.error(f"Error al redimensionar la imagen {ruta_imagen}: {e}")
        return None

    def configurar_fondo(self):
        """Configura el color de fondo de la ventana principal."""
        self.root.configure(bg="#1A1A1A")
        logger.info("Fondo configurado con color sólido.")

    def configurar_lista_chats(self):
        """Configura la lista de chats en el lateral izquierdo."""
        self.frame_lista_chats = tk.Frame(self.root, bg="#3D3D3D", width=200)
        self.frame_lista_chats.pack(side=tk.LEFT, fill=tk.Y)
        logger.info("Lista de chats configurada.")

        self.rectangulo_izquierdo = tk.Frame(
            self.frame_lista_chats,
            bg="#2D2D2D",
            width=180,
            height=50
        )
        self.rectangulo_izquierdo.pack(pady=20, padx=10, fill=tk.X)

        self.label_rectangulo = tk.Label(
            self.rectangulo_izquierdo,
            text="Chat Grupal",
            bg="#2D2D2D",
            fg="white",
            font=("Arial", 12, "bold")  # Tamaño de fuente reducido y negrita
        )
        self.label_rectangulo.pack(expand=True, fill="both")

    def configurar_titulo(self):
        """Configura el título de la ventana de chat."""
        self.frame_titulo = tk.Frame(self.root, bg="#3D3D3D")
        self.frame_titulo.pack(side=tk.TOP, fill=tk.X)

        self.label_titulo = tk.Label(
            self.frame_titulo,
            text="Chat Grupal",
            font=("Alatsi", 14, "bold"),  # Tamaño de fuente reducido y negrita
            bg="#3D3D3D",
            fg="white",
            anchor="center"
        )
        self.label_titulo.pack(pady=5)

        self.linea_separadora = tk.Frame(self.root, height=2, bg="white")
        self.linea_separadora.pack(fill=tk.X, padx=200)  # Ajusta el padding para que no ocupe toda la anchura
        logger.info("Título configurado.")

    def configurar_area_mensajes(self):
        """Configura el área donde se muestran los mensajes del chat."""
        self.frame_mensajes = tk.Frame(self.root, bg="#2D2D2D")
        self.frame_mensajes.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        logger.info("Área de mensajes configurada.")

        self.canvas_mensajes = tk.Canvas(
            self.frame_mensajes,
            bg="#2D2D2D",
            highlightthickness=0
        )
        self.canvas_mensajes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(
            self.frame_mensajes,
            command=self.canvas_mensajes.yview,
            style="Custom.Vertical.TScrollbar"
        )
        self.canvas_mensajes.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.frame_contenedor = tk.Frame(self.canvas_mensajes, bg="#2D2D2D")
        self.canvas_mensajes.create_window((0, 0), window=self.frame_contenedor, anchor='nw')

        self.frame_contenedor.bind(
            "<Configure>",
            lambda e: self.canvas_mensajes.configure(scrollregion=self.canvas_mensajes.bbox("all"))
        )

        self.scrollbar_visible = False
        self.actualizar_scrollbar_visibility()

    def configurar_barra_acciones(self):
        """Configura la barra de acciones donde se encuentran los botones y el campo de entrada."""
        self.barra_acciones = tk.Frame(self.root, bg="#1D1D1D", height=60)
        self.barra_acciones.pack(side=tk.BOTTOM, fill=tk.X)
        logger.info("Barra de acciones configurada.")

        # Frame para los botones de la izquierda
        self.frame_iconos = tk.Frame(
            self.barra_acciones,
            bg="#1D1D1D",
            borderwidth=0,
            highlightthickness=0
        )
        self.frame_iconos.pack(side=tk.LEFT, padx=10, pady=10)

        # Botones con íconos
        self.boton_foto = tk.Button(
            self.frame_iconos,
            image=self.imagenes.get('photo'),
            command=self.subir_foto,
            bg="#1D1D1D",
            borderwidth=0,
            highlightthickness=0,
            relief=tk.FLAT,
            activebackground="#1D1D1D",
            activeforeground="white"
        )
        self.boton_foto.pack(side=tk.LEFT, padx=5, pady=0)

        self.boton_mencion = tk.Button(
            self.frame_iconos,
            image=self.imagenes.get('mention'),
            command=self.activar_mencion,
            bg="#1D1D1D",
            borderwidth=0,
            highlightthickness=0,
            relief=tk.FLAT,
            activebackground="#1D1D1D",
            activeforeground="white"
        )
        self.boton_mencion.pack(side=tk.LEFT, padx=5, pady=0)

        self.boton_archivo = tk.Button(
            self.frame_iconos,
            image=self.imagenes.get('file'),
            command=self.subir_archivo,
            bg="#1D1D1D",
            borderwidth=0,
            highlightthickness=0,
            relief=tk.FLAT,
            activebackground="#1D1D1D",
            activeforeground="white"
        )
        self.boton_archivo.pack(side=tk.LEFT, padx=5, pady=0)

        # Campo de entrada con customtkinter
        self.entrada_mensaje = ctk.CTkEntry(
            self.barra_acciones,
            placeholder_text="Empieza a escribir...",
            font=self.fuente_dinamica,
            bg_color="#3D3D3D",
            fg_color="#3D3D3D",
            text_color="white",
            corner_radius=15,
            border_width=3,
            width=500,  # Reducido el ancho
            height=40
        )
        self.entrada_mensaje.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

        # Botón Enviar, alineado a la derecha con padding
        self.boton_enviar = tk.Button(
            self.barra_acciones,
            image=self.imagenes.get('send'),
            command=self.enviar_mensaje,
            bg="#1D1D1D",
            borderwidth=0,
            highlightthickness=0,
            relief=tk.FLAT,
            activebackground="#1D1D1D",
            activeforeground="white"
        )
        # Posicionar el botón de enviar un poco más a la derecha con padding
        self.boton_enviar.pack(side=tk.RIGHT, padx=(0, 20), pady=10)

    # ------------------------------
    # Funciones de botones/acciones
    # ------------------------------
    def subir_foto(self):
        """Permite al usuario seleccionar una foto."""
        ruta_foto = filedialog.askopenfilename(
            title="Seleccionar foto",
            filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg;*.gif")]
        )
        if ruta_foto:
            messagebox.showinfo("Foto Seleccionada", f"Has seleccionado: {ruta_foto}")
            logger.info(f"Foto seleccionada: {ruta_foto}")

    def activar_mencion(self):
        """Activa una mención en el campo de entrada."""
        self.entrada_mensaje.insert(tk.END, "@")
        logger.info("Mención activada en el campo de entrada.")

    def subir_archivo(self):
        """Sube un archivo al servidor."""
        subir_archivo()  # Llamada a la función global definida antes de la clase

    # ----------------------------
    # Manejo de mensajes en el chat
    # ----------------------------
    def actualizar_chat(self, mensaje: str):
        """
        Renderiza un mensaje en el frame_contenedor con el nombre del remitente en naranja y en negrita para otros usuarios.

        Args:
            mensaje (str): El mensaje a mostrar, esperado en formato "Remitente: contenido".
        """
        frame_mensaje = tk.Frame(self.frame_contenedor, bg="#2D2D2D")

        # Dividir el mensaje en remitente y contenido
        if ": " in mensaje:
            remitente, contenido = mensaje.split(": ", 1)
        else:
            remitente, contenido = "Desconocido", mensaje  # En caso de formato inesperado

        # Determinar colores
        if remitente == "Tú":
            fg_remitente = "white"
        else:
            fg_remitente = "#FFA500"  # Naranja

        # Etiqueta para el remitente
        etiqueta_remitente = tk.Label(
            frame_mensaje,
            text=f"{remitente}: ",
            bg="#2D2D2D",
            fg=fg_remitente,
            font=(self.fuente_dinamica[0], self.fuente_dinamica[1], "bold"),
            anchor='w'
        )
        etiqueta_remitente.pack(side=tk.LEFT, padx=(10, 5), pady=2)

        # Etiqueta para el contenido del mensaje
        etiqueta_contenido = tk.Label(
            frame_mensaje,
            text=contenido,
            bg="#2D2D2D",
            fg="white",
            font=self.fuente_dinamica,
            wraplength=500,  # Ajustado al nuevo ancho del campo de entrada
            justify='left'
        )
        etiqueta_contenido.pack(side=tk.LEFT, padx=(0, 10), pady=2, fill=tk.BOTH, expand=True)

        # Empaquetar el marco del mensaje a la izquierda
        frame_mensaje.pack(pady=2, anchor='w')  # Siempre a la izquierda

        # Actualizar el canvas para mostrar el nuevo mensaje
        self.canvas_mensajes.update_idletasks()
        self.canvas_mensajes.yview_moveto(1.0)
        self.actualizar_scrollbar_visibility()

    def enviar_mensaje_evento(self, event):
        """Cuando presione Enter se envía el mensaje."""
        self.enviar_mensaje()

    def enviar_mensaje(self, evento=None):
        """
        Envía el mensaje escrito en el campo de entrada,
        usando la función global send_message.
        """
        send_message()

    # ----------------------------
    # Scrollbar y eventos de mouse
    # ----------------------------
    def actualizar_scrollbar_visibility(self):
        can_scroll = self._can_scroll()
        if can_scroll and not getattr(self, 'scrollbar_visible', False):
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.scrollbar_visible = True
            logger.info("Scrollbar mostrada.")
        elif not can_scroll and getattr(self, 'scrollbar_visible', False):
            self.scrollbar.pack_forget()
            self.scrollbar_visible = False
            logger.info("Scrollbar oculta.")

    def _can_scroll(self) -> bool:
        """Determina si el contenido del canvas requiere scrollbar."""
        self.canvas_mensajes.update_idletasks()
        bbox = self.canvas_mensajes.bbox("all")
        if not bbox:
            return False
        content_height = bbox[3] - bbox[1]
        visible_height = self.canvas_mensajes.winfo_height()
        return content_height > visible_height

    def vincular_eventos_mouse(self):
        """Vincula los eventos de scroll del mouse según el sistema operativo."""
        sistema = platform.system()
        if sistema == 'Windows':
            self.canvas_mensajes.bind_all("<MouseWheel>", self._on_mousewheel_windows)
        elif sistema == 'Darwin':
            self.canvas_mensajes.bind_all("<MouseWheel>", self._on_mousewheel_mac)
        else:
            self.canvas_mensajes.bind_all("<Button-4>", self._on_mousewheel_linux)
            self.canvas_mensajes.bind_all("<Button-5>", self._on_mousewheel_linux)
        logger.info(f"Eventos de mouse vinculados para: {sistema}")

    def _on_mousewheel_windows(self, event):
        """Maneja el scroll del mouse en Windows."""
        if self._can_scroll():
            self.canvas_mensajes.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_mac(self, event):
        """Maneja el scroll del mouse en macOS."""
        if self._can_scroll():
            self.canvas_mensajes.yview_scroll(int(-1 * event.delta), "units")

    def _on_mousewheel_linux(self, event):
        """Maneja el scroll del mouse en Linux."""
        if event.num == 4:
            if self._can_scroll():
                self.canvas_mensajes.yview_scroll(-1, "units")
        elif event.num == 5:
            if self._can_scroll():
                self.canvas_mensajes.yview_scroll(1, "units")

    # ----------------------------
    # Cierre de la aplicación
    # ----------------------------
    def cerrar_aplicacion(self):
        """Cierra la aplicación correctamente."""
        logger.info("Cerrando la aplicación.")
        global client_socket
        if client_socket:
            try:
                client_socket.close()
                logging.info("Socket cerrado correctamente.")
            except Exception as e:
                logging.error(f"Error cerrando el socket: {e}")
        self.root.destroy()

# -------------------------
# EJECUCIÓN DEL CHAT
# -------------------------
def run_chat() -> None:
    """
    Inicializa y ejecuta la interfaz de chat con la clase ChatUI.
    """
    global root, app

    pygame.init()
    root = tk.Tk()
    # Creamos la interfaz
    app = ChatUI(root)

    # Vinculamos el evento <Map> para resetear notificaciones
    root.bind("<Map>", reset_notifications)

    # Conexión al servidor
    connect_to_server()

    # Manejar el cierre de la ventana correctamente
    root.protocol("WM_DELETE_WINDOW", app.cerrar_aplicacion)
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
