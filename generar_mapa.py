import os
import config
from loader import load_multiple_gpx_with_stats
from renderer import render_poster, render_html_map

def main():
    os.makedirs(config.INPUT_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    gpx_files = [os.path.join(config.INPUT_DIR, f) for f in os.listdir(config.INPUT_DIR) if f.lower().endswith('.gpx')]

    if not gpx_files:
        print("❌ No se encontraron archivos GPX.")
        return

    try:
        geometry, stats = load_multiple_gpx_with_stats(gpx_files)
        output_base_path = os.path.join(config.OUTPUT_DIR, "mis_rutas")
        
        print("🗺️  Generando póster estático...")
        render_poster(geometry, stats, output_base_path)

        # Si en config.py se activa EXPORT_HTML, genera el mapa interactivo
        if getattr(config, 'EXPORT_HTML', False):
            render_html_map(geometry, f"{output_base_path}_interactivo.html")
            
        print(f"✅ ¡Éxito! Archivos generados en: {config.OUTPUT_DIR}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()