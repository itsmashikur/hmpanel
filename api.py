from flask import Flask, request, jsonify
from werkzeug.exceptions import NotFound
from flask_cors import CORS
from CloudFlare import CloudFlare
import sqlite3
import os
import secrets

app = Flask(__name__)
CORS(app)

# Dummy secret key for token authentication (replace with a strong and secure key in production)
SECRET_KEY = "your_secret_key"

CF_EMAIL = "your_cloudflare_email"
CF_API_KEY = "your_cloudflare_api_key"
CF_ZONE_ID = "your_cloudflare_zone_id"
IP_ADDRESS = "your_server_ip_address"
DATABASE_NAME = "web.db"
VHOST_DIR = '/etc/httpd/conf.d/'
WEBSITE_ROOT_DIR = '/var/www/html/'

# Function to generate a new token for authentication
def generate_token():
    return secrets.token_hex(16)

# Function to validate the token received in the request headers
def validate_token(request):
    token = request.headers.get('Authorization')
    if not token:
        return False

    # Extract the token from the "Bearer" token scheme
    token = token.replace('Bearer ', '').strip()

    # Dummy token validation (replace with a more secure authentication mechanism)
    return token == SECRET_KEY

# Function to add an A record to Cloudflare
def add_cloudflare_a_record(domain, ip_address):
    cf = CloudFlare(email=CF_EMAIL, token=CF_API_KEY)
    zone = cf.zones.get(CF_ZONE_ID)
    
    # Check if the A record already exists in the zone
    records = cf.zones.dns_records.get(zone["id"], params={'name': domain, 'type': 'A'})
    if records:
        return None

    params = {
        "name": domain,
        "type": "A",
        "content": ip_address,
        "proxied": True
    }
    
    record = cf.zones.dns_records.post(zone["id"], data=params)
    return record

# Function to validate the website directory
def validate_website_directory(directory):
    if not directory.startswith(WEBSITE_ROOT_DIR):
        return False
    return os.path.exists(directory)

# SQLite database operations
def initialize_database():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS websites
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT, directory TEXT)''')
    conn.commit()
    conn.close()

def add_website_to_database(domain, directory):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO websites (domain, directory) VALUES (?, ?)", (domain, directory))
    conn.commit()
    conn.close()

def update_website_in_database(domain, new_directory):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("UPDATE websites SET directory = ? WHERE domain = ?", (new_directory, domain))
    conn.commit()
    conn.close()

def delete_website_from_database(domain):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM websites WHERE domain = ?", (domain,))
    conn.commit()
    conn.close()

# Virtual host manager
class VHostManager:
    @staticmethod
    def generate_vhost_contents(domain):
        vhost_template = f'''\
<VirtualHost *:80>
    ServerAdmin webmaster@{domain}
    ServerName {domain}
    ServerAlias www.{domain}
    DocumentRoot /var/www/html/{domain}
    <Directory /var/www/html/{domain}>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    ErrorLog /var/log/httpd/{domain}-error.log
    CustomLog /var/log/httpd/{domain}-access.log combined
</VirtualHost>
'''
        return vhost_template

    @staticmethod
    def create_virtual_host(domain):
        vhost_contents = VHostManager.generate_vhost_contents(domain)
        vhost_file_path = os.path.join(VHOST_DIR, f'{domain}.conf')
        if os.path.exists(vhost_file_path):
            return f'Virtual host {domain} already exists'
        with open(vhost_file_path, 'w') as vhost_file:
            vhost_file.write(vhost_contents)
        os.chmod(vhost_file_path, 0o644)
        return f'Virtual host {domain} created successfully'

    @staticmethod
    def delete_virtual_host(domain):
        vhost_file_path = os.path.join(VHOST_DIR, f'{domain}.conf')
        if os.path.exists(vhost_file_path):
            os.remove(vhost_file_path)
            return f'Virtual host {domain} deleted successfully'
        else:
            return f'Virtual host {domain} does not exist'

# Custom error handler
@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, NotFound):
        return jsonify({'message': 'The requested resource was not found.', 'status_code': 404}), 404
    elif isinstance(e, sqlite3.Error):
        return jsonify({'message': 'A database error occurred.', 'status_code': 500}), 500
    else:
        return jsonify({'message': 'An internal server error occurred.', 'status_code': 500, 'error': str(e)}), 500

# Endpoint to generate a new authentication token
@app.route('/auth/token', methods=['POST'])
def get_token():
    token = generate_token()
    return jsonify({'token': token}), 200

# Endpoint to create a virtual host and directory and add Cloudflare A record
@app.route('/website/create', methods=['POST'])
def create_website():
    data = request.json
    domain = data.get('domain')
    directory = data.get('directory')

    # Check token authentication
    if not validate_token(request):
        return jsonify({'message': 'Unauthorized. Token is missing or invalid.', 'status_code': 401}), 401

    # Validate the website directory
    if not validate_website_directory(directory):
        return jsonify({'message': 'Invalid directory. Only directories inside /var/www/html are allowed.', 'status_code': 400}), 400

    # Check if Apache and PHP are installed
    if not check_apache_installed():
        return jsonify({'message': 'Apache is not installed.', 'status_code': 500}), 500

    if not check_php_installed():
        return jsonify({'message': 'PHP is not installed.', 'status_code': 500}), 500

    # Create virtual host
    vhost_manager = VHostManager()
    vhost_message = vhost_manager.create_virtual_host(domain)

    # Create directory
    website_directory = f'/var/www/html/{domain}'
    os.makedirs(website_directory)

    # Create index.php file
    index_php_path = os.path.join(website_directory, 'index.php')
    with open(index_php_path, 'w') as index_php_file:
        index_php_content = f"<?php echo '{domain} is ready'; ?>"
        index_php_file.write(index_php_content)

    # Add Cloudflare A record
    ip_address = IP_ADDRESS
    cf_record = add_cloudflare_a_record(domain, ip_address)

    # Save website data to the database
    add_website_to_database(domain, directory)

    return jsonify({
        'message': f'Website {domain} created successfully',
        'vhost_message': vhost_message,
        'cloudflare_record': cf_record
    })

# Endpoint to edit website data and update Cloudflare A record
@app.route('/website/edit', methods=['POST'])
def edit_website():
    data = request.json
    domain = data.get('domain')
    new_directory = data.get('new_directory')

    # Check token authentication
    if not validate_token(request):
        return jsonify({'message': 'Unauthorized. Token is missing or invalid.', 'status_code': 401}), 401

    # Validate the new website directory
    if not validate_website_directory(new_directory):
        return jsonify({'message': 'Invalid directory. Only directories inside /var/www/html are allowed.', 'status_code': 400}), 400

    # Update virtual host directory
    vhost_manager = VHostManager()
    vhost_message = vhost_manager.update_virtual_host(domain, new_directory)

    # Update Cloudflare A record
    ip_address = IP_ADDRESS
    cf_record = add_cloudflare_a_record(domain, ip_address)

    # Update website data in the database
    update_website_in_database(domain, new_directory)

    return jsonify({
        'message': f'Website {domain} updated successfully',
        'vhost_message': vhost_message,
        'cloudflare_record': cf_record
    })

# Endpoint to delete a website and remove Cloudflare A record
@app.route('/website/delete', methods=['POST'])
def delete_website():
    data = request.json
    domain = data.get('domain')

    # Check token authentication
    if not validate_token(request):
        return jsonify({'message': 'Unauthorized. Token is missing or invalid.', 'status_code': 401}), 401

    # Delete virtual host and directory
    vhost_manager = VHostManager()
    vhost_message = vhost_manager.delete_virtual_host(domain)
    directory_path = f'/var/www/html/{domain}'
    if os.path.exists(directory_path):
        os.rmdir(directory_path)

    # Delete Cloudflare A record
    cf_record = delete_cloudflare_a_record(domain)

    # Delete website data from the database
    delete_website_from_database(domain)

    return jsonify({
        'message': f'Website {domain} deleted successfully',
        'vhost_message': vhost_message,
        'cloudflare_record_deleted': cf_record
    })

# Endpoint to view all website data as JSON
@app.route('/website/list', methods=['GET'])
def list_websites():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM websites")
    rows = c.fetchall()
    websites_list = []
    for row in rows:
        websites_list.append({
            'id': row['id'],
            'domain': row['domain'],
            'directory': row['directory']
        })
    conn.close()
    return jsonify({
        'message': 'List of all websites',
        'websites': websites_list
    })

if __name__ == '__main__':
    initialize_database()
    app.run(host='0.0.0.0', port=5000)
