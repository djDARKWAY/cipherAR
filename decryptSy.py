import os
import time
from tqdm import tqdm
from logo import logoPrint
from cryptography.hazmat.primitives.ciphers import Cipher, modes
from cryptography.hazmat.primitives.ciphers.algorithms import AES, ChaCha20, TripleDES
from cryptography.hazmat.backends import default_backend
from hashVerifier import verifyHash

# Dicionário de algoritmos suportados, incluindo tamanhos de chave
ALGORITHMS = {
    'AES-128': {'keySize': 16, 'algorithm': AES},
    'AES-256': {'keySize': 32, 'algorithm': AES},
    'ChaCha20': {'keySize': 32, 'algorithm': ChaCha20},
    'TripleDES': {'keySize': 24, 'algorithm': TripleDES}
}

def decryptFile(inputFile, outputFile, key):
    logoPrint()
    startTime = time.time()

    # Abre o ficheiro de entrada para leitura
    with open(inputFile, 'rb') as f:
        algorithmName = f.readline().decode().strip()
        data = f.read()

    # Extraí o IV/nonce, o texto cifrado e o hash armazenado com base no algoritmo
    if algorithmName.startswith("AES"):
        iv, ciphertext, hashValueStored = data[:16], data[16:-128], data[-128:].decode()
    elif algorithmName == 'ChaCha20':
        nonce, ciphertext, hashValueStored = data[:16], data[16:-128], data[-128:].decode()
    elif algorithmName == 'TripleDES':
        iv, ciphertext, hashValueStored = data[:8], data[8:-128], data[-128:].decode()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithmName}")

    # Cria o objeto Cipher com base no algoritmo e modo apropriados
    if algorithmName.startswith("AES"):
        cipher = Cipher(ALGORITHMS[algorithmName]['algorithm'](key), modes.CBC(iv), backend=default_backend())
    elif algorithmName == 'ChaCha20':
        cipher = Cipher(ALGORITHMS['ChaCha20']['algorithm'](key, nonce), mode=None, backend=default_backend())
    elif algorithmName == 'TripleDES':
        cipher = Cipher(ALGORITHMS['TripleDES']['algorithm'](key), modes.CBC(iv), backend=default_backend())

    # Desencripta os dados com barra de progresso
    decryptor = cipher.decryptor()
    chunkSize = 20 * 1024 * 1024  # 20 MB
    decryptedPadded = b""
    for i in tqdm(range(0, len(ciphertext), chunkSize), unit='MB', desc='Decrypting'):
        chunk = ciphertext[i:i + chunkSize]
        decryptedPadded += decryptor.update(chunk)
    decryptedPadded += decryptor.finalize()

    # Remove o padding se necessário (aplica-se a AES e TripleDES)
    if algorithmName.startswith("AES") or algorithmName == 'TripleDES':
        paddingLength = decryptedPadded[-1]
        decryptedData = decryptedPadded[:-paddingLength]
    else:
        decryptedData = decryptedPadded

    # Verifica a integridade dos dados usando a hash armazenada
    if verifyHash(decryptedData, hashValueStored):
        print("\033[92m\nIntegrity check: OK!\033[0m")
    else:
        print("\033[91m\nIntegrity check: FAILED!\033[0m")

    # Escreve os dados decifrados no ficheiro de saída
    print("Writing to output file...")
    with open(outputFile, 'wb') as f:
        f.write(decryptedData)
    
    # Calcular o tempo de execução
    endTime = time.time()
    elapsedTime = endTime - startTime
    hours, rem = divmod(elapsedTime, 3600)
    minutes, seconds = divmod(rem, 60)
    milliseconds = (seconds - int(seconds)) * 1000
    print(f"\nTime elapsed: {int(hours):02}:{int(minutes):02}:{int(seconds):02}:{int(milliseconds):03} seconds")
