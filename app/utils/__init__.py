"""
Module for helper/utilities functions
"""
import hashlib
import random

CHAR_SAMPLE = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

def sha3_224(s: str) -> str:
    return hashlib.sha3_224(s.encode('utf-8')).hexdigest()

def hash_password(password: str) -> str:
	salt = ''.join([random.choice(CHAR_SAMPLE) for x in range(8)])
	return salt + sha3_224(salt + sha3_224(password))

def check_hashed_password(password: str, hashed_password: str) -> bool:
	salt = hashed_password[:8]
	return hashed_password == (salt + sha3_224(salt + sha3_224(password)))