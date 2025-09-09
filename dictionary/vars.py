from dotenv import load_dotenv
import os


load_dotenv()

API_HOST = os.getenv('DJANGO_API_URL')

API_BASE_URL = f"{API_HOST}/api/v1"
TOKEN_URL = f"{API_BASE_URL}/authentication/token/"

ABSOLUTE_APP_PATH = os.getcwd()

SERVER_CONFIG = """
[server]
headless = true
enableStaticServing = true"""

lorem_ipsum = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n
Maecenas a tincidunt justo. Mauris imperdiet ultricies libero semper mollis.\n
Ut feugiat rhoncus odio id commodo.
"""

C0NFIG_FILE_PATH: str = ".streamlit/config.toml"

PLATFORMS = {
    "FCB": "Facebook",
    "TTK": "Tiktok",
    "INT": "Instagram",
    "LKN": "Linkedin"
}
