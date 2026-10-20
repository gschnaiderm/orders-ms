import os
from datetime import date, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from starlette.exceptions import HTTPException as StarletteHTTPException

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME", "ordenes-ms")
VERSION = "1.0.0"
ESTADOS = {"pendiente", "pagada", "enviada", "entregada", "cancelada"}

client = MongoClient(os.environ["MONGODB_URI"])
orders = client["orders-ms"]["orders"]

app = FastAPI(title="Microservicio de ordenes", version=VERSION)

# Permite que páginas de otros dominios (p. ej. el monitor del dashboard) llamen al servicio
# desde el navegador. El servicio es público y de solo lectura.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    err = exc.errors()[0]
    param = err["loc"][-1]
    return error(400, "bad_request", f"El parámetro {param} es inválido: {err['msg']}")


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request, exc: StarletteHTTPException):
    code = "not_found" if exc.status_code == 404 else "bad_request"
    return error(exc.status_code, code, str(exc.detail))


@app.get("/health")
def health():
    client.admin.command("ping")
    return {"status": "ok", "service": SERVICE_NAME, "collection": "ordenes", "version": VERSION}


@app.get("/items")
def list_items(
    clienteId: str | None = Query(None, pattern=r"(?i)^CLI[0-9]+$"),
    estado: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    filtro = {}
    if clienteId:
        filtro["clienteId"] = clienteId.upper()
    if estado:
        if estado.lower() not in ESTADOS:
            return error(400, "bad_request", f"El parámetro estado debe ser uno de: {', '.join(sorted(ESTADOS))}.")
        filtro["estado"] = estado.lower()

    # fecha se guarda como string ISO 8601 UTC, así que la comparación lexicográfica es válida
    rango_fecha = {}
    if desde:
        rango_fecha["$gte"] = desde.isoformat()
    if hasta:
        rango_fecha["$lt"] = (hasta + timedelta(days=1)).isoformat()
    if rango_fecha:
        filtro["fecha"] = rango_fecha

    items = list(orders.find(filtro, {"_id": 0}).sort("id", 1).skip(offset).limit(limit))
    total = orders.count_documents(filtro)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@app.get("/items/{id}")
def get_item(id: str):
    item = orders.find_one({"id": id}, {"_id": 0})
    if item is None:
        return error(404, "not_found", f"No existe {id}.")
    return item
