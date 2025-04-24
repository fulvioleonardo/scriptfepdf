import fitz  # PyMuPDF para leer PDFs
import requests
from fpdf import FPDF
import qrcode
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
import json
import os
from datetime import datetime
import certifi

# CONFIGURACIÓN
CONFIG_FILE = "config.json"
ERRORS_DIR = "errores"
GENERATED_PDFS_DIR = "facturas_generadas"

# Crear carpetas necesarias si no existen
for directory in [ERRORS_DIR, GENERATED_PDFS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Cargar configuración desde el archivo JSON
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        default_config = {
            "API_URL": "https://api.ingjhoanyduarte.site/",
            "TOKEN": "10d2de2ff8932fa737c2bcaf495c89ca8c1a91dd46911140ff0162849489ba22"
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config

config = load_config()

def log_error(error_message):
    """Registra los errores en un archivo de texto dentro de la carpeta 'errores'."""
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    log_filename = os.path.join(ERRORS_DIR, f"errors_{now.strftime('%Y-%m-%d')}.txt")
    with open(log_filename, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {error_message}\n")

def extract_data_from_pdf(pdf_path):
    """Extrae los datos necesarios para emitir una factura electrónica desde un archivo PDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()

        # Aquí puedes ajustar la lógica para extraer los datos específicos del PDF
        # Ejemplo de datos extraídos:
        data = {
            "customer_name": "Cliente de Prueba",
            "customer_email": "cliente@prueba.com",
            "customer_nit": "123456789",
            "description": "Producto de prueba",
            "price": 100000.00,
            "tax": 19000.00,
            "total": 119000.00,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S")
        }
        return data
    except Exception as e:
        raise Exception(f"Error al extraer datos del PDF: {e}")

def generar_pdf_con_qr(factura, cufe, qr_data, pdf_base_path):
    """Genera un nuevo PDF basado en el original, añadiendo el QR, CUFE y la información de la factura."""
    try:
        # Abrir el PDF base
        doc = fitz.open(pdf_base_path)
        page = doc[0]  # Trabajar con la primera página

        # Añadir el CUFE
        page.insert_text((50, 700), f"CUFE: {cufe}", fontsize=12, color=(0, 0, 0))

        # Añadir el QR
        qr = qrcode.make(qr_data)
        qr_path = os.path.join(GENERATED_PDFS_DIR, "qr_temp.png")
        qr.save(qr_path)
        page.insert_image((50, 750, 150, 850), filename=qr_path)

        # Guardar el nuevo PDF
        pdf_path = os.path.join(GENERATED_PDFS_DIR, f"factura_{factura['number']}.pdf")
        doc.save(pdf_path)
        os.remove(qr_path)  # Eliminar el QR temporal
        return pdf_path
    except Exception as e:
        raise Exception(f"Error al generar el PDF con QR: {e}")

def procesar_factura():
    """Selecciona un PDF, extrae los datos necesarios y emite la factura electrónica."""
    pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if not pdf_path:
        return

    try:
        # Extraer datos del PDF
        data = extract_data_from_pdf(pdf_path)

        # Construir el JSON para la factura electrónica
        factura = {
            "number": 990000001,
            "type_document_id": 1,
            "date": data["date"],
            "time": data["time"],
            "customer": {
                "identification_number": data["customer_nit"],
                "name": data["customer_name"],
                "email": data["customer_email"]
            },
            "legal_monetary_totals": {
                "line_extension_amount": f"{data['price']:.2f}",
                "tax_exclusive_amount": f"{data['price']:.2f}",
                "tax_inclusive_amount": f"{data['total']:.2f}",
                "payable_amount": f"{data['total']:.2f}"
            },
            "invoice_lines": [
                {
                    "description": data["description"],
                    "price_amount": f"{data['price']:.2f}",
                    "quantity": 1,
                    "taxes": [
                        {
                            "tax_id": 1,
                            "tax_amount": f"{data['tax']:.2f}",
                            "percent": "19.00"
                        }
                    ]
                }
            ]
        }

        # Enviar la factura electrónica
        cufe, qr_data = enviar_factura_electronica(factura)

        # Generar el PDF con QR y CUFE
        pdf_generado = generar_pdf_con_qr(factura, cufe, qr_data, pdf_path)
        messagebox.showinfo("Éxito", f"Factura procesada y guardada en: {pdf_generado}")
    except Exception as e:
        error_message = f"Error al procesar la factura: {e}"
        log_error(error_message)
        messagebox.showerror("Error", error_message)

def enviar_factura_electronica(factura):
    """Envía una factura electrónica a la DIAN."""
    url = f"{config['API_URL']}ubl2.1/invoice"
    headers = {
        "Authorization": f"Bearer {config['TOKEN']}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=factura, verify=False)  # Deshabilitar verificación SSL
        if response.status_code == 200:
            response_data = response.json()
            cufe = response_data.get("cufe", "CUFE_NO_DISPONIBLE")
            qr_data = response_data.get("qr_data", "QR_NO_DISPONIBLE")
            return cufe, qr_data
        else:
            raise Exception(f"Error en la API: {response.status_code} - {response.text}")
    except Exception as e:
        error_message = f"Error al enviar la factura: {e}"
        log_error(error_message)
        messagebox.showerror("Error", error_message)
        raise

def verificar_estado_conexion():
    """Verifica el estado de conexión con la API."""
    url = f"{config['API_URL']}ubl2.1/status"
    headers = {"Authorization": f"Bearer {config['TOKEN']}"}

    try:
        response = requests.get(url, headers=headers, verify=False)  # Deshabilitar verificación SSL
        if response.status_code == 200:
            messagebox.showinfo("Conexión Exitosa", "La conexión con la API es exitosa.")
        else:
            raise Exception(f"Error en la API: {response.status_code} - {response.text}")
    except Exception as e:
        error_message = f"Error al verificar la conexión con la API: {e}"
        log_error(error_message)
        messagebox.showerror("Error", error_message)

def main():
    """Interfaz gráfica principal."""
    root = tk.Tk()
    root.title("Facturas Electrónicas Eleventas")
    root.geometry("800x600")
    root.resizable(False, False)

    # Encabezado
    header_frame = ttk.Frame(root)
    header_frame.pack(fill="x", pady=10)

    header_label = ttk.Label(
        header_frame,
        text="Facturas Electrónicas Eleventas\nDiseñado por Fullsys Tecnología Santa Marta",
        font=("Arial", 16, "bold"),
        anchor="center"
    )
    header_label.pack(pady=10)

    # Contenedor principal
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill="both", expand=True)

    # Botones organizados en dos columnas
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(expand=True)

    ttk.Button(button_frame, text="Seleccionar PDF y Procesar", command=procesar_factura).grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    ttk.Button(button_frame, text="Verificar Conexión con API", command=verificar_estado_conexion).grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    root.mainloop()


if __name__ == "__main__":
    main()