from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from ultralytics import YOLO
import io
from PIL import Image
import torch

app = FastAPI(title="YOLOv8 Inference API")

# Load your model ONCE at startup
model = YOLO("models/best.pt")  # make sure this path is correct

@app.post("/detect/")
async def detect(file: UploadFile = File(...), conf: float = 0.25, imgsz: int = 640):
    """Accepts an image file, returns an image with boxes drawn."""
    # Validate inputs
    if conf <= 0 or conf >= 1:
        raise HTTPException(status_code=400, detail="conf must be between 0 and 1")
    if imgsz % 32 != 0:
        raise HTTPException(status_code=400, detail="imgsz must be multiple of 32")

    # Read image bytes
    img_bytes = await file.read()
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # Run inference
    results = model.predict(
        source=pil_img,
        conf=conf,
        imgsz=imgsz,
        stream=False  # batch of one, synchronous
    )

    # Take the first result (since we passed a single image)
    annotated = results[0].plot()  # returns a NumPy array (H, W, 3)

    # Convert back to bytes
    annotated_pil = Image.fromarray(annotated)
    buf = io.BytesIO()
    annotated_pil.save(buf, format="JPEG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/jpeg")

@app.get("/")
def root():
    return {"message": "YOLOv8 FastAPI is up and running!"}
