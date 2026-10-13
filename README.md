# Microservicio de órdenes

API de solo lectura (FastAPI + MongoDB Atlas) que implementa el contrato de `ordenes.yaml`.

## Correr localmente

```bash
python -m venv .venv
source .venv/bin/activate        # en fish: source .venv/bin/activate.fish
pip install -r requirements.txt
cp .env.example .env             # completar MONGODB_URI
uvicorn main:app --port 3000 --reload
```

- Documentación interactiva: http://localhost:3000/docs

## Endpoints

| Método | Ruta          | Descripción                                                              |
|--------|---------------|--------------------------------------------------------------------------|
| GET    | `/health`     | Estado del servicio y de la base de datos                                |
| GET    | `/items`      | Lista paginada. Filtros: `clienteId`, `estado`, `desde`, `hasta`, `limit`, `offset` |
| GET    | `/items/{id}` | Detalle de una orden (404 si no existe)                                  |

## Deploy en Render

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Variable de entorno: `MONGODB_URI`
