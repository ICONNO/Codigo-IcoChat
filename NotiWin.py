from win10toast import ToastNotifier

# Crear una instancia del notificador
notificador = ToastNotifier()

# Función para mostrar notificaciones
def mostrar_notificacionWin(titulo, mensaje):
    notificador.show_toast(titulo, mensaje, duration=5, icon_path=None)
