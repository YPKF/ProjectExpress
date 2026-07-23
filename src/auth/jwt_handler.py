# JWT Token Handler
from datetime import timedelta

ACCESS_TOKEN_EXPIRY = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRY = timedelta(days=7)

def create_token_pair(user_id):
    access = create_access_token(user_id, ACCESS_TOKEN_EXPIRY)
    refresh = create_refresh_token(user_id, REFRESH_TOKEN_EXPIRY)
    return access, refresh
