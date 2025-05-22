import requests
import base64
import cv2
from PIL import Image
import numpy as np

def preprocess_image(path: str) -> str:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.equalizeHist(img)
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    processed_path = path.replace(".jpg", "_processed.jpg").replace(".jpeg", "_processed.jpg").replace(".png", "_processed.jpg")
    cv2.imwrite(processed_path, thresh)
    return processed_path

def get_text_from_yandex(image_path, iam_token, folder_id):
    processed_image_path = preprocess_image(image_path)

    with open(processed_image_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode("utf-8")

    url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
    headers = {"Authorization": f"Bearer {iam_token}"}
    body = {
        "folderId": folder_id,
        "analyze_specs": [{
            "content": encoded_image,
            "features": [{"type": "TEXT_DETECTION", "text_detection_config": {"language_codes": ["ru"]}}]
        }]
    }

    response = requests.post(url, headers=headers, json=body)
    result = response.json()

    try:
        return result["results"][0]["results"][0]["textDetection"]["pages"][0]["blocks"][0]["lines"][0]["text"]
    except Exception:
        return "[Ошибка чтения OCR]"
