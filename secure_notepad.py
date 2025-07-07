#!/usr/bin/env python3
# gui_secure_notepad.py
"""
Bloc de notas cifrado con interfaz gráfica: permite añadir título y cuerpo, editar, eliminar y ver.
"""
import os
import json
import base64
import hashlib
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, Toplevel
from cryptography.fernet import Fernet, InvalidToken

NOTES_FILE = "notes.enc"

# ==== Funciones de cifrado ==== #
def make_key(password: str) -> bytes:
    digest = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(digest)

def load_notes(fernet: Fernet) -> list:
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE, "rb") as file:
        data = file.read()
    plaintext = fernet.decrypt(data)
    return json.loads(plaintext.decode())

def save_notes(notes: list, fernet: Fernet):
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

        self.listbox = tk.Listbox(root, width=50, height=15)
        self.listbox.pack(padx=10, pady=5)
        self.listbox.bind("<Double-1>", self.view_note)
        self.refresh_listbox()

        buttons_frame = tk.Frame(root)
        buttons_frame.pack(pady=10)

        tk.Button(buttons_frame, text="Añadir Nota", command=self.add_note).grid(row=0, column=0, padx=5)
        tk.Button(buttons_frame, text="Editar Nota", command=self.edit_note).grid(row=0, column=1, padx=5)
        tk.Button(buttons_frame, text="Eliminar Nota", command=self.delete_note).grid(row=0, column=2, padx=5)
        tk.Button(buttons_frame, text="Refrescar", command=self.refresh_listbox).grid(row=0, column=3, padx=5)
        tk.Button(buttons_frame, text="Salir", command=root.quit).grid(row=0, column=4, padx=5)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, note in enumerate(self.notes, 1):
            title = note["title"]
            self.listbox.insert(tk.END, f"{i}. {title}")

    def add_note(self):
        title = simpledialog.askstring("Título de la Nota", "Ingresa el título de la nueva nota:")
        if not title:
            return
        self.open_note_editor(title, "", self.save_new_note)

    def save_new_note(self, title, body):
        self.notes.append({"title": title, "body": body})
        save_notes(self.notes, self.fernet)
        self.refresh_listbox()
        messagebox.showinfo("Éxito", "Nota guardada correctamente.")

    def edit_note(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selecciona una nota", "Debes seleccionar una nota para editar.")
            return
        idx = sel[0]
        note = self.notes[idx]
        self.open_note_editor(note["title"], note["body"], lambda t, b: self.save_edited_note(idx, t, b))

    def save_edited_note(self, idx, title, body):
        self.notes[idx] = {"title": title, "body": body}
        save_notes(self.notes, self.fernet)
        self.refresh_listbox()
        messagebox.showinfo("Editado", "Nota editada correctamente.")

    def delete_note(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selecciona una nota", "Debes seleccionar una nota para eliminar.")
            return
        idx = sel[0]
        confirm = messagebox.askyesno("Eliminar", "¿Estás seguro de eliminar esta nota?")
        if confirm:
            del self.notes[idx]
            save_notes(self.notes, self.fernet)
            self.refresh_listbox()
            messagebox.showinfo("Eliminado", "Nota eliminada correctamente.")

    def view_note(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        note = self.notes[idx]
        self.open_note_viewer(note["title"], note["body"])

    def open_note_editor(self, title_default, body_default, on_save):
        win = Toplevel(self.root)
        win.title("Editor de Nota")

        tk.Label(win, text="Título:").pack()
        title_entry = tk.Entry(win, width=50)
        title_entry.pack(padx=10, pady=5)
        title_entry.insert(0, title_default)

        tk.Label(win, text="Contenido:").pack()
        body_text = scrolledtext.ScrolledText(win, width=60, height=15)
        body_text.pack(padx=10, pady=5)
        body_text.insert("1.0", body_default)

        def guardar():
            title = title_entry.get().strip()
            body = body_text.get("1.0", tk.END).strip()
            if not title or not body:
                messagebox.showwarning("Campos requeridos", "El título y cuerpo no pueden estar vacíos.")
                return
            on_save(title, body)
            win.destroy()

        tk.Button(win, text="Guardar", command=guardar).pack(pady=5)

    def open_note_viewer(self, title, body):
        win = Toplevel(self.root)
        win.title(title)
        text = scrolledtext.ScrolledText(win, width=60, height=20)
        text.pack(padx=10, pady=10)
        text.insert("1.0", body)
        text.config(state="disabled")


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
