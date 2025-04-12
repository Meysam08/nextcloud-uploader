

# Nextcloud Uploader API

A simple RESTful API built with **FastAPI** that allows you to upload files to a Nextcloud instance. It can integrate seamlessly with other services (like a Django backend) or operate as a standalone file storage tool.

---

## 🚀 Features

- **File Uploads:** Easily upload files (e.g., videos, documents) directly to Nextcloud.
- **Custom Destination Paths:** Specify your target directory within Nextcloud.
- **Secure Access:** Authentication is managed via environment variables.
- **Lightweight & Clean:** Developed with FastAPI for a straightforward, performant experience.

---

## 📦 Requirements

- Python **3.9** or newer
- A running Nextcloud instance
- Valid Nextcloud credentials:
  - **Username**
  - **App password** (recommended for enhanced security)
- **Docker** (optional, for containerized deployment)

---

## 🔧 Setup

### 1. Clone the Repository

Clone the repository and change to the project directory:

```bash
git clone https://github.com/Meysam08/nextcloud-uploader.git
cd nextcloud-uploader
```

### 2. Create Environment File

In the root directory, create a file named `.env` with the following variables:

```ini
NEXTCLOUD_URL=https://your-nextcloud-instance.com
NEXTCLOUD_USERNAME=your_username
NEXTCLOUD_PASSWORD=your_app_password
```

> **Tip:** Use an App Password for better security.

### 3. Install Dependencies

Install the required packages (if you're not using Docker):

```bash
pip install -r requirements.txt
```

### 4. Run the API

Start the FastAPI server with:

```bash
uvicorn main:app --reload
```

---

## 🐳 Running with Docker

If you prefer to use Docker:

1. **Build the Docker Image:**

   ```bash
   docker build -t nextcloud-uploader .
   ```

2. **Run the Container:**

   ```bash
   docker run --env-file .env -p 8000:8000 nextcloud-uploader
   ```

---

## 🔁 API Usage

### Endpoint

**POST** `/upload/`

Uploads a file to your Nextcloud folder.

### Request Details

- **Headers:** `Content-Type: multipart/form-data`
- **Body Parameters:**
  - `file`: The file to upload.
  - `folder` (optional): Target folder path (defaults to `/` if not specified).

### Example Using curl

```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@video.mp4" \
  -F "folder=/videos"
```

### Expected Response

```json
{
  "status": "success",
  "file_url": "https://your-nextcloud.com/remote.php/dav/files/user/videos/video.mp4"
}
```

---

## 📁 Folder Structure

```
nextcloud-uploader/
├── main.py              # Main FastAPI app
├── uploader.py          # File upload logic
├── .env.example         # Sample environment configuration file
├── requirements.txt     # Python dependencies list
├── Dockerfile           # Docker build configuration
└── README.md            # Project documentation
```

---

## 🤝 Contribution

Contributions are welcome! Feel free to fork the repository, modify the code, or suggest improvements. For issues, feature requests, or pull requests, please refer to the [GitHub issues](https://github.com/Meysam08/nextcloud-uploader/issues) section.

---

## 📜 License

This project is licensed under the **MIT License** – see the [LICENSE](./LICENSE) file for details.

---

## 📬 Contact

Created by **Meysam Kheyrollahie**  
Email: [wwwmeysam08@gmail.com](mailto:wwwmeysam08@gmail.com)  
GitHub Profile: [Meysam08](https://github.com/Meysam08)

