# modules/interfaz.py
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
from PIL import Image, ImageTk
import customtkinter as ctk
from .utilidades import cargar_nombre_usuario, guardar_nombre_usuario, redimensionar_imagen

import os
import platform  # Para detectar el sistema operativo


class ChatUI:
    """Clase para manejar la interfaz gráfica del chat."""
    def __init__(self, root):
        self.root = root
        self.root.title("Chat")
        
        # Obtener dimensiones de la pantalla
        ancho_pantalla = root.winfo_screenwidth()
        alto_pantalla = root.winfo_screenheight()
        root.geometry(f"{ancho_pantalla}x{alto_pantalla}")
        
        # Tamaños dinámicos
        self.tamano_fuente = max(10, int(alto_pantalla * 0.02))
        self.tamano_icono = (int(alto_pantalla * 0.04), int(alto_pantalla * 0.04))
        self.fuente_dinamica = ("Arial", self.tamano_fuente)
        
        # Inicializar el diccionario de imágenes
        self.imagenes = {}
        
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
        
       
        
        # Vincular tecla Enter
        self.root.bind('<Return>', self.enviar_mensaje_evento)
        
        # Vincular eventos de la rueda del mouse para el Canvas de mensajes
        self.vincular_eventos_mouse()

    def configurar_estilos(self):
        """Configura los estilos para los widgets de ttk."""
        style = ttk.Style()
        style.theme_use('clam')  # Cambiar a 'clam'
        
        # Configurar el estilo de la scrollbar vertical
        style.configure("Custom.Vertical.TScrollbar",
                        background="#808080",  # Color de la barra de desplazamiento
                        troughcolor="#2D2D2D",  # Color de la zona por donde se desplaza
                        bordercolor="#2D2D2D")  # Color del borde
        
        # Opcional: Configurar el comportamiento de los estados
        style.map("Custom.Vertical.TScrollbar",
                  background=[('active', '#2D2D2D')])
                  # arrowcolor no es soportado directamente por 'clam', se omite

    def cargar_imagenes(self):
        """Carga y redimensiona las imágenes necesarias."""
        ruta_base = os.path.dirname(os.path.abspath(__file__))
        ruta_assets = os.path.join(ruta_base, '..', 'assets')
        
        self.rutas_imagenes = {
            'fondo': os.path.join(ruta_assets, 'fondo', 'Rectangle 2.png'),
            'send': os.path.join(ruta_assets, 'iconos', 'send.png'),
            'photo': os.path.join(ruta_assets, 'iconos', 'photo.png'),
            'mention': os.path.join(ruta_assets, 'iconos', 'mention.png'),
            'file': os.path.join(ruta_assets, 'iconos', 'file.png'),
            'menu': os.path.join(ruta_assets, 'iconos', 'menu.png')  # Ruta para el ícono del menú
        }
        
        for clave, ruta in self.rutas_imagenes.items():
            imagen = redimensionar_imagen(ruta, self.tamano_icono)
            if imagen:
                self.imagenes[clave] = imagen
            else:
                print(f"Fallo al cargar la imagen: {ruta}")

    def configurar_fondo(self, ancho, alto):
        """Configura el fondo de la ventana."""
        fondo_redimensionado = redimensionar_imagen(self.rutas_imagenes['fondo'], (ancho, alto))
        if fondo_redimensionado:
            self.etiqueta_fondo = tk.Label(
                self.root, 
                image=fondo_redimensionado, 
                borderwidth=0,         # Eliminar borde
                highlightthickness=0   # Eliminar resalto
            )
            self.etiqueta_fondo.image = fondo_redimensionado  # Mantener referencia
            self.etiqueta_fondo.place(relwidth=1, relheight=1)

    def configurar_lista_chats(self):
        """Configura la sección izquierda con la lista de chats."""
        self.frame_lista_chats = tk.Frame(self.root, bg="#3D3D3D")
        self.frame_lista_chats.place(relx=0, rely=0, relwidth=0.2, relheight=1)
        # La etiqueta "#Chat Grupal" ha sido eliminada

    def configurar_titulo(self):
        """Configura el título de la aplicación."""
        # Crear un único frame para el título
        self.frame_titulo = tk.Frame(self.root, bg="#3D3D3D")  # Fondo gris oscuro para el título
        self.frame_titulo.place(relx=0.2, rely=0, relwidth=0.8, relheight=0.1)
    
         # Agregar el botón de menú al lado izquierdo
        self.boton_menu = tk.Button(
        self.frame_lista_chats,
        image=self.imagenes.get('menu'),
        bg="#3D3D3D",
        borderwidth=0,
        highlightthickness=0,
        relief=tk.FLAT,
        activebackground="#3D3D3D"
    )
        self.boton_menu.place(relx=0.80, rely=1.70, anchor="nw")  # Posicionar en la esquina superior izquierda


        
        self.boton_menu.place(relx=0.05, rely=0.5, anchor='w')  # Posicionar a la izquierda
        
        # Label para el título
        self.label_titulo = tk.Label(
            self.frame_titulo,
            text="Chat Grupal",  # Texto del título
            font=("Alatsi", 16, "bold"),  # Fuente y tamaño
            bg="#3D3D3D",  # Fondo gris oscuro
            fg="white",  # Texto blanco
            anchor="center"
        )
        self.label_titulo.place(relx=0.5, rely=0.5, anchor="center")
    
        # Línea separadora debajo del título
        self.linea_separadora = tk.Frame(self.root, height=2, bg="white")  # Línea blanca de 2 píxeles
        self.linea_separadora.place(relx=0.2, rely=0.1, relwidth=0.8)

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
        # No empacar la scrollbar inicialmente
        
        self.canvas_mensajes.configure(yscrollcommand=self.scrollbar.set)
        
        # Crear un Frame dentro del Canvas para contener los mensajes
        self.frame_contenedor = tk.Frame(self.canvas_mensajes, bg="#2D2D2D")
        self.canvas_mensajes.create_window((0,0), window=self.frame_contenedor, anchor='nw')
        
        # Configurar la actualización del tamaño del Canvas
        self.frame_contenedor.bind("<Configure>", lambda e: self.canvas_mensajes.configure(scrollregion=self.canvas_mensajes.bbox("all")))
        
        # Inicializar la variable de estado de la scrollbar
        self.scrollbar_visible = False
        
        # Actualizar la visibilidad de la scrollbar inicialmente
        self.actualizar_scrollbar_visibility()

    def configurar_barra_acciones(self):
        """Configura la barra inferior con los botones y campo de entrada."""
        self.barra_acciones = tk.Frame(self.root, bg="#1D1D1D")
        self.barra_acciones.place(relx=0.2, rely=0.8, relwidth=0.8, relheight=0.2)
        
        # Marco para los íconos
        self.frame_iconos = tk.Frame(self.barra_acciones, bg="#1D1D1D", borderwidth=0, highlightthickness=0)
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

    def subir_foto(self):
        """Funcionalidad para subir una foto."""
        ruta_foto = filedialog.askopenfilename(
            title="Seleccionar foto",
            filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg;*.gif")]
        )
        if ruta_foto:
            # Aquí puedes agregar la lógica para enviar la foto al servidor
            pass

    def activar_mencion(self):
        """Funcionalidad para activar una mención (@)."""
        # Insertar '@' en el campo de entrada
        self.entrada_mensaje.insert(tk.END, "@")

    def subir_archivo(self):
        """Funcionalidad para subir un archivo."""
        ruta_archivo = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("Todos los archivos", "*.*")]
        )
        if ruta_archivo:
            # Aquí puedes agregar la lógica para enviar el archivo al servidor
            pass

    def actualizar_chat(self, mensaje, direccion='left'):
        """Actualiza el área de chat con un nuevo mensaje alineado."""
        # Crear un Frame para el mensaje
        frame_mensaje = tk.Frame(self.frame_contenedor, bg="#2D2D2D")
        
        # Crear el Label del mensaje
        etiqueta_mensaje = tk.Label(
            frame_mensaje, 
            text=mensaje, 
            bg="#2D2D2D", 
            fg="white", 
            font=self.fuente_dinamica,
            wraplength=400,  # Ajusta el ancho según sea necesario
            justify='left'
        )
        etiqueta_mensaje.pack(padx=10, pady=2, anchor='w')  # Por defecto a la izquierda
        
        # Alinear el Frame según la dirección
        if direccion == 'left':
            frame_mensaje.pack(fill='x', pady=2, anchor='w')
        elif direccion == 'center':
            frame_mensaje.pack(fill='x', pady=2, anchor='center')
        elif direccion == 'right':
            frame_mensaje.pack(fill='x', pady=2, anchor='e')
            # Cambiar el color de fondo y texto para mensajes alineados a la derecha
            etiqueta_mensaje.config(fg="white", justify='right')  # Blanco y alineado a la derecha
        
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
        elif not self._can_scroll() and self.scrollbar_visible:
            self.scrollbar.pack_forget()
            self.scrollbar_visible = False

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
        """Envía el mensaje escrito al servidor y lo muestra en la interfaz."""
        mensaje = self.entrada_mensaje.get().strip()  # Eliminar espacios en blanco
        if mensaje:
            self.actualizar_chat(f"Tú: {mensaje}", direccion='right')
            self.entrada_mensaje.delete(0, tk.END)
            self.cliente.enviar_mensaje(mensaje)
        else:
            messagebox.showwarning("Mensaje vacío", "No puedes enviar un mensaje vacío.")

    def conectar_al_servidor(self):
        """Conecta al servidor de chat."""
        nombre_usuario = cargar_nombre_usuario()
        if not nombre_usuario:
            nombre_usuario = simpledialog.askstring("Nombre", "¿Cómo te llamas?")
            if not nombre_usuario:
                nombre_usuario = "Anónimo"
            guardar_nombre_usuario(nombre_usuario)
        
        self.cliente.conectar(nombre_usuario)

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
        self.root.destroy()


# Asegúrate de que solo se cree una instancia de Tk
if __name__ == "__main__":
    import sys
    from modules.interfaz import ChatUI

    def main():
        root = tk.Tk()
        app = ChatUI(root)
        root.protocol("WM_DELETE_WINDOW", lambda: app.cerrar_aplicacion())
        root.mainloop()

    main()
