# utils/paystack.py
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class PaystackAPI:
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.base_url = "https://api.paystack.co"

    def initialize_payment(self, email, amount, reference, callback_url=None):
        try:
            url = f"{self.base_url}/transaction/initialize"
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            # Ensure amount is an integer (kobo)
            amount = int(amount)
            
            payload = {
                "email": email,
                "amount": amount,  # Amount is already in kobo
                "reference": reference,
                "callback_url": callback_url
            }

            logger.info(f"Initializing payment with payload: {payload}")
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment initialization failed: {str(e)}")
            return {"status": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during payment initialization: {str(e)}")
            return {"status": False, "message": "An unexpected error occurred"}

    def verify_payment(self, reference):
        try:
            url = f"{self.base_url}/transaction/verify/{reference}"
            headers = {
                "Authorization": f"Bearer {self.secret_key}"
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment verification failed: {str(e)}")
            return {"status": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            return {"status": False, "message": "An unexpected error occurred"}