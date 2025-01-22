import notify2
import os
import pygame

# Inicializar solo el módulo mixer de pygame para manejar audio de notificación
pygame.mixer.init()

# Cargar el sonido una vez
audio_path = "mayonesa.wav"  # Convierte tu archivo a WAV para mayor compatibilidad
if os.path.exists(audio_path):
    try:
        sonido_notificacion = pygame.mixer.Sound(audio_path)
    except pygame.error as e:
        print(f"No se pudo cargar el sonido: {e}")
        sonido_notificacion = None
else:
    print(f"Error: El archivo de audio {audio_path} no existe.")
    sonido_notificacion = None

# Función para reproducir sonido de notificación
def reproducir_sonido():
    if sonido_notificacion:
        try:
            sonido_notificacion.play()
            print("Reproduciendo sonido...")
        except pygame.error as e:
            print(f"No se pudo reproducir el sonido: {e}")
    else:
        print("No hay sonido cargado para reproducir.")

# Función para mostrar una notificación visual en Ubuntu
def mostrar_notificacion(mensaje):
    reproducir_sonido()  # Reproduce el sonido al recibir el mensaje
    
    # Inicializar las notificaciones
    notify2.init("Notificación de Chat")

    # Crear la notificación
    n = notify2.Notification("Nuevo mensaje", mensaje, "notification-message-im")

    # Configurar la duración de la notificación (en milisegundos)
    n.set_timeout(3000)

    # Mostrar la notificación
    n.show()
