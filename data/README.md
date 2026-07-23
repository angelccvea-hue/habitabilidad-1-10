# Carpeta `data/` — qué va aquí

Esta carpeta **no** debe versionar datos personales ni inventarios masivos.

## Estructura esperada en runtime

| Ruta | Contenido | ¿Git? |
|------|-----------|-------|
| `uploads/` | Excel/CSV fuente subidos por admin | No (solo `.gitkeep`) |
| `processed/` | Parquet del cruce + summary | No |
| `auth/` | `users.json` (hashes bcrypt + TOTP) | No |
| `audit/` | `audit.jsonl` | No |
| `gis_lite/` | Capas abordaje livianas | Opcional / generado |
| `external_nasa/` | Cruces y lite NASA/IA | No (muy pesado) |

## Cómo obtener datos para probar

1. Subir Excel en la UI (rol admin) y pulsar «Procesar cruce», o  
2. Configurar rutas en `config.toml` y ejecutar `python src/prepare_data.py`, o  
3. Copiar un paquete de datos de prueba **sin PII** acordado con el equipo.

## Cifrado

Si define `BI_DATA_KEY`, uploads/processed/auth se escriben cifrados.  
Ver `scripts/encrypt_data_at_rest.py` y `docs/03-SEGURIDAD.md`.
