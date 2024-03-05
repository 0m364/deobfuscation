import base64

# Placeholder for custom deobfuscation methods
def custom_obfuscation_method_1(data):
    # your custom method here
    return data

def custom_obfuscation_method_2(data):
    # your custom method here
    return data

def base64_decode(data):
    try:
        return base64.b64decode(data).decode('utf-8')
    except:
        return data

def reverse_obfuscation(code):
    possible_obfuscation_methods = [base64_decode, custom_obfuscation_method_1, custom_obfuscation_method_2]

    for method in possible_obfuscation_methods:
        decoded_code = method(code)
        
        if decoded_code != code:
            return decoded_code, method.__name__

    return code, "No obfuscation detected... add more obfuscation methods to the script or maybe... it's clear"

# input
file_path = input("Where's the file? (location e.g., /etc/apt/file.name): ")


try:
    with open(file_path, 'r') as file:
        obfuscated_code = file.read()
except Exception as e:
    print(f"Failed to read the file: {e}")
    exit()

for i in range(10):
    deobfuscated_code, method = reverse_obfuscation(obfuscated_code)
    
    print(f"Layer {i + 1} deobfuscated using method: {method}")
    print(deobfuscated_code)
    
    # nothing found end loop
    if method == "No obfuscation detected":
        break
    
    obfuscated_code = deobfuscated_code
