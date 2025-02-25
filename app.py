from flask import Flask, render_template, jsonify
import requests
from dotenv import load_dotenv
import os
import logging
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ID del plugin Amazing Fields (actualizado con el ID correcto)
AMAZING_FIELDS_PLUGIN_ID = "60e068efb294647187bbe4f5"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/board')
def get_board_data():
    try:
        api_key = os.getenv('TRELLO_API_KEY')
        token = os.getenv('TRELLO_API_TOKEN')
        board_id = os.getenv('TRELLO_BOARD_ID')
        
        logger.debug(f"Getting data for board ID: {board_id}")
        logger.debug(f"Using API Key: {api_key[:4]}... and Token: {token[:4]}...")
        
        # Get plugin data for Amazing Fields
        plugins_url = f"https://api.trello.com/1/boards/{board_id}/plugins"
        plugins_response = requests.get(
            plugins_url,
            params={
                'key': api_key,
                'token': token
            }
        )
        
        if plugins_response.status_code == 200:
            plugins_data = plugins_response.json()
            logger.debug(f"Plugins data: {json.dumps(plugins_data, indent=2)}")
        else:
            logger.error(f"Error getting plugins: {plugins_response.status_code}")
            logger.error(f"Response: {plugins_response.text}")
        
        # Get custom fields definitions
        custom_fields_url = f"https://api.trello.com/1/boards/{board_id}/customFields"
        custom_fields_response = requests.get(
            custom_fields_url,
            params={
                'key': api_key,
                'token': token
            }
        )
        
        if custom_fields_response.status_code != 200:
            logger.error(f"Error getting custom fields: {custom_fields_response.status_code}")
            logger.error(f"Response: {custom_fields_response.text}")
            return jsonify({'error': f"Error getting custom fields: {custom_fields_response.status_code}"}), 500
            
        custom_fields_data = custom_fields_response.json()
        logger.debug("=== Custom Fields Definitions ===")
        for field in custom_fields_data:
            logger.debug(f"Field: {field['name']} (ID: {field['id']}) - Type: {field.get('type', 'unknown')}")
        logger.debug("===============================")
        custom_fields_definitions = {field['id']: field for field in custom_fields_data}
        
        # Get lists with cards
        lists_url = f"https://api.trello.com/1/boards/{board_id}/lists"
        lists_response = requests.get(
            lists_url,
            params={
                'key': api_key,
                'token': token,
                'cards': 'open',
                'card_fields': 'name,desc,due,labels,id,pluginData',
                'card_customFieldItems': 'true',
                'customFields': 'true',
                'fields': 'name,id'
            }
        )
        
        if lists_response.status_code != 200:
            logger.error(f"Error getting lists: {lists_response.status_code}")
            logger.error(f"Response: {lists_response.text}")
            return jsonify({'error': f"Error getting lists: {lists_response.status_code}"}), 500
            
        lists_data = lists_response.json()
        logger.debug(f"Lists data: {json.dumps(lists_data, indent=2)}")
        
        # Format response
        formatted_data = {
            'name': 'Tablero de Trello',
            'lists': []
        }
        
        # Filter lists that contain "Factura"
        for list_data in lists_data:
            if 'factura' in list_data['name'].lower():
                list_info = {
                    'name': list_data['name'],
                    'cards': []
                }
                
                for card in list_data.get('cards', []):
                    logger.debug(f"\nProcessing card: {card['name']}")
                    logger.debug(f"Card data: {json.dumps(card, indent=2)}")
                    
                    # Initialize amazing_fields with empty values
                    amazing_fields = {
                        'Nombre': '',
                        'Fecha': '',
                        'Provincia': '',
                        'Población': '',
                        'C.Postal': '',
                        'Dirección': '',
                        'DNI': ''
                    }
                    
                    # Get custom field data
                    custom_fields_url = f"https://api.trello.com/1/cards/{card['id']}/customFieldItems"
                    custom_fields_response = requests.get(
                        custom_fields_url,
                        params={
                            'key': api_key,
                            'token': token
                        }
                    )
                    
                    if custom_fields_response.status_code == 200:
                        custom_fields_items = custom_fields_response.json()
                        logger.debug(f"Custom fields items for card {card['name']}: {json.dumps(custom_fields_items, indent=2)}")
                        
                        # Process custom fields
                        for field_item in custom_fields_items:
                            field_def = custom_fields_definitions.get(field_item.get('idCustomField'))
                            if not field_def:
                                continue
                                
                            field_name = field_def.get('name', '')
                            field_type = field_def.get('type', '')
                            field_value = ''
                            
                            # Extract value based on field type
                            if field_type == 'text':
                                field_value = field_item.get('value', {}).get('text', '')
                            elif field_type == 'date':
                                field_value = field_item.get('value', {}).get('date', '')
                            elif field_type == 'number':
                                field_value = field_item.get('value', {}).get('number', '')
                            
                            logger.debug(f"Processing field: {field_name} ({field_type}) = {field_value}")
                            
                            # Map field names to our structure
                            field_name_lower = field_name.lower()
                            if field_name_lower == 'nombre':
                                amazing_fields['Nombre'] = field_value
                            elif field_name_lower == 'fecha':
                                amazing_fields['Fecha'] = field_value
                            elif field_name_lower == 'provincia':
                                amazing_fields['Provincia'] = field_value
                            elif field_name_lower in ['poblacion', 'población']:
                                amazing_fields['Población'] = field_value
                            elif field_name_lower == 'c.postal' or 'postal' in field_name_lower:
                                amazing_fields['C.Postal'] = field_value
                            elif field_name_lower in ['direccion', 'dirección']:
                                amazing_fields['Dirección'] = field_value
                            elif field_name_lower == 'dni':
                                amazing_fields['DNI'] = field_value
                    else:
                        logger.error(f"Error getting custom fields for card {card['name']}: {custom_fields_response.status_code}")
                        logger.error(f"Response: {custom_fields_response.text}")
                    
                    # Add card data to list
                    card_info = {
                        'name': card['name'],
                        'description': card.get('desc', ''),
                        'labels': [label['name'] for label in card.get('labels', [])],
                        'due_date': card.get('due'),
                        'amazing_fields': amazing_fields
                    }
                    list_info['cards'].append(card_info)
                    
                formatted_data['lists'].append(list_info)
        
        logger.debug(f"Final formatted data: {json.dumps(formatted_data, indent=2)}")
        return jsonify(formatted_data)
    
    except Exception as e:
        logger.exception("Error accessing Trello API")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
