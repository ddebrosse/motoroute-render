import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as cx
import folium
from shapely.geometry import MultiLineString
import config

def render_poster(rutas_individuales, stats, output_base_path):
    """Sigue generando el póster estático a todo color unificando geometrías."""
    lineas = [r["geometry"] for r in rutas_individuales]
    route_geometry = MultiLineString(lineas) if len(lineas) > 1 else lineas[0]

    gdf_routes = gpd.GeoDataFrame(geometry=[route_geometry], crs="EPSG:4326")
    gdf_routes = gdf_routes.to_crs(epsg=3857)

    print("🗺️  Calculando fronteras para el encuadre...")
    url_mapa = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
    world = gpd.read_file(url_mapa)
    world = world.to_crs(epsg=3857)
    
    modo_automatico = True
    region_encuadre = gpd.GeoDataFrame()
    paises_objetivo = getattr(config, 'TARGET_COUNTRIES', ['ALL'])
    if isinstance(paises_objetivo, str): paises_objetivo = [paises_objetivo]

    if 'ALL' not in [p.upper() for p in paises_objetivo]:
        modo_automatico = False
        patron_busqueda = '|'.join(paises_objetivo)
        region_encuadre = world[world['ADMIN'].str.contains(patron_busqueda, case=False, na=False)]
        if region_encuadre.empty: modo_automatico = True

    if modo_automatico:
        world_parts = world.explode(index_parts=False)
        region_encuadre = world_parts[world_parts.intersects(gdf_routes.geometry.iloc[0])]

    fig, ax = plt.subplots(figsize=(12, 16))
    ax.set_axis_off()

    gdf_routes.plot(ax=ax, color=config.ROUTE_COLOR, linewidth=config.ROUTE_LINEWIDTH, capstyle='round', zorder=4)

    if not region_encuadre.empty:
        minx, miny, maxx, maxy = region_encuadre.total_bounds
        margen_x = (maxx - minx) * 0.05
        margen_y = (maxy - miny) * 0.05
        ax.set_xlim(minx - margen_x, maxx + margen_x)
        ax.set_ylim(miny - margen_y, maxy + margen_y)
    else:
        minx, miny, maxx, maxy = gdf_routes.total_bounds
        margin_meters = config.MARGIN_DEGREES * 111000 
        ax.set_xlim(minx - margin_meters, maxx + margin_meters)
        ax.set_ylim(miny - margin_meters, maxy + margin_meters)

    cx.add_basemap(ax, source=cx.providers.OpenStreetMap.Mapnik, zorder=1)

    for fmt in config.EXPORT_FORMATS:
        output_path = f"{output_base_path}_poster.{fmt}"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()


def render_html_map(rutas_individuales, output_path):
    """Genera un mapa HTML interactivo con información flotante al pasar el ratón (Hover)"""
    print("🌐 Generando mapa HTML interactivo con información de ruta...")
    
    # Calcular el centro aproximado usando la primera ruta para inicializar el mapa
    lineas = [r["geometry"] for r in rutas_individuales]
    gdf_all = gpd.GeoDataFrame(geometry=lineas, crs="EPSG:4326")
    minx, miny, maxx, maxy = gdf_all.total_bounds
    center_lat = (miny + maxy) / 2
    center_lon = (minx + maxx) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='OpenStreetMap')

    # Añadir cada ruta de forma independiente para asociarle sus propios datos
    for ruta in rutas_individuales:
        geom = ruta["geometry"]
        coords = [(y, x) for x, y in zip(*geom.xy)]

        # Diseñamos un bocadillo flotante (Tooltip) muy limpio usando HTML y CSS
        html_tooltip = f"""
        <div style="font-family: 'Arial', sans-serif; min-width: 180px; padding: 4px;">
            <b style="color: {config.ROUTE_COLOR}; font-size: 14px;">🏍️ {ruta['nombre']}</b><br>
            <hr style="border: 0; border-top: 1px solid #ddd; margin: 4px 0;">
            <span style="color: #555;">📅 Fecha:</span> <b>{ruta['fecha']}</b><br>
            <span style="color: #555;">📏 Distancia:</span> <b>{ruta['km']} km</b>
        </div>
        """

        # Estilo visual de la línea al pasar el ratón por encima (se vuelve un poco más gruesa)
        estilo_highlight = {'weight': (config.ROUTE_LINEWIDTH * 2) + 3, 'opacity': 1.0}

        # Dibujar la línea en el mapa interactivo
        folium.PolyLine(
            coords,
            color=config.ROUTE_COLOR,
            weight=config.ROUTE_LINEWIDTH * 2,
            opacity=0.8,
            tooltip=folium.Tooltip(html_tooltip, sticky=True), # sticky=True hace que el texto siga al cursor
            highlight_function=lambda x: estilo_highlight      # Efecto visual al pasar el ratón
        ).add_to(m)

    # Ajustar el mapa para que encuadre todas las rutas juntas perfectamente al abrirse
    m.fit_bounds([[miny, minx], [maxy, maxx]])
    m.save(output_path)
    print(f"💾 Guardado HTML interactivo en: {output_path}")