import os

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

from src.utils.logger import setup_logger

log = setup_logger("crypto")


def gen_keypair():
    priv = X25519PrivateKey.generate()
    pub = priv.public_key()
    pub_bytes = pub.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return priv, pub_bytes


def derive_shared_key(priv_key, peer_pub_bytes):
    peer_pub = X25519PublicKey.from_public_bytes(peer_pub_bytes)
    shared = priv_key.exchange(peer_pub)

    derived = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"rat-session-key",
    ).derive(shared)

    return derived


def encrypt_msg(key, plaintext):
    chacha = ChaCha20Poly1305(key)
    nonce = os.urandom(12)
    ct = chacha.encrypt(nonce, plaintext, None)
    return nonce + ct


def decrypt_msg(key, data):
    if len(data) < 12:
        raise ValueError("donnees trop courtes")
    nonce = data[:12]
    ct = data[12:]
    chacha = ChaCha20Poly1305(key)
    return chacha.decrypt(nonce, ct, None)
