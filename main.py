import os
from dotenv import load_dotenv

# Detect the environment (default: development)
load_dotenv(".env")

print(f"Running in {os.getenv('ENV')} mode")
print(f"Debug Mode: {os.getenv('DEBUG')}")
