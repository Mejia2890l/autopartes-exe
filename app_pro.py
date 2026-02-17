import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from rembg import remove
from PIL import Image, ImageOps

# ================= LA FÓRMULA MERCADO LIBRE =================
TAMANO_FINAL = (1200, 1200) # Resolución que activa el ZOOM
MARGEN_PIEZA = 50           # Píxeles de aire alrededor (para que no toque el borde)
CALIDAD_JPG = 95            # Calidad máxima sin pesar demasiado
# ============================================================

class AutoPartesFinalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Optimizador Mercado Libre 1200px | NIDUAL")
        self.root.geometry("700x600")
        
        # Variables
        self.ruta_entrada = tk.StringVar()
        self.ruta_salida = tk.StringVar()
        self.procesando = False

        # --- Interfaz Gráfica Limpia ---
        main_container = ttk.Frame(root, padding=20)
        main_container.pack(fill=BOTH, expand=YES)

        # Título
        lbl_header = ttk.Label(main_container, text="Estándar Mercado Libre (1200x1200px)", font=("Helvetica", 16, "bold"), bootstyle="primary")
        lbl_header.pack(pady=(0, 20))

        # 1. Entrada
        lbl_f1 = ttk.Label(main_container, text="1. Carpeta con FOTOS CRUDAS", font=("Helvetica", 10, "bold"))
        lbl_f1.pack(anchor="w")
        frame_entrada = ttk.Frame(main_container)
        frame_entrada.pack(fill=X, pady=5)
        ttk.Entry(frame_entrada, textvariable=self.ruta_entrada).pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        ttk.Button(frame_entrada, text="📂 Buscar Carpeta", command=self.seleccionar_entrada, bootstyle="secondary-outline").pack(side=LEFT)

        # 2. Salida
        lbl_f2 = ttk.Label(main_container, text="2. Carpeta DESTINO (Listas para publicar)", font=("Helvetica", 10, "bold"))
        lbl_f2.pack(anchor="w", pady=(20, 0))
        frame_salida = ttk.Frame(main_container)
        frame_salida.pack(fill=X, pady=5)
        ttk.Entry(frame_salida, textvariable=self.ruta_salida).pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        ttk.Button(frame_salida, text="📂 Buscar Carpeta", command=self.seleccionar_salida, bootstyle="secondary-outline").pack(side=LEFT)

        # Botón de Acción
        self.btn_iniciar = ttk.Button(main_container, text="⚡ PROCESAR Y ESTANDARIZAR IMÁGENES", bootstyle="success", command=self.iniciar_hilo)
        self.btn_iniciar.pack(fill=X, pady=30, ipady=15)

        # Barra de Progreso
        lbl_prog = ttk.Label(main_container, text="Progreso:", font=("Helvetica", 9))
        lbl_prog.pack(anchor="w")
        self.barra = ttk.Progressbar(main_container, orient="horizontal", mode="determinate", bootstyle="success-striped")
        self.barra.pack(fill=X, pady=(0,10))

        # Consola
        self.log = scrolledtext.ScrolledText(main_container, height=10, state='disabled', font=("Consolas", 9))
        self.log.pack(fill=BOTH, expand=YES)

    def log_msg(self, mensaje, tipo="info"):
        self.log.config(state='normal')
        tag = "normal"
        if tipo == "error":
             self.log.tag_config("err", foreground="red")
             tag = "err"
        elif tipo == "success":
             self.log.tag_config("succ", foreground="green")
             tag = "succ"
        self.log.insert(tk.END, "• " + mensaje + "\n", tag)
        self.log.see(tk.END)
        self.log.config(state='disabled')

    def seleccionar_entrada(self):
        f = filedialog.askdirectory()
        if f: self.ruta_entrada.set(f)

    def seleccionar_salida(self):
        f = filedialog.askdirectory()
        if f: self.ruta_salida.set(f)

    def iniciar_hilo(self):
        if not self.ruta_entrada.get() or not self.ruta_salida.get():
            messagebox.showwarning("Error", "Selecciona ambas carpetas.")
            return
        if self.procesando: return

        self.procesando = True
        self.btn_iniciar.config(state="disabled", text="⏳ Optimizando resoluciones...")
        hilo = threading.Thread(target=self.procesar_imagenes)
        hilo.start()

    def procesar_una_imagen(self, ruta_img_entrada, ruta_img_salida):
        # 1. Cargar imagen original
        inp = Image.open(ruta_img_entrada)
        
        # 2. IA: Eliminar fondo
        img_sin_fondo = remove(inp)

        # 3. Recortar espacios vacíos (Bounding Box)
        # Esto es vital para que la pieza ocupe el máximo espacio posible real
        bbox = img_sin_fondo.getbbox()
        if bbox:
            img_trimmed = img_sin_fondo.crop(bbox)
        else:
            img_trimmed = img_sin_fondo

        # 4. Crear Lienzo Mercado Libre (1200x1200 Blanco Puro)
        lienzo = Image.new("RGB", TAMANO_FINAL, (255, 255, 255))

        # 5. Calcular tamaño seguro (1200 menos el margen)
        ancho_util = TAMANO_FINAL[0] - (MARGEN_PIEZA * 2)
        alto_util = TAMANO_FINAL[1] - (MARGEN_PIEZA * 2)
        
        # 6. Redimensionar INTELIGENTE (ImageOps.contain)
        # Esto escala la pieza para que encaje en el área útil SIN deformarse
        # Y usa el filtro LANCZOS (el mejor para nitidez)
        img_lista = ImageOps.contain(img_trimmed, (ancho_util, alto_util), method=Image.Resampling.LANCZOS)
        
        # 7. Centrar Matemáticamente
        pos_x = (TAMANO_FINAL[0] - img_lista.width) // 2
        pos_y = (TAMANO_FINAL[1] - img_lista.height) // 2
        
        # Pegar pieza sobre lienzo blanco
        lienzo.paste(img_lista, (pos_x, pos_y), img_lista)

        # 8. Guardar como JPG Optimizado
        # 'optimize=True' reduce el peso del archivo sin bajar calidad visible
        ruta_salida_jpg = os.path.splitext(ruta_img_salida)[0] + ".jpg"
        lienzo.save(ruta_salida_jpg, "JPEG", quality=CALIDAD_JPG, optimize=True)

    def procesar_imagenes(self):
        entrada = self.ruta_entrada.get()
        salida = self.ruta_salida.get()
        
        archivos = []
        for raiz, dirs, ficheros in os.walk(entrada):
            for nombre in ficheros:
                if nombre.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
                    archivos.append(os.path.join(raiz, nombre))

        total = len(archivos)
        self.barra["maximum"] = total
        exitos = 0
        errores = 0

        for i, ruta in enumerate(archivos):
            try:
                # Replicar estructura de carpetas
                relativa = os.path.relpath(ruta, entrada)
                destino = os.path.join(salida, relativa)
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                
                self.procesar_una_imagen(ruta, destino)
                
                exitos += 1
                self.log_msg(f"OK (1200px): {os.path.basename(ruta)}", "success")
            except Exception as e:
                errores += 1
                self.log_msg(f"Error: {str(e)}", "error")
            
            self.barra["value"] = i + 1
            self.root.update_idletasks()

        self.procesando = False
        self.btn_iniciar.config(state="normal", text="⚡ PROCESAR Y ESTANDARIZAR IMÁGENES")
        messagebox.showinfo("Proceso Terminado", f"¡Listo!\n\nSe generaron {exitos} imágenes.\nTodas cumplen el estándar 1200x1200px de Mercado Libre.")

if __name__ == "__main__":
    root = ttk.Window(themename="journal") 
    app = AutoPartesFinalApp(root)
    root.mainloop()