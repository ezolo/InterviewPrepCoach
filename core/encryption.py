"""
Encryption utilities for secure API key storage
"""
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class Encryptor:
    """Handle encryption and decryption of sensitive data"""
    
    def __init__(self):
        encryption_key = os.getenv('ENCRYPTION_KEY')
        
        if not encryption_key:
            # Generate a key if not exists
            encryption_key = Fernet.generate_key().decode()
            print(f"[WARNING] No ENCRYPTION_KEY found. Generated new key: {encryption_key}")
            print("Please add this to your .env file as ENCRYPTION_KEY")
        
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self.cipher_suite = Fernet(encryption_key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return ""
        
        encrypted_bytes = self.cipher_suite.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt a string
        
        Args:
            encrypted_text: Encrypted string to decrypt
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted_text:
            return ""
        
        try:
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return ""

# Global encryptor instance
_encryptor = None

def get_encryptor() -> Encryptor:
    """Get singleton encryptor instance"""
    global _encryptor
    if _encryptor is None:
        _encryptor = Encryptor()
    return _encryptor

class Encryption:
    """Static wrapper for encryption operations"""
    
    @staticmethod
    def encrypt(plaintext: str) -> str:
        """Encrypt a string"""
        return get_encryptor().encrypt(plaintext)
    
    @staticmethod
    def decrypt(encrypted_text: str) -> str:
        """Decrypt a string"""
        return get_encryptor().decrypt(encrypted_text)
