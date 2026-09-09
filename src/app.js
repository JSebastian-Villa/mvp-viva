const API_URL = "http://127.0.0.1:8000/api";

async function cargarProductos() {
    try {
        const respuesta = await fetch(`${API_URL}/productos`);
        const productos = await respuesta.json();
        const contenedor = document.getElementById('contenedor-productos');
        contenedor.innerHTML = '';

        productos.forEach(prod => {
            const div = document.createElement('div');
            div.className = 'card';
            const tieneStock = prod.stock_disponible > 0;
            
            div.innerHTML = `
                <div>
                    <div class="card-header">
                        <h2 class="card-title">${prod.nombre}</h2>
                        <span class="badge ${tieneStock ? 'badge-success' : 'badge-danger'}">
                            ${tieneStock ? `Stock: ${prod.stock_disponible}` : 'Agotado temporalmente'}
                        </span>
                    </div>
                    ${tieneStock ? `
                        <div class="card-body">
                            <div class="input-group">
                                <label for="cant-${prod.id}">Cantidad:</label>
                                <input type="number" id="cant-${prod.id}" value="1" min="1" max="${prod.stock_disponible}">
                            </div>
                        </div>
                    ` : ''}
                </div>
                <button class="btn" ${!tieneStock ? 'disabled' : ''} onclick="iniciarCompra(${prod.id})">
                    ${tieneStock ? 'Agregar y Pagar' : 'Sin disponibilidad'}
                </button>
            `;
            contenedor.appendChild(div);
        });
    } catch (error) {
        console.error("Error al cargar productos:", error);
    }
}

async function iniciarCompra(productoId) {
    const cantidad = document.getElementById(`cant-${productoId}`).value;
    try {
        const resReserva = await fetch(`${API_URL}/reservar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ producto_id: productoId, cantidad: parseInt(cantidad) })
        });
        const dataReserva = await resReserva.json();
        
        if (!resReserva.ok) {
            alert("Error: " + dataReserva.detail);
            cargarProductos();
            return;
        }

        const confirmacion = confirm(`Reserva exitosa (ID: ${dataReserva.reserva_id}). ¿Deseas confirmar el pago?`);
        if (confirmacion) {
            const resCompra = await fetch(`${API_URL}/comprar/${dataReserva.reserva_id}`, { method: 'POST' });
            if (resCompra.ok) {
                alert("Compra exitosa. El stock se ha descontado de la base de datos.");
            }
        } else {
            await fetch(`${API_URL}/reservar/${dataReserva.reserva_id}`, { method: 'DELETE' });
            alert("Compra cancelada. El stock ha sido liberado.");
        }
        cargarProductos();
    } catch (error) {
        alert("Error de comunicación con el servidor.");
    }
}

cargarProductos();