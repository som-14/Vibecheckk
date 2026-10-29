# Plain-English description: This script generates an RSA keypair (private and public keys) for RS256 JWT signing and verification.

import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_rsa_keypair(output_dir="."):
    # Generate 2048-bit RSA private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Serialize private key to PEM format
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Serialize public key to PEM format
    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    priv_path = os.path.join(output_dir, "jwt_rs256.key")
    pub_path = os.path.join(output_dir, "jwt_rs256.key.pub")

    with open(priv_path, "wb") as f:
        f.write(pem_private)

    with open(pub_path, "wb") as f:
        f.write(pem_public)

    print("RSA Keypair generated successfully:")
    print(f"Private Key saved to: {priv_path}")
    print(f"Public Key saved to:  {pub_path}")
    print("\nIMPORTANT: Never commit jwt_rs256.key to version control!")

if __name__ == "__main__":
    generate_rsa_keypair()

