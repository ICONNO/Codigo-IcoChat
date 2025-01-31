import notify2
import os
import pygame

# Inicializar pygame para manejar audio de notificación
pygame.init()
pygame.mixer.init()

# Función para reproducir sonido de notificación
def reproducir_sonido():
    audio_path = "C:\Users\Cliente\Documents\assets/mayonesa.mp3"  # Ruta del archivo de audio
    
    # Verificar si el archivo de audio existe
    if not os.path.exists(audio_path):
        print(f"Error: El archivo de audio {audio_path} no existe.")
    else:
        try:
            sound = pygame.mixer.Sound(audio_path)
            sound.play()
            print("Reproduciendo sonido...")
        except pygame.error as e:
            print(f"No se pudo reproducir el sonido: {e}")

# Función para mostrar una notificación visual en Ubuntu
def mostrar_notificacion(self, mensaje):
    reproducir_sonido()  # Reproduce el sonido al recibir el mensaje

    # Inicializar las notificaciones
    notify2.init("Notificación de Chat")

    # Crear la notificación
    n = notify2.Notification("Nuevo mensaje", mensaje, "notification-message-im")

    # Configurar la duración de la notificación (en milisegundos)
    n.set_timeout(3000)

    # Mostrar la notificación
    n.show()
