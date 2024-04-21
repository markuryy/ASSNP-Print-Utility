import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageDraw, ImageFont, ImageTk
import subprocess
import os

def find_printers():
    try:
        output = subprocess.check_output(['ippfind'])
        return [printer for printer in output.decode('utf-8').split('\n') if printer.strip()]
    except subprocess.CalledProcessError:
        return []

def convert_image(input_file, output_file, width=576):
    command = [
        'convert', input_file,
        '-resize', f'{width}x', '-monochrome', '-colors', '2',
        'BMP3:' + output_file
    ]
    subprocess.run(command, check=True)

def print_image(printer_url, bmp_file):
    command = [
        'ipptool', '-tv', '-f', bmp_file,
        printer_url,
        '-d', 'fileType=image/reverse-encoding-bmp',
        'print-job.test'
    ]
    subprocess.run(command, check=True)

from PIL import Image, ImageDraw, ImageFont

def create_receipt_image(image_file, text_lines, output_file, header="Markury", footer="Thank you for choosing Markury!", for_printing=False):
    logo = Image.open(image_file).convert('L')
    logo_width, logo_height = logo.size
    aspect_ratio = logo_width / logo_height
    new_height = 100
    new_width = int(new_height * aspect_ratio)
    logo = logo.resize((new_width, new_height), Image.LANCZOS)
    logo = logo.point(lambda x: 0 if x < 128 else 255, '1')
    font = ImageFont.truetype('arial.ttf', 36)
    header_font = ImageFont.truetype('arial.ttf', 48)
    footer_font = ImageFont.truetype('arial.ttf', 24)
    line_spacing = 30

    receipt = Image.new('1', (576, 2000), 'white')
    draw = ImageDraw.Draw(receipt)
    logo_x = (576 - new_width) // 2
    receipt.paste(logo, (logo_x, 0))

    header_bbox = header_font.getbbox(header)
    header_width = header_bbox[2] - header_bbox[0]
    draw.text(((576 - header_width) // 2, new_height + 20), header, font=header_font, fill=0)
    y_offset = new_height + 20 + header_font.getbbox(header)[3] + line_spacing

    for line in text_lines:
        if line.startswith('<bul>'):
            line = line.replace('<bul>', '')
            draw.text((50, y_offset), '• ' + line, font=font, fill=0)
        elif line.startswith('<check>'):
            line = line.replace('<check>', '')
            draw.rectangle([30, y_offset + 10, 45, y_offset + 25], outline=0)
            draw.text((50, y_offset), line, font=font, fill=0)
        else:
            draw.text((10, y_offset), line, font=font, fill=0)
        y_offset += font.getbbox(line)[3] - font.getbbox(line)[1] + line_spacing

    footer_bbox = footer_font.getbbox(footer)
    footer_width = footer_bbox[2] - footer_bbox[0]
    draw.text(((576 - footer_width) // 2, y_offset), footer, font=footer_font, fill=0)

    y_offset += footer_font.getbbox(footer)[3] + 30
    final_receipt = receipt.crop((0, 0, 576, y_offset))

    if for_printing:
        final_receipt = final_receipt.transpose(Image.FLIP_TOP_BOTTOM)

    final_receipt.save(output_file)

def update_preview(canvas, text_widget, header_entry, footer_entry):
    text_lines = text_widget.get("1.0", "end").strip().split('\n')
    header = header_entry.get()
    footer = footer_entry.get()
    temp_receipt_file = 'temp_preview.bmp'
    create_receipt_image('logo.png', text_lines, temp_receipt_file, header, footer)
    img = Image.open(temp_receipt_file)
    # Ensure the image fits within the canvas
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    img.thumbnail((canvas_width, canvas_height), Image.BICUBIC)
    photo = ImageTk.PhotoImage(img)
    canvas.image = photo  # Keep reference
    canvas.create_image(0, 0, image=photo, anchor='nw')
    os.remove(temp_receipt_file)  # Clean up after preview update

class ReceiptPrinterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Receipt Printer Application")
        self.geometry("1000x700")

        left_frame = tk.Frame(self, width=500)
        left_frame.pack(side='left', fill='y', padx=20, pady=20)
        right_frame = tk.Frame(self, width=500)
        right_frame.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        self.printer_var = tk.StringVar(self)
        self.printer_dropdown = tk.OptionMenu(left_frame, self.printer_var, '')
        self.printer_dropdown.pack(fill='x', pady=10)
        self.update_printer_list()

        # Header entry with uniform width
        self.header_entry = tk.Entry(left_frame, font=('Arial', 24))
        self.header_entry.insert(0, "Markury")
        self.header_entry.pack(fill='x', pady=10)

        # Main text input
        self.text_input = tk.Text(left_frame, height=10, font=('Arial', 16))
        self.text_input.pack(fill='x', pady=10, expand=True)

        # Footer entry with uniform width
        self.footer_entry = tk.Entry(left_frame, font=('Arial', 24))
        self.footer_entry.insert(0, "Please recycle me :)")
        self.footer_entry.pack(fill='x', pady=10)

        self.print_button = tk.Button(left_frame, text="Print Receipt", command=self.print_receipt)
        self.print_button.pack(fill='x', pady=10)

        self.preview_button = tk.Button(left_frame, text="Preview Receipt", command=self.preview_receipt)
        self.preview_button.pack(fill='x', pady=10)

        self.preview_canvas = tk.Canvas(right_frame, bg='white')
        self.preview_canvas.pack(fill='both', expand=True)

    def update_printer_list(self):
        printers = find_printers()
        menu = self.printer_dropdown['menu']
        menu.delete(0, 'end')
        if printers:
            self.printer_var.set(printers[0])
            for printer in printers:
                menu.add_command(label=printer, command=lambda p=printer: self.printer_var.set(p))
        else:
            self.printer_var.set('')
            menu.add_command(label="No printers found")

    def print_receipt(self):
        selected_printer = self.printer_var.get()
        text_lines = self.text_input.get("1.0", "end").strip().split('\n')
        receipt_file = 'receipt.bmp'
        # Pass for_printing=True when creating the image for printing
        create_receipt_image('logo.png', text_lines, receipt_file, self.header_entry.get(), self.footer_entry.get(), for_printing=True)
        convert_image(receipt_file, 'final_receipt.bmp')
        print_image(selected_printer, 'final_receipt.bmp')
        os.remove(receipt_file)
        os.remove('final_receipt.bmp')

    def preview_receipt(self):
        text_lines = self.text_input.get("1.0", "end").strip().split('\n')
        # No flipping for preview
        update_preview(self.preview_canvas, self.text_input, self.header_entry, self.footer_entry)

if __name__ == '__main__':
    app = ReceiptPrinterApp()
    app.mainloop()
