# modules/utilidades.py
import os
import json
from PIL import Image, ImageTk

ARCHIVO_USUARIO = "user_name.json"

def cargar_nombre_usuario():
    """Carga el nombre de usuario desde un archivo JSON."""
    if os.path.exists(ARCHIVO_USUARIO):
        with open(ARCHIVO_USUARIO, "r", encoding="utf-8") as archivo:
            try:
                datos = json.load(archivo)
                return datos.get("user_name", "")
            except json.JSONDecodeError:
                return ""
    return ""

def guardar_nombre_usuario(nombre_usuario):
    """Guarda el nombre de usuario en un archivo JSON."""
    datos = {"user_name": nombre_usuario}
    with open(ARCHIVO_USUARIO, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=4)

def redimensionar_imagen(ruta_imagen, tamaño):
    """Redimensiona una imagen a un tamaño específico."""
    try:
        imagen = Image.open(ruta_imagen)
        imagen = imagen.resize(tamaño, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(imagen)
    except Exception as e:
        print(f"Error al cargar la imagen {ruta_imagen}: {e}")
        return None
