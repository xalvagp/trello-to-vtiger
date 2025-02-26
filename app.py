from flask import Flask, render_template, jsonify, request, send_from_directory
import requests
from dotenv import load_dotenv
import os
import logging
import json
import datetime
import io
import csv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
AMAZING_FIELDS_PLUGIN_ID = '5d2cac7c242c7d3a3a5588b6'
AMAZING_FIELDS_API_URL = 'https://api.amazingfields.com/api/v1'

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/amazing-fields/<card_id>')
def get_amazing_fields_data(card_id):
    """
    Get Amazing Fields data for a specific card using the Amazing Fields API
    """
    try:
        api_key = os.getenv('TRELLO_API_KEY')
        token = os.getenv('TRELLO_API_TOKEN')
        amazing_fields_token = os.getenv('AMAZING_FIELDS_TOKEN', '')
        
        if not amazing_fields_token:
            logger.warning("Amazing Fields token not found. You need a supporter account to access the Amazing Fields API.")
            return jsonify({'error': 'Amazing Fields token not configured'}), 400
        
        # Get plugin data directly from Trello API
        plugin_data_url = f"https://api.trello.com/1/cards/{card_id}/pluginData"
        plugin_data_response = requests.get(
            plugin_data_url,
            params={
                'key': api_key,
                'token': token
            }
        )
        
        if plugin_data_response.status_code != 200:
            logger.error(f"Error getting plugin data: {plugin_data_response.status_code}")
            logger.error(f"Response: {plugin_data_response.text}")
            return jsonify({'error': f"Error getting plugin data: {plugin_data_response.status_code}"}), 500
            
        plugin_data = plugin_data_response.json()
        logger.debug(f"Plugin data for card {card_id}: {json.dumps(plugin_data, indent=2)}")
        
        # Filter for Amazing Fields plugin data
        amazing_fields_data = None
        for data in plugin_data:
            if data.get('idPlugin') == AMAZING_FIELDS_PLUGIN_ID:
                amazing_fields_data = data
                break
                
        if not amazing_fields_data:
            logger.warning(f"No Amazing Fields data found for card {card_id}")
            return jsonify({'error': 'No Amazing Fields data found for this card'}), 404
            
        # Use Amazing Fields API to decode the data
        amazing_fields_response = requests.get(
            f"{AMAZING_FIELDS_API_URL}/card/{card_id}",
            headers={
                'Authorization': f'Bearer {amazing_fields_token}'
            }
        )
        
        if amazing_fields_response.status_code != 200:
            logger.error(f"Error accessing Amazing Fields API: {amazing_fields_response.status_code}")
            logger.error(f"Response: {amazing_fields_response.text}")
            return jsonify({
                'error': 'Error accessing Amazing Fields API', 
                'raw_data': amazing_fields_data,
                'status': amazing_fields_response.status_code
            }), 500
            
        decoded_data = amazing_fields_response.json()
        return jsonify(decoded_data)
        
    except Exception as e:
        logger.exception(f"Error processing Amazing Fields data for card {card_id}")
        return jsonify({'error': str(e)}), 500

def get_amazing_fields(card_id, amazing_fields_token, api_key, token):
    try:
        # Get plugin data directly from Trello API
        plugin_data_url = f"https://api.trello.com/1/cards/{card_id}/pluginData"
        plugin_data_response = requests.get(
            plugin_data_url,
            params={
                'key': api_key,
                'token': token
            }
        )
        
        if plugin_data_response.status_code != 200:
            logger.error(f"Error getting plugin data: {plugin_data_response.status_code}")
            logger.error(f"Response: {plugin_data_response.text}")
            return None
            
        plugin_data = plugin_data_response.json()
        logger.debug(f"Plugin data for card {card_id}: {json.dumps(plugin_data, indent=2)}")
        
        # Filter for Amazing Fields plugin data
        amazing_fields_data = None
        for data in plugin_data:
            if data.get('idPlugin') == AMAZING_FIELDS_PLUGIN_ID:
                amazing_fields_data = data
                break
                
        if not amazing_fields_data:
            logger.warning(f"No Amazing Fields data found for card {card_id}")
            return None
            
        # Use Amazing Fields API to decode the data
        amazing_fields_response = requests.get(
            f"{AMAZING_FIELDS_API_URL}/card/{card_id}",
            headers={
                'Authorization': f'Bearer {amazing_fields_token}'
            }
        )
        
        if amazing_fields_response.status_code != 200:
            logger.error(f"Error accessing Amazing Fields API: {amazing_fields_response.status_code}")
            logger.error(f"Response: {amazing_fields_response.text}")
            return None
            
        decoded_data = amazing_fields_response.json()
        return decoded_data
        
    except Exception as e:
        logger.exception(f"Error processing Amazing Fields data for card {card_id}")
        return None

@app.route('/board')
def get_board_data():
    try:
        logger.info("Fetching board data...")
        api_key = os.getenv('TRELLO_API_KEY')
        token = os.getenv('TRELLO_API_TOKEN')
        board_id = os.getenv('TRELLO_BOARD_ID')
        
        # Get the board data
        logger.info(f"Fetching board data for board ID: {board_id}")
        board_url = f"https://api.trello.com/1/boards/{board_id}"
        board_response = requests.get(
            board_url,
            params={
                'key': api_key,
                'token': token,
                'lists': 'open',
                'cards': 'open',
                'card_fields': 'name,desc,labels,due,idChecklists',
                'fields': 'name,url'
            }
        )
        
        if board_response.status_code != 200:
            logger.error(f"Error getting board data: {board_response.status_code}")
            return jsonify({'error': f"Error getting board data: {board_response.status_code}"}), 500
            
        board = board_response.json()
        logger.info(f"Board data fetched successfully: {board['name']}")
        
        # Get all lists
        logger.info("Fetching lists...")
        lists_url = f"https://api.trello.com/1/boards/{board_id}/lists"
        lists_response = requests.get(
            lists_url,
            params={
                'key': api_key,
                'token': token,
                'cards': 'open',
                'card_fields': 'name,desc,labels,due,idChecklists'
            }
        )
        
        if lists_response.status_code != 200:
            logger.error(f"Error getting lists: {lists_response.status_code}")
            return jsonify({'error': f"Error getting lists: {lists_response.status_code}"}), 500
            
        lists = lists_response.json()
        logger.info(f"Lists fetched successfully: {len(lists)} lists found")
        
        # Find the "Factura" list
        factura_list = None
        for list_item in lists:
            if list_item['name'] == 'Factura':
                factura_list = list_item
                break
                
        if not factura_list:
            logger.error("Factura list not found")
            return jsonify({'error': "Factura list not found"}), 404
            
        logger.info(f"Factura list found: {factura_list['id']}")
        
        # Get cards from the Factura list
        cards = factura_list.get('cards', [])
        logger.info(f"Found {len(cards)} cards in the Factura list")
        
        # Get checklists for each card
        for card in cards:
            logger.info(f"Processing card: {card['name']} ({card['id']})")
            if 'idChecklists' in card and card['idChecklists']:
                logger.info(f"Card has {len(card['idChecklists'])} checklists")
                card['checklists'] = []
                for checklist_id in card['idChecklists']:
                    logger.info(f"Fetching checklist: {checklist_id}")
                    checklist_url = f"https://api.trello.com/1/checklists/{checklist_id}"
                    checklist_response = requests.get(
                        checklist_url,
                        params={
                            'key': api_key,
                            'token': token,
                            'fields': 'name,checkItems',
                            'checkItems': 'all',
                            'checkItem_fields': 'name,state'
                        }
                    )
                    
                    if checklist_response.status_code == 200:
                        checklist = checklist_response.json()
                        logger.info(f"Checklist fetched: {checklist['name']} with {len(checklist.get('checkItems', []))} items")
                        card['checklists'].append(checklist)
                    else:
                        logger.warning(f"Error getting checklist {checklist_id}: {checklist_response.status_code}")
            else:
                logger.info(f"Card has no checklists")
        
        # Get custom fields for each card
        for card in cards:
            try:
                # Get custom fields from Trello API
                logger.info(f"Fetching custom fields for card: {card['id']}")
                custom_fields_url = f"https://api.trello.com/1/cards/{card['id']}/customFieldItems"
                custom_fields_response = requests.get(
                    custom_fields_url,
                    params={
                        'key': api_key,
                        'token': token
                    }
                )
                
                if custom_fields_response.status_code == 200:
                    card['customFieldItems'] = custom_fields_response.json()
                    logger.info(f"Custom fields fetched: {len(card['customFieldItems'])} fields found")
                else:
                    logger.warning(f"Error getting custom fields for card {card['id']}: {custom_fields_response.status_code}")
                    card['customFieldItems'] = []
                    
                # Try to get Amazing Fields data
                amazing_fields_token = os.getenv('AMAZING_FIELDS_TOKEN')
                if amazing_fields_token:
                    try:
                        logger.info(f"Fetching Amazing Fields data for card: {card['id']}")
                        amazing_fields = get_amazing_fields(card['id'], amazing_fields_token, api_key, token)
                        if amazing_fields:
                            logger.info(f"Amazing Fields data fetched: {len(amazing_fields)} fields found")
                            card['customFields'] = amazing_fields
                        else:
                            logger.warning(f"No Amazing Fields data found for card {card['id']}")
                            card['customFields'] = {}
                    except Exception as e:
                        logger.exception(f"Error getting Amazing Fields data for card {card['id']}")
                        card['customFields'] = {}
                else:
                    logger.warning("Amazing Fields token not set")
                    card['customFields'] = {}
            except Exception as e:
                logger.exception(f"Error processing custom fields for card {card['id']}")
                card['customFieldItems'] = []
                card['customFields'] = {}
        
        # Return the data
        logger.info("Returning board data")
        return jsonify({
            'board': board,
            'factura_list': factura_list
        })
        
    except Exception as e:
        logger.exception("Error getting board data")
        return jsonify({'error': str(e)}), 500

@app.route('/board-data')
def get_board_data_simplified():
    try:
        logger.info("Fetching simplified board data...")
        api_key = os.getenv('TRELLO_API_KEY')
        token = os.getenv('TRELLO_API_TOKEN')
        board_id = os.getenv('TRELLO_BOARD_ID')
        
        # Get the board data
        logger.info(f"Fetching board data for board ID: {board_id}")
        
        # Get all lists
        lists_url = f"https://api.trello.com/1/boards/{board_id}/lists"
        lists_response = requests.get(
            lists_url,
            params={
                'key': api_key,
                'token': token,
                'filter': 'open',
                'fields': 'name,id'
            }
        )
        
        if lists_response.status_code != 200:
            logger.error(f"Error getting lists: {lists_response.status_code}")
            return jsonify({'error': f"Error getting lists: {lists_response.status_code}"}), 500
            
        lists = lists_response.json()
        logger.info(f"Found {len(lists)} lists")
        
        # Find the "Factura" list
        factura_list = None
        for list_item in lists:
            if "factura" in list_item['name'].lower():
                factura_list = list_item
                break
        
        if not factura_list:
            logger.error("Factura list not found")
            return jsonify({'error': "Lista 'Factura' no encontrada"}), 404
        
        logger.info(f"Found Factura list: {factura_list['name']}")
        
        # Get cards from the Factura list
        cards_url = f"https://api.trello.com/1/lists/{factura_list['id']}/cards"
        cards_response = requests.get(
            cards_url,
            params={
                'key': api_key,
                'token': token,
                'fields': 'name,desc,labels,due,idChecklists',
                'checklists': 'all'
            }
        )
        
        if cards_response.status_code != 200:
            logger.error(f"Error getting cards: {cards_response.status_code}")
            return jsonify({'error': f"Error getting cards: {cards_response.status_code}"}), 500
            
        cards = cards_response.json()
        logger.info(f"Found {len(cards)} cards in Factura list")
        
        # Get custom fields for each card
        for card in cards:
            # Get custom fields from Trello
            custom_fields_url = f"https://api.trello.com/1/cards/{card['id']}/customFields"
            custom_fields_response = requests.get(
                custom_fields_url,
                params={
                    'key': api_key,
                    'token': token
                }
            )
            
            if custom_fields_response.status_code == 200:
                card['customFields'] = custom_fields_response.json()
            else:
                card['customFields'] = []
        
        return jsonify({'cards': cards})
        
    except Exception as e:
        logger.exception(f"Error in get_board_data_simplified: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-vtiger-file', methods=['POST'])
def generate_vtiger_file():
    """Generate a file for vTiger import from card data."""
    try:
        logger.info("Received request to generate vTiger file")
        data = request.json
        if not data or 'cardData' not in data:
            logger.error("No card data provided in request")
            return jsonify({'error': 'No card data provided'}), 400
        
        card_data = data['cardData']
        logger.info(f"Generating vTiger file for card: {card_data.get('name', 'Unknown')}")
        
        # Create CSV content for vTiger import
        csv_content = generate_vtiger_csv(card_data)
        logger.info(f"Generated CSV content: {csv_content[:100]}...")
        
        # Create a unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_name = ''.join(c if c.isalnum() else '_' for c in card_data.get('name', 'card'))
        filename = f"vtiger_import_{sanitized_name}_{timestamp}.csv"
        logger.info(f"Generated filename: {filename}")
        
        # Save the file
        file_path = os.path.join('static', 'exports', filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        logger.info(f"Saving file to: {os.path.abspath(file_path)}")
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_content)
        
        download_url = f"/download-file/{filename}"
        logger.info(f"File saved successfully. Download URL: {download_url}")
        
        # Return the file path
        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': download_url
        })
    
    except Exception as e:
        logger.exception(f"Error generating vTiger file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download-file/<filename>')
def download_file(filename):
    """Direct file download endpoint."""
    try:
        logger.info(f"Download request for file: {filename}")
        file_path = os.path.join('static', 'exports', filename)
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return jsonify({'error': 'File not found'}), 404
        
        logger.info(f"Serving file: {file_path}")
        return send_from_directory(
            os.path.join(os.getcwd(), 'static', 'exports'),
            filename,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.exception(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test-direct-download')
def test_direct_download():
    """Test direct file download"""
    try:
        filename = 'test.csv'
        logger.info(f"Test direct download for file: {filename}")
        
        return send_from_directory(
            os.path.join(os.getcwd(), 'static', 'exports'),
            filename,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.exception(f"Error in test direct download: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_vtiger_csv(card_data):
    """Generate CSV content for vTiger import."""
    logger.info("Starting CSV generation")
    
    # Define vTiger CSV headers
    headers = ["accountname", "account_no", "phone", "email1", "website", 
               "bill_street", "bill_city", "bill_state", "bill_code", "bill_country",
               "description"]
    
    # Initialize data row with empty values
    data_row = {header: "" for header in headers}
    
    # Extract card name for account name
    data_row["accountname"] = card_data.get('name', '')
    logger.info(f"Account name: {data_row['accountname']}")
    
    # Extract description
    data_row["description"] = card_data.get('desc', '')
    
    # Process checklists to extract specific data
    if 'checklists' in card_data:
        logger.info(f"Processing {len(card_data['checklists'])} checklists")
        for checklist in card_data['checklists']:
            logger.info(f"Processing checklist: {checklist['name']}")
            
            if checklist['name'] == 'Cuenta':
                # Extract account number from Cuenta checklist
                for item in checklist['checkItems']:
                    data_row["account_no"] = extract_value_from_checklist_item(item['name'])
                    logger.info(f"Extracted account_no: {data_row['account_no']}")
            
            elif checklist['name'] == 'DNI':
                # Could be used as account_no if not already set
                if not data_row["account_no"]:
                    for item in checklist['checkItems']:
                        data_row["account_no"] = extract_value_from_checklist_item(item['name'])
                        logger.info(f"Extracted account_no from DNI: {data_row['account_no']}")
            
            elif checklist['name'] == 'Dirección':
                # Extract address
                for item in checklist['checkItems']:
                    data_row["bill_street"] = extract_value_from_checklist_item(item['name'])
                    logger.info(f"Extracted bill_street: {data_row['bill_street']}")
            
            elif checklist['name'] == 'Código postal':
                # Extract postal code
                for item in checklist['checkItems']:
                    data_row["bill_code"] = extract_value_from_checklist_item(item['name'])
                    logger.info(f"Extracted bill_code: {data_row['bill_code']}")
            
            elif checklist['name'] == 'Población':
                # Extract city
                for item in checklist['checkItems']:
                    data_row["bill_city"] = extract_value_from_checklist_item(item['name'])
                    logger.info(f"Extracted bill_city: {data_row['bill_city']}")
            
            elif checklist['name'] == 'Provincia':
                # Extract state/province
                for item in checklist['checkItems']:
                    data_row["bill_state"] = extract_value_from_checklist_item(item['name'])
                    logger.info(f"Extracted bill_state: {data_row['bill_state']}")
            
            elif checklist['name'] == 'eMail':
                # Extract email
                for item in checklist['checkItems']:
                    data_row["email1"] = extract_value_from_checklist_item(item['name'])
                    logger.info(f"Extracted email1: {data_row['email1']}")
    else:
        logger.warning("No checklists found in card data")
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerow(data_row)
    
    csv_content = output.getvalue()
    logger.info("CSV generation complete")
    return csv_content

def extract_value_from_checklist_item(item_text):
    """Extract value from checklist item text, assuming format like 'Field: Value'."""
    if ':' in item_text:
        return item_text.split(':', 1)[1].strip()
    return item_text.strip()

@app.route('/test-modal')
def test_modal():
    """Test page for Bootstrap modal functionality"""
    return render_template('test_modal.html')

@app.route('/test-download')
def test_download():
    """Test page for file download functionality"""
    return render_template('test_download.html')

if __name__ == '__main__':
    app.run(debug=True, port=5002)
