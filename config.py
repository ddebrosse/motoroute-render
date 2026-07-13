import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, 'data', 'gpx')

# El póster estático se seguirá guardando en output/
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# NUEVO: La web interactiva se guardará en docs/ para que GitHub Pages pueda leerla
HTML_OUTPUT_DIR = os.path.join(BASE_DIR, 'docs')

# Paleta de colores estándar (OpenStreetMap)
ROUTE_COLOR = "#FF9900"      # Naranja intenso/cobrizo
ROUTE_LINEWIDTH = 1.5
GLOW_COLOR = "#FF6600"
GLOW_LINEWIDTH = 4.0
GLOW_ALPHA = 0.2             
MARGIN_DEGREES = 0.1         

EXPORT_FORMATS = ['png']
EXPORT_HTML = True           

# ==========================================
# CONFIGURACIÓN DEL ENCUADRE
# ==========================================
TARGET_COUNTRIES = ['Spain', 'Portugal']