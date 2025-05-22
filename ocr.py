import base64
import cv2
import numpy as np
import os
from yandexcloud import SDK
from yandexcloud._auth import static_credentials

def preprocess_image(path: str) -> str:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.equalizeHist(img)
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_path = path.replace(".jpg", "_processed.jpg").replace(".jpeg", "_processed.jpg").replace(".png", "_processed.jpg")
    cv2.imwrite(processed_path, thresh)
    return processed_path

def get_text_from_yandex(image_path, folder_id):
    processed_image_path = preprocess_image(image_path)

    access_key = os.environ["YANDEX_VISION_ACCESS_KEY_ID"]
    secret_key = os.environ["YANDEX_VISION_SECRET_ACCESS_KEY"]

    sdk = SDK(authorizer=static_credentials.StaticCredentials(access_key, secret_key))
    client = sdk.client("vision")

    with open(processed_image_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode("utf-8")

    body = {
        "folderId": folder_id,
        "analyze_specs": [{
            "content": encoded_image,
            "features": [{
                "type": "TEXT_DETECTION",
                "text_detection_config": {"language_codes": ["ru"]}
            }]
        }]
    }

    try:
        result = client.batch_analyze(body)
        return result["results"][0]["results"][0]["textDetection"]["pages"][0]["blocks"][0]["lines"][0]["text"]
    except Exception:
        return "[Ошибка чтения OCR]"
    finally:
        if os.path.exists(processed_image_path):
            os.remove(processed_image_path)
