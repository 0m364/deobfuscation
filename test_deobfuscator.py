import unittest
import base64
import binascii
import zlib
import gzip
import bz2
import lzma
import io
import os
from deobfuscate import Deobfuscator

class TestDeobfuscator(unittest.TestCase):
    def test_base64(self):
        original = b"Hello World"
        encoded = base64.b64encode(original)
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, original)
        self.assertIn("Base64", deobfuscator.layers)

    def test_hex(self):
        original = b"Hello World"
        encoded = binascii.hexlify(original)
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, original)
        self.assertIn("Hex", deobfuscator.layers)

    def test_hex_escaped(self):
        encoded = b"\\x48\\x65\\x6c\\x6c\\x6f" # Hello
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, b"Hello")
        self.assertIn("Hex Escaped", deobfuscator.layers)

    def test_octal_escaped(self):
        encoded = b"\\101\\102\\103" # ABC
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, b"ABC")
        self.assertIn("Octal Escaped", deobfuscator.layers)

    def test_url_encoding(self):
        encoded = b"Hello%20World"
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, b"Hello World")
        self.assertIn("URL Encoding", deobfuscator.layers)

    def test_binary(self):
        encoded = b"01000001 01000010 01000011" # ABC
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, b"ABC")
        self.assertIn("Binary", deobfuscator.layers)

    def test_zlib(self):
        original = b"Hello World repeated " * 10
        encoded = zlib.compress(original)
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, original)
        self.assertIn("Zlib", deobfuscator.layers)

    def test_gzip(self):
        original = b"Hello World repeated " * 10
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode='wb') as f:
            f.write(original)
        encoded = out.getvalue()
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, original)
        self.assertIn("Gzip", deobfuscator.layers)

    def test_bzip2(self):
        original = b"Hello World repeated " * 10
        encoded = bz2.compress(original)
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, original)
        self.assertIn("Bzip2", deobfuscator.layers)

    def test_lzma(self):
        original = b"Hello World repeated " * 10
        encoded = lzma.compress(original)
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, original)
        self.assertIn("LZMA", deobfuscator.layers)

    def test_rot13(self):
        original = b"Hello World"
        encoded = b"Uryyb Jbeyq" # ROT13 of Hello World
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, original)
        self.assertIn("ROT13", deobfuscator.layers)

    def test_reverse(self):
        original = b"Hello World"
        encoded = b"dlroW olleH"
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, original)
        self.assertIn("Reverse", deobfuscator.layers)

    def test_xor(self):
        original = b"Hello World"
        key = 0x42
        encoded = bytes([b ^ key for b in original])
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, original)
        self.assertIn("XOR", deobfuscator.layers)

    def test_stealth_zero_width(self):
        encoded = "Hello\u200bWorld".encode('utf-8')
        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, b"HelloWorld")
        self.assertIn("Stealth Cleanup", deobfuscator.layers)

    def test_nested(self):
        # Nested: Base64 -> Hex -> Gzip -> "Hello World"
        original = b"Hello World" * 5

        # Gzip
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode='wb') as f:
            f.write(original)
        step1 = out.getvalue()

        # Hex
        step2 = binascii.hexlify(step1)

        # Base64
        encoded = base64.b64encode(step2)

        deobfuscator = Deobfuscator(encoded)
        result = deobfuscator.deobfuscate()
        self.assertEqual(result, original)
        self.assertIn("Base64", deobfuscator.layers)
        self.assertIn("Hex", deobfuscator.layers)
        self.assertIn("Gzip", deobfuscator.layers)

if __name__ == '__main__':
    unittest.main()
