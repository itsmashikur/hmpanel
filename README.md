# Hosting Management Panel API

The Web Management API is a Flask-based web application that allows users to manage websites, virtual hosts, and Cloudflare DNS records. It provides endpoints for creating, editing, and deleting websites, as well as listing all existing websites.

## Base URL

- http://your_server_ip_address:5000

Replace `your_server_ip_address` with the actual IP address of your server.

## Authentication

- **Token-Based Authentication**
  - To access the API endpoints, you need to obtain an authentication token.
  - Use the `/auth/token` endpoint to generate a new token.
  - Include the token in the `Authorization` header using the Bearer token scheme for subsequent requests.

## Endpoints

### 1. Generate Authentication Token

- **URL:** `/auth/token`
- **Method:** `POST`
- **Description:** Generates a new authentication token.
- **Response:** Returns the generated token.

### 2. Create Website

- **URL:** `/website/create`
- **Method:** `POST`
- **Description:** Creates a new website, virtual host, directory, and Cloudflare A record.
- **Request Body:**
  - `domain`: (string) The domain name of the website to be created.
  - `directory`: (string) The directory path where the website files will be stored (inside `/var/www/html`).
- **Headers:** Include the authentication token in the `Authorization` header.
- **Response:** Returns the status of the operation along with details of the virtual host and Cloudflare record.

### 3. Edit Website

- **URL:** `/website/edit`
- **Method:** `POST`
- **Description:** Edits an existing website by updating the website directory and the associated Cloudflare A record.
- **Request Body:**
  - `domain`: (string) The domain name of the website to be edited.
  - `new_directory`: (string) The new directory path where the website files will be moved (inside `/var/www/html`).
- **Headers:** Include the authentication token in the `Authorization` header.
- **Response:** Returns the status of the operation along with details of the updated virtual host and Cloudflare record.

### 4. Delete Website

- **URL:** `/website/delete`
- **Method:** `POST`
- **Description:** Deletes an existing website, virtual host, directory, and Cloudflare A record.
- **Request Body:**
  - `domain`: (string) The domain name of the website to be deleted.
- **Headers:** Include the authentication token in the `Authorization` header.
- **Response:** Returns the status of the operation along with details of the deleted virtual host and Cloudflare record.

### 5. List Websites

- **URL:** `/website/list`
- **Method:** `GET`
- **Description:** Retrieves a list of all websites and their associated data.
- **Headers:** Include the authentication token in the `Authorization` header.
- **Response:** Returns a JSON array containing information about all websites, including their IDs, domains, and directories.

## Error Handling

- The API handles various types of errors, including 404 Not Found, 500 Internal Server Error, and database errors.
- Proper error messages are returned in the response to help identify and resolve issues.

## Security Considerations

- Ensure that the token is kept secure and is not shared publicly.
- Set appropriate file and directory permissions to prevent unauthorized access.
- Implement rate limiting and other security measures to protect against potential attacks.
- Always validate user input to prevent SQL injection and other vulnerabilities.
- Securely store sensitive data, such as Cloudflare credentials, using environment variables or a secure configuration management system.

## Deployment Considerations

- For production deployment, use a production-grade web server (e.g., Gunicorn or uWSGI) to serve the Flask application.
- Use a reverse proxy (e.g., Nginx or Apache) to handle incoming requests and provide extra security and performance benefits.
- Thoroughly review and test the code before deploying it to a live server.

## Note

This API is intended for educational purposes and may require additional security enhancements and optimizations for production use. Always follow best practices and security guidelines when deploying web applications in a production environment.

