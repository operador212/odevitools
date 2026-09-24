from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid

app = FastAPI(title="ODEVI+ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://odevitools.com",
        "https://www.odevitools.com",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "/tmp/odevi_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class DownloadRequest(BaseModel):
    url: str
    format: str = "mp4"


@app.get("/")
def home():
    return {
        "status": "online",
        "service": "ODEVI+",
    }


@app.post("/download")
def download_media(request: DownloadRequest):

    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL inválida.")

    if request.format not in ["mp4", "mp3"]:
        raise HTTPException(
            status_code=400,
            detail="Formato deve ser mp4 ou mp3."
        )

    file_id = str(uuid.uuid4())

    output_template = os.path.join(
        DOWNLOAD_DIR,
        f"{file_id}.%(ext)s"
    )

    # Primeira versão: YouTube
    allowed_hosts = (
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "www.youtube-nocookie.com",
    )

    if not any(host in request.url.lower() for host in allowed_hosts):
        raise HTTPException(
            status_code=400,
            detail="Nesta primeira versão, use um link do YouTube."
        )

    if request.format == "mp3":
        options = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "noplaylist": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
    else:
        options = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": output_template,
            "merge_output_format": "mp4",
            "noplaylist": True,
        }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                request.url,
                download=True
            )

        title = info.get("title", "ODEVI Download")

        if request.format == "mp3":
            filename = f"{file_id}.mp3"
            media_type = "audio/mpeg"
        else:
            filename = f"{file_id}.mp4"
            media_type = "video/mp4"

        filepath = os.path.join(
            DOWNLOAD_DIR,
            filename
        )

        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=500,
                detail="O arquivo não foi criado."
            )

        safe_title = "".join(
            c for c in title
            if c.isalnum() or c in " -_"
        ).strip()

        return FileResponse(
            filepath,
            media_type=media_type,
            filename=f"{safe_title}.{request.format}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no processamento: {str(e)}"
        )
