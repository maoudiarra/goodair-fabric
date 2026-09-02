from minio import Minio
import os
from dotenv import load_dotenv

load_dotenv()

def get_minio_client():
    # Dans Docker : utiliser le nom du service "minio"
    # En local (Anaconda) : utiliser "localhost"
    host = os.getenv("MINIO_HOST", "localhost:9000")
    
    return Minio(
        host,
        access_key=os.getenv("MINIO_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_PASSWORD", "minioadmin"),
        secure=False
    )