import os
from pathlib import Path
import notify2
import pygame

# Configuración global
AUDIO_PATH = Path("/home/admns/dfdgs/mayonesa.mp3")
NOTIFICATION_APP_NAME = "Notificación de Chat"
NOTIFICATION_ICON = "notification-message-im"
NOTIFICATION_TIMEOUT = 3000  # Milisegundos


class Notificador:
    """Clase para manejar notificaciones visuales y sonoras."""

    def __init__(self, audio_path: Path):
        """
        Inicializa el notificador con el sonido de notificación.

        :param audio_path: Ruta al archivo de sonido de notificación.
        """
        pygame.mixer.init()
        self.sonido_notificacion = self._cargar_sonido(audio_path)
        notify2.init(NOTIFICATION_APP_NAME)

    def _cargar_sonido(self, audio_path: Path):
        """
        Carga el sonido de notificación desde la ruta especificada.

        :param audio_path: Ruta al archivo de sonido.
        :return: Objeto Sound si se carga correctamente, de lo contrario None.
        """
        if audio_path.exists():
            try:
                sonido = pygame.mixer.Sound(str(audio_path))
                print(f"Sonido cargado desde: {audio_path}")
                return sonido
            except pygame.error as e:
                print(f"Error al cargar el sonido: {e}")
        else:
            print(f"Archivo de audio no encontrado: {audio_path}")
        return None

    def reproducir_sonido(self):
        """Reproduce el sonido de notificación si está disponible."""
        if self.sonido_notificacion:
            try:
                self.sonido_notificacion.play()
                print("Sonido reproducido.")
            except pygame.error as e:
                print(f"Error al reproducir el sonido: {e}")
        else:
            print("No hay sonido disponible para reproducir.")

    def mostrar_notificacion(self, mensaje: str):
        """
        Muestra una notificación visual y reproduce un sonido.

        :param mensaje: Mensaje a mostrar en la notificación.
        """
        self.reproducir_sonido()

        try:
            notificacion = notify2.Notification(
                "Nuevo mensaje",
                mensaje,
                icon=NOTIFICATION_ICON
            )
            notificacion.set_timeout(NOTIFICATION_TIMEOUT)
            notificacion.show()
            print("Notificación mostrada.")
        except Exception as e:
            print(f"Error al mostrar la notificación: {e}")


# Instancia global del notificador
notificador = Notificador(AUDIO_PATH)


def mostrar_notificacion(mensaje: str):
    """
    Función global para mostrar una notificación.

    :param mensaje: Mensaje a mostrar en la notificación.
    """
    notificador.mostrar_notificacion(mensaje)
