from cryptography.fernet import Fernet
key = Fernet.generate_key()
f = Fernet(key)
encrypted = f.encrypt(open(".env", "rb").read())
with open(".env.enc", "wb") as out:
    out.write(encrypted)
print(key.decode())  # 🔑 Save this securely! You’ll paste this at runtime.