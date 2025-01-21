# modules/red.py
import socket
import threading

class ClienteChat:
    """Clase para manejar la conexión del cliente al servidor de chat."""
    def __init__(self, ip_servidor, puerto_servidor, al_recibir_mensaje):
        self.ip_servidor = ip_servidor
        self.puerto_servidor = puerto_servidor
        self.al_recibir_mensaje = al_recibir_mensaje
        self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.activo = False

    def conectar(self, nombre_usuario):
        """Conecta al servidor y envía el nombre de usuario."""
        try:
            self.socket_cliente.connect((self.ip_servidor, self.puerto_servidor))
            self.socket_cliente.send(nombre_usuario.encode('utf-8'))
            self.activo = True
            threading.Thread(target=self.recibir_mensajes, daemon=True).start()
        except Exception as e:
            print(f"Error de conexión: {e}")

    def recibir_mensajes(self):
        """Recibe mensajes del servidor."""
        while self.activo:
            try:
                mensaje = self.socket_cliente.recv(1024).decode('utf-8')
                if mensaje:
                    self.al_recibir_mensaje(mensaje)
                else:
                    self.activo = False
            except Exception as e:
                print(f"Error al recibir mensaje: {e}")
                self.activo = False

    def enviar_mensaje(self, mensaje):
        """Envía un mensaje al servidor."""
        try:
            self.socket_cliente.send(mensaje.encode('utf-8'))
        except Exception as e:
            print(f"Error al enviar mensaje: {e}")

    def desconectar(self):
        """Desconecta del servidor."""
        self.activo = False
        self.socket_cliente.close()
