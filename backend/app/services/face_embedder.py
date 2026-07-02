from io import BytesIO

import numpy as np
from PIL import Image


class FaceEmbeddingError(RuntimeError):
    pass


class FaceEmbedder:
    def __init__(self) -> None:
        self._mtcnn = None
        self._resnet = None
        self._torch = None

    def _load(self) -> None:
        if self._mtcnn is not None and self._resnet is not None:
            return
        try:
            import torch
            from facenet_pytorch import InceptionResnetV1, MTCNN
        except ImportError as exc:
            raise FaceEmbeddingError(
                "facenet-pytorch and torch are required for face embedding. Install backend requirements."
            ) from exc

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._torch = torch
        self._mtcnn = MTCNN(image_size=160, margin=20, keep_all=False, post_process=True, device=device)
        self._resnet = InceptionResnetV1(pretrained="vggface2").eval().to(device)

    def extract_from_bytes(self, image_bytes: bytes) -> list[float]:
        self._load()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        face = self._mtcnn(image)
        if face is None:
            raise FaceEmbeddingError("No face detected in image")
        with self._torch.no_grad():
            embedding = self._resnet(face.unsqueeze(0).to(next(self._resnet.parameters()).device))
        vector = embedding.squeeze(0).detach().cpu().numpy().astype(np.float32)
        norm = np.linalg.norm(vector)
        if norm == 0:
            raise FaceEmbeddingError("Invalid zero embedding")
        return (vector / norm).tolist()


face_embedder = FaceEmbedder()
