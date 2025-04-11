# Nextcloud Python Client (WebDAV)

A Python client script for interacting with a Nextcloud instance using the WebDAV API. This script provides basic functionalities for file and directory management.

## Description

This script encapsulates Nextcloud WebDAV operations within a `NextcloudClient` class, making it easier to integrate file management tasks into other Python applications (like Django). It handles authentication, URL construction, and basic API interactions for common tasks.

## Features

* **Upload Files:** Upload local files to a specified path on Nextcloud.
* **Create Directories:** Create new directories (collections) on Nextcloud.
* **List Directory Contents:** List files and subdirectories within a specified Nextcloud directory.
* **Delete Files/Directories:** Delete files or entire directories from Nextcloud.
* **Configuration:** Uses environment variables for Nextcloud URL and credentials.
* **Proxy Handling:** Attempts to disable system proxies to avoid common connection issues.

## Requirements

* Python 3.x
* `requests` library (`pip install requests`)

## Configuration

The script requires the following configuration details, preferably set as environment variables:

* `NEXTCLOUD_URL`: The base URL of your Nextcloud instance (e.g., `https://cloud.example.com`). Defaults to `http://localhost:8080` if not set.
* `NEXTCLOUD_USERNAME`: Your Nextcloud username. Defaults to `Meysam08` if not set.
* `NEXTCLOUD_PASSWORD`: Your Nextcloud password or preferably an **App Password/Token** generated from Nextcloud's security settings. Defaults to `12mm12mm` if not set ( **Change this default!** ).

**Security Note:** It is strongly recommended to use environment variables or a secure configuration management system (like Django settings) rather than hardcoding credentials directly in the script, especially when committing to version control. Use App Passwords for better security.

## Usage

1.  **Import the client:**
    ```python
    from nextcloud_client import NextcloudClient # Assuming you saved the script as nextcloud_client.py
    import os
    ```

2.  **Set Configuration (Example using environment variables):**
    ```python
    # Load from environment variables or set directly (less secure)
    url = os.getenv('NEXTCLOUD_URL', 'YOUR_NEXTCLOUD_URL')
    user = os.getenv('NEXTCLOUD_USERNAME', 'YOUR_USERNAME')
    password = os.getenv('NEXTCLOUD_PASSWORD', 'YOUR_APP_PASSWORD')
    ```

3.  **Instantiate the client:**
    ```python
    try:
        client = NextcloudClient(url, user, password)
    except ValueError as e:
        print(f"Configuration Error: {e}")
        # Handle error appropriately
    except Exception as e:
        print(f"An unexpected error occurred during client initialization: {e}")
        # Handle error appropriately
    ```

4.  **Perform Operations:**

    * **Create a Directory:**
        ```python
        try:
            remote_dir = '/my_app_uploads'
            client.create_directory(remote_dir)
            print(f"Directory '{remote_dir}' created or already exists.")
        except Exception as e:
            print(f"Failed to create directory: {e}")
        ```

    * **Upload a File:**
        ```python
        try:
            local_file = 'path/to/your/local/file.txt'
            remote_path = f'{remote_dir}/uploaded_file.txt'
            client.upload_file(local_file, remote_path)
            print(f"File uploaded to '{remote_path}'.")
        except FileNotFoundError as e:
             print(f"Local file not found: {e}")
        except Exception as e:
            print(f"Failed to upload file: {e}")
        ```

    * **List Directory Contents:**
        ```python
        try:
            items = client.list_directory(remote_dir)
            print(f"Contents of '{remote_dir}':")
            for item in items:
                item_type = "Directory" if item['is_dir'] else "File"
                print(f"- {item['name']} ({item_type})")
        except Exception as e:
            print(f"Failed to list directory: {e}")
        ```

    * **Delete a File or Directory:**
        ```python
        try:
            path_to_delete = f'{remote_dir}/uploaded_file.txt'
            # Or path_to_delete = remote_dir to delete the whole directory
            was_deleted = client.delete(path_to_delete)
            if was_deleted:
                 print(f"Successfully deleted '{path_to_delete}'.")
            else:
                 print(f"Could not delete '{path_to_delete}' (might not exist).")
        except Exception as e:
            print(f"Failed to delete item: {e}")
        ```

## Error Handling

The client methods will raise exceptions (e.g., `requests.exceptions.RequestException`, `FileNotFoundError`, `ET.ParseError`) upon failure. Ensure you wrap calls in `try...except` blocks to handle potential errors gracefully in your application.

## Integration Example (Conceptual Django)

```python
# In a Django view
from django.conf import settings
from .nextcloud_client import NextcloudClient # Adjust import
import os

def handle_upload(request):
    # ... get uploaded_file from request ...
    # ... save uploaded_file temporarily to local_temp_path ...

    try:
        client = NextcloudClient(
            settings.NEXTCLOUD_URL,
            settings.NEXTCLOUD_USERNAME,
            settings.NEXTCLOUD_PASSWORD
        )
        remote_path = f"/django_uploads/{uploaded_file.name}"
        client.create_directory("/django_uploads") # Ensure base dir exists
        client.upload_file(local_temp_path, remote_path)
        # ... handle success ...
    except Exception as e:
        # ... handle error, log it, return error response ...
    finally:
