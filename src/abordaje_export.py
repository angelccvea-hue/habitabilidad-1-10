"""Cruce territorial 1×10 × capas GIS de abordaje (+ Habitable, IA, NASA).

Genera el **archivo maestro** para el equipo 1×10 (Excel/CSV desde la UI).

Por cada ubicación representante con GPS ok:
- Estado de cruce Habitable (ya en el parquet de solicitudes).
- Intersección punto-en-polígono con capas de ``data/gis_lite``.
- Vecino IA ≤ radio (prioriza alertas de riesgo).
- Campos NASA 1×10 si existe el parquet precalculado.

UI: ``pages_abordaje._render_abordaje_descarga``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IA_PQ = ROOT / "data" / "external_nasa" / "cruce_ia_nasa" / "ia_estructuras.parquet"
IA_NASA_PQ = (
    ROOT / "data" / "external_nasa" / "cruce_ia_nasa" / "cruce_ia_nasa_detallado.parquet"
)
NASA_1X10_PQ = (
    ROOT
    / "data"
    / "external_nasa"
    / "cruce_1x10_nasa"
    / "cruce_1x10_nasa_detallado.parquet"
)
R_EARTH = 6_371_000.0

# Capas poligonales a cruzar (excluye puntos del paquete GIS).
EXPORT_LAYER_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "mascara_altagracia",
        "col": "mascara_altagracia",
        "label": "Máscara Altagracia",
        "prop_keys": ("Parroquia", "Municipio", "ENTIDAD", "Estado", "Name"),
    },
    {
        "id": "mascara_san_bernardino",
        "col": "mascara_san_bernardino",
        "label": "Máscara San Bernardino",
        "prop_keys": ("Parroquia", "Municipio", "ENTIDAD", "Estado", "Name"),
    },
    {
        "id": "mascara_san_jose",
        "col": "mascara_san_jose",
        "label": "Máscara San José",
        "prop_keys": ("Parroquia", "Municipio", "ENTIDAD", "Estado", "Name"),
    },
    {
        "id": "mascara_petare",
        "col": "mascara_petare",
        "label": "Máscara Petare",
        "prop_keys": ("Parroquia", "Municipio", "Estado", "Name"),
    },
    {
        "id": "cuadricula_petare",
        "col": "cuadricula_petare",
        "label": "Cuadrícula Petare",
        "prop_keys": ("id", "row_index", "col_index", "Name"),
    },
    {
        "id": "cuadricula_abordaje",
        "col": "cuadricula_abordaje",
        "label": "Cuadrícula abordaje",
        "prop_keys": ("id", "row_index", "col_index", "Name"),
    },
    {
        "id": "bloques_la_guaira",
        "col": "bloque_la_guaira",
        "label": "Bloque La Guaira",
        "prop_keys": ("BLOQUE", "SECTOR", "ZONA", "NOM_MAPA", "Name"),
    },
    {
        "id": "microzonas_amenaza",
        "col": "microzona_amenaza",
        "label": "Microzona amenaza",
        "prop_keys": ("Name", "NOMBRE", "name"),
    },
    {
        "id": "microzonas_laderas",
        "col": "microzona_laderas",
        "label": "Microzona laderas",
        "prop_keys": ("Name", "NOMBRE", "name"),
    },
    {
        "id": "microzonas_sedimentos",
        "col": "microzona_sedimentos",
        "label": "Microzona sedimentos",
        "prop_keys": ("Name", "NOMBRE", "name"),
    },
    {
        "id": "parroquias",
        "col": "parroquia_capa",
        "label": "Parroquia (capa)",
        "prop_keys": ("Parroquia", "Municipio", "Estado", "Name"),
    },
    {
        "id": "parroquias_ine_2025",
        "col": "parroquia_ine_2025",
        "label": "Parroquia INE 2025",
        "prop_keys": ("Parroquia", "Municipio", "ENTIDAD", "Name"),
    },
    {
        "id": "segmentos_censales",
        "col": "segmento_censal",
        "label": "Segmento censal",
        "prop_keys": ("COD_SEG", "NOM_PARROQ", "NOM_MUNICI", "NOM_ENTIDA", "Name"),
        "heavy": True,
    },
)


def _prop_label(props: dict, keys: tuple[str, ...]) -> str:
    parts: list[str] = []
    for k in keys:
        if k in props and props[k] not in (None, "", "null"):
            parts.append(str(props[k]).strip())
    # dedupe preservando orden
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return " · ".join(out) if out else "sí"


def _match_habitable_label(cat: object) -> str:
    return {
        "solo_1x10": "No — pendiente (solo 1×10)",
        "coincide_alta": "Sí — coincidencia alta",
        "coincide_media": "Sí — coincidencia media",
        "coincide_geo_solo": "Cerca en mapa (revisar)",
        "no_mapeable": "Sin GPS / no mapeable",
    }.get(str(cat or ""), str(cat or "—"))


def _ia_es_alerta(estatus: object) -> bool:
    s = str(estatus or "").strip().lower()
    if not s or "no afect" in s:
        return False
    return True


def _ia_prioridad(estatus: object) -> int:
    s = str(estatus or "").strip().lower()
    if "afectado" in s and "posible" not in s and "no afect" not in s:
        return 3
    if "posible" in s:
        return 2
    if "revision" in s or "revisión" in s:
        return 1
    return 0


def load_ia_estructuras() -> pd.DataFrame | None:
    """Carga snapshot IA (parquet) o Excel de respaldo en Descargas."""
    if IA_PQ.exists():
        df = pd.read_parquet(IA_PQ)
    else:
        xlsx = Path.home() / "Downloads" / "Reporte_Estructuras.xlsx"
        if not xlsx.exists():
            return None
        raw = pd.read_excel(xlsx, sheet_name="Estructuras", dtype=str)
        rename = {
            "Código": "codigo",
            "Codigo": "codigo",
            "Estatus de Riesgo": "estatus_riesgo",
            "Tipo de Estructura": "tipo_estructura",
            "Zona": "zona",
            "Descripción de Daños": "descripcion_danos",
            "Descripcion de Danos": "descripcion_danos",
            "Latitud": "lat",
            "Longitud": "lng",
        }
        df = raw.rename(columns={k: v for k, v in rename.items() if k in raw.columns})
    need = {"lat", "lng"}
    if not need.issubset(df.columns):
        return None
    out = df.copy()
    out["lat"] = pd.to_numeric(out["lat"], errors="coerce")
    out["lng"] = pd.to_numeric(out["lng"], errors="coerce")
    out = out.dropna(subset=["lat", "lng"])
    if out.empty:
        return None
    if IA_NASA_PQ.exists() and "codigo" in out.columns:
        nasa = pd.read_parquet(IA_NASA_PQ)
        keep = [
            c
            for c in (
                "codigo",
                "nasa_label",
                "nasa_damage_probability",
                "nasa_dist_m",
                "nasa_prioridad",
            )
            if c in nasa.columns
        ]
        if len(keep) > 1:
            nasa = nasa[keep].drop_duplicates(subset=["codigo"], keep="first")
            out = out.merge(nasa, on="codigo", how="left", suffixes=("", "_n"))
    return out.reset_index(drop=True)


def enrich_with_ia(
    out: pd.DataFrame,
    *,
    radius_m: float = 50.0,
    k_neighbors: int = 8,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Nearest-neighbor 1×10 → IA; prioriza alertas dentro del radio."""
    from sklearn.neighbors import BallTree

    meta: dict[str, Any] = {
        "ia_disponible": False,
        "ia_n_estructuras": 0,
        "ia_n_con_match": 0,
        "ia_n_alerta": 0,
        "ia_radius_m": float(radius_m),
    }
    empty_cols = {
        "ia_match": "",
        "ia_codigo": "",
        "ia_estatus_riesgo": "",
        "ia_alerta": "",
        "ia_tipo_estructura": "",
        "ia_zona": "",
        "ia_dist_m": np.nan,
        "ia_descripcion_danos": "",
        "ia_nasa_label": "",
        "ia_nasa_prob": np.nan,
    }
    for c, v in empty_cols.items():
        if c not in out.columns:
            out[c] = v

    ia = load_ia_estructuras()
    if ia is None or ia.empty or out.empty:
        return out, meta

    meta["ia_disponible"] = True
    meta["ia_n_estructuras"] = int(len(ia))

    out = out.reset_index(drop=True)
    coords_ia = np.radians(ia[["lat", "lng"]].to_numpy(dtype=float))
    tree = BallTree(coords_ia, metric="haversine")
    coords_s = np.radians(out[["lat", "lng"]].to_numpy(dtype=float))
    k = int(min(max(k_neighbors, 1), len(ia)))
    dist, nn = tree.query(coords_s, k=k)
    if k == 1:
        dist = dist.reshape(-1, 1)
        nn = nn.reshape(-1, 1)
    dist_m = dist * R_EARTH

    ia_match: list[str] = []
    ia_codigo: list[str] = []
    ia_estatus: list[str] = []
    ia_alerta: list[str] = []
    ia_tipo: list[str] = []
    ia_zona: list[str] = []
    ia_dist: list[float] = []
    ia_desc: list[str] = []
    ia_nasa_lab: list[str] = []
    ia_nasa_prob: list[float] = []

    n_match = n_alerta = 0
    for i in range(len(out)):
        best_j = None
        best_d = None
        best_pri = -1
        for t in range(k):
            d = float(dist_m[i, t])
            if d > radius_m:
                continue
            j = int(nn[i, t])
            est = ia.iloc[j]["estatus_riesgo"] if "estatus_riesgo" in ia.columns else ""
            pri = _ia_prioridad(est)
            if best_j is None or pri > best_pri or (pri == best_pri and d < best_d):
                best_j, best_d, best_pri = j, d, pri
        if best_j is None:
            ia_match.append("No")
            ia_codigo.append("")
            ia_estatus.append("")
            ia_alerta.append("")
            ia_tipo.append("")
            ia_zona.append("")
            ia_dist.append(np.nan)
            ia_desc.append("")
            ia_nasa_lab.append("")
            ia_nasa_prob.append(np.nan)
            continue
        row = ia.iloc[best_j]
        est = str(row.get("estatus_riesgo", "") or "")
        alerta = _ia_es_alerta(est)
        desc = str(row.get("descripcion_danos", "") or "")
        if len(desc) > 400:
            desc = desc[:397] + "…"
        ia_match.append("Sí")
        ia_codigo.append(str(row.get("codigo", "") or ""))
        ia_estatus.append(est)
        ia_alerta.append("Sí" if alerta else "No")
        ia_tipo.append(str(row.get("tipo_estructura", "") or ""))
        ia_zona.append(str(row.get("zona", "") or ""))
        ia_dist.append(round(float(best_d), 1))
        ia_desc.append(desc)
        ia_nasa_lab.append(str(row.get("nasa_label", "") or ""))
        try:
            prob = row.get("nasa_damage_probability")
            ia_nasa_prob.append(float(prob) if pd.notna(prob) else np.nan)
        except Exception:
            ia_nasa_prob.append(np.nan)
        n_match += 1
        if alerta:
            n_alerta += 1

    out["ia_match"] = ia_match
    out["ia_codigo"] = ia_codigo
    out["ia_estatus_riesgo"] = ia_estatus
    out["ia_alerta"] = ia_alerta
    out["ia_tipo_estructura"] = ia_tipo
    out["ia_zona"] = ia_zona
    out["ia_dist_m"] = ia_dist
    out["ia_descripcion_danos"] = ia_desc
    out["ia_nasa_label"] = ia_nasa_lab
    out["ia_nasa_prob"] = ia_nasa_prob

    meta["ia_n_con_match"] = n_match
    meta["ia_n_alerta"] = n_alerta
    meta["ia_pct_match"] = round(100.0 * n_match / max(len(out), 1), 1)
    return out, meta


def enrich_with_nasa_1x10(out: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Pega NASA ya cruzado a 1×10 por ``codigo_caso`` (si existe el parquet)."""
    meta: dict[str, Any] = {
        "nasa_1x10_disponible": False,
        "nasa_1x10_n_con_label": 0,
    }
    cols = {
        "nasa_label": "",
        "nasa_damage_probability": np.nan,
        "nasa_dist_m": np.nan,
        "nasa_prioridad": "",
        "nasa_within": "",
    }
    for c, v in cols.items():
        if c not in out.columns:
            out[c] = v
    if not NASA_1X10_PQ.exists() or "codigo_caso" not in out.columns:
        return out, meta
    nasa = pd.read_parquet(NASA_1X10_PQ)
    keep = [
        c
        for c in (
            "codigo_caso",
            "nasa_label",
            "nasa_damage_probability",
            "nasa_dist_m",
            "nasa_prioridad",
            "nasa_within",
        )
        if c in nasa.columns
    ]
    if "codigo_caso" not in keep:
        return out, meta
    nasa = nasa[keep].drop_duplicates(subset=["codigo_caso"], keep="first")
    # Evitar colisión: quitar columnas destino antes del merge
    drop_existing = [c for c in keep if c != "codigo_caso" and c in out.columns]
    base = out.drop(columns=drop_existing, errors="ignore")
    merged = base.merge(nasa, on="codigo_caso", how="left")
    meta["nasa_1x10_disponible"] = True
    if "nasa_label" in merged.columns:
        meta["nasa_1x10_n_con_label"] = int(
            merged["nasa_label"].fillna("").astype(str).str.strip().ne("").sum()
        )
    return merged, meta


def _build_layer_index(geojson: dict, prop_keys: tuple[str, ...]):
    from shapely.geometry import shape
    from shapely.strtree import STRtree

    geoms = []
    labels = []
    for feat in geojson.get("features") or []:
        geom = feat.get("geometry")
        if not geom:
            continue
        try:
            g = shape(geom)
            if g.is_empty:
                continue
            if not g.is_valid:
                g = g.buffer(0)
        except Exception:  # noqa: BLE001
            continue
        props = feat.get("properties") or {}
        geoms.append(g)
        labels.append(_prop_label(props, prop_keys))
    if not geoms:
        return None, []
    return STRtree(geoms), labels


def _lookup_point(tree, labels: list[str], lon: float, lat: float) -> str:
    from shapely.geometry import Point

    if tree is None or not labels:
        return ""
    pt = Point(float(lon), float(lat))
    try:
        idxs = tree.query(pt, predicate="intersects")
    except TypeError:
        idxs = tree.query(pt)
    if idxs is None:
        return ""
    try:
        import numpy as np

        arr = np.asarray(idxs).ravel()
        if len(arr) == 0:
            return ""
        # Preferir el polígono de menor área (más específico) si hay solapes
        best_i = int(arr[0])
        best_area = None
        geoms = getattr(tree, "geometries", None)
        for raw in arr:
            i = int(raw)
            area = None
            if geoms is not None:
                try:
                    area = float(geoms[i].area)
                except Exception:  # noqa: BLE001
                    area = None
            if best_area is None or (area is not None and area < best_area):
                best_area = area if area is not None else best_area
                best_i = i
        return labels[best_i] if 0 <= best_i < len(labels) else ""
    except Exception:  # noqa: BLE001
        try:
            i = int(idxs[0])
            return labels[i] if 0 <= i < len(labels) else ""
        except Exception:  # noqa: BLE001
            return ""


def construir_cruce_1x10_capas(
    sol: pd.DataFrame,
    *,
    layer_ids: list[str] | None = None,
    solo_mapeables: bool = True,
    solo_representantes: bool = True,
    incluir_ia: bool = True,
    ia_radius_m: float = 50.0,
    incluir_nasa: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Cruza puntos 1×10 con capas poligonales de ``data/gis_lite``.

    Opcionalmente enriquece con IA (vecino espacial) y NASA 1×10 (por código).
    Devuelve (dataframe listo para Excel, meta).
    """
    from pages_abordaje import _load_geojson_dict, _layer_path

    if sol is None or sol.empty:
        raise ValueError("No hay solicitudes 1×10 para cruzar.")

    work = sol.copy()
    if solo_representantes and "es_representante" in work.columns:
        # Si la columna existe, preferir representantes; si todo es False, no filtrar
        mask_rep = work["es_representante"].fillna(False).astype(bool)
        if bool(mask_rep.any()):
            work = work.loc[mask_rep].copy()
    if solo_mapeables and "mapeable" in work.columns:
        work = work.loc[work["mapeable"].fillna(False).astype(bool)].copy()
    if "mapa_ok" in work.columns:
        # Preferir GPS fiable, pero no vaciar el universo
        ok = work["mapa_ok"].fillna(False).astype(bool)
        if bool(ok.any()):
            work = work.loc[ok].copy()

    work = work.dropna(subset=["lat", "lng"]).copy()
    if work.empty:
        raise ValueError("No quedan puntos 1×10 con coordenadas tras el filtro.")

    wanted = set(layer_ids) if layer_ids else {s["id"] for s in EXPORT_LAYER_SPECS}
    specs = [s for s in EXPORT_LAYER_SPECS if s["id"] in wanted]

    meta: dict[str, Any] = {
        "n_puntos": int(len(work)),
        "capas": {},
        "capas_faltantes": [],
        "ia": {},
        "nasa_1x10": {},
    }

    # Columnas base de negocio
    base_cols = [
        c
        for c in (
            "codigo_caso",
            "codigos_grupo",
            "cedula",
            "denunciante",
            "telefono",
            "telefono_alt",
            "estado",
            "estado_n",
            "municipio",
            "municipio_n",
            "parroquia",
            "parroquia_n",
            "direccion",
            "descripcion",
            "lat",
            "lng",
            "match_cat",
            "match_dist_m",
            "match_score",
            "hab_id",
            "hab_nombre",
            "hab_etiqueta",
            "n_reportes",
            "tipo_ubicacion",
            "tipo_dir",
        )
        if c in work.columns
    ]
    out = work[base_cols].copy().reset_index(drop=True)
    if "match_cat" in out.columns:
        cat = out["match_cat"]
        out["en_habitable"] = cat.map(
            lambda c: "Sí"
            if str(c) in ("coincide_alta", "coincide_media")
            else (
                "Cerca"
                if str(c) == "coincide_geo_solo"
                else ("No" if str(c) == "solo_1x10" else "—")
            )
        )
        out["estado_cruce_habitable"] = cat.map(_match_habitable_label)
    else:
        out["en_habitable"] = "—"
        out["estado_cruce_habitable"] = "—"
    if "hab_etiqueta" in out.columns:
        out["etiqueta_inspeccion_habitable"] = (
            out["hab_etiqueta"].fillna("").astype(str).str.strip().str.upper()
        )
    else:
        out["etiqueta_inspeccion_habitable"] = ""
    if "hab_nombre" in out.columns:
        out["edificio_habitable"] = out["hab_nombre"].fillna("").astype(str)
    else:
        out["edificio_habitable"] = ""
    if "hab_id" in out.columns:
        out["id_inspeccion_habitable"] = out["hab_id"].fillna("").astype(str)
    else:
        out["id_inspeccion_habitable"] = ""

    lats = out["lat"].astype(float).to_numpy()
    lngs = out["lng"].astype(float).to_numpy()

    for spec in specs:
        stem = spec["id"]
        col = spec["col"]
        if _layer_path(stem) is None:
            meta["capas_faltantes"].append(stem)
            out[col] = ""
            continue
        gj = _load_geojson_dict(stem)
        if not gj:
            meta["capas_faltantes"].append(stem)
            out[col] = ""
            continue
        tree, labels = _build_layer_index(gj, tuple(spec["prop_keys"]))
        vals = [
            _lookup_point(tree, labels, float(lon), float(lat))
            for lon, lat in zip(lngs, lats)
        ]
        out[col] = vals
        n_hit = sum(1 for v in vals if v)
        meta["capas"][stem] = {
            "label": spec["label"],
            "n_con_match": int(n_hit),
            "pct": round(100.0 * n_hit / max(len(vals), 1), 1),
        }

    if incluir_ia:
        out, ia_meta = enrich_with_ia(out, radius_m=float(ia_radius_m))
        meta["ia"] = ia_meta
    if incluir_nasa:
        out, nasa_meta = enrich_with_nasa_1x10(out)
        meta["nasa_1x10"] = nasa_meta

    # Orden de columnas legible
    front = [
        c
        for c in (
            "codigo_caso",
            "codigos_grupo",
            "denunciante",
            "cedula",
            "telefono",
            "telefono_alt",
            "estado_n",
            "municipio_n",
            "parroquia_n",
            "direccion",
            "lat",
            "lng",
            "en_habitable",
            "estado_cruce_habitable",
            "etiqueta_inspeccion_habitable",
            "id_inspeccion_habitable",
            "edificio_habitable",
            "match_dist_m",
            "match_score",
            "ia_match",
            "ia_alerta",
            "ia_estatus_riesgo",
            "ia_codigo",
            "ia_dist_m",
            "ia_tipo_estructura",
            "ia_zona",
            "ia_nasa_label",
            "ia_nasa_prob",
            "nasa_label",
            "nasa_damage_probability",
            "nasa_dist_m",
            "nasa_prioridad",
            "nasa_within",
            "n_reportes",
            "tipo_ubicacion",
        )
        if c in out.columns
    ]
    capa_cols = [s["col"] for s in specs if s["col"] in out.columns]
    rest = [c for c in out.columns if c not in front and c not in capa_cols]
    out = out[front + capa_cols + rest]
    return out.reset_index(drop=True), meta


__all__ = [
    "EXPORT_LAYER_SPECS",
    "construir_cruce_1x10_capas",
    "load_ia_estructuras",
]
