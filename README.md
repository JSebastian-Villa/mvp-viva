# Mercado VIVA - Módulo de Verificación de Inventario

MVP desarrollado para el caso de estudio de la cadena de supermercados **Mercado VIVA**, enfocado en resolver las problemáticas críticas de disponibilidad de inventario en compras digitales, garantizando la integridad de las transacciones y evitando sobreventas de productos agotados.

## Acceso a la Aplicación

La aplicación se encuentra completamente publicada y accesible en la nube:
* **URL de Producción:** [https://mvp-viva.onrender.com](https://mvp-viva.onrender.com)
* **Nota de Arranque:** Al estar alojada en el plan gratuito de Render, el servidor entra en suspensión tras unos minutos de inactividad (*cold start*). La primera carga puede tomar aproximadamente 50 segundos; se recomienda abrir el enlace previamente antes de realizar demostraciones o evaluaciones.

## Tecnologías Utilizadas

* **Python & FastAPI:** Framework web asíncrono de alto rendimiento que sirve como el núcleo del Backend. Procesa los endpoints de la API REST, aplica las reglas del negocio, valida los datos y sirve de forma unificada los archivos estáticos de la interfaz.
* **Supabase PostgreSQL:** Base de datos relacional en la nube responsable de la persistencia de la información (`productos` y `reservas`). Implementa lógica transaccional avanzada con bloqueos pesimistas (`FOR UPDATE`) y gestión automatizada de tiempos de expiración (`NOW() + INTERVAL`).
* **HTML5, CSS3 & Vanilla JavaScript (`app.js`):** Conjunto tecnológico para el desarrollo del Frontend de la aplicación. Ofrece una interfaz visual limpia basada en tarjetas interactivas que consumen la API de forma asíncrona mediante peticiones `fetch`.
* **Render:** Plataforma de computación en la nube utilizada para el despliegue del servicio web completo, garantizando el aislamiento seguro de credenciales mediante variables de entorno y conectividad cifrada hacia la base de datos.

## Características de la Arquitectura

* **Doble Capa de Seguridad y Validación:** El frontend implementa filtros preventivos que limitan la selección de stock para guiar al usuario, mientras que el backend y la base de datos validan de forma estricta cada transacción para bloquear operaciones inválidas incluso ante peticiones externas directas.
* **Integridad ante Concurrencia:** Utiliza bloqueos a nivel de base de datos para asegurar que dos clientes que intenten comprar el último producto disponible de forma simultánea no generen inconsistencias ni sobreventas en el sistema.

## Cómo Ejecutar o Probar la Aplicación

Al tratarse de una arquitectura desplegada en la nube, no requiere instalación local de dependencias ni bases de datos para su evaluación:
1. Asegúrate de que el servicio web esté activo ingresando a [https://mvp-viva.onrender.com](https://mvp-viva.onrender.com).
2. Interactúa directamente con la interfaz gráfica para consultar el catálogo, realizar reservas temporales y confirmar compras.
3. Opcionalmente, puedes explorar la documentación interactiva de la API ingresando a [https://mvp-viva.onrender.com/docs](https://mvp-viva.onrender.com/docs).
