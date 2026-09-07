from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Render inyectará la variable DATABASE_URL automáticamente
DB_URL = os.getenv("DATABASE_URL", "tu_url_de_conexion_a_supabase")

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

class ReservaRequest(BaseModel):
    producto_id: int
    cantidad: int

@app.get("/api/productos")
def consultar_inventario():
    query = """
        SELECT p.id, p.nombre, p.stock_total,
               COALESCE(SUM(r.cantidad), 0) as reservado,
               (p.stock_total - COALESCE(SUM(r.cantidad), 0)) as stock_disponible
        FROM productos p
        LEFT JOIN reservas r ON p.id = r.producto_id AND r.expira_en > NOW()
        GROUP BY p.id;
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query)
    productos = cursor.fetchall()
    conn.close()
    return productos

@app.post("/api/reservar")
def reservar_producto(req: ReservaRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT (stock_total - COALESCE((SELECT SUM(cantidad) FROM reservas WHERE producto_id = %s AND expira_en > NOW()), 0)) as disponible 
        FROM productos WHERE id = %s
    """, (req.producto_id, req.producto_id))
    resultado = cursor.fetchone()
    
    if not resultado or resultado['disponible'] < req.cantidad:
        conn.close()
        raise HTTPException(status_code=400, detail="Inventario insuficiente o producto no encontrado.")
    
    cursor.execute(
        "INSERT INTO reservas (producto_id, cantidad, expira_en) VALUES (%s, %s, NOW() + INTERVAL '5 minutes') RETURNING id",
        (req.producto_id, req.cantidad)
    )
    reserva_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()
    return {"mensaje": "Reserva exitosa", "reserva_id": reserva_id}

@app.post("/api/comprar/{reserva_id}")
def confirmar_compra(reserva_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT producto_id, cantidad FROM reservas WHERE id = %s", (reserva_id,))
    reserva = cursor.fetchone()
    
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada o expirada")
        
    cursor.execute("UPDATE productos SET stock_total = stock_total - %s WHERE id = %s", (reserva['cantidad'], reserva['producto_id']))
    cursor.execute("DELETE FROM reservas WHERE id = %s", (reserva_id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Compra confirmada exitosamente"}

# Esta línea debe ir SIEMPRE al final para no bloquear las rutas /api
app.mount("/", StaticFiles(directory="src", html=True), name="static")