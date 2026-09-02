from minio import Minio
from minio.error import S3Error

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

BUCKETS = ["bronze", "silver", "gold"]

def setup_buckets():
    print("=" * 40)
    print("SETUP MINIO BUCKETS")
    print("=" * 40)

    for bucket in BUCKETS:
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                print(f"OK Bucket '{bucket}' cree")
            else:
                print(f"-> Bucket '{bucket}' existe deja")
        except S3Error as e:
            print(f"ERREUR pour '{bucket}' : {e}")

    print("\nBuckets disponibles :")
    for b in client.list_buckets():
        print(f"  - {b.name}")

    print("\nSETUP TERMINE")

if __name__ == "__main__":
    setup_buckets()