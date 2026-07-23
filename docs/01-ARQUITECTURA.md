# Arquitectura del aplicativo

## Qué es

Una aplicación **Streamlit** (Python) que:

1. Carga y limpia **solicitudes 1×10** e **inspecciones Habitable**.  
2. Hace **matching espacial** (radio ~50 m + score de nombre).  
3. Expone tableros: mapa, análisis, abordaje GIS, NASA/IA.  
4. Aplica **controles de seguridad** (auth, roles, PII, cifrado, tiles, límites).

## Diagrama lógico

```text
┌─────────────────────────────────────────────────────────────┐
│  Navegador (HTTPS en producción)                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  app.py                                                     │
│  1) auth_gate.require_login (usuario + TOTP)                │
│  2) secure_io + assert crypto en prod                       │
│  3) load_data (parquet) → pii_policy según rol              │
│  4) nav_schema → pages_*                                    │
└───────┬─────────────────┬─────────────────┬─────────────────┘
        │                 │                 │
   map_robust      pages_analysis     pages_abordaje
   pages_nasa      pages_caract.      abordaje_export
        │                 │                 │
        └────────────┬────┴─────────────────┘
                     │
          data/processed/*.parquet  (cifrado si BI_DATA_KEY)
          data/uploads/*            (cifrado si BI_DATA_KEY)
          data/gis_lite/*           (capas abordaje)
          data/external_nasa/*      (cruces NASA/IA precalculados)
          data/auth/users.json      (hashes + secretos TOTP)
          data/audit/audit.jsonl    (append-only)
```

## Capas de código

| Capa | Módulos | Responsabilidad |
|------|---------|-----------------|
| Entrada UI | `app.py`, `ui_theme.py`, `nav_schema.py` | Shell, menú, estilos |
| Seguridad | `auth_*`, `pii_policy`, `secure_io`, `audit_*`, `map_tiles`, `runtime_limits` | Acceso, datos, mapas, DoS |
| Dominio datos | `prepare_data`, `dedupe_1x10`, `geo_utils`, `text_encoding` | Limpieza y cruce |
| Dominio mapas | `map_robust`, `pages_abordaje`, `pages_nasa*` | Folium / capas |
| Dominio análisis | `pages_analysis`, `habitable_reports`, `depuracion_1x10` | Tablas, KPIs, exports |
| Ingestión | `data_ingest` | Upload admin → pipeline |

## Flujo de datos (happy path)

1. **Admin** sube Excel 1×10 + Habitable (`data_ingest`).  
2. `run_pipeline` escribe `solicitudes.parquet` + `inspecciones.parquet` + `summary.json`.  
3. Usuario autenticado abre el tablero; `load_data` lee parquet (descifrado si aplica).  
4. Rol **ejecutivo**: se quitan columnas de contacto en memoria (`pii_policy`).  
5. Páginas consumen DataFrames en sesión/cache; descargas pasan por `audit_ui`.

## Dependencias principales

- Streamlit, pandas, pyarrow, scikit-learn (BallTree), folium  
- bcrypt, pyotp, qrcode (auth)  
- cryptography (Fernet, reposo)  
- openpyxl (Excel)

Ver `requirements.txt`.
