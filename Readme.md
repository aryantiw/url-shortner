# URL Shortener Pro

A modern, user-friendly URL shortener application built with Python Flask and Firebase.

## Features

- Shorten long URLs to manageable links
- User-specific recent URLs tracking
- Modern, responsive UI with animations
- Copy to clipboard functionality
- Firebase integration for analytics and database

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Firebase configuration:
   ```
   FIREBASE_DATABASE_URL=your_firebase_database_url
   ```
4. Run the application:
   ```bash
   python url/url.py
   ```

## Deployment on Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the following settings:
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn url.url:app`
4. Add the following environment variables:
   - `FIREBASE_DATABASE_URL`: Your Firebase database URL
   - `PYTHON_VERSION`: 3.9.0

## Project Structure

```
url-shortener/
├── url/
│   ├── static/
│   │   └── indexer.html
│   └── url.py
├── render.yaml
├── requirements.txt
└── README.md
```

## Technologies Used

- Python Flask
- Firebase Realtime Database
- Gunicorn
- TailwindCSS
- Font Awesome