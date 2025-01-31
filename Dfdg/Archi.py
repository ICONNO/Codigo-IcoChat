import json
import socket
from pathlib import Path
from typing import Dict, Tuple
 
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


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
    canvas = tk.Canvas(archivos_ventana)
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

    archivo_labels: Dict[str, Tuple[tk.Label, tk.Button]] = {}

    def actualizar_lista_archivos() -> None:
        """Actualiza la lista de archivos mostrados en la ventana."""
        try:
            client_socket.sendall("LISTA_ARCHIVOS".encode('utf-8'))
            data_length = int(client_socket.recv(10).decode('utf-8').strip())
            data = client_socket.recv(data_length)
            archivos_actuales = json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"Error obteniendo la lista de archivos: {e}")
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
        """Maneja el desplazamiento con la rueda del ratón."""
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    archivos_ventana.bind_all("<MouseWheel>", on_mouse_wheel)


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
            client_socket.sendall(f"DESCARGAR_ARCHIVO:{archivo}".encode('utf-8'))
            with open(destino, 'wb') as f:
                while True:
                    bytes_read = client_socket.recv(1024)
                    if not bytes_read:
                        break
                    f.write(bytes_read)
            messagebox.showinfo("Éxito", f"Archivo '{archivo}' descargado exitosamente!")
    except Exception as e:
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
            with archivo_path.open('rb') as f:
                for bytes_read in iter(lambda: f.read(1024), b''):
                    client_socket.sendall(bytes_read)

            # Mensaje para el chat
            messagebox.showinfo("Éxito", f"Archivo '{nombre_archivo}' subido exitosamente!")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo subir el archivo: {e}")
