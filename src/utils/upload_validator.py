# Upload Validator
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_TYPES = ["image/png", "image/jpeg"]

def validate_upload(file):
    if file.size > MAX_FILE_SIZE:
        raise ValueError("File exceeds 5MB limit")
