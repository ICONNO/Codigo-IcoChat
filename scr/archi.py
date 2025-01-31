# src/Archi.py
import platform
import json
import socket
from pathlib import Path
from typing import Dict, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import logging

from config import DATA_DIR, ASSETS_DIR  # Importamos DATA_DIR y ASSETS_DIR desde config.py

def mostrar_archivos(client_socket: socket.socket) -> None:
    """
    Muestra una ventana con la lista de archivos subidos y opciones para descargarlos.

    Args:
        client_socket (socket.socket): El socket del cliente para comunicarse con el servidor.
    """
    archivos_ventana = tk.Toplevel()
    archivos_ventana.title("Archivos Subidos")
    archivos_ventana.geometry("600x400")  # Tamaño inicial de la ventana

    # Configuración del canvas con barra de desplazamiento
    canvas = tk.Canvas(archivos_ventana, bg="#2D2D2D", highlightthickness=0)
    scrollbar = ttk.Scrollbar(archivos_ventana, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    archivo_labels: Dict[str, Tuple[ttk.Label, ttk.Button]] = {}

    def actualizar_lista_archivos() -> None:
        """Actualiza la lista de archivos mostrados en la ventana."""
        try:
            client_socket.sendall("LISTA_ARCHIVOS".encode('utf-8'))
            # Recibir primero el tamaño de los datos (por ejemplo, 10 bytes)
            data_length_bytes = client_socket.recv(10)
            if not data_length_bytes:
                raise ConnectionError("No se recibió la longitud de los datos.")
            data_length = int(data_length_bytes.decode('utf-8').strip())
            data = b""
            while len(data) < data_length:
                packet = client_socket.recv(data_length - len(data))
                if not packet:
                    break
                data += packet
            archivos_actuales = json.loads(data.decode('utf-8'))
            logging.info(f"Archivos actuales recibidos: {archivos_actuales}")
        except (ConnectionError, json.JSONDecodeError) as e:
            logging.error(f"Error obteniendo la lista de archivos: {e}")
            archivos_actuales = []
        except Exception as e:
            logging.error(f"Error inesperado al obtener la lista de archivos: {e}")
            archivos_actuales = []

        # Agregar nuevos archivos
        for archivo in archivos_actuales:
            if archivo not in archivo_labels:
                archivo_label = ttk.Label(scrollable_frame, text=archivo, background="lightgrey")
                archivo_label.pack(fill=tk.X, padx=5, pady=5)

                download_button = ttk.Button(
                    scrollable_frame,
                    text="Descargar",
                    command=lambda archivo=archivo: descargar_archivo(archivo, client_socket)
                )
                download_button.pack(fill=tk.X, padx=5, pady=5)

                archivo_labels[archivo] = (archivo_label, download_button)

        # Eliminar archivos que ya no existen
        for archivo in list(archivo_labels.keys()):
            if archivo not in archivos_actuales:
                archivo_labels[archivo][0].destroy()
                archivo_labels[archivo][1].destroy()
                del archivo_labels[archivo]

        # Programar la próxima actualización
        archivos_ventana.after(1000, actualizar_lista_archivos)

    actualizar_lista_archivos()

    def on_mouse_wheel(event: tk.Event) -> None:
        """Maneja el desplazamiento con la rueda del ratón según el sistema operativo."""
        sistema = platform.system()
        if sistema == 'Windows':
            delta = int(-1 * (event.delta / 120))
        elif sistema == 'Darwin':  # macOS
            delta = int(-1 * event.delta)
        else:  # Linux
            if event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1
            else:
                delta = 0
        if delta != 0:
            canvas.yview_scroll(delta, "units")

    # Vincular eventos de scroll según el sistema operativo
    sistema = platform.system()
    if sistema == 'Windows':
        archivos_ventana.bind_all("<MouseWheel>", on_mouse_wheel)
    elif sistema == 'Darwin':
        archivos_ventana.bind_all("<MouseWheel>", on_mouse_wheel)
    else:
        archivos_ventana.bind_all("<Button-4>", on_mouse_wheel)
        archivos_ventana.bind_all("<Button-5>", on_mouse_wheel)

def descargar_archivo(archivo: str, client_socket: socket.socket) -> None:
    """
    Descarga un archivo desde el servidor y lo guarda en la ubicación seleccionada.

    Args:
        archivo (str): El nombre del archivo a descargar.
        client_socket (socket.socket): El socket del cliente para comunicarse con el servidor.
    """
    try:
        destino = filedialog.asksaveasfilename(
            defaultextension=Path(archivo).suffix or ".txt",
            filetypes=[("Todos los archivos", "*.*")],
            initialfile=archivo,
            title="Guardar archivo como"
        )
        if destino:
            # Enviar solicitud de descarga al servidor
            client_socket.sendall(f"DESCARGAR_ARCHIVO:{archivo}".encode('utf-8'))

            # Recibir primero el tamaño del archivo (por ejemplo, 10 bytes)
            data_length_bytes = client_socket.recv(10)
            if not data_length_bytes:
                raise ConnectionError("No se recibió la longitud del archivo.")
            data_length = int(data_length_bytes.decode('utf-8').strip())
            with open(destino, 'wb') as f:
                bytes_received = 0
                while bytes_received < data_length:
                    bytes_read = client_socket.recv(1024)
                    if not bytes_read:
                        break
                    f.write(bytes_read)
                    bytes_received += len(bytes_read)
            messagebox.showinfo("Éxito", f"Archivo '{archivo}' descargado exitosamente!")
            logging.info(f"Archivo '{archivo}' descargado exitosamente a '{destino}'.")
    except (ConnectionError, json.JSONDecodeError) as e:
        logging.error(f"Error descargando archivo: {e}")
        messagebox.showerror("Error", f"No se pudo descargar el archivo: {e}")
    except Exception as e:
        logging.error(f"Error inesperado descargando archivo: {e}")
        messagebox.showerror("Error", f"No se pudo descargar el archivo: {e}")

def seleccionar_archivo(client_socket: socket.socket) -> None:
    """
    Abre un diálogo para seleccionar un archivo y lo sube al servidor.

    Args:
        client_socket (socket.socket): El socket del cliente para comunicarse con el servidor.
    """
    archivo_path = Path(filedialog.askopenfilename(
        title="Seleccionar archivo",
        filetypes=[("Todos los archivos", "*.*")]
    ))

    if archivo_path and archivo_path.is_file():
        nombre_archivo = archivo_path.name
        try:
            # Notificar al servidor sobre el archivo subido
            client_socket.sendall(f"ARCHIVO:{nombre_archivo}".encode("utf-8"))

            # Obtener el tamaño del archivo
            tamaño_archivo = archivo_path.stat().st_size
            client_socket.sendall(f"{tamaño_archivo:010}".encode('utf-8'))  # Enviar tamaño en 10 bytes

            with archivo_path.open('rb') as f:
                while True:
                    bytes_read = f.read(1024)
                    if not bytes_read:
                        break
                    client_socket.sendall(bytes_read)

            # Mensaje para el chat
            messagebox.showinfo("Éxito", f"Archivo '{nombre_archivo}' subido exitosamente!")
            logging.info(f"Archivo '{nombre_archivo}' subido exitosamente al servidor.")
        except (ConnectionError, socket.error) as e:
            logging.error(f"Error subiendo archivo: {e}")
            messagebox.showerror("Error", f"No se pudo subir el archivo: {e}")
        except Exception as e:
            logging.error(f"Error inesperado subiendo archivo: {e}")
            messagebox.showerror("Error", f"No se pudo subir el archivo: {e}")
