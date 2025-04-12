import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Import your Nextcloud client class from your module (adjust the import as needed)
from nextcloud_api import NextcloudClient

# Configuration – it is advisable to load these from environment variables.
NEXTCLOUD_URL = os.getenv('NEXTCLOUD_URL', 'http://localhost:8081')
USERNAME = os.getenv('NEXTCLOUD_USERNAME', 'Meysam08')
PASSWORD = os.getenv('NEXTCLOUD_PASSWORD', '12mm12mm')

# Initialize the Nextcloud client once and reuse it in your endpoints.
nc_client = NextcloudClient(NEXTCLOUD_URL, USERNAME, PASSWORD)

app = FastAPI(
    title="Nextcloud FastAPI Service",
    description="A service that wraps Nextcloud operations using FastAPI",
    version="1.0.0",
)

# Optionally add CORS middleware if your frontend needs to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Schemas for request bodies, if needed
class CreateDirectoryRequest(BaseModel):
    remote_path: str


class DeleteRequest(BaseModel):
    remote_path: str


# ---------------------------
# Endpoint: Create Directory
# ---------------------------
@app.post("/create-directory", response_model=dict)
def create_directory(request: CreateDirectoryRequest):
    try:
        success = nc_client.create_directory(request.remote_path)
        return {"message": f"Directory '{request.remote_path}' created or already exists.", "success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# Endpoint: Upload File
# ---------------------------
@app.post("/upload-file", response_model=dict)
async def upload_file(
        remote_path: str = Form(...),
        file: UploadFile = File(...)
):
    """
    Upload a file to the specified remote path in Nextcloud.
    The endpoint expects a form-data submission with:
      - remote_path: the destination path (including the filename)
      - file: the file to be uploaded
    """
    # Save the uploaded file to a temporary location
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)

        # Use Nextcloud client to upload the file
        success = nc_client.upload_file(temp_file_path, remote_path)
        if success:
            return {"message": f"File uploaded to {remote_path}", "success": success}
        else:
            raise HTTPException(status_code=500, detail="File upload failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Remove temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


# ---------------------------
# Endpoint: List Directory
# ---------------------------
@app.get("/list-directory", response_model=dict)
def list_directory(remote_path: str):
    """
    List the contents of the provided remote directory.
    Query Parameter:
      - remote_path: directory to list (e.g., /my_django_uploads_test)
    """
    try:
        items = nc_client.list_directory(remote_path)
        return {"remote_path": remote_path, "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# Endpoint: Delete Resource
# ---------------------------
@app.delete("/delete", response_model=dict)
def delete_resource(request: DeleteRequest):
    """
    Delete a file or directory at the specified remote path in Nextcloud.
    """
    try:
        success = nc_client.delete(request.remote_path)
        if success:
            return {"message": f"Resource at '{request.remote_path}' deleted.", "success": success}
        else:
            # If the delete function returns False, it means the resource was not found.
            return JSONResponse(status_code=404,
                                content={"message": f"Resource '{request.remote_path}' not found.", "success": False})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the application using uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
