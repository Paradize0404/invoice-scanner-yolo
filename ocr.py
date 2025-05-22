import base64
import json
import os
import requests
import cv2
import uuid


def preprocess_image(path: str) -> str:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.equalizeHist(img)
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_path = f"/tmp/{uuid.uuid4().hex}_processed.jpg"
    cv2.imwrite(processed_path, thresh)
    return processed_path


def get_iam_token_from_json() -> str:
    service_account_json = os.environ["YANDEX_AUTHORIZED_KEY_JSON"]
    sa = json.loads(service_account_json)

    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    response = requests.post(url, json={"yandexPassportOauthToken": None, "jwt": None}, data={
        "service_account_id": sa["service_account_id"],
        "key_id": sa["id"],
        "private_key": sa["private_key"]
    })

    if response.status_code != 200:
        raise Exception(f"Ошибка получения IAM-токена: {response.text}")

    return response.json()["iamToken"]


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
            "analyze_specs": [{
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
        return result["results"][0]["results"][0]["textDetection"]["pages"][0]["blocks"][0]["lines"][0]["text"]

    except Exception as e:
        return f"[Ошибка OCR: {e}]"

    finally:
        if os.path.exists(processed_image_path):
            os.remove(processed_image_path)
