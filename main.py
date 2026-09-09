from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = FastAPI(title="API Mercado VIVA")

# Configuración de CORS para permitir solicitudes del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Servir archivos estáticos del frontend (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="src"), name="static")

# Ruta principal que sirve directamente la aplicación visual (index.html)
@app.get("/")
def inicio():
    return FileResponse("src/index.html")

# Conexión a la base de datos PostgreSQL alojada en Supabase
def get_db_connection():
    try:
        conn = psycopg2.connect(
            os.getenv("DATABASE_URL"),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Error conectando a la BD: {e}")
        return None

# Modelo de validación de datos para solicitudes de reserva
class ReservaRequest(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0)

# 1. Endpoint para consultar el catálogo calculando el stock real dinámicamente
@app.get("/api/productos")
def obtener_productos():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a BD")
    
    try:
        cur = conn.cursor()
        query = '''
            SELECT 
                p.id, 
                p.nombre, 
                p.stock_total,
                (p.stock_total - COALESCE((
                    SELECT SUM(r.cantidad) 
                    FROM reservas r 
                    WHERE r.producto_id = p.id AND r.expira_en > NOW()
                ), 0)) AS stock_disponible
            FROM productos p
            ORDER BY p.id;
        '''
        cur.execute(query)
        productos = cur.fetchall()
        return productos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# 2. Endpoint para crear una reserva temporal con control de concurrencia
@app.post("/api/reservar")
def crear_reserva(reserva: ReservaRequest):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a BD")
    
    try:
        cur = conn.cursor()
        conn.autocommit = False
        
        # Bloqueo con FOR UPDATE para prevenir condiciones de carrera
        cur.execute('''
            SELECT 
                p.stock_total,
                (p.stock_total - COALESCE((
                    SELECT SUM(r.cantidad) 
                    FROM reservas r 
                    WHERE r.producto_id = p.id AND r.expira_en > NOW()
                ), 0)) AS stock_disponible
            FROM productos p
            WHERE p.id = %s FOR UPDATE;
        ''', (reserva.producto_id,))
        
        producto = cur.fetchone()
        
        if not producto:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Producto no encontrado")
            
        if producto['stock_disponible'] < reserva.cantidad:
            conn.rollback()
            raise HTTPException(status_code=400, detail=f"Stock insuficiente. Solo quedan {producto['stock_disponible']} unidades.")
        
        # Generar expiración a 5 minutos en UTC
        expira_en = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        cur.execute('''
            INSERT INTO reservas (producto_id, cantidad, expira_en)
            VALUES (%s, %s, %s) RETURNING id;
        ''', (reserva.producto_id, reserva.cantidad, expira_en))
        
        reserva_id = cur.fetchone()['id']
        conn.commit()
        
        return {
            "mensaje": "Reserva creada exitosamente por 5 minutos.",
            "reserva_id": reserva_id,
            "expira_en": expira_en
        }
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.post("/api/comprar/{reserva_id}")
def confirmar_compra(reserva_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a BD")

    try:
        conn.autocommit = False
        cur = conn.cursor()
        cur.execute('''
            SELECT r.id, r.cantidad, r.expira_en, p.id AS producto_id
            FROM reservas r
            JOIN productos p ON p.id = r.producto_id
            WHERE r.id = %s
            FOR UPDATE;
        ''', (reserva_id,))
        reserva = cur.fetchone()

        if not reserva:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Reserva no encontrada")

        fecha_actual = datetime.now(timezone.utc).replace(tzinfo=None)
        if reserva['expira_en'] <= fecha_actual:
            conn.rollback()
            raise HTTPException(status_code=400, detail="La reserva ha expirado")

        cur.execute('''
            UPDATE productos
            SET stock_total = stock_total - %s
            WHERE id = %s;
        ''', (reserva['cantidad'], reserva['producto_id']))
        cur.execute("DELETE FROM reservas WHERE id = %s;", (reserva_id,))
        conn.commit()

        return {"mensaje": "Compra confirmada", "reserva_id": reserva_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.delete("/api/reservar/{reserva_id}")
def cancelar_reserva(reserva_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a BD")

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM reservas WHERE id = %s RETURNING id;", (reserva_id,))
        reserva = cur.fetchone()
        conn.commit()

        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")

        return {"mensaje": "Reserva cancelada", "reserva_id": reserva_id}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()