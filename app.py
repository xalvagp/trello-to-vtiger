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
                        custom_fields_data = custom_fields_response.json()
                        logger.debug(f"Custom fields data: {json.dumps(custom_fields_data, indent=2)}")
                        
                        # Process custom fields
                        for field in custom_fields_data:
                            field_value = field.get('value', {}).get('text', '')
                            field_name = field.get('idCustomField', '')
                            
                            # Map custom field IDs to field names
                            if field_name and field_value:
                                if 'nombre' in field_name.lower():
                                    amazing_fields['Nombre'] = field_value
                                elif 'fecha' in field_name.lower():
                                    amazing_fields['Fecha'] = field_value
                                elif 'provincia' in field_name.lower():
                                    amazing_fields['Provincia'] = field_value
                                elif 'poblacion' in field_name.lower():
                                    amazing_fields['Población'] = field_value
                                elif 'postal' in field_name.lower():
                                    amazing_fields['C.Postal'] = field_value
                                elif 'direccion' in field_name.lower():
                                    amazing_fields['Dirección'] = field_value
                                elif 'dni' in field_name.lower():
                                    amazing_fields['DNI'] = field_value
                    
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
