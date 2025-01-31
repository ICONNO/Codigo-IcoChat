import logging
from typing import Optional

from win10toast import ToastNotifier

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("icocchat.log"),
        logging.StreamHandler()
    ]
)


class NotificadorWin:
    """
    Clase para manejar las notificaciones de Windows.
    """

    def __init__(self) -> None:
        """
        Inicializa una instancia del notificador de Windows.
        """
        self.notificador = ToastNotifier()
        logging.info("Inicializado ToastNotifier para notificaciones de Windows.")

    def mostrar_notificacion(
        self, 
        titulo: str, 
        mensaje: str, 
        duracion: int = 5, 
        icon_path: Optional[str] = None
    ) -> None:
        """
        Muestra una notificación en Windows.

        Args:
            titulo (str): Título de la notificación.
            mensaje (str): Mensaje de la notificación.
            duracion (int, optional): Duración de la notificación en segundos. Defaults to 5.
            icon_path (Optional[str], optional): Ruta al icono de la notificación. Defaults to None.
        """
        try:
            self.notificador.show_toast(
                titulo, 
                mensaje, 
                duration=duracion, 
                icon_path=icon_path, 
                threaded=True  # Permite que la notificación no bloquee el hilo principal
            )
            logging.info(f"Notificación mostrada: '{titulo}' - '{mensaje}'")
        except Exception as e:
            logging.error(f"Error mostrando notificación '{titulo}': {e}")


# Instancia única del notificador
notificador_win = NotificadorWin()


def mostrar_notificacionWin(
    titulo: str, 
    mensaje: str, 
    duracion: int = 5, 
    icon_path: Optional[str] = None
) -> None:
    """
    Función para mostrar notificaciones en Windows.

    Args:
        titulo (str): Título de la notificación.
        mensaje (str): Mensaje de la notificación.
        duracion (int, optional): Duración de la notificación en segundos. Defaults to 5.
        icon_path (Optional[str], optional): Ruta al icono de la notificación. Defaults to None.
    """
    notificador_win.mostrar_notificacion(titulo, mensaje, duracion, icon_path)
