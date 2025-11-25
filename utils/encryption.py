"""
Encryption utility for securing sensitive configuration data.
Uses Fernet (symmetric encryption) from cryptography library.
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialEncryption:
    """Handle encryption and decryption of sensitive credentials."""
    
    # This key is derived from application-specific data
    # In production, you could also use machine-specific data
    _APP_SALT = b'DuckyTrading_2025_Crypto_App_Salt_v1'
    
    @staticmethod
    def _get_encryption_key():
        """
        Generate encryption key from app-specific data.
        This uses a deterministic key so the app can decrypt without user input.
        """
        # Use app name and version as password base
        password = b'DuckyTrading_v1.0_Encryption_Key_2025'
        
        # Derive a key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=CredentialEncryption._APP_SALT,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    @staticmethod
    def encrypt_string(plaintext: str) -> str:
        """
        Encrypt a string and return base64 encoded ciphertext.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        if not plaintext:
            return ''
        
        key = CredentialEncryption._get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(plaintext.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def decrypt_string(ciphertext: str) -> str:
        """
        Decrypt a base64 encoded ciphertext and return plaintext.
        
        Args:
            ciphertext: Base64 encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ''
        
        try:
            key = CredentialEncryption._get_encryption_key()
            f = Fernet(key)
            encrypted = base64.b64decode(ciphertext.encode('utf-8'))
            decrypted = f.decrypt(encrypted)
            return decrypted.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials: {e}")
    
    @staticmethod
    def encrypt_file(input_path: str, output_path: str):
        """
        Encrypt an entire file.
        
        Args:
            input_path: Path to plaintext file
            output_path: Path to save encrypted file
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            plaintext = f.read()
        
        encrypted = CredentialEncryption.encrypt_string(plaintext)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(encrypted)
    
    @staticmethod
    def decrypt_file(input_path: str, output_path: str):
        """
        Decrypt an entire file.
        
        Args:
            input_path: Path to encrypted file
            output_path: Path to save decrypted file
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            ciphertext = f.read()
        
        plaintext = CredentialEncryption.decrypt_string(ciphertext)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(plaintext)


def test_encryption():
    """Test encryption/decryption functionality."""
    print("Testing encryption utility...")
    
    # Test string encryption
    original = "postgresql://user:password@host/db"
    print(f"\nOriginal: {original}")
    
    encrypted = CredentialEncryption.encrypt_string(original)
    print(f"Encrypted: {encrypted[:50]}...")
    
    decrypted = CredentialEncryption.decrypt_string(encrypted)
    print(f"Decrypted: {decrypted}")
    
    if original == decrypted:
        print("✅ Encryption test passed!")
    else:
        print("❌ Encryption test failed!")
    
    return original == decrypted


if __name__ == '__main__':
    test_encryption()
