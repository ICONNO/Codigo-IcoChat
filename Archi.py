import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar

# Función para mostrar los archivos subidos
def mostrar_archivos(client_socket):
    archivos_ventana = tk.Toplevel()
    archivos_ventana.title("Archivos Subidos")
    archivos_ventana.geometry("600x400")  # Ajustar tamaño inicial de la ventana

    # Crear un Canvas para poder agregar una barra de desplazamiento
    canvas = tk.Canvas(archivos_ventana)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Crear la barra de desplazamiento
    scrollbar = tk.Scrollbar(archivos_ventana, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas.configure(yscrollcommand=scrollbar.set)

    # Crear un frame dentro del canvas para los archivos
    archivo_label_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=archivo_label_frame, anchor="nw")

    archivo_labels = {}

    # Función para actualizar la lista de archivos
    def actualizar_lista_archivos():
        try:
            client_socket.send("LISTA_ARCHIVOS".encode('utf-8'))
            data_length = int(client_socket.recv(10).decode('utf-8').strip())
            data = b""
            while len(data) < data_length:
                part = client_socket.recv(4096)
                if not part:
                    break
                data += part
            archivos_actuales = json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"Error obteniendo la lista de archivos: {e}")
            archivos_actuales = []

        # Agregar nuevos archivos
        for archivo in archivos_actuales:
            if archivo not in archivo_labels:
                archivo_label = tk.Label(archivo_label_frame, text=archivo, bg="lightgrey")
                archivo_label.pack(fill=tk.X, padx=5, pady=5)

                download_button = tk.Button(
                    archivo_label_frame,
                    text="Descargar",
                    command=lambda archivo=archivo: descargar_archivo(archivo, client_socket),
                    bg="lightblue"
                )
                download_button.pack(fill=tk.X, padx=5, pady=5)

                archivo_labels[archivo] = (archivo_label, download_button)

        # Eliminar archivos que ya no existen
        for archivo in list(archivo_labels.keys()):
            if archivo not in archivos_actuales:
                archivo_labels[archivo][0].destroy()
                archivo_labels[archivo][1].destroy()
                del archivo_labels[archivo]

        # Continuar actualizando cada 1000 ms (1 segundo)
        archivos_ventana.after(1000, actualizar_lista_archivos)

    # Llamada inicial para mostrar archivos existentes
    actualizar_lista_archivos()

    # Actualizar el scroll region para que la barra de desplazamiento se ajuste al contenido
    archivo_label_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # Función para manejar el desplazamiento con la rueda del ratón
    def on_mouse_wheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # Asociar la rueda del ratón con la acción de desplazamiento
    archivos_ventana.bind_all("<MouseWheel>", on_mouse_wheel)

# Función para descargar un archivo
def descargar_archivo(archivo, client_socket):
    try:
        destino = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Todos los archivos", "*.*")],
            initialfile=archivo,
        )
        if destino:
            client_socket.send(f"DESCARGAR_ARCHIVO:{archivo}".encode('utf-8'))
            with open(destino, 'wb') as f:
                while True:
                    bytes_read = client_socket.recv(1024)
                    if not bytes_read:
                        break
                    f.write(bytes_read)
            messagebox.showinfo("Éxito", f"Archivo {archivo} descargado exitosamente!")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo descargar el archivo: {e}")

# Función para seleccionar y subir un archivo
def seleccionar_archivo(client_socket):
    archivo = filedialog.askopenfilename(
        title="Seleccionar archivo", filetypes=[("Todos los archivos", "*.*")]
    )
    if archivo:
        nombre_archivo = os.path.basename(archivo)
        try:
            # Notificar al servidor sobre el archivo subido
            client_socket.send(f"ARCHIVO:{nombre_archivo}".encode("utf-8"))
            with open(archivo, 'rb') as f:
                while (bytes_read := f.read(1024)):
                    client_socket.send(bytes_read)

            # Mensaje para el chat
            return f"Has subido el archivo: {nombre_archivo}"
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo subir el archivo: {e}")
    return None