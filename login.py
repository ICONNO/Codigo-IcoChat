import tkinter as tk
from tkinter import messagebox
import socket
import json
import os

class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Iniciar sesión - IcoChat")
        self.root.configure(bg="#2C2F33")
        
        # Mantemos una base de 400x300
        # y escalamos si la pantalla es más pequeña
        self.root.resizable(False, False)  # Para no permitir redimensionamiento manual

        # Cambiar el ícono de la ventana
        self.root.iconphoto(False, tk.PhotoImage(file="icochat.png"))

        # Centrar (y escalar si la pantalla es muy pequeña)
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

    def center_window(self, base_width, base_height):
        """
        Centra la ventana en la pantalla y, si la resolución es menor
        que base_width x base_height, reduce proporcionalmente el tamaño.
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

    def create_widgets(self):
        frame = tk.Frame(self.root, bg="#2C2F33", padx=20, pady=20)
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="Correo electrónico", bg="#2C2F33", fg="#FFFFFF", font=("Arial", 10)).pack(anchor="w", pady=5)
        tk.Entry(frame, textvariable=self.email, font=("Arial", 12)).pack(fill="x", pady=5)

        tk.Label(frame, text="Contraseña", bg="#2C2F33", fg="#FFFFFF", font=("Arial", 10)).pack(anchor="w", pady=5)
        password_frame = tk.Frame(frame, bg="#2C2F33")
        password_frame.pack(fill="x", pady=5)
        self.password_entry = tk.Entry(password_frame, textvariable=self.password, font=("Arial", 12), show="*")
        self.password_entry.pack(side=tk.LEFT, expand=True, fill="x")
        self.show_password_btn = tk.Button(
            password_frame, text="👁", command=self.toggle_password, bg="#2C2F33", fg="#FFFFFF", borderwidth=0
        )
        self.show_password_btn.pack(side=tk.LEFT)

        tk.Button(frame, text="Iniciar sesión", command=self.sign_in, font=("Arial", 12), bg="#FF8C00", fg="#FFFFFF").pack(fill="x", pady=10)

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

    def toggle_password(self):
        if self.password_visible:
            self.password_entry.config(show="*")
            self.show_password_btn.config(text="👁")
        else:
            self.password_entry.config(show="")
            self.show_password_btn.config(text="👁‍🗨")
        self.password_visible = not self.password_visible

    def sign_in(self):
        email = self.email.get()
        password = self.password.get()

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('190.107.177.156', 12345))  # Cambia a la IP y puerto del servidor
            print("conectado")
            login_data = {"email": email, "password": password}
            client_socket.send(f"CREDENTIALS:{json.dumps(login_data)}".encode('utf-8'))
            print("enviado")
            response = client_socket.recv(1024).decode('utf-8')
            client_socket.close()
            print("cerrado")
            print(response)

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
        except Exception as e:
            messagebox.showerror("Error de conexión", f"No se pudo conectar al servidor: {e}")

    def on_close(self):
        """
        Se llama al cerrar la ventana manualmente (la X).
        No abrimos el chat si login_success=False.
        """
        self.root.destroy()

    def load_credentials(self):
        if os.path.exists("credentials.json"):
            with open("credentials.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                self.email.set(data.get("email", ""))
                self.password.set(data.get("password", ""))

    def save_credentials(self, email, password):
        with open("credentials.json", "w", encoding="utf-8") as file:
            json.dump({"email": email, "password": password}, file, ensure_ascii=False, indent=4)

    def clear_credentials(self):
        if os.path.exists("credentials.json"):
            os.remove("credentials.json")

    def forgot_password(self):
        messagebox.showinfo("Recuperar contraseña", "Por favor, contacta con soporte para restablecer tu contraseña.")

def run_login():
    """
    Ejecuta la ventana de Login y retorna True si login fue exitoso,
    False si el usuario cerró la ventana sin credenciales correctas.
    """
    app = LoginWindow()
    app.root.mainloop()
    return app.login_success
