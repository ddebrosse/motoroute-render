import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as cx
import folium
from shapely.geometry import MultiLineString
import config

def render_poster(rutas_individuales, stats, output_base_path):
    """Genera la exportación del póster PNG estático."""
    print("🗺️  Generando póster estático...")
    lineas = [r["geometry"] for r in rutas_individuales]
    route_geometry = MultiLineString(lineas) if len(lineas) > 1 else lineas[0]

    gdf_routes = gpd.GeoDataFrame(geometry=[route_geometry], crs="EPSG:4326")
    gdf_routes = gdf_routes.to_crs(epsg=3857)

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
    """Genera el mapa interactivo definitivo con capas y panel global, sin puntos molestos."""
    print("🌐 Compilando mapa web interactivo limpio...")
    
    # 1. Configurar límites y centro
    lineas = [r["geometry"] for r in rutas_individuales]
    gdf_all = gpd.GeoDataFrame(geometry=lineas, crs="EPSG:4326")
    minx, miny, maxx, maxy = gdf_all.total_bounds
    center_lat = (miny + maxy) / 2
    center_lon = (minx + maxx) / 2

    # 2. Inicializar el mapa base vacío
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles=None)

    # 3. Añadir los 3 mapas base alternativos
    folium.TileLayer('OpenStreetMap', name='🗺️ Mapa de Carreteras (OSM)', control=True).add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri, DigitalGlobe, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community',
        name='🛰️ Vista Satélite (Esri)',
        control=True
    ).add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='🕶️ Modo Nocturno Oscuro', control=True).add_to(m)

    fg_rutas = folium.FeatureGroup(name="🏍️ Mis Rutas", control=False).add_to(m)

    # 4. Dibujar las líneas de las rutas limpias
    for ruta in rutas_individuales:
        geom = ruta["geometry"]
        coords = [(y, x) for x, y in zip(*geom.xy)]

        # Info del bocadillo de la ruta (Hover)
        desnivel_texto = f"{ruta['desnivel']} m" if ruta['desnivel'] > 0 else "No disponible"
        html_tooltip = f"""
        <div style="font-family: 'Arial', sans-serif; min-width: 190px; padding: 4px;">
            <b style="color: {config.ROUTE_COLOR}; font-size: 14px;">🏍️ {ruta['nombre']}</b><br>
            <hr style="border: 0; border-top: 1px solid #ddd; margin: 4px 0;">
            <span style="color: #555;">📅 Fecha:</span> <b>{ruta['fecha']}</b><br>
            <span style="color: #555;">📏 Distancia:</span> <b>{ruta['km']} km</b><br>
            <span style="color: #555;">⛰️ Desnivel +:</span> <b>{desnivel_texto}</b>
        </div>
        """

        estilo_highlight = {'weight': (config.ROUTE_LINEWIDTH * 2) + 3, 'opacity': 1.0}

        # Pintar línea de ruta
        folium.PolyLine(
            coords,
            color=config.ROUTE_COLOR,
            weight=config.ROUTE_LINEWIDTH * 2,
            opacity=0.8,
            tooltip=folium.Tooltip(html_tooltip, sticky=True),
            highlight_function=lambda x: estilo_highlight
        ).add_to(fg_rutas)

    # 5. Calcular estadísticas GLOBALES para el Panel flotante
    total_km_global = sum(r["km"] for r in rutas_individuales)
    total_rutas_global = len(rutas_individuales)
    total_desnivel_global = sum(r["desnivel"] for r in rutas_individuales)

    # 6. Inyectar Panel de Estadísticas Flotante
    html_dashboard = f"""
    <div style="
        position: fixed; 
        bottom: 30px; left: 30px; 
        width: 240px; height: auto; 
        background-color: rgba(255, 255, 255, 0.95); 
        box-shadow: 0 0 15px rgba(0,0,0,0.2);
        border-radius: 10px; 
        padding: 15px; 
        z-index: 9999;
        font-family: 'Arial', sans-serif;
        font-size: 13px;
        color: #333;
        border-left: 6px solid {config.ROUTE_COLOR};
    ">
        <h4 style="margin: 0 0 10px 0; color: #111; font-size: 15px;">📊 CUADRO DE MANDOS</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 6px 0; color: #666;">🏍️ Viajes totales:</td>
                <td style="text-align: right; font-weight: bold;">{total_rutas_global}</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 6px 0; color: #666;">📏 Distancia total:</td>
                <td style="text-align: right; font-weight: bold; color: {config.ROUTE_COLOR};">{round(total_km_global, 1)} km</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #666;">⛰️ Ascenso total:</td>
                <td style="text-align: right; font-weight: bold; color: #2e7d32;">{total_desnivel_global} m</td>
            </tr>
        </table>
    </div>
    """
    m.get_root().html.add_child(folium.Element(html_dashboard))

    # 7. Activar el botón selector de capas
    folium.LayerControl(position='topright', collapsed=False).add_to(m)

    m.fit_bounds([[miny, minx], [maxy, maxx]])
    m.save(output_path)
    print(f"💾 ¡Mapa limpio guardado con éxito!")