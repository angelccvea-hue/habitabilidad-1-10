# Datos y pipeline de cruce

## Fuentes

| Fuente | Contenido típico | Código de preparación |
|--------|------------------|------------------------|
| 1×10 | Solicitudes ciudadanas (caso, contacto, dirección, GPS) | `prepare_solicitudes` |
| Habitable | Inspecciones post-sismo (etiqueta semáforo, edificio, GPS) | `prepare_habitable` |
| IA Excel | Estructuras con estatus de riesgo (`INF_*`) | snapshot en `data/external_nasa/cruce_ia_nasa/` |
| NASA S1 | Footprints radar / labels daño | scripts `cruzar_*_nasa_*` |

## Matching 1×10 ↔ Habitable

Archivo: `prepare_data.match_solicitudes`

1. Solo puntos **mapeables** (GPS válido en Venezuela, sin hotspot basura).  
2. Vecinos Habitable con **BallTree** (haversine), radio configurable (~50 m).  
3. Score de nombre (`rapidfuzz`) para clasificar:  
   - `coincide_alta` / `coincide_media` → «ya atendidas»  
   - `coincide_geo_solo` → cerca en mapa, revisar  
   - `solo_1x10` → pendiente  

Unificación de reportes cercanos: `dedupe_1x10` (representante + `n_reportes`).

## Artefactos generados

```text
data/processed/
  solicitudes.parquet   # 1×10 + columnas de match
  inspecciones.parquet  # Habitable limpio
  summary.json          # KPIs del corte

data/uploads/
  solicitudes_1x10.xlsx
  inspecciones_habitable.csv|.xlsx
```

Con `BI_DATA_KEY`, esos archivos se guardan **cifrados** (`secure_io`).

## Excel maestro para el equipo 1×10

`abordaje_export.construir_cruce_1x10_capas`:

- Filas: representantes 1×10 con GPS ok.  
- Columnas Habitable (estado de cruce, etiqueta).  
- Columnas por capa GIS (punto dentro de polígono).  
- IA por vecino ≤ 50 m (prioriza alertas).  
- NASA por `codigo_caso` si existe el parquet precalculado.

UI: Mapas de abordaje → Descargar cruce territorial.

## Datos que no versionamos

Ver `data/README.md`. Los revisores deben pedir un **paquete de datos de prueba anonimizado** o generar parquet desde Excel de ejemplo.
