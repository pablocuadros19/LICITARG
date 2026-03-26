# CLAUDE_HANDOFF — LICITARG

## Qué es esto
LICITARG es el motor de datos compartido del ecosistema de apps de Pablo (Banco Provincia).
Convierte datos de compras públicas en prospectos comerciales con domicilio, sector y situación financiera.

## Datos disponibles (no volver a descargar)

| Archivo | Tamaño | Descripción |
|---|---|---|
| `data/raw/adjudicaciones/adjudicaciones-2015..2020.csv` | ~27MB total | Adjudicaciones nacionales COMPR.AR |
| `data/raw/contratar/onc-contratar-ofertas.csv` | 257KB | Obra pública CONTRAT.AR |
| `data/raw/sipro/proveedores.csv` | 4.7MB | Registro SIPRO (28K proveedores) |
| `data/raw/sociedades/sociedades-ba-caba.csv` | ~300MB | **1.67M empresas BA/CABA con domicilio + CLAE** |
| `data/raw/sociedades/registro-nacional-sociedades-2026.zip` | 110MB | ZIP original (no extraer, ya filtrado) |
| `data/processed/adjudicaciones.parquet` | — | 26,228 adjudicaciones unificadas |
| `data/processed/proveedores.parquet` | — | **5,615 proveedores del estado con geo** |
| `data/processed/agro-proveedores-estado.parquet` | — | 120K empresas agro BA/CABA + flag proveedor estado |

## Números clave
- Proveedores del estado con zona asignada: **2,135**
- CABA: 1,836 · San Isidro: 37 · San Martín: 35 · Tigre: 15
- Monto total procesado: $1.29T ARS
- Empresas agro BA/CABA: **120,209** (de las cuales 481 también proveedoras del estado)

## Arquitectura
```
config.py                  — URLs, sucursales, provincias de interés
services/data_loader.py    — descarga y carga de fuentes
services/data_processor.py — normalización + cruce geo + asignación sucursal
services/enrichment.py     — BCRA API (deuda por CUIT, sin auth)
services/analytics.py      — rankings, resumen por sucursal, ficha prospecto
app.py                     — dashboard Streamlit
```

## Fuentes de datos — estado
- COMPR.AR adjudicaciones: datos hasta 2020 (congelado). Gap 2021-2026 → pendiente Boletín Oficial.
- CONTRAT.AR: obra pública, pocos registros (651).
- SIPRO: 28K proveedores legacy, tiene localidad/provincia.
- Registro Sociedades: actualizado a feb-2026, es la fuente de domicilio principal.
- BCRA API: libre, sin auth. `GET https://api.bcra.gob.ar/CentralDeDeudores/v1.0/Deudas/{cuit}`

## Integración con otros proyectos
- **NyPer** (`C:\PRUEBA 101`): usa `proveedores.parquet` vía `services/licitarg_enricher.py`
- **AgroBip** (`C:\AgroBip`): puede leer `agro-proveedores-estado.parquet` y `sociedades-ba-caba.csv`
- El CSV de sociedades BA/CABA es la fuente compartida de CUIT + domicilio para los tres proyectos

## Reprocesar todo
```bash
cd C:\LICITARG
python -c "from services.data_processor import procesar_todo; procesar_todo()"
```

## Correr app
```bash
streamlit run app.py
```
Puerto: 8501. Si está ocupado usar `--server.port 8502`.

## Pendientes prioritarios
- [ ] Incorporar Boletín Oficial sección 3 (adjudicaciones 2021-2026)
- [ ] Descargar ZIP completo del Registro MiPyME (1.8M PyMEs certificadas)
- [ ] Mejorar matching geo con Georef API para localidades con variantes
- [ ] Búsqueda web de contacto on-demand (scraping en ficha del prospecto)
