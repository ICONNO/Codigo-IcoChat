# src/config.py

from pathlib import Path
import logging

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

# Verificar si el root logger ya tiene handlers
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger('config')
    logger.info("Configuración de logging inicializada.")
else:
    logger = logging.getLogger('config')
    logger.info("Logging ya estaba configurado.")
