# Visor de Tablero Trello

Esta aplicación permite visualizar un tablero de Trello y sus tarjetas en una interfaz web amigable.

## Configuración

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Obtén tus credenciales de Trello:
   - Ve a https://trello.com/app-key para obtener tu API Key
   - En la misma página, genera tu Token
   - Obtén el ID de tu tablero desde la URL del tablero en Trello

3. Crea un archivo `.env` basado en `env.template` y completa tus credenciales:
```bash
cp env.template .env
```

4. Edita el archivo `.env` y añade tus credenciales:
```
TRELLO_API_KEY=tu_api_key
TRELLO_API_TOKEN=tu_token
TRELLO_BOARD_ID=id_del_tablero
```

## Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## Características

- Visualización de todas las listas del tablero
- Muestra las tarjetas con sus descripciones
- Visualización de etiquetas
- Fechas de vencimiento
- Actualización automática cada 30 segundos
