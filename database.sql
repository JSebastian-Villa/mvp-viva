-- Tabla principal de inventario
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    stock_total INT NOT NULL
);

-- Tabla temporal para manejar el bloqueo de concurrencia y reservas
CREATE TABLE reservas (
    id SERIAL PRIMARY KEY,
    producto_id INT REFERENCES productos(id),
    cantidad INT NOT NULL,
    expira_en TIMESTAMP NOT NULL
);

-- Insertar catálogo de Mercado VIVA
INSERT INTO productos (nombre, stock_total) VALUES 
('Café Premium 500g', 3),                   -- Ideal para probar el límite de cantidad manual
('Aceite de Oliva 1L', 5),
('Arroz Blanco 1kg', 45),
('Leche Deslactosada 1L (Six Pack)', 12),
('Detergente Líquido 3L', 8),
('Papel Higiénico 12 Rollos', 20),
('Televisor Smart 50" 4K', 2),
('Consola PlayStation 5 Slim', 1),          -- Perfecto para probar la condición de carrera con 2 navegadores
('Galletas de Chocolate', 0),               -- Útil para mostrar la interfaz visual de "Agotado" por defecto
('Shampoo Anticaspa 400ml', 15);