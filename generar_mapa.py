import os
import config
from loader import load_multiple_gpx_with_stats
from renderer import render_poster, render_html_map

def main():
    os.makedirs(config.INPUT_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # NUEVO: Asegurar que se crea la carpeta docs/ en el servidor
    html_out_dir = getattr(config, 'HTML_OUTPUT_DIR', config.OUTPUT_DIR)
    os.makedirs(html_out_dir, exist_ok=True)

    gpx_files = [os.path.join(config.INPUT_DIR, f) for f in os.listdir(config.INPUT_DIR) if f.lower().endswith('.gpx')]

    if not gpx_files:
        print("❌ No se encontraron archivos GPX.")
        return

    try:
        geometry, stats = load_multiple_gpx_with_stats(gpx_files)
        output_base_path = os.path.join(config.OUTPUT_DIR, "mis_rutas")
        
        print("🗺️  Generando póster estático...")
        render_poster(geometry, stats, output_base_path)

        if getattr(config, 'EXPORT_HTML', False):
            # MODIFICADO: Ahora se guarda como 'index.html' en la carpeta docs/
            html_path = os.path.join(html_out_dir, "index.html")
            render_html_map(geometry, html_path)
            
        print(f"✅ ¡Éxito! Archivos generados.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()