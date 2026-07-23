# Guía de lectura del código

Orden recomendado para revisar el aplicativo sin perderse.

## 1. Visión (15 min)

1. `README.md` — qué es el producto  
2. `docs/01-ARQUITECTURA.md` — diagrama de capas  
3. `docs/03-SEGURIDAD.md` — por qué hay auth/PII/cifrado/tiles  

## 2. Arranque de la app (30 min)

1. `app.py` — login → carga de datos → navegación → páginas  
2. `src/nav_schema.py` — menú lateral (secciones e ids)  
3. `src/auth_gate.py` + `src/auth_users.py` — sesión, roles, TOTP  

## 3. Datos (45 min)

1. `src/prepare_data.py` — limpieza 1×10 / Habitable + matching espacial  
2. `src/data_ingest.py` — subida Excel y regeneración del cruce  
3. `src/secure_io.py` — lectura/escritura cifrada  
4. `docs/04-DATOS-Y-PIPELINE.md`  

## 4. Pantallas (según interés)

| Si te interesa… | Empieza en… |
|-----------------|-------------|
| Mapa operativo | `src/map_robust.py`, `docs/05-MAPAS-Y-CAPAS.md` |
| Mapas de abordaje + Excel maestro | `src/pages_abordaje.py`, `src/abordaje_export.py` |
| Análisis 1×10 / Habitable | `src/pages_analysis.py` |
| NASA / IA | `src/pages_nasa.py`, `src/pages_nasa_analisis.py` |
| PII visible/oculto | `src/pii_policy.py` |
| Descargas auditadas | `src/audit_ui.py`, `src/audit_log.py` |

## 5. Scripts batch (opcional)

Carpeta `scripts/`: cruces NASA, cifrado de datos existentes, auditoría de unificación. No forman parte del request HTTP de Streamlit; se ejecutan a mano.

## Convención de comentarios en este repo

- Cada módulo `src/*.py` tiene un **docstring de cabecera** (qué hace, entradas/salidas, riesgos).  
- Funciones críticas de seguridad y matching tienen notas de **por qué**, no solo de qué.  
- La explicación larga de producto está en `docs/`, no repetida línea a línea en el código.
