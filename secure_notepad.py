"""
Bloc de Notas Cifrado

Esta aplicación permite crear, editar, eliminar y visualizar notas
que se almacenan de forma cifrada en un archivo local. Solo un usuario
con la contraseña correcta puede acceder a las notas.

Utiliza cifrado simétrico (Fernet/AES) para proteger la información.
"""
import os
import json
import base64
import hashlib
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, Toplevel
from cryptography.fernet import Fernet, InvalidToken

NOTES_FILE = "notes.enc" #Nombre del archivo donde se guardan las notas cifradas

# Funciones de cifrado #
def make_key(password: str) -> bytes:
    """
    Deriva/genera una clave criptográfica a partir de la contraseña del usuario.
     
    Args:
        password: La contraseña proporcionada por el usuario

    Returns:
        Una clave de 32 bytes codificada en base64 para el cifrado Fernet
    """
    digest = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(digest)

def load_notes(fernet: Fernet) -> list:
    """
    Carga y descifra las notas guardadas.
    
    Args:
        fernet: Objeto Fernet inicializado con la clave derivada de la contraseña 
        proporcionada por el usuario
    
    Returns:
        Lista de notas descifradas, oh una lista vacía si no existen notas guardadas.
        
    Raises:
        Invalid Token: Si la contraseña es incorrecta o el archivo está corrupto.
    """
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE, "rb") as file:
        data = file.read()
    plaintext = fernet.decrypt(data)
    return json.loads(plaintext.decode())

def save_notes(notes: list, fernet: Fernet):
    """
    Cifra y guarda las notas en el archivo .enc
    
    Args:
        notes: Lista de notas a guardar
        fernet: Objeto Fernet inicializado con la clave derivada de la contraseña
        proporcionada por el usuario
    """
    plaintext = json.dumps(notes).encode()
    token = fernet.encrypt(plaintext)
    with open(NOTES_FILE, "wb") as file:
        file.write(token)

# GUI
class SecureNotepadApp:
    """
    Clase principal de la aplicación de Notes Crypted
    Maneja la interfaz gráfica y las operaciones con notas.
    """
    def __init__(self, root, fernet: Fernet, notes: list):
        """
        Inicializa la interfaz gráfica de la aplicación.
        
        Args:
            root: Ventana principal de Tkinter
            fernet: Objeto Fernet para cifrado/descifrado
            notes: Lista de notas descifradas
        """
        self.root = root
        self.root.title("Bloc de Notas Cifrado")
        self.fernet = fernet
        self.notes = notes

        #Lista de notas
        self.listbox = tk.Listbox(root, width=50, height=15)
        self.listbox.pack(padx=10, pady=5)
        self.listbox.bind("<Double-1>", self.view_note)
        self.refresh_listbox()

        # Barra de botones
        buttons_frame = tk.Frame(root)
        buttons_frame.pack(pady=10)

        tk.Button(buttons_frame, text="Añadir Nota", command=self.add_note).grid(row=0, column=0, padx=5)
        tk.Button(buttons_frame, text="Editar Nota", command=self.edit_note).grid(row=0, column=1, padx=5)
        tk.Button(buttons_frame, text="Eliminar Nota", command=self.delete_note).grid(row=0, column=2, padx=5)
        tk.Button(buttons_frame, text="Refrescar", command=self.refresh_listbox).grid(row=0, column=3, padx=5)
        tk.Button(buttons_frame, text="Salir", command=root.quit).grid(row=0, column=4, padx=5)

    def refresh_listbox(self):
        """
        Actualiza el listado de notas en la interfaz.
        """
        self.listbox.delete(0, tk.END)
        for i, note in enumerate(self.notes, 1):
            title = note["title"]
            self.listbox.insert(tk.END, f"{i}. {title}")

    def add_note(self):
        """
        Inicia el proceso para añadir una nueva nota.
        """
        title = simpledialog.askstring("Título de la Nota", "Ingresa el título de la nueva nota:")
        if not title:
            return # El usuario canceló o no ingresó un título
        self.open_note_editor(title, "", self.save_new_note)

    def save_new_note(self, title, body):
        """
        Guarda una nueva nota en la lista de notas.
        
        Args:
            title: Título de la nueva nota.
            body: Contenido de la nota.
        """
        self.notes.append({"title": title, "body": body})
        save_notes(self.notes, self.fernet)
        self.refresh_listbox()
        messagebox.showinfo("Éxito", "Nota guardada correctamente.")

    def edit_note(self):
        """
        Inicia el proceso de edición de una nota existente.
        """
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selecciona una nota", "Debes seleccionar una nota para editar.")
            return
        idx = sel[0]
        note = self.notes[idx]
        self.open_note_editor(note["title"], note["body"], lambda t, b: self.save_edited_note(idx, t, b))

    def save_edited_note(self, idx, title, body):
        """
        Actualiza una nota existente con nuevo contenido.
        
        Args:
            idx: índice de la nota a editar.
            title: Nuevo título
            body: Nuevo contenido de la nota.
        """
        self.notes[idx] = {"title": title, "body": body}
        save_notes(self.notes, self.fernet)
        self.refresh_listbox()
        messagebox.showinfo("Editado", "Nota editada correctamente.")

    def delete_note(self):
        """
        Elimina una nota después de pedir confirmación al usuario.
        """
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
        """
        Muestra el contenido de una nota (al hacer doble clic en ella).
        
        Args:
            event: Evento del mouse.
        """
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        note = self.notes[idx]
        self.open_note_viewer(note["title"], note["body"])

    def open_note_editor(self, title_default, body_default, on_save):
        """
        Abre un editor para crear o modificar una nota.
        
        Args:
            title_default: Título predeterminado (puede estar vacío).
            body_default: Contenido predeterminado (puede estar vacío).
            on_save: Función callback que se llama al guardar una nota
        """
        win = Toplevel(self.root)
        win.title("Editor de Nota")

        #Campo de título
        tk.Label(win, text="Título:").pack()
        title_entry = tk.Entry(win, width=50)
        title_entry.pack(padx=10, pady=5)
        title_entry.insert(0, title_default)

        #Campo de contenido
        tk.Label(win, text="Contenido:").pack()
        body_text = scrolledtext.ScrolledText(win, width=60, height=15)
        body_text.pack(padx=10, pady=5)
        body_text.insert("1.0", body_default)

        def guardar():
            """
            Valida los campos y guarda la nota utilizando el callback (on_save).
            """
            title = title_entry.get().strip()
            body = body_text.get("1.0", tk.END).strip()
            if not title or not body:
                messagebox.showwarning("Campos requeridos", "El título y cuerpo no pueden estar vacíos.")
                return
            on_save(title, body)
            win.destroy()

        tk.Button(win, text="Guardar", command=guardar).pack(pady=5)

    def open_note_viewer(self, title, body):
        """
        Abre una ventana de solo lectura para ver el contenido de una nota.
        
        Args:
            title: Título de la nota.
            body: Contenido de la nota.
        """
        win = Toplevel(self.root)
        win.title(title)
        text = scrolledtext.ScrolledText(win, width=60, height=20)
        text.pack(padx=10, pady=10)
        text.insert("1.0", body)
        text.config(state="disabled") #Solo lectura.
        


def main():
    """
    Función principal que inicializa la aplicación,
    Solicita la contraseña al usuario y carga la interfaz.
    """
    root = tk.Tk()
    root.withdraw() # Oculta la ventana principal mientras se solicita la contraseña
    
    #Solicita la contraseña al usuario
    password = simpledialog.askstring("Contraseña", "Ingresa tu contraseña:", show='*')
    if not password:
        return # El usuario canceló o no ingresó una contraseña
    
    #Deriva clave y crea objeto de cifrado Fernet
    key = make_key(password)
    fernet = Fernet(key)

    try:
        #Intenta cargar notas con la contraseña proporcionada
        notes = load_notes(fernet)
    except InvalidToken:
        messagebox.showerror("Error de Autenticación", "Contraseña incorrecta o archivo corrupto.")
        return

    # Muestra la interfaz principal
    root.deiconify()
    app = SecureNotepadApp(root, fernet, notes)
    root.mainloop()

if __name__ == "__main__":
    main()
