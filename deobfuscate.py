import argparse
import sys
import os
import base64
import binascii
import urllib.parse
import re
import zlib
import gzip
import bz2
import lzma
import io
import string
import unicodedata
import math

class Deobfuscator:
    def __init__(self, content, verbose=False):
        self.content = content
        self.original_content = content
        self.layers = []
        self.verbose = verbose
        # Common keywords to detect successful deobfuscation
        self.keywords = [
            b'function', b'return', b'var ', b'let ', b'const ',
            b'eval(', b'exec(', b'system(', b'import ',
            b'<?php', b'<html>', b'<body>', b'<script',
            b'http://', b'https://', b'cmd.exe', b'powershell',
            b'socket', b'subprocess', b'base64',
            b'Hello World' # For testing
        ]

        self.indicators = {
            'Suspicious Functions': [b'eval', b'exec', b'system', b'popen', b'subprocess', b'spawn', b'win32', b'ctypes'],
            'Network': [b'socket', b'connect', b'bind', b'listen', b'http://', b'https://', b'ftp://', b'ws://'],
            'Obfuscation': [b'base64', b'rot13', b'xor', b'chr', b'ord', b'unhexlify'],
            'Shells': [b'cmd.exe', b'powershell', b'/bin/sh', b'/bin/bash', b'nc ', b'netcat']
        }

    def log(self, message):
        if self.verbose:
            print(f"[+] {message}")

    def is_text(self, data):
        try:
            text = data.decode('utf-8')
            printable = sum(1 for c in text if c in string.printable)
            return printable / len(text) > 0.9
        except:
            return False

    def contains_keywords(self, data):
        count = 0
        for keyword in self.keywords:
            if keyword in data:
                count += 1
        return count > 0

    # ... [Encoding Methods] ...
    def try_base64(self, data):
        try:
            s_data = data.strip()
            if not s_data: return None
            if len(s_data) % 4 != 0: return None
            if not re.match(rb'^[A-Za-z0-9+/=]+$', s_data): return None
            decoded = base64.b64decode(s_data, validate=True)
            if not decoded or decoded == data: return None
            return decoded
        except: return None

    def try_hex(self, data):
        try:
            s_data = data.strip()
            if not s_data: return None
            clean_data = re.sub(rb'\s+', b'', s_data)
            if not re.match(rb'^[0-9a-fA-F]+$', clean_data): return None
            if len(clean_data) % 2 != 0: return None
            decoded = binascii.unhexlify(clean_data)
            if not decoded or decoded == data: return None
            return decoded
        except: return None

    def try_hex_escaped(self, data):
        try:
            try: s_data = data.decode('utf-8')
            except: return None
            if '\\x' not in s_data: return None
            pattern = r'\\x([0-9a-fA-F]{2})'
            if not re.search(pattern, s_data): return None
            def replace_hex(match): return chr(int(match.group(1), 16))
            decoded_str = re.sub(pattern, replace_hex, s_data)
            if decoded_str == s_data: return None
            return decoded_str.encode('utf-8')
        except: return None

    def try_octal_escaped(self, data):
        try:
            try: s_data = data.decode('utf-8')
            except: return None
            if '\\' not in s_data: return None
            pattern = r'\\([0-7]{1,3})'
            if not re.search(pattern, s_data): return None
            def replace_octal(match):
                val = int(match.group(1), 8)
                return chr(val) if val < 256 else match.group(0)
            decoded_str = re.sub(pattern, replace_octal, s_data)
            if decoded_str == s_data: return None
            return decoded_str.encode('utf-8')
        except: return None

    def try_url_encoding(self, data):
        try:
            try: s_data = data.decode('utf-8')
            except: return None
            if '%' not in s_data: return None
            decoded_str = urllib.parse.unquote(s_data)
            if decoded_str == s_data: return None
            return decoded_str.encode('utf-8')
        except: return None

    def try_binary(self, data):
        try:
            s_data = data.strip()
            if not s_data: return None
            clean_data = re.sub(rb'\s+', b'', s_data)
            if not re.match(rb'^[01]+$', clean_data): return None
            if len(clean_data) % 8 != 0: return None
            byte_array = bytearray()
            for i in range(0, len(clean_data), 8):
                byte_chunk = clean_data[i:i+8]
                byte_array.append(int(byte_chunk, 2))
            return bytes(byte_array)
        except: return None

    # ... [Compression Methods] ...
    def try_zlib(self, data):
        try:
            decoded = zlib.decompress(data)
            if not decoded or decoded == data: return None
            return decoded
        except: return None

    def try_gzip(self, data):
        try:
            if not data.startswith(b'\x1f\x8b'): return None
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:
                decoded = f.read()
            if not decoded or decoded == data: return None
            return decoded
        except: return None

    def try_bzip2(self, data):
        try:
            if not data.startswith(b'BZh'): return None
            decoded = bz2.decompress(data)
            if not decoded or decoded == data: return None
            return decoded
        except: return None

    def try_lzma(self, data):
        try:
            decoded = lzma.decompress(data)
            if not decoded or decoded == data: return None
            return decoded
        except: return None

    # ... [Cipher Methods] ...
    def try_rot13(self, data):
        try:
            try: s_data = data.decode('utf-8')
            except: return None
            import codecs
            decoded_str = codecs.decode(s_data, 'rot_13')
            if decoded_str == s_data: return None
            res_data = decoded_str.encode('utf-8')
            if self.contains_keywords(res_data): return res_data
            return None
        except: return None

    def try_reverse(self, data):
        try:
            decoded = data[::-1]
            if decoded == data: return None
            if self.contains_keywords(decoded): return decoded
            return None
        except: return None

    def try_xor(self, data):
        for k in range(1, 256):
            xored = bytes([b ^ k for b in data])
            if self.contains_keywords(xored): return xored
        return None

    # ... [Stealth Methods] ...
    def try_stealth(self, data):
        try:
            try: s_data = data.decode('utf-8')
            except: return None
            original_s = s_data
            zero_width = ['\u200b', '\u200c', '\u200d', '\ufeff', '\u2060']
            for char in zero_width: s_data = s_data.replace(char, '')
            s_data = unicodedata.normalize('NFKC', s_data)
            if s_data != original_s: return s_data.encode('utf-8')
            return None
        except: return None

    def calculate_entropy(self, data):
        if not data: return 0
        entropy = 0
        for x in range(256):
            p_x = float(data.count(x))/len(data)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        return entropy

    def find_indicators(self, data):
        found = {}
        for category, patterns in self.indicators.items():
            for pattern in patterns:
                if pattern in data:
                    if category not in found: found[category] = []
                    found[category].append(pattern.decode('utf-8', errors='ignore'))
        
        # Regex for IPs and URLs
        try:
            s_data = data.decode('utf-8', errors='ignore')
            ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', s_data)
            if ips:
                if 'Network' not in found: found['Network'] = []
                found['Network'].extend(ips)

            urls = re.findall(r'https?://[^\s]+', s_data)
            if urls:
                if 'Network' not in found: found['Network'] = []
                found['Network'].extend(urls)
        except: pass

        return found

    def deobfuscate(self):
        current_content = self.content
        max_iterations = 50
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            found_layer = False

            methods = [
                (self.try_binary, "Binary"),
                (self.try_hex, "Hex"),
                (self.try_base64, "Base64"),
                (self.try_hex_escaped, "Hex Escaped"),
                (self.try_octal_escaped, "Octal Escaped"),
                (self.try_url_encoding, "URL Encoding"),
                (self.try_zlib, "Zlib"),
                (self.try_gzip, "Gzip"),
                (self.try_bzip2, "Bzip2"),
                (self.try_lzma, "LZMA"),
                (self.try_rot13, "ROT13"),
                (self.try_reverse, "Reverse"),
                (self.try_xor, "XOR"),
                (self.try_stealth, "Stealth Cleanup")
            ]

            for method, name in methods:
                result = method(current_content)
                if result and result != current_content:
                    if len(result) == 0: continue
                    self.log(f"Decoded {name}")
                    self.layers.append(name)
                    current_content = result
                    found_layer = True
                    break

            if not found_layer:
                break

        self.content = current_content
        return current_content

def main():
    parser = argparse.ArgumentParser(description="Advanced Deobfuscation Tool")
    parser.add_argument("input_file", help="Path to the file to deobfuscate")
    parser.add_argument("-o", "--output", help="Path to save the deobfuscated output")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found.")
        sys.exit(1)

    try:
        with open(args.input_file, 'rb') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    print(f"Processing {args.input_file}...")
    
    deobfuscator = Deobfuscator(content, verbose=args.verbose)
    result = deobfuscator.deobfuscate()
    
    print("\n--- Deobfuscation Complete ---")
    if deobfuscator.layers:
        print(f"Layers peeled: {', '.join(deobfuscator.layers)}")
    else:
        print("No obfuscation detected.")
    
    print("\n--- Analysis Report ---")
    entropy = deobfuscator.calculate_entropy(result)
    print(f"Shannon Entropy: {entropy:.2f}")
    if entropy > 7.5:
        print("Warning: High entropy (> 7.5). Content might be packed, encrypted, or compressed.")
    elif entropy < 4.0:
        print("Note: Low entropy (< 4.0). Content likely text or simple code.")

    indicators = deobfuscator.find_indicators(result)
    if indicators:
        print("\nSuspicious Indicators Found:")
        for category, items in indicators.items():
            # Deduplicate items
            items = list(set(items))
            print(f"  [{category}]: {', '.join(items[:10])}" + ("..." if len(items) > 10 else ""))
    else:
        print("\nNo common suspicious indicators found.")

    if args.output:
        try:
            with open(args.output, 'wb') as f:
                f.write(result)
            print(f"\nOutput saved to {args.output}")
        except Exception as e:
            print(f"Error saving output: {e}")
    else:
        print("\nResult Preview:")
        try:
            print(result.decode('utf-8')[:500])
        except:
            print(result[:500])

if __name__ == "__main__":
    main()
