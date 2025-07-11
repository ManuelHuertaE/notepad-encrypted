"""
Bloc de Notas Cifrado Mejorado

Esta aplicación permite crear, editar, eliminar y visualizar notas
almacenadas de forma cifrada en un archivo local.
Sólo un usuario con la contraseña correcta puede acceder o modificar las notas.

Se utiliza cifrado simétrico (Fernet/AES) para proteger la información.
"""
import os
import json
import base64
import hashlib
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, Toplevel, font as tkFont
from tkinter import ttk, filedialog
from cryptography.fernet import Fernet, InvalidToken

# Nombre del archivo cifrado de notas
NOTES_FILENAME = "notes.enc"
notes_path = ""  # Ruta completa al archivo, se define dinámicamente

# ---------- Funciones de cifrado ----------

def make_key(password: str) -> bytes:
    """
    Genera una clave de cifrado a partir de la contraseña.

    Args:
        password (str): Contraseña proporcionada por el usuario.

    Returns:
        bytes: Clave de 32 bytes codificada en base64 para Fernet.
    """
    digest = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(digest)

def load_notes(fernet: Fernet) -> list:
    """
    Carga y descifra la lista de notas desde el archivo cifrado.

    Args:
        fernet (Fernet): Objeto Fernet instanciado con la clave derivada.

    Returns:
        list: Lista de diccionarios con claves 'title' y 'body'.

    Raises:
        InvalidToken: Si la clave no coincide o el archivo está corrupto.
    """
    if not os.path.exists(notes_path):
        return []
    with open(notes_path, "rb") as file:
        data = file.read()
    plaintext = fernet.decrypt(data)
    return json.loads(plaintext.decode())

def save_notes(notes: list, fernet: Fernet):
    """
    Cifra y guarda la lista de notas en el archivo.

    Args:
        notes (list): Lista de diccionarios de notas.
        fernet (Fernet): Objeto Fernet instanciado con la clave derivada.
    """
    plaintext = json.dumps(notes).encode()
    token = fernet.encrypt(plaintext)
    with open(notes_path, "wb") as file:
        file.write(token)

# ---------- Clase de la Aplicación ----------
class SecureNotepadApp:
    """
    Interfaz gráfica para gestionar notas cifradas.

    Permite añadir, editar, eliminar y visualizar notas.
    """
    def __init__(self, root, fernet: Fernet, notes: list):
        self.root = root
        self.root.title("Bloc de Notas Cifrado")
        self.fernet = fernet
        self.notes = notes

        style = ttk.Style(root)
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TButton', padding=6)
        style.configure('TLabel', background='#f0f0f0')
        style.configure('Listbox.TFrame', background='#ffffff', relief='sunken')

        self.font_title = tkFont.Font(family="Helvetica", size=14, weight="bold")
        self.font_body = tkFont.Font(family="Helvetica", size=12)

        main_frame = ttk.Frame(root, padding="10 10 10 10")
        main_frame.grid(row=0, column=0, sticky='nsew')
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        list_frame = ttk.Frame(main_frame, style='Listbox.TFrame')
        list_frame.grid(row=0, column=0, columnspan=5, sticky='nsew', pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(list_frame, font=self.font_body, bd=0, highlightthickness=0)
        self.listbox.grid(row=0, column=0, sticky='nsew')
        self.listbox.bind("<Double-1>", self.view_note)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.listbox['yscrollcommand'] = scrollbar.set

        self.refresh_listbox()

        ttk.Button(main_frame, text="➕ Añadir", command=self.add_note).grid(row=1, column=0, pady=5, sticky='ew')
        ttk.Button(main_frame, text="✏️ Editar", command=self.edit_note).grid(row=1, column=1, pady=5, sticky='ew')
        ttk.Button(main_frame, text="🗑️ Eliminar", command=self.delete_note).grid(row=1, column=2, pady=5, sticky='ew')
        ttk.Button(main_frame, text="🔄 Refrescar", command=self.refresh_listbox).grid(row=1, column=3, pady=5, sticky='ew')
        ttk.Button(main_frame, text="🚪 Salir", command=root.quit).grid(row=1, column=4, pady=5, sticky='ew')

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, note in enumerate(self.notes, 1):
            self.listbox.insert(tk.END, f"{i}. {note['title']}")

    def add_note(self):
        title = simpledialog.askstring("Título de la Nota", "Ingresa el título:", parent=self.root)
        if not title:
            return
        self.open_note_editor(title, "", self.save_new_note)

    def save_new_note(self, title: str, body: str):
        self.notes.append({"title": title, "body": body})
        save_notes(self.notes, self.fernet)
        self.refresh_listbox()
        messagebox.showinfo("Éxito", "Nota guardada.", parent=self.root)

    def edit_note(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selecciona una nota", "Selecciona una nota para editar.", parent=self.root)
            return
        idx = sel[0]
        note = self.notes[idx]
        self.open_note_editor(note["title"], note["body"], lambda t, b: self.save_edited_note(idx, t, b))

    def save_edited_note(self, idx: int, title: str, body: str):
        self.notes[idx] = {"title": title, "body": body}
        save_notes(self.notes, self.fernet)
        self.refresh_listbox()
        messagebox.showinfo("Editado", "Nota actualizada.", parent=self.root)

    def delete_note(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selecciona una nota", "Selecciona una nota para eliminar.", parent=self.root)
            return
        idx = sel[0]
        if messagebox.askyesno("Eliminar", "¿Seguro que deseas eliminar?", parent=self.root):
            del self.notes[idx]
            save_notes(self.notes, self.fernet)
            self.refresh_listbox()
            messagebox.showinfo("Eliminado", "Nota borrada.", parent=self.root)

    def view_note(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        note = self.notes[sel[0]]
        self.open_note_viewer(note["title"], note["body"])

    def open_note_editor(self, title_default: str, body_default: str, on_save):
        win = Toplevel(self.root)
        win.title("Editor de Nota")
        win.resizable(False, False)

        ttk.Label(win, text="Título:", font=self.font_title).pack(pady=(10,0))
        title_entry = ttk.Entry(win, width=50)
        title_entry.pack(padx=10, pady=5)
        title_entry.insert(0, title_default)

        ttk.Label(win, text="Contenido:", font=self.font_title).pack(pady=(10,0))
        body_text = scrolledtext.ScrolledText(win, width=60, height=15, font=self.font_body)
        body_text.pack(padx=10, pady=5)
        body_text.insert("1.0", body_default)

        def guardar():
            t = title_entry.get().strip()
            b = body_text.get("1.0", tk.END).strip()
            if not t or not b:
                messagebox.showwarning("Campos vacíos", "Título y contenido no pueden estar vacíos.", parent=win)
                return
            on_save(t, b)
            win.destroy()

        ttk.Button(win, text="Guardar", command=guardar).pack(pady=10)

    def open_note_viewer(self, title: str, body: str):
        win = Toplevel(self.root)
        win.title(title)
        text = scrolledtext.ScrolledText(win, width=60, height=20, font=self.font_body)
        text.pack(padx=10, pady=10)
        text.insert("1.0", body)
        text.config(state="disabled")


def main():
    """
    Punto de entrada. Solicita contraseña y lanza la aplicación.
    """
    global notes_path

    root = tk.Tk()
    root.withdraw()

    password = simpledialog.askstring("Contraseña", "Ingresa tu contraseña:", show='*', parent=root)
    if not password:
        return

    # Si es primera vez, pedir carpeta de guardado y confirmar contraseña
    if not os.path.exists(NOTES_FILENAME):
        confirm = simpledialog.askstring("Confirmar", "Confirma tu contraseña:", show='*', parent=root)
        if confirm != password:
            messagebox.showerror("Error", "Contraseñas no coinciden.", parent=root)
            return

        folder = filedialog.askdirectory(title="Selecciona carpeta para guardar las notas")
        if not folder:
            messagebox.showwarning("Cancelado", "No se seleccionó carpeta.", parent=root)
            return

        notes_path = os.path.join(folder, NOTES_FILENAME)
    else:
        # Si ya existe, buscar en el mismo directorio
        notes_path = os.path.abspath(NOTES_FILENAME)

    key = make_key(password)
    fernet = Fernet(key)

    try:
        notes = load_notes(fernet)
    except InvalidToken:
        messagebox.showerror("Autenticación", "Contraseña incorrecta o archivo corrupto.", parent=root)
        return

    root.deiconify()
    app = SecureNotepadApp(root, fernet, notes)
    root.mainloop()

if __name__ == "__main__":
    main()
