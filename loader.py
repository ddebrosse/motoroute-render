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
    rutas_individuales = []
    
    total_km = 0.0
    longest_route_km = 0.0
    total_routes = 0

    for path in file_paths:
        file_hash = get_file_hash(path)
        if file_hash in seen_hashes: continue
        seen_hashes.add(file_hash)

        try:
            with open(path, 'r', encoding='utf-8') as gpx_file:
                gpx = gpxpy.parse(gpx_file)

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
                    desnivel_positivo = 0.0
                    
                    for point in segment.points:
                        points.append((point.longitude, point.latitude))
                        if prev_point:
                            # Calcular distancia
                            dist = haversine_distance(prev_point.latitude, prev_point.longitude, 
                                                      point.latitude, point.longitude)
                            current_segment_km += dist
                            total_km += dist
                            
                            # Calcular desnivel positivo (solo si el GPX tiene datos de altitud)
                            if point.elevation is not None and prev_point.elevation is not None:
                                diff = point.elevation - prev_point.elevation
                                if diff > 0:
                                    desnivel_positivo += diff
                                    
                        prev_point = point
                    
                    if len(points) >= 2:
                        rutas_individuales.append({
                            "geometry": LineString(points),
                            "nombre": nombre_archivo.replace('_', ' '),
                            "fecha": fecha_ruta,
                            "km": round(current_segment_km, 1),
                            "desnivel": round(desnivel_positivo),
                            "inicio_coords": (points[0][1], points[0][0]), # (lat, lon) para Folium
                            "fin_coords": (points[-1][1], points[-1][0])
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