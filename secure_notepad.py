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
from tkinter import ttk
from cryptography.fernet import Fernet, InvalidToken

# Path del archivo cifrado de notas\
NOTES_FILE = "notes.enc"

# ---------- Funciones de cifrado ----------

def make_key(password: str) -> bytes:
    """
    Genera una clave de cifrado a partir de la contraseña.

    Args:
        password (str): Contraseña proporcionada por el usuario.

    Returns:
        bytes: Clave de 32 bytes codificada en base64 para Fernet.
    """
    # Derivar hash SHA-256 de la contraseña
    digest = hashlib.sha256(password.encode()).digest()
    # Codificar en base64 URL-safe para Fernet
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
    # Si el archivo no existe, devolver lista vacía
    if not os.path.exists(NOTES_FILE):
        return []
    # Leer datos cifrados
    with open(NOTES_FILE, "rb") as file:
        data = file.read()
    # Descifrar y parsear JSON
    plaintext = fernet.decrypt(data)
    return json.loads(plaintext.decode())


def save_notes(notes: list, fernet: Fernet):
    """
    Cifra y guarda la lista de notas en el archivo.

    Args:
        notes (list): Lista de diccionarios de notas.
        fernet (Fernet): Objeto Fernet instanciado con la clave derivada.
    """
    # Convertir lista a JSON y cifrar
    plaintext = json.dumps(notes).encode()
    token = fernet.encrypt(plaintext)
    # Escribir datos cifrados en disco
    with open(NOTES_FILE, "wb") as file:
        file.write(token)


# ---------- Clase de la Aplicación ----------
class SecureNotepadApp:
    """
    Interfaz gráfica para gestionar notas cifradas.

    Permite añadir, editar, eliminar y visualizar notas.
    """
    def __init__(self, root, fernet: Fernet, notes: list):
        """
        Inicializa la ventana principal y widgets.

        Args:
            root (tk.Tk): Ventana raíz de Tkinter.
            fernet (Fernet): Objeto para cifrar/descifrar notas.
            notes (list): Lista inicial de notas descifradas.
        """
        self.root = root
        self.root.title("Bloc de Notas Cifrado")
        self.fernet = fernet
        self.notes = notes

        # Configuración de estilos ttk para aspecto moderno
        style = ttk.Style(root)
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TButton', padding=6)
        style.configure('TLabel', background='#f0f0f0')
        style.configure('Listbox.TFrame', background='#ffffff', relief='sunken')

        # Fuentes personalizadas
        self.font_title = tkFont.Font(family="Helvetica", size=14, weight="bold")
        self.font_body = tkFont.Font(family="Helvetica", size=12)

        # Marco principal con padding
        main_frame = ttk.Frame(root, padding="10 10 10 10")
        main_frame.grid(row=0, column=0, sticky='nsew')
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Marco para la lista de notas (con borde)
        list_frame = ttk.Frame(main_frame, style='Listbox.TFrame')
        list_frame.grid(row=0, column=0, columnspan=5, sticky='nsew', pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Listbox para títulos de notas
        self.listbox = tk.Listbox(list_frame, font=self.font_body, bd=0, highlightthickness=0)
        self.listbox.grid(row=0, column=0, sticky='nsew')
        self.listbox.bind("<Double-1>", self.view_note)

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.listbox['yscrollcommand'] = scrollbar.set

        self.refresh_listbox()

        # Botones de acciones
        ttk.Button(main_frame, text="➕ Añadir", command=self.add_note).grid(row=1, column=0, pady=5, sticky='ew')
        ttk.Button(main_frame, text="✏️ Editar", command=self.edit_note).grid(row=1, column=1, pady=5, sticky='ew')
        ttk.Button(main_frame, text="🗑️ Eliminar", command=self.delete_note).grid(row=1, column=2, pady=5, sticky='ew')
        ttk.Button(main_frame, text="🔄 Refrescar", command=self.refresh_listbox).grid(row=1, column=3, pady=5, sticky='ew')
        ttk.Button(main_frame, text="🚪 Salir", command=root.quit).grid(row=1, column=4, pady=5, sticky='ew')

    def refresh_listbox(self):
        """
        Actualiza los títulos mostrados en la lista.
        """
        self.listbox.delete(0, tk.END)
        for i, note in enumerate(self.notes, 1):
            display = f"{i}. {note['title']}"
            self.listbox.insert(tk.END, display)

    def add_note(self):
        """
        Solicita título y abre editor para nueva nota.
        """
        title = simpledialog.askstring("Título de la Nota", "Ingresa el título:", parent=self.root)
        if not title:
            return  # Cancelado
        self.open_note_editor(title, "", self.save_new_note)

    def save_new_note(self, title: str, body: str):
        """
        Guarda una nueva nota en memoria y en disco.
        """
        self.notes.append({"title": title, "body": body})
        save_notes(self.notes, self.fernet)
        self.refresh_listbox()
        messagebox.showinfo("Éxito", "Nota guardada.", parent=self.root)

    def edit_note(self):
        """
        Abre el editor para la nota seleccionada.
        """
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selecciona una nota", "Selecciona una nota para editar.", parent=self.root)
            return
        idx = sel[0]
        note = self.notes[idx]
        self.open_note_editor(note["title"], note["body"], lambda t, b: self.save_edited_note(idx, t, b))

    def save_edited_note(self, idx: int, title: str, body: str):
        """
        Actualiza nota existente y guarda cambios.
        """
        self.notes[idx] = {"title": title, "body": body}
        save_notes(self.notes, self.fernet)
        self.refresh_listbox()
        messagebox.showinfo("Editado", "Nota actualizada.", parent=self.root)

    def delete_note(self):
        """
        Elimina la nota seleccionada tras confirmación.
        """
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
        """
        Muestra el contenido de la nota en modo sólo lectura.
        """
        sel = self.listbox.curselection()
        if not sel:
            return
        note = self.notes[sel[0]]
        self.open_note_viewer(note["title"], note["body"])

    def open_note_editor(self, title_default: str, body_default: str, on_save):
        """
        Ventana de edición/creación de nota.
        """
        win = Toplevel(self.root)
        win.title("Editor de Nota")
        win.resizable(False, False)

        # Campo de título
        ttk.Label(win, text="Título:", font=self.font_title).pack(pady=(10,0))
        title_entry = ttk.Entry(win, width=50)
        title_entry.pack(padx=10, pady=5)
        title_entry.insert(0, title_default)

        # Campo de contenido
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
        """
        Ventana de sólo lectura para ver nota.
        """
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
    root = tk.Tk()
    root.withdraw()  # Oculta ventana principal hasta autenticación

    # Solicitar contraseña
    password = simpledialog.askstring("Contraseña", "Ingresa tu contraseña:", show='*', parent=root)
    if not password:
        return  # Cancelado por el usuario

    # Si no hay notas guardadas, pedir confirmación de contraseña
    if not os.path.exists(NOTES_FILE):
        confirm = simpledialog.askstring("Confirmar", "Confirma tu contraseña:", show='*', parent=root)
        if confirm != password:
            messagebox.showerror("Error", "Contraseñas no coinciden.", parent=root)
            return

    # Derivar clave y crear objeto Fernet
    key = make_key(password)
    fernet = Fernet(key)

    try:
        # Cargar notas descifradas
        notes = load_notes(fernet)
    except InvalidToken:
        messagebox.showerror("Autenticación", "Contraseña incorrecta o archivo corrupto.", parent=root)
        return

    # Mostrar ventana principal
    root.deiconify()
    app = SecureNotepadApp(root, fernet, notes)
    root.mainloop()

if __name__ == "__main__":
    main()
