CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    stock_total INT NOT NULL
);

CREATE TABLE reservas (
    id SERIAL PRIMARY KEY,
    producto_id INT REFERENCES productos(id),
    cantidad INT NOT NULL,
    expira_en TIMESTAMP NOT NULL
);

INSERT INTO productos (nombre, stock_total) VALUES ('Café Premium 500g', 3);
INSERT INTO productos (nombre, stock_total) VALUES ('Aceite de Oliva 1L', 5);