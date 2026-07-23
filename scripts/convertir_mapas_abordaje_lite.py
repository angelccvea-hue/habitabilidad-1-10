"""Inventario + conversión ligera de capas MAPAS ABORDAJE.

Simplificación suave (calidad visual alta):
  ~0.00003° ≈ 3 m · ~0.00005° ≈ 5 m · ~0.00008° ≈ 8–9 m
(en latitud de Caracas). Conserva topología.
"""
from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import geopandas as gpd
import pyogrio

# Shapefiles incompletos (p. ej. sin .shx): regenerar índice al leer
os.environ.setdefault("SHAPE_RESTORE_SHX", "YES")

# Entrada: carpeta local de shapefiles/GPKG de abordaje (ajustar si hace falta).
ROOT = Path.home() / "Downloads" / "MAPAS ABORDAJE"
# Salida: capas lite dentro de este repositorio
OUT = Path(__file__).resolve().parents[1] / "data" / "gis_lite"
OUT.mkdir(parents=True, exist_ok=True)

# Preset calidad máxima práctica para web (~2 m)
TOL_FINE = 0.000018  # ~2 m — máscaras / bloques / cuadrícula
TOL_PARRO = 0.000018  # ~2 m — parroquias
TOL_SEG = 0.000018  # ~2 m — segmentos censales
TOL_MICRO = 0.000018  # ~2 m — microzonas


def mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024) if path.exists() else 0.0


def simplify_gdf(gdf: gpd.GeoDataFrame, tol: float) -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["geometry"] = out.geometry.simplify(tol, preserve_topology=True)
    return out


def export_layer(
    gdf: gpd.GeoDataFrame,
    stem: str,
    *,
    keep_cols: list[str] | None = None,
    simplify_tol: float | None = TOL_PARRO,
    write_raw: bool = False,
) -> dict:
    gdf = gdf.copy()
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    else:
        gdf = gdf.to_crs(4326)

    if keep_cols:
        cols = [c for c in keep_cols if c in gdf.columns] + ["geometry"]
        gdf = gdf[cols]

    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()

    raw_mb = None
    if write_raw:
        raw_geojson = OUT / f"{stem}_raw.geojson"
        gdf.to_file(raw_geojson, driver="GeoJSON")
        raw_mb = round(mb(raw_geojson), 2)

    if simplify_tol and gdf.geom_type.str.contains("Polygon|Line", regex=True).any():
        gdf_s = simplify_gdf(gdf, simplify_tol)
    else:
        gdf_s = gdf

    # Quitar Z si existe (Folium / web)
    try:
        gdf_s = gdf_s.set_geometry(gdf_s.geometry.force_2d())
    except Exception:
        pass

    geojson = OUT / f"{stem}.geojson"
    parquet = OUT / f"{stem}.parquet"
    gdf_s.to_file(geojson, driver="GeoJSON")
    gdf_s.to_parquet(parquet, index=False)

    zpath = OUT / f"{stem}.geojson.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(geojson, arcname=f"{stem}.geojson")

    return {
        "stem": stem,
        "n": int(len(gdf_s)),
        "simplify_tol_deg": simplify_tol,
        "simplify_tol_m_approx": (
            round(float(simplify_tol) * 111_000, 1) if simplify_tol else None
        ),
        "geojson_mb": round(mb(geojson), 2),
        "geojson_zip_mb": round(mb(zpath), 2),
        "parquet_mb": round(mb(parquet), 2),
        "raw_geojson_mb": raw_mb,
        "cols": [c for c in gdf_s.columns if c != "geometry"],
    }


def slim_cols(gdf: gpd.GeoDataFrame, max_cols: int = 12) -> list[str]:
    slim = []
    for c in gdf.columns:
        if c == "geometry":
            continue
        if gdf[c].dtype == object:
            maxlen = int(gdf[c].fillna("").astype(str).str.len().max() or 0)
            if maxlen > 200:
                continue
        slim.append(c)
    return slim[:max_cols]


def main() -> None:
    # Limpiar geojson raw enormes de la pasada agresiva (opcionales)
    for p in OUT.glob("*_raw.geojson"):
        p.unlink(missing_ok=True)

    report: list[dict] = []

    gpkg = ROOT / "Base de datos abordaje.gpkg"
    print("=== GPKG layers ===")
    for name, geom in pyogrio.list_layers(gpkg):
        info = pyogrio.read_info(gpkg, layer=name)
        print(f"  {name}: n={info.get('features')} geom={geom}")

    jobs = [
        ("Parroquias.shp", "parroquias", TOL_PARRO),
        ("Parroquias INE 2025.shp", "parroquias_ine_2025", TOL_PARRO),
        ("puntos DB.shp", "puntos_db", None),
        ("LA GUAIRA/BLQOUES_LA_GUAIRA.shp", "bloques_la_guaira", TOL_FINE),
        ("mascara parroquias/mascara Altagracia.shp", "mascara_altagracia", TOL_FINE),
        (
            "mascara parroquias/mascara San Bernardino.shp",
            "mascara_san_bernardino",
            TOL_FINE,
        ),
        ("mascara parroquias/mascara San jose.shp", "mascara_san_jose", TOL_FINE),
        (
            "salidas por parroquias/Petare/Cuadricula_Petare.shp",
            "cuadricula_petare",
            TOL_FINE,
        ),
        (
            "salidas por parroquias/Petare/Mascara_Petare.shp",
            "mascara_petare",
            TOL_FINE,
        ),
    ]

    for rel, stem, tol in jobs:
        src = ROOT / rel
        if not src.exists():
            print("SKIP missing", src)
            continue
        print("converting", rel, f"tol={tol} ...")
        gdf = gpd.read_file(src)
        report.append(
            export_layer(gdf, stem, keep_cols=slim_cols(gdf), simplify_tol=tol)
        )

    seg = ROOT / "Segmentos Censales.shp"
    if seg.exists():
        print("converting Segmentos Censales (calidad alta)...")
        gdf = gpd.read_file(seg)
        prefer = [
            c
            for c in gdf.columns
            if c != "geometry"
            and any(
                k in c.lower()
                for k in (
                    "seg",
                    "cod",
                    "parro",
                    "muni",
                    "estado",
                    "nombre",
                    "name",
                    "id",
                )
            )
        ][:10]
        report.append(
            export_layer(
                gdf,
                "segmentos_censales",
                keep_cols=prefer or slim_cols(gdf),
                simplify_tol=TOL_SEG,
            )
        )

    # Capas útiles del GPKG
    gpkg_jobs = [
        ("Cuadrícula", "cuadricula_abordaje", TOL_FINE),
        (
            "MicrozonificacionSismicaCaracas — Macrozonas_Amenaza_General",
            "microzonas_amenaza",
            TOL_MICRO,
        ),
        (
            "MicrozonificacionSismicaCaracas — Microzonas_Laderas",
            "microzonas_laderas",
            TOL_MICRO,
        ),
        (
            "MicrozonificacionSismicaCaracas — Microzonas_Sedimentos",
            "microzonas_sedimentos",
            TOL_MICRO,
        ),
    ]
    for layer, stem, tol in gpkg_jobs:
        print("converting gpkg", layer, "...")
        try:
            gdf = gpd.read_file(gpkg, layer=layer)
            report.append(
                export_layer(gdf, stem, keep_cols=slim_cols(gdf), simplify_tol=tol)
            )
        except Exception as e:
            print("  FAIL", type(e).__name__, e)

    summary = {
        "out_dir": str(OUT),
        "preset": "calidad_2m",
        "nota": (
            "Simplificación ~2 m en capas poligonales. "
            "Incluye cuadrícula GPKG (6) y Cuadricula_Petare (36)."
        ),
        "layers": report,
        "total_geojson_zip_mb": round(sum(r["geojson_zip_mb"] for r in report), 2),
        "total_parquet_mb": round(sum(r["parquet_mb"] for r in report), 2),
    }
    (OUT / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
