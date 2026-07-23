# Secciones de la interfaz (UI)

La navegación se define en `src/nav_schema.py`. Cada ítem tiene un `id` que `app.py` despacha a una función `page_*`.

## Inicio / índice

- Presentación ejecutiva y acceso a secciones.  
- Expander de **carga de archivos** (solo rol `admin`).

## Mapa operativo

- **Código:** `map_robust.render_map_ui`  
- Capas: Habitable, coincidencias, pendientes 1×10, dudosos, heatmaps.  
- Mapa base según política de tiles (`map_tiles`).

## Características / info

- `pages_caracteristicas` — perfiles de 1×10 y Habitable (distribuciones, calidad GPS).

## Análisis 1×10 y Habitable

- `pages_analysis` — colas, KPIs, tablas, descargas CSV/Excel.  
- Depuración 1×10: `depuracion_1x10`.  
- Reportes Habitable: `habitable_reports` / `reportes_inspecciones`.

## Mapas de abordaje

- `pages_abordaje`  
  - **Capas:** GIS lite (máscaras, cuadrículas, microzonas, parroquias, segmentos).  
  - **Descarga:** Excel maestro 1×10 × capas + Habitable + IA + NASA (`abordaje_export`).

## Mapa NASA y análisis por fuente

- `pages_nasa` — capas visuales NASA × 1×10 × Habitable × IA.  
- `pages_nasa_analisis` — pestañas de análisis 1×10 / Habitable / IA vs radar.

## Roles y lo que ven

| Rol | Contacto PII | Subir Excel | Admin usuarios | Auditoría |
|-----|--------------|-------------|----------------|-----------|
| ejecutivo | No | No | No | No |
| operador | Sí | No | No | No |
| admin | Sí | Sí | Sí | Sí |

Definición: `auth_users.ROLE_*` + `pii_policy` + `auth_gate.can_*`.
