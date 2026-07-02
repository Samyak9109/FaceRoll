import { useEffect, useRef, useState } from "react";
import { Camera } from "lucide-react";

import { apiForm } from "../lib/api";

export function CameraPanel({ token, classId, onResult }) {
  const videoRef = useRef(null);
  const [status, setStatus] = useState("");

  useEffect(() => {
    let stream;
    navigator.mediaDevices?.getUserMedia({ video: true })
      .then((mediaStream) => {
        stream = mediaStream;
        if (videoRef.current) videoRef.current.srcObject = mediaStream;
      })
      .catch(() => setStatus("Camera permission is required."));

    return () => {
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  async function recognize() {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const context = canvas.getContext("2d");
    if (!context) {
      setStatus("Camera capture is unavailable in this browser.");
      return;
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
    if (!blob) {
      setStatus("Could not capture a camera frame.");
      return;
    }
    const form = new FormData();
    form.append("class_id", classId);
    form.append("frame", blob, "frame.jpg");

    try {
      setStatus("");
      onResult(await apiForm("/recognize", form, token));
    } catch (error) {
      setStatus(error.message);
    }
  }

  return (
    <section className="panel">
      <h2><Camera size={19} /> Live Recognition</h2>
      <video ref={videoRef} autoPlay playsInline muted />
      <button className="primary" onClick={recognize}>Recognize & mark</button>
      {status && <p className="error">{status}</p>}
    </section>
  );
}
