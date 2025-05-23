import base64
import json
import os
import requests
import cv2
import uuid



print(json.loads(os.environ["YANDEX_VISION_CREDENTIALS_JSON"]))

def get_iam_token_from_json() -> str:
    key = json.loads(os.environ["YANDEX_VISION_CREDENTIALS_JSON"])

    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    headers = {"Content-Type": "application/json"}
    payload = {
        "service_account_id": key["service_account_id"],
        "key_id": key["id"],
        "private_key": key["private_key"]
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Ошибка получения IAM-токена: {response.text}")

    return response.json()["iamToken"]


def preprocess_image(path: str) -> str:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.equalizeHist(img)
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_path = f"/tmp/{uuid.uuid4().hex}_processed.jpg"
    cv2.imwrite(processed_path, thresh)
    return processed_path


def get_text_from_yandex(image_path: str, folder_id: str) -> str:
    processed_image_path = preprocess_image(image_path)

    try:
        with open(processed_image_path, "rb") as f:
            encoded_image = base64.b64encode(f.read()).decode("utf-8")

        iam_token = get_iam_token_from_json()

        headers = {
            "Authorization": f"Bearer {iam_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "folderId": folder_id,
            "analyze_specs": [ {
                "content": encoded_image,
                "features": [{
                    "type": "TEXT_DETECTION",
                    "text_detection_config": {
                        "language_codes": ["ru"]
                    }
                }]
            }]
        }

        url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        blocks = result["results"][0]["results"][0]["textDetection"]["pages"][0].get("blocks", [])
        lines = [line["text"] for block in blocks for line in block.get("lines", [])]

        if not lines:
            raise Exception("OCR не вернул ни одной строки")

        return "\n".join(lines)

    except Exception as e:
        return f"[Ошибка OCR: {e}]"

    finally:
        if os.path.exists(processed_image_path):
            os.remove(processed_image_path)
