import secrets

'''Generating Secret Key for JWT_SECRET_KEY'''
jwt_secret_key = secrets.token_urlsafe(32)
print(f"jwt_secret_key: {jwt_secret_key}")

'''Generating SECRET_KEY'''
secret_key = secrets.token_urlsafe(32)
print(f"secret_key: {secret_key}")
