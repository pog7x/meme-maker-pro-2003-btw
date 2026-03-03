# Meme Maker Pro 2003 BTW

<div align="center">
    <img src="https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Django-4.2.3-green?logo=django&logoColor=white" alt="Django">
    <img src="https://img.shields.io/badge/HTMX-1.27-orange" alt="HTMX">
</div>

A web application for creating memes with custom top/bottom text, built with Django and HTMX. Supports real-time sharing of memes to all connected users via Server-Sent Events (SSE).

---

## Features

- Upload an image (PNG, JPG, JPEG, WEBP) and add top/bottom text in classic meme style
- Live preview of the generated meme
- Download the finished meme in the original image format
- Share a meme with all currently connected users in real time via SSE
- Shared meme gallery visible to everyone on the index page

---

## Tech Stack

| Layer     | Technology                       |
| --------- | -------------------------------- |
| Backend   | Python 3.10, Django 4.2          |
| Frontend  | HTMX 1.x, Tailwind CSS (via CDN) |
| Images    | Pillow 10.x                      |
| Realtime  | Server-Sent Events (SSE)         |
| Container | Docker                           |

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) — for the containerised workflow
- Python 3.10+ and pip — for local development without Docker

---

## Quick Start (Docker)

**Build the image:**

```bash
docker build -t meme-maker .
```

**Run the container:**

```bash
docker run \
  -v $(pwd)/meme_maker_pro_2003_btw:/app/meme_maker_pro_2003_btw \
  -p 3228:3228 \
  -it meme-maker
```

Open [http://localhost:3228](http://localhost:3228) in your browser.

> The volume mount lets you edit source files on the host and see changes without rebuilding the image.

---

## Local Development

**1. Create and activate a virtual environment:**

```bash
python -m venv .venv
source .venv/bin/activate
```

**2. Install dependencies:**

```bash
pip install -r requirements.txt
```

**3. Create the shared images directory:**

```bash
mkdir -p static/shared
```

**4. Start the development server:**

```bash
python manage.py runserver 0.0.0.0:3228
```

Open [http://localhost:3228](http://localhost:3228) in your browser.

---

## Project Structure

```
meme-maker-pro-2003-btw/
├── meme_maker_pro_2003_btw/
│   ├── meme_text_renderer.py   # Pillow-based text drawing logic
│   ├── views.py                # Django views (IndexView, MemeView, StreamView, SSEBroker)
│   ├── urls.py                 # URL routing
│   └── settings.py
├── templates/
│   ├── base.html
│   ├── index.html              # Gallery of shared memes
│   └── meme.html               # Meme creation form & preview
├── static/
│   ├── css/
│   ├── fonts/                  # Impact font for meme text
│   ├── js/
│   └── shared/                 # Runtime directory — shared meme images are saved here
├── Dockerfile
├── manage.py
└── requirements.txt
```

---

## API Endpoints

| Method | Path    | Description                                                       |
| ------ | ------- | ----------------------------------------------------------------- |
| `GET`  | `/`     | Index page with shared meme gallery                               |
| `POST` | `/meme` | Generate a meme from an uploaded image; also handles share action |
| `GET`  | `/sse`  | SSE stream — pushes new shared memes to all connected clients     |

### POST `/meme` — form fields

| Field            | Type   | Required | Description                                    |
| ---------------- | ------ | -------- | ---------------------------------------------- |
| `upload_file`    | file   | yes\*    | Image file to use as the meme base             |
| `top_text`       | string | no       | Text rendered at the top of the image          |
| `bottom_text`    | string | no       | Text rendered at the bottom of the image       |
| `encoded_string` | string | yes\*\*  | Base64-encoded image used when sharing         |
| `file_ext`       | string | no       | Original file extension (`png`, `jpg`, `webp`) |
| `share`          | string | no       | Set to `"true"` to broadcast the meme via SSE  |

\* Required on the first upload call.  
\*\* Required when `share=true` (the client sends back the already-generated base64 image).
