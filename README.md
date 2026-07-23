# Habitabilidad 1×10 — BI de cruce

Tablero web (**Streamlit**) para cruzar la **demanda ciudadana 1×10** con las **inspecciones de campo Habitable**, ver el territorio en mapa, priorizar pendientes y enriquecer la lectura con capas de abordaje, señales de **IA** y radar **NASA**.

Este repositorio está pensado para **lectura y revisión**: incluye documentación en `docs/` y comentarios en los módulos clave.

---

## ¿Qué problema resuelve?

Tras un evento sísmico hay miles de reportes ciudadanos (1×10) e inspecciones de habitabilidad en campo (semáforo verde / amarillo / rojo / negro). Este sistema:

1. **Unifica y limpia** ambos insumos (coordenadas, direcciones, duplicados cercanos).  
2. **Cruza en el mapa** (radio configurable, típicamente 50 m + similitud de nombre) para saber qué casos **ya fueron inspeccionados** y cuáles siguen **pendientes**.  
3. Ofrece **vistas operativas y de análisis** para despacho, seguimiento y descarga de listados.  
4. Añade **contexto territorial** (máscaras, cuadrículas, microzonas, parroquias, segmentos censales) y, si hay datos cargados, **IA** y **NASA**.

---

## Funcionalidades principales

### Carga y actualización del cruce
- Subida de Excel/CSV de **1×10** y **Habitable** (rol administrador).  
- Pipeline automático: limpieza → unificación de reportes cercanos → matching espacial → parquet de trabajo.  
- Indicador del **corte de información** en uso (fecha de generación y volúmenes).

### Mapa operativo
- Capas de **inspecciones Habitable**, **coincidencias** (ya atendidas), **pendientes 1×10** y puntos dudosos de GPS.  
- Mapas de calor / densidad y búsqueda por código, dirección o edificio.  
- Filtro territorial (estado / municipio) y control de mapa base.

### Análisis 1×10
- **Depuración** del archivo fuente (calidad, duplicados, coordenadas).  
- **Territorio y cruce**: volumen por estado/parroquia y % ya atendido.  
- **Cola de pendientes**: listado priorizado para contacto o visita, con descarga.

### Análisis Habitable
- Semáforo de riesgo (verde / amarillo / rojo / negro).  
- Reportes y cortes por territorio, tipología y calidad del dato.  
- Lectura de lo inspeccionado frente a la demanda 1×10.

### Mapas de abordaje
- Capas GIS de planificación (máscaras parroquiales, cuadrículas, bloques, microzonas, parroquias INE, segmentos censales, puntos de campo).  
- Cruce visual de pendientes y semáforo sobre esas capas.  
- **Descarga del archivo maestro 1×10**: cada ubicación con estado Habitable, pertenencia a capas GIS, y (si está disponible) cruce con **IA** y **NASA**.

### Mapa y análisis NASA / IA
- Vista de daño probable radar (NASA) junto a 1×10, Habitable e IA.  
- Análisis por fuente: priorizar pendientes con señal de daño, validar acuerdo/desacuerdo entre campo, IA y radar.

### Seguridad y control de acceso
- Login por **usuario + contraseña** y **2FA** (app autenticadora).  
- Roles: **ejecutivo** (sin datos de contacto), **operador** (colas y contacto), **admin** (carga de archivos y usuarios).  
- Auditoría de accesos y descargas.  
- Cifrado en reposo de archivos sensibles, política de mapas base institucionales y límites de tamaño de subida.

Detalle técnico de seguridad: [`docs/03-SEGURIDAD.md`](docs/03-SEGURIDAD.md).

---

## Fuentes de datos que consume

| Fuente | Para qué sirve en el tablero |
|--------|------------------------------|
| **1×10** | Demanda ciudadana (casos, dirección, contacto, GPS) |
| **Habitable** | Inspecciones en campo y semáforo de habitabilidad |
| **Capas de abordaje** | Contexto territorial para priorizar y planificar |
| **IA (estructuras)** | Estatus de riesgo modelado; se pega al maestro 1×10 por cercanía |
| **NASA (radar)** | Señal de daño probable; apoyo a prioridad y validación |

---

## Empezar por aquí (revisores de código)

1. [`docs/00-GUIA-DE-LECTURA.md`](docs/00-GUIA-DE-LECTURA.md) — orden sugerido de lectura  
2. [`docs/01-ARQUITECTURA.md`](docs/01-ARQUITECTURA.md) — piezas del sistema  
3. [`docs/02-SECCIONES-UI.md`](docs/02-SECCIONES-UI.md) — pantallas del tablero  
4. [`docs/03-SEGURIDAD.md`](docs/03-SEGURIDAD.md) — auth, PII, cifrado, tiles, auditoría  
5. [`app.py`](app.py) — punto de entrada  

## Arranque local (desarrollo)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Generar parquet (rutas en config.toml) o subir Excel en la UI como admin
streamlit run app.py
```

Abrir http://localhost:8501

## Variables de entorno relevantes

| Variable | Uso |
|----------|-----|
| `BI_REQUIRE_AUTH` / `BI_ENV=production` | Modo producción (auth y crypto obligatorios) |
| `BI_BOOTSTRAP_TOKEN` / `BI_PASSWORD` | Token de arranque del primer admin |
| `BI_DATA_KEY` | Clave Fernet — cifrado en reposo |
| `BI_TILES_URL` | Tiles de mapa institucionales |
| `BI_ALLOW_PUBLIC_TILES` | Permite mapas base públicos solo si se autoriza |
| `BI_UPLOAD_MAX_MB` | Tope de tamaño de archivos subidos |
| `BI_LOW_MEMORY` / `BI_ALLOW_HEAVY_PIPELINE` | Guardas en instancias con poca memoria |

## Qué no va en Git

- Credenciales, `data/auth/`, `data/audit/`
- Excel/CSV/parquet con datos personales (`data/uploads/`, `data/processed/`)
- Capas GIS pesadas e inventarios NASA brutos (se generan o copian fuera de Git)

Ver `data/README.md` y `.gitignore`.

## Alcance de este repositorio

Código del tablero de cruce **1×10 × Habitable**, documentado para auditoría y transferencia. No incluye datos personales ni inventarios masivos.
