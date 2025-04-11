import os
import requests
import mimetypes # For guessing file types
from requests.auth import HTTPBasicAuth
from urllib.parse import quote # For encoding paths properly
from xml.etree import ElementTree as ET # For parsing PROPFIND responses

# --- Configuration ---
# Best practice: Load these from environment variables or a config file in a real application
NEXTCLOUD_URL = os.getenv('NEXTCLOUD_URL', 'http://localhost:8080') # Your Nextcloud instance URL
USERNAME = os.getenv('NEXTCLOUD_USERNAME', 'Meysam08') # Your Nextcloud username
PASSWORD = os.getenv('NEXTCLOUD_PASSWORD', '12mm12mm') # Your Nextcloud app password or regular password

# --- Clear Proxy Environment Variables ---
# This helps prevent requests from trying to use system-defined proxies,
# which seems to be causing the connection error in your case.
print("Attempting to clear proxy environment variables...")
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
print("Proxy environment variables cleared (if they were set).")


class NextcloudClient:
    """
    A client for interacting with Nextcloud via the WebDAV API.
    """
    def __init__(self, nextcloud_url, username, password):
        """
        Initializes the Nextcloud client.

        Args:
            nextcloud_url (str): The base URL of the Nextcloud instance.
            username (str): The Nextcloud username.
            password (str): The Nextcloud password or app token.
        """
        if not nextcloud_url:
            raise ValueError("NEXTCLOUD_URL cannot be empty.")
        self.base_url = nextcloud_url.rstrip('/') # Remove trailing slash if present
        self.username = username
        self.auth = HTTPBasicAuth(username, password)
        self.dav_base_path = f'/remote.php/dav/files/{self.username}'
        # Disable proxy usage for requests made by this client session
        self.session = requests.Session()
        self.session.proxies = {} # Clear proxies specifically for this session
        # Explicitly trust the environment settings regarding proxies (which we cleared above)
        self.session.trust_env = False # Tells requests not to look for proxies in env again
        print("Requests session configured to ignore environment proxy settings.")


    def _build_url(self, remote_path):
        """
        Constructs the full WebDAV URL for a given remote path.

        Args:
            remote_path (str): The path on the Nextcloud server (e.g., '/documents/report.pdf').
                               Should start with a '/'.

        Returns:
            str: The full WebDAV URL.
        """
        if not remote_path.startswith('/'):
             remote_path = '/' + remote_path
        # URL encode the path components to handle special characters like spaces
        # Use safe='/' to prevent encoding slashes
        encoded_path = '/'.join(quote(part, safe='') for part in remote_path.strip('/').split('/'))
        full_url = f"{self.base_url}{self.dav_base_path}/{encoded_path}"
        # print(f"Built URL: {full_url}") # Debug print
        return full_url

    def _handle_response(self, response, success_codes=(200, 201, 204, 207)):
        """
        Checks the response status code and raises an error for failures.

        Args:
            response (requests.Response): The response object from the request.
            success_codes (tuple): A tuple of HTTP status codes considered successful.

        Raises:
            requests.exceptions.HTTPError: If the response status code is not in success_codes.
        """
        if response.status_code not in success_codes:
            error_message = (
                f"Nextcloud API request failed.\n"
                f"URL: {response.url}\n"
                f"Method: {response.request.method}\n"
                f"Status Code: {response.status_code}\n"
                f"Response: {response.text}"
            )
            print(error_message) # Print the detailed error message
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)


    def upload_file(self, local_file_path, remote_path):
        """
        Uploads a local file to the specified path on Nextcloud.
        Overwrites the file if it already exists.

        Args:
            local_file_path (str): The path to the local file to upload.
            remote_path (str): The desired path on Nextcloud (e.g., '/uploads/data.csv').

        Returns:
            bool: True if the upload was successful.

        Raises:
            FileNotFoundError: If the local file does not exist.
            requests.exceptions.RequestException: For network or API errors.
        """
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"Local file not found: {local_file_path}")

        url = self._build_url(remote_path)
        content_type, _ = mimetypes.guess_type(local_file_path)
        headers = {'Content-Type': content_type or 'application/octet-stream'} # Default if type unknown

        print(f"Uploading '{local_file_path}' to '{url}' as type '{headers['Content-Type']}'...")

        try:
            with open(local_file_path, 'rb') as file_data:
                response = self.session.put(
                    url,
                    headers=headers,
                    data=file_data,
                    auth=self.auth
                )
            self._handle_response(response, success_codes=(200, 201, 204)) # 201 Created, 204 No Content (Overwrite)
            print("File uploaded successfully!")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to upload file. Error: {e}")
            if e.response is not None:
                 print(f"Response status: {e.response.status_code}")
                 print(f"Response text: {e.response.text}")
            raise # Re-raise the exception for the caller to handle

    def create_directory(self, remote_path):
        """
        Creates a directory (collection) at the specified path on Nextcloud.

        Args:
            remote_path (str): The path for the new directory (e.g., '/new_folder/sub_folder').

        Returns:
            bool: True if the directory was created successfully or already exists.

        Raises:
            requests.exceptions.RequestException: For network or API errors (excluding 405).
        """
        # Ensure remote_path ends with a slash for MKCOL if it's not just '/'
        if remote_path != '/' and not remote_path.endswith('/'):
            url_path = remote_path + '/'
        else:
            url_path = remote_path
        url = self._build_url(url_path)

        print(f"Attempting to create directory at '{url}'...")
        try:
            # MKCOL request has no body
            response = self.session.request("MKCOL", url, auth=self.auth)

            # Check for success or if it already exists
            if response.status_code == 201:
                print("Directory created successfully!")
                return True
            elif response.status_code == 405: # Method Not Allowed typically means it exists
                 print(f"Directory '{remote_path}' might already exist (Status 405). Assuming success.")
                 # You could add a PROPFIND here to be absolutely sure, but often 405 is sufficient indication.
                 return True
            else:
                # Handle other unexpected errors
                self._handle_response(response, success_codes=(201, 405)) # Will raise error if not 201 or 405

        except requests.exceptions.RequestException as e:
            print(f"Failed to create directory. Error: {e}")
            if e.response is not None:
                 print(f"Response status: {e.response.status_code}")
                 print(f"Response text: {e.response.text}")
            raise # Re-raise the exception

    def list_directory(self, remote_path):
        """
        Lists the contents of a directory on Nextcloud.

        Args:
            remote_path (str): The path of the directory to list (e.g., '/documents').

        Returns:
            list: A list of dictionaries, each representing a file or directory.
                  Returns an empty list if the directory is empty or not found.
                  Example item: {'href': '/remote.php/dav/files/user/docs/file.txt', 'name': 'file.txt', 'is_dir': False}

        Raises:
            requests.exceptions.RequestException: For network or API errors (excluding 404).
            ET.ParseError: If the XML response from Nextcloud is invalid.
        """
        url = self._build_url(remote_path)
        headers = {'Depth': '1'} # Get immediate children
        print(f"Listing directory contents for '{url}'...")
        try:
            response = self.session.request("PROPFIND", url, headers=headers, auth=self.auth)
            # Allow 404 Not Found as a non-error case (just return empty list)
            if response.status_code == 404:
                print(f"Directory not found: {remote_path}")
                return []
            # Handle other responses
            self._handle_response(response, success_codes=(207,)) # 207 Multi-Status is expected success

            # Parse the XML response
            root = ET.fromstring(response.content)
            namespace = {'d': 'DAV:'} # DAV namespace
            items = []

            # Construct the base path expected in hrefs for comparison
            normalized_remote_path = remote_path.strip('/')
            # Handle root directory case
            if normalized_remote_path:
                 base_href_path_check = f"{self.dav_base_path}/{normalized_remote_path}"
            else:
                 base_href_path_check = f"{self.dav_base_path}"


            for resp_element in root.findall('d:response', namespace):
                href_element = resp_element.find('d:href', namespace)
                propstat_element = resp_element.find('d:propstat', namespace)

                if href_element is None or propstat_element is None:
                    print("Skipping response element missing href or propstat.")
                    continue

                # Decode URL-encoded href before processing
                try:
                    from urllib.parse import unquote
                    href = unquote(href_element.text)
                except Exception as decode_err:
                    print(f"Warning: Could not decode href '{href_element.text}'. Skipping. Error: {decode_err}")
                    continue

                # Skip the entry for the directory itself more reliably
                # Compare the decoded href (stripping trailing slash) with the expected base path
                if href.rstrip('/') == base_href_path_check:
                    # print(f"Skipping self-entry: {href}") # Debug print
                    continue

                # Extract name from the last part of the href path
                name = href.rstrip('/').split('/')[-1]

                # Check if it's a directory (collection)
                is_dir = False
                prop_element = propstat_element.find('d:prop', namespace)
                if prop_element is not None:
                    resourcetype_element = prop_element.find('d:resourcetype', namespace)
                    if resourcetype_element is not None and resourcetype_element.find('d:collection', namespace) is not None:
                        is_dir = True

                items.append({'href': href, 'name': name, 'is_dir': is_dir})

            print(f"Found {len(items)} items in '{remote_path}'.")
            return items

        except ET.ParseError as e:
            print(f"Failed to parse XML response from PROPFIND: {e}")
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
            raise # Re-raise as it indicates an issue with the server response or parsing logic
        except requests.exceptions.RequestException as e:
            # We already handled 404 above, so other request exceptions are errors
            print(f"Failed to list directory. Error: {e}")
            if e.response is not None:
                 print(f"Response status: {e.response.status_code}")
                 print(f"Response text: {e.response.text}")
            raise # Re-raise the exception


    def delete(self, remote_path):
        """
        Deletes a file or directory at the specified path on Nextcloud.

        Args:
            remote_path (str): The path of the file or directory to delete (e.g., '/uploads/old_file.txt').

        Returns:
            bool: True if the deletion was successful. Returns False if the item was not found (404).

        Raises:
            requests.exceptions.RequestException: For network or API errors (excluding 404).
        """
        url = self._build_url(remote_path)
        print(f"Attempting to delete item at '{url}'...")
        try:
            response = self.session.delete(url, auth=self.auth)
            # 204 No Content is success for DELETE
            # 404 Not Found means it's already gone, consider it success in terms of state
            if response.status_code == 404:
                print(f"Item not found at '{remote_path}', cannot delete (already gone?).")
                return False # Indicate item was not found to delete
            # Handle other responses
            self._handle_response(response, success_codes=(204,)) # Only 204 is true success
            print("Item deleted successfully!")
            return True
        except requests.exceptions.RequestException as e:
             # We handled 404 explicitly, raise other errors
             print(f"Failed to delete item. Error: {e}")
             if e.response is not None:
                 print(f"Response status: {e.response.status_code}")
                 print(f"Response text: {e.response.text}")
             raise # Re-raise the exception


# --- Example Usage ---
if __name__ == "__main__":
    print(f"Connecting to Nextcloud at: {NEXTCLOUD_URL} as user: {USERNAME}")
    # Create a client instance
    try:
        client = NextcloudClient(NEXTCLOUD_URL, USERNAME, PASSWORD)
    except ValueError as e:
        print(f"Configuration Error: {e}")
        exit(1)

    # --- Test Variables ---
    # Create a dummy file for testing
    local_test_file = 'test_upload.txt'
    try:
        with open(local_test_file, 'w') as f:
            f.write("This is a test file for Nextcloud upload.\n")
            f.write(f"Uploaded by {USERNAME} using enhanced script.\n")
        print(f"Created local test file: {local_test_file}")
    except IOError as e:
        print(f"Error creating local test file: {e}")
        exit(1)


    # Use a path relative to the user's root
    remote_base_dir = '/my_django_uploads_test' # Use a distinct name for testing
    remote_text_file_path = f'{remote_base_dir}/{os.path.basename(local_test_file)}'

    # Example video file path (replace with your actual file if testing video)
    local_video_path = 'tekkenClone - map1 - Windows, Mac, Linux - Unity 2022.1.24f1 _DX11_ 4_7_2025 11_27_47 AM.png' # Keep your video path
    remote_video_file_path = f'{remote_base_dir}/cool_sonic_video_test.mp4' # Give it a new name on the server


    # --- Operations ---
    try:
        # 1. Create the base directory
        print(f"\n--- 1. Creating Directory: {remote_base_dir} ---")
        client.create_directory(remote_base_dir)

        # 2. Upload the text file
        print(f"\n--- 2. Uploading Text File: {local_test_file} to {remote_text_file_path} ---")
        client.upload_file(local_test_file, remote_text_file_path)

        # 3. Upload the video file (if it exists locally)
        print(f"\n--- 3. Uploading Video File (if exists): {local_video_path} to {remote_video_file_path} ---")
        if not os.path.exists(local_video_path):
             print(f"Local video file '{local_video_path}' not found. Skipping video upload test.")
        else:
            client.upload_file(local_video_path, remote_video_file_path)

        # 4. List the directory contents
        print(f"\n--- 4. Listing Directory: {remote_base_dir} ---")
        items = client.list_directory(remote_base_dir)
        if items:
            print(f"Contents of '{remote_base_dir}':")
            for item in items:
                item_type = "Directory" if item['is_dir'] else "File"
                # Decode name for printing if necessary (though it should be decoded by list_directory)
                print(f"- {item['name']} ({item_type})")
        else:
            print(f"Directory '{remote_base_dir}' is empty or could not be listed.")

        # 5. Delete the text file
        print(f"\n--- 5. Deleting Text File: {remote_text_file_path} ---")
        deleted_text = client.delete(remote_text_file_path)
        print(f"Deletion successful: {deleted_text}")


        # 6. List again to confirm deletion
        print(f"\n--- 6. Listing Directory Again: {remote_base_dir} ---")
        items = client.list_directory(remote_base_dir)
        if items:
            print(f"Contents of '{remote_base_dir}' after text file deletion:")
            for item in items:
                item_type = "Directory" if item['is_dir'] else "File"
                print(f"- {item['name']} ({item_type})")
        else:
            print(f"Directory '{remote_base_dir}' is empty or could not be listed.")

        # 7. Delete the video file (if it was uploaded)
        if os.path.exists(local_video_path):
             print(f"\n--- 7. Deleting Video File: {remote_video_file_path} ---")
             deleted_video = client.delete(remote_video_file_path)
             print(f"Deletion successful: {deleted_video}")


        # 8. Delete the base directory (optional cleanup)
        print(f"\n--- 8. Deleting Base Directory: {remote_base_dir} ---")
        deleted_dir = client.delete(remote_base_dir)
        print(f"Deletion successful: {deleted_dir}")


    except FileNotFoundError as e:
        print(f"\nOperation Error: Local file not found. {e}")
    except requests.exceptions.ConnectionError as e:
         print(f"\nConnection Error: Could not connect to Nextcloud at {NEXTCLOUD_URL}.")
         print("Please check:")
         print(f"  1. Is the URL '{NEXTCLOUD_URL}' correct?")
         print(f"  2. Is your Nextcloud instance running and accessible from this machine?")
         print(f"  3. Is there a firewall blocking the connection?")
         # The proxy error should be less likely now, but keep the check
         if "ProxyError" in str(e):
              print(f"  4. A proxy might still be interfering despite attempts to disable it.")
         print(f"Details: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: An API request failed.")
        if e.response is not None:
            if e.response.status_code == 401:
                print("Authentication failed (401 Unauthorized). Please check your USERNAME and PASSWORD/App Token.")
            elif e.response.status_code == 404:
                 print("Resource not found (404). Check if the path exists or if there's a typo.")
            else:
                print(f"Status Code: {e.response.status_code}")
                print(f"Response: {e.response.text}") # Already printed in _handle_response but good to have here too
        else:
             print(f"HTTP Error Details: {e}")
    except requests.exceptions.RequestException as e:
        print(f"\nRequest Error: An unexpected error occurred during the request.")
        print(f"Error: {e}")
    except ET.ParseError as e:
        print(f"\nXML Parsing Error: Could not parse the response from Nextcloud (likely from LIST/PROPFIND).")
        print(f"Error: {e}")
    except Exception as e:
        # Catch any other unexpected errors
        import traceback
        print(f"\nAn Unexpected Error Occurred:")
        print(traceback.format_exc()) # Print full traceback for debugging

    finally:
        # Clean up the local dummy file
        if os.path.exists(local_test_file):
            try:
                os.remove(local_test_file)
                print(f"\nCleaned up local file: {local_test_file}")
            except OSError as e:
                 print(f"\nWarning: Could not clean up local file '{local_test_file}'. Error: {e}")

