#!/usr/bin/env python3
# gui_secure_notepad.py
"""
Interfaz gráfica para el Bloc de Notas Local Cifrado con opciones de editar y eliminar.
Usa Tkinter para mostrar las notas existentes y permitir agregar, editar y eliminar notas.
"""
import os
import json
import base64
import hashlib
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
from cryptography.fernet import Fernet, InvalidToken

NOTES_FILE = "notes.enc"

# ==== Funciones de cifrado ==== #
def make_key(password: str) -> bytes:
    """
    Genera una clave de 32 bytes a partir de la contraseña
    usando SHA-256 y la codifica en base64 url-safe para Fernet.
    """
    digest = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def load_notes(fernet: Fernet) -> list:
    """
    Lee el archivo NOTES_FILE (si existe), lo descifra y devuelve
    la lista de notas en texto plano.
    """
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE, "rb") as file:
        data = file.read()
    plaintext = fernet.decrypt(data)
    return json.loads(plaintext.decode())


def save_notes(notes: list, fernet: Fernet):
    """
    Cifra la lista de notas y la escribe en NOTES_FILE.
    """
    plaintext = json.dumps(notes).encode()
    token = fernet.encrypt(plaintext)
    with open(NOTES_FILE, "wb") as file:
        file.write(token)

# ==== GUI ==== #
class SecureNotepadApp:
    def __init__(self, root, fernet: Fernet, notes: list):
        self.root = root
        self.root.title("Bloc de Notas Cifrado")
        self.fernet = fernet
        self.notes = notes

        # Lista de notas
        self.listbox = tk.Listbox(root, width=50, height=15)
        self.listbox.pack(padx=10, pady=5)
        self.refresh_listbox()

        # Text area para nueva nota o edición
        self.text_entry = scrolledtext.ScrolledText(root, width=50, height=5)
        self.text_entry.pack(padx=10, pady=(5, 0))

        # Botones
        buttons_frame = tk.Frame(root)
        buttons_frame.pack(pady=10)

        add_btn = tk.Button(buttons_frame, text="Añadir Nota", command=self.add_note)
        add_btn.grid(row=0, column=0, padx=5)
        edit_btn = tk.Button(buttons_frame, text="Editar Nota", command=self.edit_note)
        edit_btn.grid(row=0, column=1, padx=5)
        del_btn = tk.Button(buttons_frame, text="Eliminar Nota", command=self.delete_note)
        del_btn.grid(row=0, column=2, padx=5)
        refresh_btn = tk.Button(buttons_frame, text="Refrescar", command=self.refresh_listbox)
        refresh_btn.grid(row=0, column=3, padx=5)
        exit_btn = tk.Button(buttons_frame, text="Salir", command=root.quit)
        exit_btn.grid(row=0, column=4, padx=5)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, note in enumerate(self.notes, 1):
            preview = note if len(note) <= 50 else note[:47] + '...'
            self.listbox.insert(tk.END, f"{i}. {preview}")

    def add_note(self):
        text = self.text_entry.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Nota vacía", "Escribe algo para guardar la nota.")
            return
        self.notes.append(text)
        save_notes(self.notes, self.fernet)
        messagebox.showinfo("Éxito", "Nota guardada correctamente.")
        self.text_entry.delete("1.0", tk.END)
        self.refresh_listbox()

    def edit_note(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selección necesaria", "Selecciona una nota para editar.")
            return
        idx = sel[0]
        old = self.notes[idx]
        new_text = simpledialog.askstring("Editar Nota", "Modifica tu nota:", initialvalue=old)
        if new_text is None:
            return
        new_text = new_text.strip()
        if not new_text:
            messagebox.showwarning("Nota vacía", "El contenido no puede estar vacío.")
            return
        self.notes[idx] = new_text
        save_notes(self.notes, self.fernet)
        messagebox.showinfo("Éxito", "Nota editada correctamente.")
        self.refresh_listbox()

    def delete_note(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selección necesaria", "Selecciona una nota para eliminar.")
            return
        idx = sel[0]
        confirm = messagebox.askyesno("Confirmar eliminación", "¿Estás seguro que deseas eliminar esta nota?")
        if not confirm:
            return
        del self.notes[idx]
        save_notes(self.notes, self.fernet)
        messagebox.showinfo("Eliminado", "Nota eliminada correctamente.")
        self.refresh_listbox()


def main():
    root = tk.Tk()
    root.withdraw()
    password = simpledialog.askstring("Contraseña", "Ingresa tu contraseña:", show='*')
    if not password:
        return
    key = make_key(password)
    fernet = Fernet(key)

    try:
        notes = load_notes(fernet)
    except InvalidToken:
        messagebox.showerror("Error de Autenticación", "Contraseña incorrecta o archivo corrupto.")
        return

    root.deiconify()
    app = SecureNotepadApp(root, fernet, notes)
    root.mainloop()

if __name__ == "__main__":
    main()
