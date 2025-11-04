import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import fitz  # PyMuPDF

class TextDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Agregar Texto")
        self.geometry("450x350")
        self.result = None
        
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        
        # Texto
        ctk.CTkLabel(self, text="Texto:", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=20, pady=(20,5), sticky="w")
        self.text_entry = ctk.CTkTextbox(self, height=100, width=400, font=("Arial", 12))
        self.text_entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        # Frame para controles
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        controls_frame.grid_columnconfigure((0,1), weight=1)
        
        # Tamaño de fuente
        size_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        size_frame.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(size_frame, text="Tamaño:", font=("Arial", 12)).pack(side="left", padx=5)
        self.font_size = ctk.CTkEntry(size_frame, width=60)
        self.font_size.insert(0, "12")
        self.font_size.pack(side="left", padx=5)
        
        # Color
        color_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        color_frame.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        ctk.CTkLabel(color_frame, text="Color:", font=("Arial", 12)).pack(side="left", padx=5)
        self.color_var = ctk.StringVar(value="Negro")
        colors = ["Negro", "Rojo", "Azul", "Verde", "Blanco"]
        self.color_combo = ctk.CTkComboBox(color_frame, values=colors, variable=self.color_var, width=120)
        self.color_combo.pack(side="left", padx=5)
        
        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        btn_frame.grid_columnconfigure((0,1), weight=1)
        
        ctk.CTkButton(btn_frame, text="Aceptar", command=self.accept, 
                     fg_color="#2ecc71", hover_color="#27ae60").grid(row=0, column=0, padx=10, sticky="ew")
        ctk.CTkButton(btn_frame, text="Cancelar", command=self.cancel,
                     fg_color="#e74c3c", hover_color="#c0392b").grid(row=0, column=1, padx=10, sticky="ew")
        
        self.text_entry.focus()
        self.transient(parent)
        self.grab_set()
        
    def accept(self):
        text = self.text_entry.get("1.0", "end-1c").strip()
        if text:
            color_map = {
                "Negro": (0, 0, 0),
                "Rojo": (1, 0, 0),
                "Azul": (0, 0, 1),
                "Verde": (0, 0.5, 0),
                "Blanco": (1, 1, 1)
            }
            try:
                size = int(self.font_size.get())
                self.result = {
                    'text': text,
                    'size': size,
                    'color': color_map.get(self.color_var.get(), (0, 0, 0))
                }
                self.destroy()
            except ValueError:
                messagebox.showwarning("Advertencia", "El tamaño debe ser un número")
        else:
            messagebox.showwarning("Advertencia", "Por favor ingresa un texto")
    
    def cancel(self):
        self.destroy()

class PDFEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor de PDF Editor")
        self.root.geometry("1200x800")
        
        try:
            self.root.iconbitmap('icon.ico')
        except:
            try:
                icon = tk.PhotoImage(file='icon.ico')
                self.root.iconphoto(True, icon)
            except:
                pass  # Si no se encuentra el icono, continuar sin él       
        
        # Configurar tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.pdf_document = None
        self.current_page = 0
        self.pdf_path = None
        self.zoom_level = 1.0
        self.edit_mode = False
        self.delete_mode = False
        self.hide_mode = False
        self.move_mode = False
        
        self.text_annotations = {}
        self.hide_rectangles = {}  # Ahora guarda áreas para borrar permanentemente
        self.text_items = {}
        
        # Variables para selección y movimiento
        self.selection_start = None
        self.selection_rect = None
        self.dragging_text = None
        self.drag_start = None
        self.selected_text = None  # Para trackear el texto seleccionado
        
        # Panel de controles de texto
        self.text_controls = None
        self.bold_var = None
        self.italic_var = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Panel lateral izquierdo
        sidebar = ctk.CTkFrame(main_container, width=200, corner_radius=10)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)
        
        # Logo/Título
        title_label = ctk.CTkLabel(sidebar, text="PDF Editor", font=("Arial", 20, "bold"))
        title_label.pack(pady=20)
        
        # Sección Archivo
        ctk.CTkLabel(sidebar, text="ARCHIVO", font=("Arial", 12, "bold")).pack(pady=(10, 5))
        ctk.CTkButton(sidebar, text="📂 Abrir PDF", command=self.open_pdf, 
                     corner_radius=8).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(sidebar, text="💾 Guardar", command=self.save_pdf,
                     corner_radius=8).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(sidebar, text="💾 Guardar como", command=self.save_pdf_as,
                     corner_radius=8).pack(pady=5, padx=10, fill="x")
        
        # Sección Edición
        ctk.CTkLabel(sidebar, text="EDICIÓN", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        
        self.hide_btn = ctk.CTkButton(sidebar, text="🗑 Borrar Texto", 
                                      command=self.toggle_hide_mode, corner_radius=8)
        self.hide_btn.pack(pady=5, padx=10, fill="x")
        
        self.edit_btn = ctk.CTkButton(sidebar, text="✏ Agregar Texto", 
                                      command=self.toggle_edit_mode, corner_radius=8)
        self.edit_btn.pack(pady=5, padx=10, fill="x")
        
        self.move_btn = ctk.CTkButton(sidebar, text="↔ Mover y Editar Texto", 
                                      command=self.toggle_move_mode, corner_radius=8)
        self.move_btn.pack(pady=5, padx=10, fill="x")
        
        self.delete_btn = ctk.CTkButton(sidebar, text="🗑 Eliminar Texto", 
                                        command=self.toggle_delete_mode, corner_radius=8)
        self.delete_btn.pack(pady=5, padx=10, fill="x")
        
        # Sección Página
        ctk.CTkLabel(sidebar, text="PÁGINA", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        ctk.CTkButton(sidebar, text="↻ Rotar Derecha", 
                     command=lambda: self.rotate_page(90), corner_radius=8).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(sidebar, text="↺ Rotar Izquierda", 
                     command=lambda: self.rotate_page(-90), corner_radius=8).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(sidebar, text="🗑 Eliminar Página", 
                     command=self.delete_page, corner_radius=8,
                     fg_color="#e74c3c", hover_color="#c0392b").pack(pady=5, padx=10, fill="x")
        
        # Sección Limpiar
        ctk.CTkLabel(sidebar, text="LIMPIAR", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        ctk.CTkButton(sidebar, text="Textos Agregados", 
                     command=self.clear_page_texts, corner_radius=8,
                     fg_color="#95a5a6", hover_color="#7f8c8d").pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(sidebar, text="Áreas Borradas", 
                     command=self.clear_page_hides, corner_radius=8,
                     fg_color="#95a5a6", hover_color="#7f8c8d").pack(pady=5, padx=10, fill="x")
        
        # Panel derecho (contenido)
        right_panel = ctk.CTkFrame(main_container, corner_radius=10)
        right_panel.pack(side="left", fill="both", expand=True)
        
        # Barra de herramientas superior
        toolbar = ctk.CTkFrame(right_panel, height=60, corner_radius=8)
        toolbar.pack(fill="x", padx=10, pady=10)
        
        # Controles de navegación
        nav_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        nav_frame.pack(side="left", padx=10)
        
        ctk.CTkButton(nav_frame, text="◀", command=self.prev_page, width=40,
                     corner_radius=8).pack(side="left", padx=2)
        self.page_label = ctk.CTkLabel(nav_frame, text="Página: 0/0", font=("Arial", 14, "bold"))
        self.page_label.pack(side="left", padx=15)
        ctk.CTkButton(nav_frame, text="▶", command=self.next_page, width=40,
                     corner_radius=8).pack(side="left", padx=2)
        
        # Controles de zoom
        zoom_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        zoom_frame.pack(side="right", padx=10)
        
        ctk.CTkButton(zoom_frame, text="Zoom -", command=self.zoom_out, width=80,
                     corner_radius=8).pack(side="left", padx=2)
        self.zoom_label = ctk.CTkLabel(zoom_frame, text="100%", font=("Arial", 12))
        self.zoom_label.pack(side="left", padx=10)
        ctk.CTkButton(zoom_frame, text="Zoom +", command=self.zoom_in, width=80,
                     corner_radius=8).pack(side="left", padx=2)
        
        # Frame para el canvas
        canvas_container = ctk.CTkFrame(right_panel, corner_radius=8)
        canvas_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Canvas con scrollbars
        self.canvas = tk.Canvas(canvas_container, bg='#2b2b2b', highlightthickness=0)
        
        v_scroll = ctk.CTkScrollbar(canvas_container, orientation="vertical", command=self.canvas.yview)
        h_scroll = ctk.CTkScrollbar(canvas_container, orientation="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Eventos del canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux scroll down
        
        # Barra de estado
        self.status_bar = ctk.CTkLabel(right_panel, text="Abre un PDF para comenzar", 
                                       corner_radius=8, height=30)
        self.status_bar.pack(fill="x", padx=10, pady=(0, 10))
        
        # Panel de controles de texto (inicialmente oculto)
        self.create_text_controls(right_panel)
        
    def create_text_controls(self, parent):
        """Crear panel de controles para ajustar texto seleccionado"""
        self.text_controls = ctk.CTkFrame(parent, corner_radius=8, fg_color="#1a1a1a", height=80)
        
        # Fila 1: Tamaño y color
        row1 = ctk.CTkFrame(self.text_controls, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(10, 5))
        
        # Título
        ctk.CTkLabel(row1, text="Ajustar Texto:", 
                    font=("Arial", 12, "bold")).pack(side="left", padx=10)
        
        # Botón reducir tamaño
        ctk.CTkButton(row1, text="A-", width=45, command=self.decrease_text_size,
                     font=("Arial", 16, "bold")).pack(side="left", padx=3)
        
        # Label de tamaño
        self.size_label = ctk.CTkLabel(row1, text="Tamaño: 12", 
                                       font=("Arial", 13, "bold"), width=90)
        self.size_label.pack(side="left", padx=8)
        
        # Botón aumentar tamaño
        ctk.CTkButton(row1, text="A+", width=45, command=self.increase_text_size,
                     font=("Arial", 16, "bold")).pack(side="left", padx=3)
        
        # Separador
        ctk.CTkLabel(row1, text="|", font=("Arial", 20)).pack(side="left", padx=10)
        
        # Botón cambiar color
        ctk.CTkButton(row1, text="🎨 Color", width=90, 
                     command=self.change_text_color).pack(side="left", padx=3)
        
        # Fila 2: Formato
        row2 = ctk.CTkFrame(self.text_controls, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(0, 10))
        
        # Label formato
        ctk.CTkLabel(row2, text="Formato:", 
                    font=("Arial", 12, "bold")).pack(side="left", padx=10)
        
        # Checkboxes de formato
        self.bold_var = ctk.BooleanVar(value=False)
        self.bold_check = ctk.CTkCheckBox(row2, text="Negrita", variable=self.bold_var,
                                         command=self.update_text_format, width=90,
                                         font=("Arial", 11, "bold"))
        self.bold_check.pack(side="left", padx=5)
        
        self.italic_var = ctk.BooleanVar(value=False)
        self.italic_check = ctk.CTkCheckBox(row2, text="Cursiva", variable=self.italic_var,
                                           command=self.update_text_format, width=90,
                                           font=("Arial", 11, "italic"))
        self.italic_check.pack(side="left", padx=5)
        
        # Separador
        ctk.CTkLabel(row2, text="|", font=("Arial", 20)).pack(side="left", padx=10)
        
        # Selector de fuente
        ctk.CTkLabel(row2, text="Fuente:", font=("Arial", 11)).pack(side="left", padx=5)
        self.font_var = ctk.StringVar(value="Arial")
        fonts = ["Arial", "Times New Roman", "Courier", "Helvetica", "Comic Sans MS"]
        self.font_combo = ctk.CTkComboBox(row2, values=fonts, variable=self.font_var, 
                                         width=140, command=self.update_text_format)
        self.font_combo.pack(side="left", padx=5)
        
        # Botón deseleccionar
        ctk.CTkButton(row2, text="✓ Listo", width=80, command=self.deselect_text,
                     fg_color="#2ecc71", hover_color="#27ae60").pack(side="left", padx=15)
        
        # Inicialmente oculto
        self.text_controls.pack_forget()
    
    def show_text_controls(self):
        """Mostrar controles de texto"""
        if self.text_controls and self.selected_text:
            _, page_num, ann_index = self.selected_text
            annotation = self.text_annotations[page_num][ann_index]
            
            # Actualizar tamaño
            size = annotation['size']
            self.size_label.configure(text=f"Tamaño: {size}")
            
            # Actualizar formato
            bold = annotation.get('bold', False)
            italic = annotation.get('italic', False)
            font_name = annotation.get('font', 'Arial')
            
            self.bold_var.set(bold)
            self.italic_var.set(italic)
            self.font_var.set(font_name)
            
            self.text_controls.pack(fill="x", padx=10, pady=(0, 10), before=self.status_bar)
    
    def hide_text_controls(self):
        """Ocultar controles de texto"""
        if self.text_controls:
            self.text_controls.pack_forget()
    
    def update_text_format(self, *args):
        """Actualizar formato del texto (negrita, cursiva, fuente)"""
        if self.selected_text:
            _, page_num, ann_index = self.selected_text
            self.text_annotations[page_num][ann_index]['bold'] = self.bold_var.get()
            self.text_annotations[page_num][ann_index]['italic'] = self.italic_var.get()
            self.text_annotations[page_num][ann_index]['font'] = self.font_var.get()
            self.display_page()
    
    def increase_text_size(self):
        """Aumentar tamaño del texto seleccionado"""
        if self.selected_text:
            _, page_num, ann_index = self.selected_text
            current_size = self.text_annotations[page_num][ann_index]['size']
            new_size = min(current_size + 2, 144)
            self.text_annotations[page_num][ann_index]['size'] = new_size
            self.size_label.configure(text=f"Tamaño: {new_size}")
            self.display_page()
    
    def decrease_text_size(self):
        """Disminuir tamaño del texto seleccionado"""
        if self.selected_text:
            _, page_num, ann_index = self.selected_text
            current_size = self.text_annotations[page_num][ann_index]['size']
            new_size = max(current_size - 2, 6)
            self.text_annotations[page_num][ann_index]['size'] = new_size
            self.size_label.configure(text=f"Tamaño: {new_size}")
            self.display_page()
    
    def change_text_color(self):
        """Cambiar color del texto seleccionado"""
        if not self.selected_text:
            return
        
        _, page_num, ann_index = self.selected_text
        
        # Crear diálogo simple para seleccionar color
        color_dialog = ctk.CTkToplevel(self.root)
        color_dialog.title("Seleccionar Color")
        color_dialog.geometry("300x250")
        color_dialog.transient(self.root)
        color_dialog.grab_set()
        
        ctk.CTkLabel(color_dialog, text="Selecciona un color:", 
                    font=("Arial", 14, "bold")).pack(pady=20)
        
        colors = {
            "Negro": (0, 0, 0),
            "Rojo": (1, 0, 0),
            "Azul": (0, 0, 1),
            "Verde": (0, 0.5, 0),
            "Blanco": (1, 1, 1),
            "Amarillo": (1, 1, 0),
            "Naranja": (1, 0.5, 0),
            "Morado": (0.5, 0, 0.5)
        }
        
        for color_name, color_value in colors.items():
            btn = ctk.CTkButton(color_dialog, text=color_name, width=200,
                               command=lambda c=color_value, n=color_name: self.apply_color(c, color_dialog))
            btn.pack(pady=3)
    
    def apply_color(self, color, dialog):
        """Aplicar color seleccionado"""
        if self.selected_text:
            _, page_num, ann_index = self.selected_text
            self.text_annotations[page_num][ann_index]['color'] = color
            self.display_page()
            dialog.destroy()
    
    def deselect_text(self):
        """Deseleccionar texto"""
        self.selected_text = None
        self.hide_text_controls()
        self.display_page()
    
    def on_mouse_wheel(self, event):
        """Cambiar tamaño con rueda del mouse en modo mover"""
        if not self.move_mode or not self.selected_text:
            return
        
        # Detectar dirección del scroll
        if event.num == 5 or event.delta < 0:
            # Scroll down - disminuir
            self.decrease_text_size()
        elif event.num == 4 or event.delta > 0:
            # Scroll up - aumentar
            self.increase_text_size()
    
    def toggle_hide_mode(self):
        self.hide_mode = not self.hide_mode
        self.edit_mode = False
        self.delete_mode = False
        self.move_mode = False
        self.selected_text = None
        self.hide_text_controls()
        
        if self.hide_mode:
            self.hide_btn.configure(fg_color="#e74c3c", text="🗑 Borrar: ON")
            self.edit_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="✏ Agregar Texto")
            self.delete_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="🗑 Eliminar Texto")
            self.move_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="↔ Mover y Editar Texto")
            self.status_bar.configure(text="Modo borrar - Arrastra para seleccionar área de texto a eliminar permanentemente")
            self.canvas.config(cursor="crosshair")
        else:
            self.hide_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="🗑 Borrar Texto")
            self.status_bar.configure(text="Modo borrar desactivado")
            self.canvas.config(cursor="")
    
    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        self.hide_mode = False
        self.delete_mode = False
        self.move_mode = False
        self.selected_text = None
        self.hide_text_controls()
        
        if self.edit_mode:
            self.edit_btn.configure(fg_color="#2ecc71", text="✏ Agregar: ON")
            self.hide_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="▬ Ocultar Texto")
            self.delete_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="🗑 Eliminar Texto")
            self.move_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="↔ Mover y Editar Texto")
            self.status_bar.configure(text="Modo agregar - Haz clic para agregar texto")
            self.canvas.config(cursor="crosshair")
        else:
            self.edit_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="✏ Agregar Texto")
            self.status_bar.configure(text="Modo agregar desactivado")
            self.canvas.config(cursor="")
    
    def toggle_move_mode(self):
        self.move_mode = not self.move_mode
        self.edit_mode = False
        self.hide_mode = False
        self.delete_mode = False
        
        if self.move_mode:
            self.move_btn.configure(fg_color="#9b59b6", text="↔ Mover y editar: ON")
            self.edit_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="✏ Agregar Texto")
            self.hide_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="▬ Ocultar Texto")
            self.delete_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="🗑 Eliminar Texto")
            self.status_bar.configure(text="Modo mover y editar - Arrastra los textos para moverlos")
            self.canvas.config(cursor="hand2")
            self.display_page()
        else:
            self.move_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="↔ Mover y Editar Texto")
            self.status_bar.configure(text="Modo mover y editar desactivado")
            self.canvas.config(cursor="")
            self.display_page()
    
    def toggle_delete_mode(self):
        self.delete_mode = not self.delete_mode
        self.edit_mode = False
        self.hide_mode = False
        self.move_mode = False
        self.selected_text = None
        self.hide_text_controls()
        
        if self.delete_mode:
            self.delete_btn.configure(fg_color="#e74c3c", text="🗑 Eliminar: ON")
            self.edit_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="✏ Agregar Texto")
            self.hide_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="▬ Ocultar Texto")
            self.move_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="↔ Mover y Editar Texto")
            self.status_bar.configure(text="Modo eliminar - Haz clic en un texto para eliminarlo")
            self.canvas.config(cursor="X_cursor")
            self.display_page()
        else:
            self.delete_btn.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="🗑 Eliminar Texto")
            self.status_bar.configure(text="Modo eliminar desactivado")
            self.canvas.config(cursor="")
            self.display_page()
    
    def on_canvas_click(self, event):
        if not self.pdf_document:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Modo mover
        if self.move_mode:
            # Buscar si se hizo clic en un texto
            clicked_item = self.canvas.find_closest(canvas_x, canvas_y)[0]
            if clicked_item in self.text_items:
                page_num, ann_index = self.text_items[clicked_item]
                if page_num == self.current_page:
                    self.dragging_text = (clicked_item, page_num, ann_index)
                    self.selected_text = (clicked_item, page_num, ann_index)
                    self.drag_start = (canvas_x, canvas_y)
                    self.canvas.config(cursor="fleur")
                    self.show_text_controls()
            else:
                # Clic fuera del texto - deseleccionar
                self.selected_text = None
                self.hide_text_controls()
                self.display_page()
            return
        
        # Modo ocultar
        if self.hide_mode:
            self.selection_start = (canvas_x, canvas_y)
            return
        
        # Modo eliminar
        if self.delete_mode:
            clicked_item = self.canvas.find_closest(canvas_x, canvas_y)[0]
            if clicked_item in self.text_items:
                page_num, ann_index = self.text_items[clicked_item]
                if page_num == self.current_page:
                    del self.text_annotations[self.current_page][ann_index]
                    if not self.text_annotations[self.current_page]:
                        del self.text_annotations[self.current_page]
                    self.display_page()
                    self.status_bar.configure(text="Texto eliminado")
            return
        
        # Modo agregar
        if self.edit_mode:
            dialog = TextDialog(self.root)
            self.root.wait_window(dialog)
            
            if dialog.result:
                pdf_x = canvas_x / self.zoom_level
                pdf_y = canvas_y / self.zoom_level
                
                if self.current_page not in self.text_annotations:
                    self.text_annotations[self.current_page] = []
                
                self.text_annotations[self.current_page].append({
                    'x': pdf_x,
                    'y': pdf_y,
                    'text': dialog.result['text'],
                    'size': dialog.result['size'],
                    'color': dialog.result['color'],
                    'bold': False,
                    'italic': False,
                    'font': 'Arial'
                })
                
                self.display_page()
                self.status_bar.configure(text=f"Texto agregado")
    
    def on_canvas_drag(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Modo mover texto
        if self.move_mode and self.dragging_text:
            clicked_item, page_num, ann_index = self.dragging_text
            
            # Calcular desplazamiento
            dx = (canvas_x - self.drag_start[0]) / self.zoom_level
            dy = (canvas_y - self.drag_start[1]) / self.zoom_level
            
            # Actualizar posición del texto
            self.text_annotations[page_num][ann_index]['x'] += dx
            self.text_annotations[page_num][ann_index]['y'] += dy
            
            # Actualizar punto de inicio para el próximo movimiento
            self.drag_start = (canvas_x, canvas_y)
            
            # Redibujar
            self.display_page()
            return
        
        # Modo borrar - dibujar rectángulo de selección
        if self.hide_mode and self.selection_start:
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
            
            self.selection_rect = self.canvas.create_rectangle(
                self.selection_start[0], self.selection_start[1],
                canvas_x, canvas_y,
                outline='#e74c3c',
                width=3,
                dash=(5, 5),
                fill='#e74c3c',
                stipple='gray50'  # Patrón semitransparente
            )
    
    def on_canvas_release(self, event):
        # Soltar texto en modo mover
        if self.move_mode and self.dragging_text:
            self.dragging_text = None
            self.drag_start = None
            self.canvas.config(cursor="hand2")
            self.status_bar.configure(text="Texto reposicionado")
            return
        
        # Completar selección en modo ocultar
        if self.hide_mode and self.selection_start:
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            x0 = min(self.selection_start[0], canvas_x) / self.zoom_level
            y0 = min(self.selection_start[1], canvas_y) / self.zoom_level
            x1 = max(self.selection_start[0], canvas_x) / self.zoom_level
            y1 = max(self.selection_start[1], canvas_y) / self.zoom_level
            
            if abs(x1 - x0) > 5 and abs(y1 - y0) > 5:
                if self.current_page not in self.hide_rectangles:
                    self.hide_rectangles[self.current_page] = []
                
                self.hide_rectangles[self.current_page].append((x0, y0, x1, y1))
                self.status_bar.configure(text="Área marcada para borrar - El texto se eliminará al guardar")
            
            if self.selection_rect:
                self.canvas.delete(self.selection_rect)
            self.selection_start = None
            self.selection_rect = None
            
            self.display_page()
    
    def clear_page_texts(self):
        if not self.pdf_document:
            messagebox.showwarning("Advertencia", "No hay PDF abierto")
            return
        
        if self.current_page in self.text_annotations:
            result = messagebox.askyesno("Confirmar", 
                                         "¿Eliminar todos los textos agregados de esta página?")
            if result:
                del self.text_annotations[self.current_page]
                self.display_page()
                self.status_bar.configure(text="Textos eliminados")
    
    def clear_page_hides(self):
        if not self.pdf_document:
            messagebox.showwarning("Advertencia", "No hay PDF abierto")
            return
        
        if self.current_page in self.hide_rectangles:
            result = messagebox.askyesno("Confirmar", 
                                         "¿Eliminar todas las áreas marcadas para borrar de esta página?")
            if result:
                del self.hide_rectangles[self.current_page]
                self.display_page()
                self.status_bar.configure(text="Áreas de borrado eliminadas")
    
    def open_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar PDF",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        
        if file_path:
            try:
                self.pdf_document = fitz.open(file_path)
                self.pdf_path = file_path
                self.current_page = 0
                self.zoom_level = 1.0
                self.text_annotations = {}
                self.hide_rectangles = {}
                self.display_page()
                self.status_bar.configure(text=f"PDF cargado: {file_path.split('/')[-1]}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el PDF:\n{str(e)}")
    
    def display_page(self):
        if not self.pdf_document:
            return
        
        try:
            page = self.pdf_document[self.current_page]
            
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=mat)
            
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self.photo = ImageTk.PhotoImage(img)
            
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
            # Dibujar áreas ocultas
            if self.current_page in self.hide_rectangles:
                for rect in self.hide_rectangles[self.current_page]:
                    x0, y0, x1, y1 = rect
                    # Mostrar con patrón de borrado
                    self.canvas.create_rectangle(
                        x0 * self.zoom_level, y0 * self.zoom_level,
                        x1 * self.zoom_level, y1 * self.zoom_level,
                        fill='white', outline='red', width=2,
                        dash=(5, 5), tags="hide_rect"
                    )
            
            self.text_items = {}
            
            # Dibujar textos
            if self.current_page in self.text_annotations:
                for idx, annotation in enumerate(self.text_annotations[self.current_page]):
                    x = annotation['x'] * self.zoom_level
                    y = annotation['y'] * self.zoom_level
                    
                    color = annotation['color']
                    hex_color = '#{:02x}{:02x}{:02x}'.format(
                        int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
                    )
                    
                    font_size = int(annotation['size'] * self.zoom_level)
                    
                    # Construir el estilo de fuente
                    font_name = annotation.get('font', 'Arial')
                    font_style = []
                    
                    if annotation.get('bold', False):
                        font_style.append('bold')
                    if annotation.get('italic', False):
                        font_style.append('italic')
                    
                    # Si no hay estilos, usar normal
                    if not font_style:
                        font_tuple = (font_name, font_size)
                    else:
                        font_tuple = (font_name, font_size, ' '.join(font_style))
                    
                    text_id = self.canvas.create_text(
                        x, y, text=annotation['text'], anchor=tk.NW,
                        fill=hex_color, font=font_tuple,
                        tags="editable_text"
                    )
                    
                    self.text_items[text_id] = (self.current_page, idx)
                    
                    # Mostrar borde en modo eliminar o mover
                    if self.delete_mode or self.move_mode:
                        bbox = self.canvas.bbox(text_id)
                        if bbox:
                            # Si es el texto seleccionado, usar borde especial
                            if self.selected_text and self.selected_text[1:] == (self.current_page, idx):
                                border_color = '#f39c12'
                                width = 3
                            else:
                                border_color = '#e74c3c' if self.delete_mode else '#9b59b6'
                                width = 2
                            
                            self.canvas.create_rectangle(
                                bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2,
                                outline=border_color, dash=(2, 2), width=width,
                                tags="highlight"
                            )
            
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
            
            total_pages = len(self.pdf_document)
            self.page_label.configure(text=f"Página: {self.current_page + 1}/{total_pages}")
            self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar la página:\n{str(e)}")
    
    def next_page(self):
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.display_page()
    
    def prev_page(self):
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.display_page()
    
    def zoom_in(self):
        if self.pdf_document:
            self.zoom_level = min(self.zoom_level + 0.2, 3.0)
            self.display_page()
    
    def zoom_out(self):
        if self.pdf_document:
            self.zoom_level = max(self.zoom_level - 0.2, 0.5)
            self.display_page()
    
    def rotate_page(self, angle):
        if not self.pdf_document:
            messagebox.showwarning("Advertencia", "No hay PDF abierto")
            return
        
        try:
            page = self.pdf_document[self.current_page]
            page.set_rotation(page.rotation + angle)
            self.display_page()
            self.status_bar.configure(text=f"Página rotada {angle}°")
        except Exception as e:
            messagebox.showerror("Error", f"Error al rotar página:\n{str(e)}")
    
    def delete_page(self):
        if not self.pdf_document:
            messagebox.showwarning("Advertencia", "No hay PDF abierto")
            return
        
        if len(self.pdf_document) == 1:
            messagebox.showwarning("Advertencia", "No se puede eliminar la única página")
            return
        
        result = messagebox.askyesno("Confirmar", 
                                     f"¿Eliminar página {self.current_page + 1}?")
        if result:
            try:
                if self.current_page in self.text_annotations:
                    del self.text_annotations[self.current_page]
                if self.current_page in self.hide_rectangles:
                    del self.hide_rectangles[self.current_page]
                
                new_annotations = {}
                for page_num, annotations in self.text_annotations.items():
                    if page_num > self.current_page:
                        new_annotations[page_num - 1] = annotations
                    else:
                        new_annotations[page_num] = annotations
                self.text_annotations = new_annotations
                
                new_hides = {}
                for page_num, rects in self.hide_rectangles.items():
                    if page_num > self.current_page:
                        new_hides[page_num - 1] = rects
                    else:
                        new_hides[page_num] = rects
                self.hide_rectangles = new_hides
                
                self.pdf_document.delete_page(self.current_page)
                
                if self.current_page >= len(self.pdf_document):
                    self.current_page = len(self.pdf_document) - 1
                
                self.display_page()
                self.status_bar.configure(text="Página eliminada")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar página:\n{str(e)}")
    
    def apply_modifications(self):
        """Aplica todas las modificaciones al documento PDF"""
        for page_num in range(len(self.pdf_document)):
            page = self.pdf_document[page_num]
            
            # BORRAR texto en las áreas marcadas (nueva funcionalidad)
            if page_num in self.hide_rectangles:
                for rect in self.hide_rectangles[page_num]:
                    x0, y0, x1, y1 = rect
                    redact_rect = fitz.Rect(x0, y0, x1, y1)
                    
                    # Agregar anotación de redacción
                    page.add_redact_annot(redact_rect, fill=(1, 1, 1))
                
                # Aplicar las redacciones (esto elimina el texto permanentemente)
                page.apply_redactions()
            
            # Aplicar textos agregados
            if page_num in self.text_annotations:
                for annotation in self.text_annotations[page_num]:
                    try:
                        # Determinar el nombre de la fuente para PyMuPDF
                        font_name = annotation.get('font', 'Arial')
                        bold = annotation.get('bold', False)
                        italic = annotation.get('italic', False)
                        
                        # Mapear fuentes a nombres de PyMuPDF
                        font_map = {
                            'Arial': 'helv',
                            'Times New Roman': 'times',
                            'Courier': 'cour',
                            'Helvetica': 'helv',
                            'Comic Sans MS': 'helv'
                        }
                        
                        base_font = font_map.get(font_name, 'helv')
                        
                        # Construir nombre de fuente con estilo
                        if bold and italic:
                            pymupdf_font = f"{base_font}bi"
                        elif bold:
                            pymupdf_font = f"{base_font}bd"
                        elif italic:
                            pymupdf_font = f"{base_font}it"
                        else:
                            pymupdf_font = base_font
                        
                        page.insert_text(
                            (annotation['x'], annotation['y']),
                            annotation['text'],
                            fontname=pymupdf_font,
                            fontsize=annotation['size'],
                            color=annotation['color']
                        )
                    except Exception as e:
                        print(f"Error al aplicar texto en página {page_num}: {e}")
                        # Intento con fuente por defecto si falla
                        try:
                            page.insert_text(
                                (annotation['x'], annotation['y']),
                                annotation['text'],
                                fontsize=annotation['size'],
                                color=annotation['color']
                            )
                        except:
                            pass
    
    def save_pdf(self):
        if not self.pdf_document:
            messagebox.showwarning("Advertencia", "No hay PDF para guardar")
            return
        
        if not self.pdf_path:
            self.save_pdf_as()
            return
        
        try:
            self.apply_modifications()
            self.pdf_document.save(self.pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
            self.status_bar.configure(text=f"PDF guardado correctamente")
            messagebox.showinfo("Éxito", "PDF guardado correctamente")
            
            # Recargar
            temp_path = self.pdf_path
            temp_page = self.current_page
            temp_zoom = self.zoom_level
            self.pdf_document.close()
            self.pdf_document = fitz.open(temp_path)
            self.current_page = temp_page
            self.zoom_level = temp_zoom
            self.text_annotations = {}
            self.hide_rectangles = {}
            self.display_page()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar PDF:\n{str(e)}")
    
    def save_pdf_as(self):
        if not self.pdf_document:
            messagebox.showwarning("Advertencia", "No hay PDF para guardar")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Guardar PDF como",
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        
        if file_path:
            try:
                self.apply_modifications()
                self.pdf_document.save(file_path)
                self.pdf_path = file_path
                self.status_bar.configure(text=f"PDF guardado: {file_path.split('/')[-1]}")
                messagebox.showinfo("Éxito", "PDF guardado correctamente")
                
                # Recargar
                temp_page = self.current_page
                temp_zoom = self.zoom_level
                self.pdf_document.close()
                self.pdf_document = fitz.open(file_path)
                self.current_page = temp_page
                self.zoom_level = temp_zoom
                self.text_annotations = {}
                self.hide_rectangles = {}
                self.display_page()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar PDF:\n{str(e)}")

if __name__ == "__main__":
    root = ctk.CTk()
    app = PDFEditor(root)
    root.mainloop()