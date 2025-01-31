# modules/interfaz.py

import os
import platform
from pathlib import Path
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
from PIL import Image, ImageTk
import customtkinter as ctk
import json
import logging

# Configuración del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatUI:
    """Clase para manejar la interfaz gráfica del chat."""

    def __init__(self, root):
        """
        Inicializa la interfaz de usuario del chat.

        Args:
            root: Instancia de Tkinter.
        """
        self.root = root
        self.root.title("Chat")

        # Obtener dimensiones de la pantalla
        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()
        self.root.geometry(f"{ancho_pantalla}x{alto_pantalla}")

        # Tamaños dinámicos
        self.tamano_fuente = max(10, int(alto_pantalla * 0.02))
        self.tamano_icono = (int(alto_pantalla * 0.04), int(alto_pantalla * 0.04))
        self.fuente_dinamica = ("Arial", self.tamano_fuente)

        # Inicializar el diccionario de imágenes
        self.imagenes = {}

        # Rutas de archivos
        self.archivo_usuario = Path("user_name.json")
        self.archivo_chat = Path("historial_chat.json")
        self.ruta_assets = Path(__file__).resolve().parent.parent / 'assets'

        # Cargar imágenes
        self.cargar_imagenes()

        # Configurar estilos para ttk
        self.configurar_estilos()

        # Configurar UI
        self.configurar_fondo(ancho_pantalla, alto_pantalla)
        self.configurar_lista_chats()
        self.configurar_titulo()
        self.configurar_area_mensajes()
        self.configurar_barra_acciones()

        # Vincular tecla Enter para enviar mensajes
        self.root.bind('<Return>', self.enviar_mensaje_evento)

        # Vincular eventos de la rueda del mouse para el Canvas de mensajes
        self.vincular_eventos_mouse()

        # Variable para almacenar el nombre de usuario
        self.nombre_usuario = self.cargar_nombre_usuario()

    def configurar_estilos(self):
        """Configura los estilos para los widgets de ttk."""
        style = ttk.Style()
        style.theme_use('clam')  # Cambiar a 'clam'

        # Configurar el estilo de la scrollbar vertical
        style.configure(
            "Custom.Vertical.TScrollbar",
            background="#808080",  # Color de la barra de desplazamiento
            troughcolor="#2D2D2D",  # Color de la zona por donde se desplaza
            bordercolor="#2D2D2D"    # Color del borde
        )

        # Configurar el mapa de colores para estados activos
        style.map(
            "Custom.Vertical.TScrollbar",
            background=[('active', '#2D2D2D')]
        )
        logger.info("Estilos de ttk configurados.")

    def cargar_imagenes(self):
        """Carga y redimensiona las imágenes necesarias."""
        rutas_imagenes = {
            'fondo': self.ruta_assets / 'fondo' / 'Rectangle 2.png',
            'send': self.ruta_assets / 'iconos' / 'send.png',
            'photo': self.ruta_assets / 'iconos' / 'photo.png',
            'mention': self.ruta_assets / 'iconos' / 'mention.png',
            'file': self.ruta_assets / 'iconos' / 'file.png',
            'menu': self.ruta_assets / 'iconos' / 'menu.png'  # Ruta para el ícono del menú
        }

        for clave, ruta in rutas_imagenes.items():
            imagen = self.redimensionar_imagen(ruta, self.tamano_icono)
            if imagen:
                self.imagenes[clave] = imagen
                logger.info(f"Imagen cargada: {clave} desde {ruta}")
            else:
                logger.error(f"Fallo al cargar la imagen: {ruta}")

    def configurar_fondo(self, ancho, alto):
        """Configura el fondo de la ventana."""
        fondo_redimensionado = self.redimensionar_imagen(self.ruta_assets / 'fondo' / 'Rectangle 2.png', (ancho, alto))
        if fondo_redimensionado:
            self.etiqueta_fondo = tk.Label(
                self.root,
                image=fondo_redimensionado,
                borderwidth=0,
                highlightthickness=0
            )
            self.etiqueta_fondo.image = fondo_redimensionado  # Mantener referencia
            self.etiqueta_fondo.place(relwidth=1, relheight=1)
            logger.info("Fondo configurado correctamente.")
        else:
            logger.error("No se pudo configurar el fondo.")

    def configurar_lista_chats(self):
        """Configura la sección izquierda con la lista de chats."""
        self.frame_lista_chats = tk.Frame(self.root, bg="#3D3D3D")
        self.frame_lista_chats.place(relx=0, rely=0, relwidth=0.2, relheight=1)
        logger.info("Lista de chats configurada.")

    def configurar_titulo(self):
        """Configura el título de la aplicación."""
        # Crear un único frame para el título
        self.frame_titulo = tk.Frame(self.root, bg="#3D3D3D")
        self.frame_titulo.place(relx=0.2, rely=0, relwidth=0.8, relheight=0.1)

        # Agregar el botón de menú al frame de la lista de chats
        self.boton_menu = tk.Button(
            self.frame_lista_chats,
            image=self.imagenes.get('menu'),
            bg="#3D3D3D",
            borderwidth=0,
            highlightthickness=0,
            relief=tk.FLAT,
            activebackground="#3D3D3D"
        )
        self.boton_menu.place(relx=0.05, rely=0.5, anchor='w')  # Posicionar a la izquierda

        # Label para el título
        self.label_titulo = tk.Label(
            self.frame_titulo,
            text="Chat Grupal",
            font=("Alatsi", 16, "bold"),
            bg="#3D3D3D",
            fg="white",
            anchor="center"
        )
        self.label_titulo.place(relx=0.5, rely=0.5, anchor="center")

        # Línea separadora debajo del título
        self.linea_separadora = tk.Frame(self.root, height=2, bg="white")
        self.linea_separadora.place(relx=0.2, rely=0.1, relwidth=0.8)
        logger.info("Título configurado.")

    def configurar_area_mensajes(self):
        """Configura el área central donde se muestran los mensajes."""
        self.frame_mensajes = tk.Frame(self.root, bg="#2D2D2D")
        self.frame_mensajes.place(relx=0.2, rely=0.1, relwidth=0.8, relheight=0.7)

        # Crear un Canvas dentro del Frame
        self.canvas_mensajes = tk.Canvas(
            self.frame_mensajes,
            bg="#2D2D2D",
            highlightthickness=0
        )
        self.canvas_mensajes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Agregar barra de desplazamiento con ttk.Scrollbar y estilo personalizado
        self.scrollbar = ttk.Scrollbar(
            self.frame_mensajes,
            command=self.canvas_mensajes.yview,
            style="Custom.Vertical.TScrollbar"
        )
        self.canvas_mensajes.configure(yscrollcommand=self.scrollbar.set)

        # Crear un Frame dentro del Canvas para contener los mensajes
        self.frame_contenedor = tk.Frame(self.canvas_mensajes, bg="#2D2D2D")
        self.canvas_mensajes.create_window((0, 0), window=self.frame_contenedor, anchor='nw')

        # Configurar la actualización del tamaño del Canvas
        self.frame_contenedor.bind(
            "<Configure>",
            lambda e: self.canvas_mensajes.configure(scrollregion=self.canvas_mensajes.bbox("all"))
        )

        # Inicializar la variable de estado de la scrollbar
        self.scrollbar_visible = False

        # Actualizar la visibilidad de la scrollbar inicialmente
        self.actualizar_scrollbar_visibility()
        logger.info("Área de mensajes configurada.")

    def configurar_barra_acciones(self):
        """Configura la barra inferior con los botones y campo de entrada."""
        self.barra_acciones = tk.Frame(self.root, bg="#1D1D1D")
        self.barra_acciones.place(relx=0.2, rely=0.8, relwidth=0.8, relheight=0.2)

        # Marco para los íconos
        self.frame_iconos = tk.Frame(
            self.barra_acciones,
            bg="#1D1D1D",
            borderwidth=0,
            highlightthickness=0
        )
        self.frame_iconos.place(relx=0.03, rely=0.2, relwidth=0.2, relheight=0.4)

        # Botón de foto
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
        self.boton_foto.pack(side=tk.LEFT, padx=2, pady=0)

        # Botón de mención
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
        self.boton_mencion.pack(side=tk.LEFT, padx=2, pady=0)

        # Botón de archivo
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
        self.boton_archivo.pack(side=tk.LEFT, padx=2, pady=0)

        # Campo de entrada de texto con esquinas redondeadas usando customtkinter
        self.entrada_mensaje = ctk.CTkEntry(
            self.barra_acciones,
            placeholder_text="Empieza a escribir...",
            font=self.fuente_dinamica,
            bg_color="#3D3D3D",
            fg_color="#3D3D3D",
            text_color="white",
            corner_radius=15,  # Ajusta este valor según tus preferencias
            border_width=3,
            width=700,          # Ajustar el ancho según sea necesario
            height=50           # Aumentar la altura para extender más abajo
        )
        self.entrada_mensaje.place(x=180, y=42)  # Ajusta 'x' e 'y' según tus necesidades

        # Botón de enviar
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
        self.boton_enviar.place(x=870, y=42, width=50, height=50)  # Ajustar las coordenadas y tamaño según necesidad
        logger.info("Barra de acciones configurada.")

    def subir_foto(self):
        """Funcionalidad para subir una foto."""
        ruta_foto = filedialog.askopenfilename(
            title="Seleccionar foto",
            filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg;*.gif")]
        )
        if ruta_foto:
            # Aquí puedes agregar la lógica para manejar la foto seleccionada
            messagebox.showinfo("Foto Seleccionada", f"Has seleccionado: {ruta_foto}")
            logger.info(f"Foto seleccionada para subir: {ruta_foto}")

    def activar_mencion(self):
        """Funcionalidad para activar una mención (@)."""
        self.entrada_mensaje.insert(tk.END, "@")
        logger.info("Mención activada en el campo de entrada.")

    def subir_archivo(self):
        """Funcionalidad para subir un archivo."""
        ruta_archivo = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("Todos los archivos", "*.*")]
        )
        if ruta_archivo:
            # Aquí puedes agregar la lógica para manejar el archivo seleccionado
            messagebox.showinfo("Archivo Seleccionado", f"Has seleccionado: {ruta_archivo}")
            logger.info(f"Archivo seleccionado para subir: {ruta_archivo}")

    def actualizar_chat(self, mensaje, direccion='left'):
        """
        Actualiza el área de chat con un nuevo mensaje alineado.

        Args:
            mensaje (str): Mensaje a mostrar.
            direccion (str): Dirección de alineación ('left', 'center', 'right').
        """
        # Crear un Frame para el mensaje
        frame_mensaje = tk.Frame(self.frame_contenedor, bg="#2D2D2D")

        # Crear el Label del mensaje
        etiqueta_mensaje = tk.Label(
            frame_mensaje,
            text=mensaje,
            bg="#2D2D2D",
            fg="white",
            font=self.fuente_dinamica,
            wraplength=400,
            justify='left'
        )
        etiqueta_mensaje.pack(padx=10, pady=2, anchor='w')

        # Alinear el Frame según la dirección
        if direccion == 'left':
            frame_mensaje.pack(fill='x', pady=2, anchor='w')
        elif direccion == 'center':
            frame_mensaje.pack(fill='x', pady=2, anchor='center')
        elif direccion == 'right':
            frame_mensaje.pack(fill='x', pady=2, anchor='e')
            # Cambiar el color de fondo y texto para mensajes alineados a la derecha
            etiqueta_mensaje.config(fg="white", justify='right')

        # Desplazar el Canvas al final para mostrar el nuevo mensaje
        self.canvas_mensajes.update_idletasks()
        self.canvas_mensajes.yview_moveto(1.0)

        # Actualizar visibilidad de la scrollbar
        self.actualizar_scrollbar_visibility()

    def actualizar_scrollbar_visibility(self):
        """Muestra u oculta la scrollbar basada en la necesidad de desplazamiento."""
        if self._can_scroll() and not self.scrollbar_visible:
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.scrollbar_visible = True
            logger.info("Scrollbar mostrada.")
        elif not self._can_scroll() and self.scrollbar_visible:
            self.scrollbar.pack_forget()
            self.scrollbar_visible = False
            logger.info("Scrollbar oculta.")

    def _can_scroll(self):
        """Verifica si el contenido del Canvas excede su tamaño visible."""
        self.canvas_mensajes.update_idletasks()  # Asegura que el Canvas está actualizado
        bbox = self.canvas_mensajes.bbox("all")
        if not bbox:
            return False
        content_height = bbox[3] - bbox[1]
        visible_height = self.canvas_mensajes.winfo_height()
        return content_height > visible_height

    def enviar_mensaje_evento(self, event):
        """Maneja el evento de presionar la tecla Enter para enviar mensajes."""
        self.enviar_mensaje()

    def enviar_mensaje(self, evento=None):
        """Envía el mensaje escrito y lo muestra en la interfaz."""
        mensaje = self.entrada_mensaje.get().strip()  # Eliminar espacios en blanco
        if mensaje:
            self.actualizar_chat(f"Tú: {mensaje}", direccion='right')
            self.entrada_mensaje.delete(0, tk.END)
            # Aquí puedes agregar la lógica para enviar el mensaje al backend
            logger.info(f"Mensaje enviado: {mensaje}")
        else:
            messagebox.showwarning("Mensaje vacío", "No puedes enviar un mensaje vacío.")
            logger.warning("Intento de enviar un mensaje vacío.")

    def vincular_eventos_mouse(self):
        """Vincula los eventos de la rueda del mouse al Canvas de mensajes."""
        sistema = platform.system()
        if sistema == 'Windows':
            self.canvas_mensajes.bind_all("<MouseWheel>", self._on_mousewheel_windows)
        elif sistema == 'Darwin':  # macOS
            self.canvas_mensajes.bind_all("<MouseWheel>", self._on_mousewheel_mac)
        else:  # Linux y otros
            self.canvas_mensajes.bind_all("<Button-4>", self._on_mousewheel_linux)
            self.canvas_mensajes.bind_all("<Button-5>", self._on_mousewheel_linux)
        logger.info(f"Eventos de mouse vinculados para el sistema operativo: {sistema}")

    def _on_mousewheel_windows(self, event):
        """Maneja el evento de la rueda del mouse en Windows."""
        if self._can_scroll():
            self.canvas_mensajes.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_mac(self, event):
        """Maneja el evento de la rueda del mouse en macOS."""
        if self._can_scroll():
            self.canvas_mensajes.yview_scroll(int(-1 * event.delta), "units")

    def _on_mousewheel_linux(self, event):
        """Maneja el evento de la rueda del mouse en Linux."""
        if event.num == 4:
            if self._can_scroll():
                self.canvas_mensajes.yview_scroll(-1, "units")
        elif event.num == 5:
            if self._can_scroll():
                self.canvas_mensajes.yview_scroll(1, "units")

    def cerrar_aplicacion(self):
        """Cierra la aplicación limpiamente."""
        # Agrega cualquier limpieza necesaria antes de cerrar
        logger.info("Cerrando la aplicación.")
        self.root.destroy()

    # Funciones auxiliares para manejar el nombre de usuario y redimensionar imágenes

    def cargar_nombre_usuario(self) -> str:
        """
        Carga el nombre de usuario desde un archivo JSON.

        Returns:
            str: El nombre de usuario si existe, de lo contrario una cadena vacía.
        """
        if self.archivo_usuario.exists():
            try:
                with self.archivo_usuario.open("r", encoding="utf-8") as archivo:
                    datos = json.load(archivo)
                    nombre = datos.get("user_name", "")
                    logger.info(f"Nombre de usuario cargado: {nombre}")
                    return nombre
            except json.JSONDecodeError as e:
                logger.error(f"Error al decodificar JSON en {self.archivo_usuario}: {e}")
            except Exception as e:
                logger.error(f"Error al cargar el nombre de usuario: {e}")
        else:
            logger.warning(f"Archivo de usuario no encontrado: {self.archivo_usuario}")
            # Solicitar el nombre de usuario al iniciar la aplicación
            nombre = simpledialog.askstring("Nombre", "¿Cómo te llamas?")
            if nombre:
                self.guardar_nombre_usuario(nombre)
                return nombre
            else:
                return "Anónimo"
        return "Anónimo"

    def guardar_nombre_usuario(self, nombre_usuario: str) -> None:
        """
        Guarda el nombre de usuario en un archivo JSON.

        Args:
            nombre_usuario (str): El nombre de usuario a guardar.
        """
        datos = {"user_name": nombre_usuario}
        try:
            with self.archivo_usuario.open("w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=4)
                logger.info(f"Nombre de usuario guardado: {nombre_usuario}")
        except Exception as e:
            logger.error(f"Error al guardar el nombre de usuario: {e}")

    def redimensionar_imagen(self, ruta_imagen: Path, tamaño: tuple[int, int]) -> ImageTk.PhotoImage | None:
        """
        Redimensiona una imagen a un tamaño específico.

        Args:
            ruta_imagen (Path): Ruta al archivo de imagen.
            tamaño (tuple[int, int]): Nuevo tamaño de la imagen (ancho, alto).

        Returns:
            ImageTk.PhotoImage | None: Imagen redimensionada si tiene éxito, de lo contrario None.
        """
        try:
            with Image.open(ruta_imagen) as imagen:
                imagen = imagen.convert("RGBA")  # Asegura la compatibilidad con ImageTk
                imagen_redimensionada = imagen.resize(tamaño, Image.Resampling.LANCZOS)
                imagen_tk = ImageTk.PhotoImage(imagen_redimensionada)
                logger.info(f"Imagen redimensionada: {ruta_imagen} a tamaño {tamaño}")
                return imagen_tk
        except FileNotFoundError:
            logger.error(f"Archivo de imagen no encontrado: {ruta_imagen}")
        except Exception as e:
            logger.error(f"Error al redimensionar la imagen {ruta_imagen}: {e}")
        return None


def main():
    """Función principal para ejecutar la interfaz de usuario."""
    root = tk.Tk()
    app = ChatUI(root)
    root.protocol("WM_DELETE_WINDOW", app.cerrar_aplicacion)
    root.mainloop()


if __name__ == "__main__":
    main()
