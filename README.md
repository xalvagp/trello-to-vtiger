# Visor de Tablero Trello

Esta aplicación permite visualizar las tarjetas de la lista 'Factura' de un tablero de Trello en una interfaz web amigable.

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

La aplicación estará disponible en `http://localhost:5001`

## Características

- Visualización de todas las tarjetas de la lista 'Factura'
- Muestra detalles de las tarjetas incluyendo:
  - Nombre de la tarjeta
  - Descripción completa (con soporte básico de Markdown)
  - Checklists (específicamente 'Factura datos')
  - Campos personalizados de Trello y Amazing Fields
- Extracción y visualización de datos específicos del cliente desde checklists:
  - Cuenta, DNI, Dirección, Código postal, Población, Provincia y eMail
- Exportación de datos de tarjetas a archivo CSV para importación en vTiger CRM

## Endpoints

- `/`: Página principal que muestra las tarjetas de la lista 'Factura'
- `/board`: API que devuelve los datos de las tarjetas en formato JSON
- `/amazing-fields/<card_id>`: API que devuelve los datos de Amazing Fields para una tarjeta específica

## Notas sobre Amazing Fields

Si utilizas el power-up Amazing Fields, puedes configurar el token en el archivo `.env`:

```
AMAZING_FIELDS_TOKEN=tu_token_de_amazing_fields
```

Esto permitirá a la aplicación recuperar datos de campos de Amazing Fields.
