# Mapas y capas GIS

## Mapa operativo (cruce BI)

- `map_robust.py` — Folium + FastMarkerCluster / heatmaps.  
- Controles de capas y búsqueda en la UI Streamlit.  
- Base cartográfica: `map_tiles.available_basemaps()`.

## Mapas de abordaje

- Capas en `data/gis_lite/` (geojson.zip / parquet ligeros).  
- Catálogo: `pages_abordaje.LAYER_CATALOG` (máscaras, cuadrículas, microzonas, parroquias INE, segmentos censales, puntos de campo).  
- Conversión desde GPKG/SHP: `scripts/convertir_mapas_abordaje_lite.py`.

## NASA / IA

- Lite para mapa: `scripts/build_nasa_map_lite.py` → `nasa_map_lite.parquet`.  
- Cruces detallados: `scripts/cruzar_1x10_nasa_detallado.py`, `cruzar_habitable_nasa_detallado.py`, `cruzar_ia_nasa_detallado.py`.  
- UI: `pages_nasa.py`, `pages_nasa_analisis.py`.

## Política de tiles (seguridad)

En producción el navegador **no** debería pedir mosaicos a OSM/Esri (revelan el área consultada).  
Configure tiles internos:

```powershell
$env:BI_TILES_URL = "https://tiles.institucion.local/{z}/{x}/{y}.png"
$env:BI_TILES_ATTR = "© Institución"
```

Ver `docs/03-SEGURIDAD.md` §6.
