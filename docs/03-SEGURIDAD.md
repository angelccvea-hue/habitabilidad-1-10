# Capas de seguridad

Diseño orientado a despliegue controlado / auditoría. Cada control tiene módulo propio.

## 1. Autenticación y roles

| Pieza | Módulo | Notas |
|-------|--------|-------|
| Login usuario + contraseña | `auth_gate`, `auth_users` | Hash **bcrypt** |
| 2FA TOTP (Google Authenticator) | `auth_users` / `auth_gate` | Secreto por usuario; QR al enrolar |
| Roles | `ejecutivo` / `operador` / `admin` | En `users.json` |
| Bootstrap primer admin | `BI_BOOTSTRAP_TOKEN` o `BI_PASSWORD` | Solo si no hay usuarios |
| Producción sin auth imposible | `BI_REQUIRE_AUTH` / `BI_ENV` | Bloquea tablero |

La identidad vive en este aplicativo (archivo local de usuarios). Una integración futura con un IdP institucional (OIDC/SSO) es opcional y no está implementada.

## 2. Minimización de PII

- Columnas sensibles: cédula, denunciante, teléfonos (`pii_policy.CONTACT_COLUMNS`).  
- Rol **ejecutivo:** se eliminan de la sesión en memoria tras `load_data`.  
- Descargas con contacto: bloqueadas para ejecutivo.

## 3. Auditoría

- Append-only JSONL: `data/audit/audit.jsonl` (`audit_log`).  
- Eventos: login ok/fail, logout, alta usuarios, descargas, pipeline ok/fail, upload_reject.  
- UI admin: expander «Auditoría reciente».  
- Descargas: wrapper `audit_ui.download_button`.

## 4. Cifrado en reposo

- Fernet (`cryptography`) vía `secure_io`.  
- Clave: `BI_DATA_KEY` (o secrets `crypto.data_key`).  
- Formato: cabecera mágica + token Fernet (constante en `secure_io.MAGIC`).  
- Cubre: uploads, parquet procesados, `users.json`.  
- Script: `scripts/encrypt_data_at_rest.py`.  
- **No** sustituye cifrado de volumen del servidor ni TLS.

## 5. Tránsito (subida/bajada por red)

- Responsabilidad del **proxy HTTPS** (balanceador / reverse proxy del entorno de despliegue).  
- El BI no implementa TLS propio.  
- Archivos descargados al PC del usuario quedan legibles (uso operativo); el control es rol + auditoría + canal seguro.

## 6. Mapas base (fuga de área operativa)

- `map_tiles`: en producción **no** se usan OSM/Carto/Esri por defecto.  
- Configurar `BI_TILES_URL` institucional.  
- Escape: `BI_ALLOW_PUBLIC_TILES=1` solo con autorización TI.

## 7. Límites (DoS / OOM)

- `runtime_limits`: tamaño máximo de upload (`BI_UPLOAD_MAX_MB`).  
- Pipeline pesado bloqueado en bajo consumo (`RENDER` / `BI_LOW_MEMORY`) salvo `BI_ALLOW_HEAVY_PIPELINE=1`.  
- Tope de marcadores de mapa en instancias pequeñas.

## Checklist rápido para revisores

- [ ] ¿Hay login + 2FA antes de ver datos?  
- [ ] ¿Ejecutivo ve cédula/teléfono? (debe ser no)  
- [ ] ¿Existe `BI_DATA_KEY` en prod y los archivos sensibles empiezan con la cabecera de cifrado?  
- [ ] ¿Tiles públicos desactivados en prod?  
- [ ] ¿Descargas aparecen en auditoría?  
- [ ] ¿HTTPS forzado en el edge?
