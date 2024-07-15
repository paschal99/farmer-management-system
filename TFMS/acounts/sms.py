import os
from BeemAfrica import SMS  # Import the SMS class directly
from BeemAfrica import Authorize
from dotenv import load_dotenv

load_dotenv()


def send_sms(recipients, message):
    Authorize(os.getenv("BEEM_API_KEY"), os.getenv("SECRET_KEY"))
    return SMS.send_sms(message, recipients, sender_id='INFO')