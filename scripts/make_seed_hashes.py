# Plain-English description: This script generates Argon2id password hashes for local dev seed users.

from argon2 import PasswordHasher
from argon2.profiles import RFC_9106_LOW_MEMORY

def generate_dev_hashes():
    # Use standard Argon2id hasher
    ph = PasswordHasher.from_parameters(RFC_9106_LOW_MEMORY)

    creator_password = "CreatorDevPassword123!"
    admin_password = "AdminDevPassword123!"

    creator_hash = ph.hash(creator_password)
    admin_hash = ph.hash(admin_password)

    print("--- DEV PASSWORDS & ARGON2ID HASHES ---")
    print(f"Creator Email: creator@vibecheck.test")
    print(f"Creator Password: {creator_password}")
    print(f"Creator Hash: {creator_hash}\n")

    print(f"Admin Email: admin@vibecheck.test")
    print(f"Admin Password: {admin_password}")
    print(f"Admin Hash: {admin_hash}\n")

if __name__ == "__main__":
    generate_dev_hashes()

