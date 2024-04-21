import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import os
import math
from PIL import Image, ImageDraw, ImageFont

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

def create_receipt_image(image_file, text_lines, output_file, max_height=576):
    logo = Image.open(image_file).convert('L')
    logo_width, logo_height = logo.size
    aspect_ratio = logo_width / logo_height
    new_height = 100  # Increased from 50 to 100 for a bigger logo
    new_width = int(new_height * aspect_ratio)
    logo = logo.resize((new_width, new_height), Image.LANCZOS)
    logo = logo.point(lambda x: 0 if x < 128 else 255, '1')
    font = ImageFont.truetype('arial.ttf', 36)
    line_spacing = 30  # Additional spacing between lines
    text_height = sum(font.getbbox(line)[3] - font.getbbox(line)[1] + line_spacing for line in text_lines)
    receipt_height = new_height + text_height + 50
    receipt = Image.new('1', (576, receipt_height), color=1)
    draw = ImageDraw.Draw(receipt)
    logo_x = (576 - new_width) // 2
    receipt.paste(logo, (logo_x, 0))
    y_offset = new_height + 20
    for line in text_lines:
        draw.text((10, y_offset), line, font=font, fill=0)
        y_offset += font.getbbox(line)[3] - font.getbbox(line)[1] + line_spacing
    thank_you_text = "Markury is awesome. Recycle this."
    thank_you_font = ImageFont.truetype('Arial.ttf', 24)
    thank_you_bbox = thank_you_font.getbbox(thank_you_text)
    thank_you_width = thank_you_bbox[2] - thank_you_bbox[0]
    thank_you_height = thank_you_bbox[3] - thank_you_bbox[1]
    thank_you_x = (576 - thank_you_width) // 2
    thank_you_y = receipt_height - thank_you_height
    draw.text((thank_you_x, thank_you_y), thank_you_text, font=thank_you_font, fill=0)
    receipt = receipt.transpose(Image.FLIP_TOP_BOTTOM)
    receipt.save(output_file)

class ReceiptPrinterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Receipt Printer Application")
        self.geometry("600x400")

        # Printer variable and dropdown menu
        self.printer_var = tk.StringVar(self)
        self.printer_dropdown = tk.OptionMenu(self, self.printer_var, '')
        self.printer_dropdown.pack()
        self.update_printer_list()

        # Text input for receipt details
        self.text_input = tk.Text(self, height=10, width=50)
        self.text_input.pack()

        # Print and Preview buttons
        self.print_button = tk.Button(self, text="Print Receipt", command=self.print_receipt)
        self.print_button.pack()

        self.preview_button = tk.Button(self, text="Preview Receipt", command=self.preview_receipt)
        self.preview_button.pack()

        # Console for log messages
        self.console = scrolledtext.ScrolledText(self, height=10)
        self.console.pack()

    def update_printer_list(self):
        printers = find_printers()
        menu = self.printer_dropdown['menu']
        menu.delete(0, 'end')  # Clear existing menu entries

        if printers:
            self.printer_var.set(printers[0])  # Set the default printer
            for printer in printers:
                menu.add_command(label=printer, command=lambda p=printer: self.printer_var.set(p))
        else:
            self.printer_var.set('')
            menu.add_command(label="No printers found")

    def print_receipt(self):
        selected_printer = self.printer_var.get()
        text_lines = self.text_input.get("1.0", "end").strip().split('\n')
        receipt_file = 'receipt.bmp'
        create_receipt_image('logo.png', text_lines, receipt_file)
        convert_image(receipt_file, 'final_receipt.bmp')
        print_image(selected_printer, 'final_receipt.bmp')
        os.remove('receipt.bmp')
        os.remove('final_receipt.bmp')
        self.console.insert('end', f"Receipt printed successfully on {selected_printer}\n")

    def preview_receipt(self):
        text_lines = self.text_input.get("1.0", "end").strip().split('\n')
        receipt_file = 'preview_receipt.bmp'
        create_receipt_image('logo.png', text_lines, receipt_file)
        receipt_image = Image.open(receipt_file)
        receipt_image = receipt_image.transpose(Image.FLIP_TOP_BOTTOM)  # Flip the image vertically
        receipt_image.show()  # Show the preview using the default image viewer
        self.console.insert('end', "Receipt preview generated.\n")

if __name__ == '__main__':
    app = ReceiptPrinterApp()
    app.mainloop()
