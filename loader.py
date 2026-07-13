import hashlib
import math
import os
import gpxpy
import gpxpy.gpx
from shapely.geometry import LineString

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def load_multiple_gpx_with_stats(file_paths):
    seen_hashes = set()
    rutas_individuales = [] # Nueva estructura para guardar geometría + metadatos por ruta
    
    total_km = 0.0
    longest_route_km = 0.0
    total_routes = 0

    for path in file_paths:
        file_hash = get_file_hash(path)
        if file_hash in seen_hashes:
            print(f"⚠️  Ignorando duplicado: {os.path.basename(path)}")
            continue
        seen_hashes.add(file_hash)

        try:
            with open(path, 'r', encoding='utf-8') as gpx_file:
                gpx = gpxpy.parse(gpx_file)

            # Intentar extraer la fecha de inicio de la ruta
            fecha_ruta = "Desconocida"
            if gpx.time:
                fecha_ruta = gpx.time.strftime("%d/%m/%Y")
            elif gpx.tracks and gpx.tracks[0].segments and gpx.tracks[0].segments[0].points:
                first_point = gpx.tracks[0].segments[0].points[0]
                if first_point.time:
                    fecha_ruta = first_point.time.strftime("%d/%m/%Y")

            nombre_archivo = os.path.splitext(os.path.basename(path))[0]

            for track in gpx.tracks:
                for segment in track.segments:
                    points = []
                    prev_point = None
                    current_segment_km = 0.0
                    
                    for point in segment.points:
                        points.append((point.longitude, point.latitude))
                        if prev_point:
                            dist = haversine_distance(prev_point.latitude, prev_point.longitude, 
                                                      point.latitude, point.longitude)
                            current_segment_km += dist
                            total_km += dist
                        prev_point = point
                    
                    if len(points) >= 2:
                        # Guardamos de forma independiente cada tramo con sus datos para el HTML
                        rutas_individuales.append({
                            "geometry": LineString(points),
                            "nombre": nombre_archivo.replace('_', ' '),
                            "fecha": fecha_ruta,
                            "km": round(current_segment_km, 1)
                        })
                        
                        if current_segment_km > longest_route_km:
                            longest_route_km = current_segment_km
                        total_routes += 1
                        
        except Exception as e:
            print(f"❌ Error leyendo {path}: {e}")

    if not rutas_individuales:
        raise ValueError("No se encontraron rutas válidas.")

    stats_globales = {
        "routes": total_routes,
        "total_km": round(total_km, 1),
        "longest_km": round(longest_route_km, 1)
    }
    
    return rutas_individuales, stats_globales