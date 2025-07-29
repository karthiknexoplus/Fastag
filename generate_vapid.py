from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

private_key = ec.generate_private_key(ec.SECP256R1())
private_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
public_key = private_key.public_key()
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
# VAPID keys in base64url format
def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=') .decode('utf-8')

# Save private key
with open('vapid_private.pem', 'w') as f:
    f.write(private_bytes.decode())
# Save public key
with open('vapid_public.txt', 'w') as f:
    f.write(b64url(public_bytes))

print('VAPID keys generated and saved to vapid_private.pem and vapid_public.txt') 