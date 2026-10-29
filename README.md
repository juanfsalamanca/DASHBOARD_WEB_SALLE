# Mortalidad en Colombia 2019 (Dash + Plotly)

Dashboard interactivo de defunciones no fetales (DANE EEVV 2019).

## Objetivo

Explorar mortalidad por departamento, mes, causas, sexo, edad, homicidios X95 y municipios.

## Estructura

```
app.py
requirements.txt
Dockerfile
.gitignore
.dockerignore
assets/          # CSS y GeoJSON del mapa
data/            # Excel DANE
scripts/         # prepare_cache.py (arranque rápido)
src/
  data_loader.py
  processing.py
  charts.py
README.md
```

## Requisitos

Python 3.11+ (local también 3.14). Ver `requirements.txt`.

```bash
pip install -r requirements.txt
python scripts/prepare_cache.py   # opcional
python app.py
```

Abrir: http://127.0.0.1:8050

## Interacción

- Filtros Departamento / Sexo
- Clic en mapa o barras de sexo → filtra
- Otro clic en el mismo → vuelve a todos
- Botón Limpiar filtros

## Despliegue Cloud Run

```bash
gcloud run deploy dashboard --source . --region us-central1 --allow-unauthenticated --memory 2Gi --cpu 2 --timeout 300 --port 8080
```

URL: https://dashboard-335416550484.us-central1.run.app

## Software

Python, Dash, Plotly, Pandas, openpyxl, Gunicorn, Cloud Run.

## Visualizaciones

1. Mapa por departamento
2. Líneas por mes
3. Top 5 violentas (X95)
4. Circular menor mortalidad
5. Tabla top 10 causas
6. Barras apiladas sexo × departamento
7. Histograma grupos de edad

## Entrega aula

- Integrantes:
- URL Cloud Run: https://dashboard-335416550484.us-central1.run.app
- URL GitHub: https://github.com/juanfsalamanca/DASHBOARD_WEB_SALLE
