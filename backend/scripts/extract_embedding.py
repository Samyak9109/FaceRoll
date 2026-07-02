import argparse
import json
from pathlib import Path

from app.services.face_embedder import face_embedder


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a FaceNet 512-d embedding from an image.")
    parser.add_argument("image", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    embedding = face_embedder.extract_from_bytes(args.image.read_bytes())
    payload = {"image": str(args.image), "dimensions": len(embedding), "embedding": embedding}
    if args.out:
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
