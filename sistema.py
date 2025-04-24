import fitz  # PyMuPDF para leer PDFs
import requests
from fpdf import FPDF
import qrcode
from tkinter import ttk, messagebox, filedialog, simpledialog
import tkinter as tk
import json
import os
from datetime import datetime

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

def configurar_api():
    """Permite configurar el URL de la API y el token."""
    api_url = simpledialog.askstring("Configurar API", "Ingrese el URL de la API:", initialvalue=config["API_URL"])
    token = simpledialog.askstring("Configurar Token", "Ingrese el token de la API:", initialvalue=config["TOKEN"])

    if api_url and token:
        config["API_URL"] = api_url
        config["TOKEN"] = token
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        messagebox.showinfo("Configuración", "La configuración se ha guardado correctamente.")
    else:
        messagebox.showwarning("Configuración", "No se realizaron cambios en la configuración.")

def verificar_conexion():
    """Verifica la conexión con la API."""
    url = f"{config['API_URL']}ubl2.1/status"
    headers = {"Authorization": f"Bearer {config['TOKEN']}"}

    try:
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            messagebox.showinfo("Conexión Exitosa", "La conexión con la API es exitosa.")
        else:
            raise Exception(f"Error en la API: {response.status_code} - {response.text}")
    except Exception as e:
        error_message = f"Error al verificar la conexión con la API: {e}"
        log_error(error_message)
        messagebox.showerror("Error", error_message)

def enviar_nota_credito():
    """Envía una nota crédito a la DIAN solicitando los datos necesarios."""
    try:
        # Solicitar datos al usuario
        cufe = simpledialog.askstring("Nota Crédito", "Ingrese el CUFE de la factura a la que se aplicará la nota:")
        if not cufe:
            messagebox.showwarning("Datos incompletos", "Debe ingresar el CUFE.")
            return

        number = simpledialog.askinteger("Nota Crédito", "Ingrese el número de la nota crédito:")
        discrepancy_code = simpledialog.askinteger("Nota Crédito", "Ingrese el código de discrepancia (1: Anulación, 2: Corrección):", initialvalue=2)
        discrepancy_description = simpledialog.askstring("Nota Crédito", "Ingrese la descripción de la discrepancia:", initialvalue="Corrección de factura")
        notes = simpledialog.askstring("Nota Crédito", "Ingrese las notas de la nota crédito:", initialvalue="Nota crédito generada")
        total = simpledialog.askfloat("Nota Crédito", "Ingrese el total de la nota crédito:")

        if not all([number, discrepancy_code, discrepancy_description, notes, total]):
            messagebox.showwarning("Datos incompletos", "Debe ingresar todos los datos necesarios.")
            return

        # Construir el JSON de la nota crédito
        nota_credito = {
            "billing_reference": {
                "number": number,
                "uuid": cufe,
                "issue_date": datetime.now().strftime("%Y-%m-%d")
            },
            "discrepancyresponsecode": discrepancy_code,
            "discrepancyresponsedescription": discrepancy_description,
            "notes": notes,
            "resolution_number": "0000000000",
            "prefix": "NC",
            "number": number,
            "type_document_id": 4,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "customer": {
                "identification_number": "123456789",
                "name": "Cliente de Prueba",
                "phone": "3101234567",
                "address": "Dirección de Prueba",
                "email": "cliente@prueba.com",
                "merchant_registration": "0000-00",
                "type_document_identification_id": 3,
                "type_organization_id": 2,
                "municipality_id": 149,
                "type_regime_id": 2
            },
            "legal_monetary_totals": {
                "line_extension_amount": f"{total:.2f}",
                "tax_exclusive_amount": f"{total:.2f}",
                "tax_inclusive_amount": f"{total:.2f}",
                "payable_amount": f"{total:.2f}"
            },
            "credit_note_lines": [
                {
                    "unit_measure_id": 70,
                    "invoiced_quantity": "1",
                    "line_extension_amount": f"{total:.2f}",
                    "free_of_charge_indicator": False,
                    "description": "Corrección de factura",
                    "code": "NC",
                    "price_amount": f"{total:.2f}",
                    "base_quantity": "1"
                }
            ]
        }

        # Enviar la nota crédito a la API
        url = f"{config['API_URL']}ubl2.1/credit-note"
        headers = {
            "Authorization": f"Bearer {config['TOKEN']}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=nota_credito, verify=False)
        if response.status_code == 200:
            messagebox.showinfo("Éxito", "Nota crédito enviada correctamente.")
        else:
            raise Exception(f"Error en la API: {response.status_code} - {response.text}")
    except Exception as e:
        error_message = f"Error al enviar la nota crédito: {e}"
        log_error(error_message)
        messagebox.showerror("Error", error_message)


def enviar_nota_debito():
    """Envía una nota débito a la DIAN solicitando los datos necesarios."""
    try:
        # Solicitar datos al usuario
        cufe = simpledialog.askstring("Nota Débito", "Ingrese el CUFE de la factura a la que se aplicará la nota:")
        if not cufe:
            messagebox.showwarning("Datos incompletos", "Debe ingresar el CUFE.")
            return

        number = simpledialog.askinteger("Nota Débito", "Ingrese el número de la nota débito:")
        notes = simpledialog.askstring("Nota Débito", "Ingrese las notas de la nota débito:", initialvalue="Nota débito generada")
        total = simpledialog.askfloat("Nota Débito", "Ingrese el total de la nota débito:")

        if not all([number, notes, total]):
            messagebox.showwarning("Datos incompletos", "Debe ingresar todos los datos necesarios.")
            return

        # Construir el JSON de la nota débito
        nota_debito = {
            "billing_reference": {
                "number": number,
                "uuid": cufe,
                "issue_date": datetime.now().strftime("%Y-%m-%d")
            },
            "notes": notes,
            "resolution_number": "0000000000",
            "prefix": "ND",
            "number": number,
            "type_document_id": 5,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "customer": {
                "identification_number": "123456789",
                "name": "Cliente de Prueba",
                "phone": "3101234567",
                "address": "Dirección de Prueba",
                "email": "cliente@prueba.com",
                "merchant_registration": "0000-00",
                "type_document_identification_id": 3,
                "type_organization_id": 2,
                "municipality_id": 149,
                "type_regime_id": 2
            },
            "legal_monetary_totals": {
                "line_extension_amount": f"{total:.2f}",
                "tax_exclusive_amount": f"{total:.2f}",
                "tax_inclusive_amount": f"{total:.2f}",
                "payable_amount": f"{total:.2f}"
            },
            "debit_note_lines": [
                {
                    "unit_measure_id": 70,
                    "invoiced_quantity": "1",
                    "line_extension_amount": f"{total:.2f}",
                    "free_of_charge_indicator": False,
                    "description": "Ajuste de factura",
                    "code": "ND",
                    "price_amount": f"{total:.2f}",
                    "base_quantity": "1"
                }
            ]
        }

        # Enviar la nota débito a la API
        url = f"{config['API_URL']}ubl2.1/debit-note"
        headers = {
            "Authorization": f"Bearer {config['TOKEN']}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=nota_debito, verify=False)
        if response.status_code == 200:
            messagebox.showinfo("Éxito", "Nota débito enviada correctamente.")
        else:
            raise Exception(f"Error en la API: {response.status_code} - {response.text}")
    except Exception as e:
        error_message = f"Error al enviar la nota débito: {e}"
        log_error(error_message)
        messagebox.showerror("Error", error_message)

def consultar_resolucion():
    """Consulta las resoluciones configuradas en la API."""
    try:
        url = f"{config['API_URL']}ubl2.1/config/resolution"
        headers = {"Authorization": f"Bearer {config['TOKEN']}"}

        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            resoluciones = response.json()
            messagebox.showinfo("Resoluciones", f"Resoluciones configuradas: {resoluciones}")
        else:
            raise Exception(f"Error en la API: {response.status_code} - {response.text}")
    except Exception as e:
        error_message = f"Error al consultar resoluciones: {e}"
        log_error(error_message)
        messagebox.showerror("Error", error_message)

def subir_resolucion():
    """Sube una nueva resolución a la API solicitando los datos al usuario."""
    try:
        # Solicitar datos al usuario
        type_document_id = simpledialog.askinteger("Subir Resolución", "Ingrese el ID del tipo de documento (1 para facturas):", initialvalue=1)
        prefix = simpledialog.askstring("Subir Resolución", "Ingrese el prefijo de la resolución:", initialvalue="SETP")
        resolution = simpledialog.askstring("Subir Resolución", "Ingrese el número de la resolución:", initialvalue="18760000001")
        resolution_date = simpledialog.askstring("Subir Resolución", "Ingrese la fecha de la resolución (YYYY-MM-DD):", initialvalue="2019-01-19")
        technical_key = simpledialog.askstring("Subir Resolución", "Ingrese la llave técnica:", initialvalue="fc8eac422eba16e22ffd8c6f94b3f40a6e38162c")
        from_number = simpledialog.askinteger("Subir Resolución", "Ingrese el número inicial del rango:", initialvalue=990000000)
        to_number = simpledialog.askinteger("Subir Resolución", "Ingrese el número final del rango:", initialvalue=995000000)
        date_from = simpledialog.askstring("Subir Resolución", "Ingrese la fecha de inicio de la resolución (YYYY-MM-DD):", initialvalue="2019-01-19")
        date_to = simpledialog.askstring("Subir Resolución", "Ingrese la fecha de fin de la resolución (YYYY-MM-DD):", initialvalue="2030-01-19")

        # Validar que todos los datos fueron ingresados
        if not all([type_document_id, prefix, resolution, resolution_date, technical_key, from_number, to_number, date_from, date_to]):
            messagebox.showwarning("Datos incompletos", "Debe ingresar todos los datos para subir la resolución.")
            return

        # Construir el JSON de la resolución
        resolution_data = {
            "type_document_id": type_document_id,
            "prefix": prefix,
            "resolution": resolution,
            "resolution_date": resolution_date,
            "technical_key": technical_key,
            "from": from_number,
            "to": to_number,
            "generated_to_date": 0,
            "date_from": date_from,
            "date_to": date_to
        }

        # Enviar la resolución a la API
        url = f"{config['API_URL']}ubl2.1/config/resolution"
        headers = {
            "Authorization": f"Bearer {config['TOKEN']}",
            "Content-Type": "application/json"
        }

        response = requests.put(url, headers=headers, json=resolution_data, verify=False)
        if response.status_code == 200:
            messagebox.showinfo("Éxito", "Resolución subida correctamente.")
        else:
            raise Exception(f"Error en la API: {response.status_code} - {response.text}")
    except Exception as e:
        error_message = f"Error al subir resolución: {e}"
        log_error(error_message)
        messagebox.showerror("Error", error_message)

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
        pdf_generado = generar_pdf_con_qr(factura, cufe, qr_data)
        messagebox.showinfo("Éxito", f"Factura procesada y guardada en: {pdf_generado}")
    except Exception as e:
        error_message = f"Error al procesar la factura: {e}"
        log_error(error_message)
        messagebox.showerror("Error", error_message)

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

def generar_pdf_con_qr(factura, cufe, qr_data):
    """Genera un PDF con la información de la factura, incluyendo el QR y el CUFE."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Título
    pdf.cell(200, 10, txt="Factura Electrónica", ln=True, align="C")

    # Información del cliente
    pdf.cell(200, 10, txt=f"Cliente: {factura['customer']['name']}", ln=True)
    pdf.cell(200, 10, txt=f"NIT: {factura['customer']['identification_number']}", ln=True)
    pdf.cell(200, 10, txt=f"Email: {factura['customer']['email']}", ln=True)

    # Información de la factura
    pdf.cell(200, 10, txt=f"Fecha: {factura['date']}", ln=True)
    pdf.cell(200, 10, txt=f"Hora: {factura['time']}", ln=True)
    pdf.cell(200, 10, txt=f"Total: {factura['legal_monetary_totals']['payable_amount']}", ln=True)

    # CUFE
    pdf.cell(200, 10, txt=f"CUFE: {cufe}", ln=True)

    # Generar el QR
    qr = qrcode.make(qr_data)
    qr_path = os.path.join(GENERATED_PDFS_DIR, "qr_temp.png")
    qr.save(qr_path)
    pdf.image(qr_path, x=10, y=100, w=50)

    # Guardar el PDF
    pdf_path = os.path.join(GENERATED_PDFS_DIR, f"factura_{factura['number']}.pdf")
    pdf.output(pdf_path)
    os.remove(qr_path)  # Eliminar el QR temporal
    return pdf_path

# Agregar el botón en la interfaz gráfica
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

    ttk.Button(button_frame, text="Configurar API", command=configurar_api).grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    ttk.Button(button_frame, text="Verificar Conexión", command=verificar_conexion).grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    ttk.Button(button_frame, text="Enviar Nota Crédito", command=enviar_nota_credito).grid(row=2, column=0, padx=10, pady=10, sticky="ew")
    ttk.Button(button_frame, text="Consultar Resolución", command=consultar_resolucion).grid(row=3, column=0, padx=10, pady=10, sticky="ew")
    ttk.Button(button_frame, text="Subir Resolución", command=subir_resolucion).grid(row=4, column=0, padx=10, pady=10, sticky="ew")
    ttk.Button(button_frame, text="Seleccionar PDF y Enviar a DIAN", command=procesar_factura).grid(row=5, column=0, padx=10, pady=10, sticky="ew")
    ttk.Button(button_frame, text="Enviar Nota Débito", command=enviar_nota_debito).grid(row=3, column=0, padx=10, pady=10, sticky="ew")
    ttk.Button(button_frame, text="Salir", command=root.quit).grid(row=6, column=0, padx=10, pady=10, sticky="ew")

    root.mainloop()


if __name__ == "__main__":
    main()