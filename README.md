# RandomSearchRepo

Una herramienta CLI en Python para descubrir repositorios semi-aleatorios en GitHub, explorar proyectos de código abierto independientes y aprender de bases de código variadas.

## 🚀 Estructura del Proyecto

```text
RamdomSearchRepo/
├── src/
│   ├── __init__.py
│   └── github_client.py    # Cliente API de GitHub, lógica semi-aleatoria y control de cuotas
├── .env.example            # Plantilla para variables de entorno (Token opcional)
├── requirements.txt        # Dependencias (requests, python-dotenv)
├── main.py                 # Script de prueba e inicio rápido
└── README.md
```

## ⚙️ Estrategia de Búsqueda Semi-Aleatoria

Para evitar repeticiones, saltar bloqueos por rate limit y descubrir repositorios poco conocidos o proyectos independientes interesantes:
1. **Filtro de estrellas balanceado:** Se restringe por defecto el rango (ej. `5..300` estrellas) para descartar proyectos masivos que siempre encabezan las búsquedas o repositorios vacíos.
2. **Palabras clave y tópicos diversos:** Selecciona al azar palabras clave técnicas (`cli`, `crawler`, `parser`, `minimal`, `engine`, `api`, etc.).
3. **Muestreo temporal dinámico:** Introduce rangos de fecha de creación aleatorios en los últimos años (`created:YYYY-MM-DD..YYYY-MM-DD`).
4. **Paginación con entropía:** Calcula el total de resultados y consulta páginas aleatorias en lugar de siempre mostrar la primera.
5. **Monitoreo de Rate Limits:** Monitorea las cabeceras `X-RateLimit-*` de GitHub para avisar al usuario antes de saturar la cuota (10 req/min sin autenticación, 30 req/min con `GITHUB_TOKEN`).

## 🛠️ Instalación y Prueba

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. (Opcional) Configurar un Token Personal de GitHub para aumentar los límites de tasa:
   ```bash
   cp .env.example .env
   # Agregar GITHUB_TOKEN=tu_token_aqui
   ```

3. Ejecutar la prueba de conexión:
   ```bash
   python main.py
   ```
