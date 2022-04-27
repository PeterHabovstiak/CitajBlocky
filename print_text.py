import win32print
import win32ui
import win32con
from tkinter import *
from tkinter import font 


def print_to_printer(path=None, font_height=60):
    path = path
    font_height = font_height
    # Vytvorenie top okna
    top_print = Toplevel()
    top_print.title("Okno tlače")
    top_print.geometry("410x310")
    top_print.resizable(False, False)
    top_print.tk.call('encoding', 'system', 'utf-8')

    # definícia fontu
    def font_size(fs):
        return font.Font(family='Helvetica', size=fs, weight='bold')

    def print_action(path_print, font_height):
        """funkcia na vyvolanie tlače, ako parameter sa posiela cesta k tlačenému txt"""
        x = 90
        y = 90
        # Otvorenie textového súboru na tlač
        fd = open(path_print + "blocky.txt", "r", encoding="windows-1250")
        # načítanie ako string
        input_string = fd.read()
        # Spojenie textu
        multi_line_string = input_string.splitlines()
        # vytorenie
        dc = win32ui.CreateDC()
        # zadefinovanie tlačiarne
        dc.CreatePrinterDC(_printer.get())
        dc.StartDoc("Printing...")
        dc.StartPage()
        fontdata = {'name': 'Arial', 'height': font_height, 'italic': False, 'weight': win32con.FW_NORMAL}
        font_print = win32ui.CreateFont(fontdata)
        dc.SelectObject(font_print)
        nr_of_page = 1
        for line in multi_line_string:
            dc.TextOut(x, y, line)
            y += font_height + 5
            if y > 6500:
                dc.EndPage()
                dc.StartPage()
                y = 90
        dc.EndPage()
        dc.EndDoc()
        fd.close()
        top_print.destroy()

    # vytorenie frame
    mainframe = Frame(top_print)
    mainframe.grid(column=0, row=0, sticky=N)
    mainframe.columnconfigure(0, weight=1)
    mainframe.rowconfigure(0, weight=1)
    mainframe.pack(pady=10, padx=0)

    # Create a _printer variable
    _printer = StringVar(top_print)
    # zvolenie tlačiarne
    choices = [printer[2] for printer in win32print.EnumPrinters(2)]
    # ako prvá sa nastaví ako vychodzia
    _printer.set(win32print.GetDefaultPrinter())  # set the default option
    # vyskakovacie menu s názvami tlačiarní
    popup_menu = OptionMenu(mainframe, _printer, *choices)
    popup_menu['font'] = font_size(12)
    Label(mainframe, text="Výber tlačiarne").grid(row=1, column=1, pady=(30, 0))
    popup_menu.grid(row=2, column=1)

    Label(mainframe).grid(row=10, column=1)
    p_button = Button(mainframe, text=u'\uD83D\uDDB6' + " TLAČIŤ",
                      command=lambda: print_action(path, font_height), fg="dark green", bg="white")
    p_button['font'] = font_size(18)
    p_button.grid(row=11, column=1, pady=20)

    top_print.mainloop()
