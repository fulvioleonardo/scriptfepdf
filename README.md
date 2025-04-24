# Fullsys Tecnología Santa Marta - Integración de Facturación Electrónica

**Aplicación para integrar programas externos locales con la DIAN para emitir facturas electrónicas a partir de archivos PDF.**

---

## Descripción

Esta aplicación ha sido diseñada por **Fullsys Tecnología Santa Marta** para facilitar la emisión de facturas electrónicas mediante la integración de programas locales, como **Eleventa**, con los servicios de la DIAN. La herramienta permite procesar archivos PDF, extraer la información necesaria y generar facturas electrónicas que cumplen con los estándares requeridos.

---

## Características

- **Procesamiento de PDFs**: Extrae automáticamente la información necesaria para generar facturas electrónicas.
- **Envío a la DIAN**: Integra directamente con la API de la DIAN para el envío de facturas electrónicas.
- **Gestión de Notas Crédito y Débito**: Permite generar y enviar notas crédito y débito asociadas a facturas existentes.
- **Configuración Personalizable**: Configura fácilmente el URL de la API y el token de autenticación.
- **Generación de PDFs con QR**: Crea facturas electrónicas en formato PDF con códigos QR y CUFE.
- **Interfaz Gráfica Intuitiva**: Diseñada para facilitar el uso por parte de los usuarios.

---

## Requisitos

- **Python 3.8 o superior**
- Librerías necesarias (instalables con `pip`):
  - `PyMuPDF` (`fitz`)
  - `requests`
  - `fpdf`
  - `qrcode`
  - `tkinter`

---

## Instalación

1. Clona este repositorio o descarga los archivos.
2. Instala las dependencias necesarias ejecutando:
   ```bash
   pip install pymupdf requests fpdf qrcode