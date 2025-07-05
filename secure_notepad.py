import os
import json
import getpass
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken

NOTES_FILE = "notes.enc"

def make_key(password: str) -> bytes:
    """
    Genera una clave de 32 Bytes a partir de una contraseña.
    Para esto, se utiliza SHA-256 para crear un hash de la contraseña
    y luego se codifica en base64 url-sage para Fernet.
    """
    digest = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(digest)

def load_notes(f: Fernet) -> list:
    """
    Lee el archivo NOTES_FILE (si existe), lo descifra y devuelve
    la lista de notas en texto plano
    """
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE, "rb") as file:
        data = file.read()
    try:
        plaintext = f.decrypt(data)
        return json.loads(plaintext.decode())
    except InvalidToken:
        print("Error: La clave proporcionada es incorrecta o el archivo está corrupto.")
        return []

def save_notes(notes: list, f: Fernet):
    """
    Cifra la lista de notas y la escribe en NOTES_FILE.
    """
    plaintext = json.dumps(notes).encode()
    token = f.encrypt(plaintext)
    with open(NOTES_FILE, "wb") as file:
        file.write(token)

def menu() -> None:
    print("""
          ========== Secure Notepad =========
          1) Ver todas las notas
          2) Agregar una nueva nota
          3) Salir
        """)

def main():
    #Pedir contraseña al usuario
    password = getpass.getpass("Ingrese su contraseña: ")
    key = make_key(password)
    fernet = Fernet(key)
    
    notes = load_notes(fernet)
    if notes is None:
        return
    
    while True:
        menu()
        choice = input("Selecciona una opción [1-3]: ").strip()
        if(choice == "1"):
            if not notes:
                print("No hay notas guardadas.")
            else:
                print("\n--- Tus Notas ---")
                for i, note in enumerate(notes, 1):
                    print(f"{i}. {note}")
                print("------------------\n")
        elif choice == "2":
            text = input("Escribe tu nueva nota: ").strip()
            if text:
                notes.append(text)
                save_notes(notes, fernet)
                print("Nota guardada exitosamente.\n")
            else: 
                print("La nota no puede estar vacía.\n")
        elif choice == "3":
            print("Saliendo del programa. ¡Hasta luego!")
            break
        else:
            print("Opción no válida. Por favor, elige una opción del menú.\n")

if __name__ == "__main__":
    main()