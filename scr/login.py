import json
import logging
from pathlib import Path
from typing import Optional

import socket
import tkinter as tk
from tkinter import messagebox

# Ruta absoluta al directorio raíz del proyecto
BASE_DIR = Path(__file__).parent.parent.resolve()

# Rutas a las carpetas específicas
DATA_DIR = BASE_DIR / 'data'
ASSETS_DIR = BASE_DIR / 'assets'

# Asegurarse de que las carpetas existen
DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de logging
LOG_FILE = DATA_DIR / "icocchat.log"

def run_login() -> bool:
    """
    Ejecuta la ventana de Login y retorna True si el inicio de sesión fue exitoso,
    False si el usuario cerró la ventana sin credenciales correctas.

    Returns:
        bool: Resultado del inicio de sesión.
    """
    app = LoginWindow()
    app.root.mainloop()
    return app.login_success

class LoginWindow:
    """
    Clase para manejar la ventana de inicio de sesión de IcoChat.
    """

    def __init__(self):
        """
        Inicializa la ventana de inicio de sesión.
        """
        self.root = tk.Tk()
        self.root.title("Iniciar sesión - IcoChat")
        self.root.configure(bg="#2C2F33")
        self.root.resizable(False, False)  # No permitir redimensionamiento manual

        # Cambiar el ícono de la ventana
        try:
            self.root.iconphoto(False, tk.PhotoImage(file="icochat.png"))
        except Exception as e:
            logging.error(f"Error cargando el icono de la ventana: {e}")

        # Centrar y escalar la ventana
        self.center_window(400, 300)

        # Variables para email, contraseña y recordarme
        self.email = tk.StringVar()
        self.password = tk.StringVar()
        self.remember_me = tk.BooleanVar(value=False)

        # Cargar credenciales si "Recordarme" está activo
        self.load_credentials()

        # Visibilidad de la contraseña
        self.password_visible = False

        # Indica si el login fue exitoso (Resp=1)
        self.login_success = False

        # Crear el formulario
        self.create_widgets()

        # Interceptar el cierre de la ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def center_window(self, base_width: int, base_height: int) -> None:
        """
        Centra la ventana en la pantalla y, si la resolución es menor
        que base_width x base_height, reduce proporcionalmente el tamaño.

        Args:
            base_width (int): Ancho base de la ventana.
            base_height (int): Alto base de la ventana.
        """
        # Obtener resolución actual
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculamos factor de escala, manteniendo la proporción
        scale_factor = min(
            screen_width / base_width,
            screen_height / base_height
        )

        if scale_factor < 1:
            # Pantalla más pequeña que 400x300 => escalar
            width = int(base_width * scale_factor)
            height = int(base_height * scale_factor)
        else:
            # Pantalla suficientemente grande => usar 400x300
            width = base_width
            height = base_height

        # Calcular coordenadas para centrar
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self) -> None:
        """
        Crea y organiza los widgets de la ventana de inicio de sesión.
        """
        frame = tk.Frame(self.root, bg="#2C2F33", padx=20, pady=20)
        frame.pack(expand=True, fill="both")

        # Correo electrónico
        tk.Label(
            frame,
            text="Correo electrónico",
            bg="#2C2F33",
            fg="#FFFFFF",
            font=("Arial", 10)
        ).pack(anchor="w", pady=5)
        tk.Entry(
            frame,
            textvariable=self.email,
            font=("Arial", 12)
        ).pack(fill="x", pady=5)

        # Contraseña
        tk.Label(
            frame,
            text="Contraseña",
            bg="#2C2F33",
            fg="#FFFFFF",
            font=("Arial", 10)
        ).pack(anchor="w", pady=5)

        password_frame = tk.Frame(frame, bg="#2C2F33")
        password_frame.pack(fill="x", pady=5)

        self.password_entry = tk.Entry(
            password_frame,
            textvariable=self.password,
            font=("Arial", 12),
            show="*"
        )
        self.password_entry.pack(side=tk.LEFT, expand=True, fill="x")

        self.show_password_btn = tk.Button(
            password_frame,
            text="👁",
            command=self.toggle_password,
            bg="#2C2F33",
            fg="#FFFFFF",
            borderwidth=0
        )
        self.show_password_btn.pack(side=tk.LEFT)

        # Botón de inicio de sesión
        tk.Button(
            frame,
            text="Iniciar sesión",
            command=self.sign_in,
            font=("Arial", 12),
            bg="#FF8C00",
            fg="#FFFFFF"
        ).pack(fill="x", pady=10)

        # Opciones de recordarme y olvidar contraseña
        options_frame = tk.Frame(frame, bg="#2C2F33")
        options_frame.pack(fill="x", pady=10)

        tk.Checkbutton(
            options_frame,
            text="Recordarme",
            variable=self.remember_me,
            bg="#2C2F33",
            fg="#FFFFFF",
            font=("Arial", 10),
            activebackground="#2C2F33",
            activeforeground="#FFFFFF",
            selectcolor="#2C2F33",
        ).pack(side=tk.LEFT)

        tk.Button(
            options_frame,
            text="Olvidé mi contraseña",
            command=self.forgot_password,
            font=("Arial", 10),
            bg="#2C2F33",
            fg="#FFFFFF",
            borderwidth=0,
            activebackground="#2C2F33",
            activeforeground="#FFFFFF",
        ).pack(side=tk.RIGHT)

    def toggle_password(self) -> None:
        """
        Alterna la visibilidad de la contraseña en el campo de entrada.
        """
        if self.password_visible:
            self.password_entry.config(show="*")
            self.show_password_btn.config(text="👁")
        else:
            self.password_entry.config(show="")
            self.show_password_btn.config(text="👁‍🗨")
        self.password_visible = not self.password_visible

    def sign_in(self) -> None:
        """
        Maneja el proceso de inicio de sesión al hacer clic en el botón correspondiente.
        """
        email = self.email.get().strip()
        password = self.password.get().strip()

        if not email or not password:
            messagebox.showwarning("Campos vacíos", "Por favor, ingresa tu correo electrónico y contraseña.")
            return

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect(('190.107.177.156', 12345))  # Cambia a la IP y puerto del servidor
                logging.info("Conectado al servidor para inicio de sesión.")

                login_data = {"email": email, "password": password}
                client_socket.sendall(f"CREDENTIALS:{json.dumps(login_data)}".encode('utf-8'))
                logging.info("Datos de inicio de sesión enviados al servidor.")

                response = client_socket.recv(1024).decode('utf-8')
                logging.info(f"Respuesta del servidor: {response}")

            response_data = json.loads(response)
            if response_data.get("status") == "received":
                resp_val = response_data.get("Resp", 0)
                mens_val = response_data.get("Mens", "Sin mensaje")

                if resp_val == 1:
                    # Éxito
                    if self.remember_me.get():
                        self.save_credentials(email, password)
                    else:
                        self.clear_credentials()

                    self.login_success = True
                    messagebox.showinfo("Inicio exitoso", mens_val)
                    self.root.destroy()  # Cierra la ventana de login
                else:
                    self.login_success = False
                    messagebox.showerror("Error de credenciales", mens_val)
            else:
                messagebox.showerror("Error", "El servidor envió una respuesta inesperada.")
                logging.warning("Respuesta inesperada del servidor durante el inicio de sesión.")
        except ConnectionRefusedError:
            messagebox.showerror("Error de conexión", "No se pudo conectar al servidor. Inténtalo de nuevo más tarde.")
            logging.error("Conexión rechazada por el servidor.")
        except socket.timeout:
            messagebox.showerror("Error de conexión", "Tiempo de espera agotado al intentar conectarse al servidor.")
            logging.error("Tiempo de espera agotado al conectarse al servidor.")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Respuesta del servidor no válida.")
            logging.error("Error al decodificar la respuesta JSON del servidor.")
        except Exception as e:
            messagebox.showerror("Error de conexión", f"No se pudo conectar al servidor: {e}")
            logging.error(f"Error inesperado durante el inicio de sesión: {e}")

    def on_close(self) -> None:
        """
        Maneja el evento de cierre de la ventana.
        No abre el chat si login_success=False.
        """
        if not self.login_success:
            logging.info("Ventana de login cerrada sin éxito en el inicio de sesión.")
        self.root.destroy()

    def load_credentials(self) -> str:
        """
        Carga las credenciales almacenadas si la opción "Recordarme" está activa.

        Returns:
            str: Correo electrónico cargado.
            str: Contraseña cargada.
        """
        credentials_file = DATA_DIR/"credentials.json"
        if credentials_file.exists():
            try:
                with credentials_file.open("r", encoding="utf-8") as file:
                    data = json.load(file)
                    self.email.set(data.get("email", ""))
                    self.password.set(data.get("password", ""))
                logging.info("Credenciales cargadas desde credentials.json.")
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Error cargando las credenciales: {e}")

    def save_credentials(self, email: str, password: str) -> None:
        """
        Guarda las credenciales del usuario en un archivo.

        Args:
            email (str): Correo electrónico del usuario.
            password (str): Contraseña del usuario.
        """
        credentials_file =  DATA_DIR/"credentials.json"

        data = {"email": email, "password": password}
        try:
            with (DATA_DIR / "credentials.json").open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            logging.info("credenciales guardadas en credentials.json.")
        except IOError as e:
            logging.error(f"Error guardando las credenciales: {e}")

    def clear_credentials(self) -> None:
        """
        Elimina las credenciales almacenadas.
        """
        credentials_file = DATA_DIR/"credentials.json"
        if credentials_file.exists():
            try:
                credentials_file.unlink()
                logging.info("Credenciales eliminadas de credentials.json.")
            except IOError as e:
                logging.error(f"Error eliminando las credenciales: {e}")

    def forgot_password(self) -> None:
        """
        Maneja la acción de "Olvidé mi contraseña".
        """
        messagebox.showinfo("Recuperar contraseña", "Por favor, contacta con soporte para restablecer tu contraseña.")
        logging.info
