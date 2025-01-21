# main.py
import tkinter as tk
from modules.interfaz import ChatUI

def main():
    """Función principal para iniciar la aplicación de chat."""
    root = tk.Tk()
    app = ChatUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
