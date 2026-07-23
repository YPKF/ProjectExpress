# Auth Middleware
def require_auth(handler):
    async def wrapper(request):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not validate_token(token):
            return Response(status=401)
        return await handler(request)
    return wrapper
