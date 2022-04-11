# pip install requests
# pip install opencv
# pip install pywin32
# pip install win32printing
# pip install temp

# v1.2 - doplnené automatické ukladanie do txt
# v1.3 - doplnená tlač txt, focus na entry id bloku
# v1.4 - doplnený sumár pri tlači a txt vždy na vrchu
# v1.5 - doplnene skenovanie qr kodu cez webkameru, doplnený config json
# v1.6 - vyriešený problém so skenerom honeywell "data correct"
# v1.7 - Riešenie problému s tlačou win32print

from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import requests
from requests.structures import CaseInsensitiveDict
import os
import cv2
import json
import print_text

# VZOROVE CISLA BLOCKOV
# O-4CCD1C78526A43BC8D1C78526AB3BCA7
# O-AC6D5656CDC64336AD5656CDC60336E0

cumulative = [0, 0, 0, 0, 0, 0, 0, 0]
nr_blok = [0]
add_blok = []

# skontroluj či existuje json, ak nie tak ho vyrob
if os.path.exists("config.json"):
    with open('config.json', 'r') as f_json:
        config_j = json.load(f_json)
else:
    # vytvor nový config
    config = {"_cam": "císlo kamery: 0 alebo 1", "cam": "0", "cam_read_qr": "1",
              "_cam_read_qr": "nastav 1 ak chces zobrazit, 0 ak nie",
              "path": "", "_path": "zadaj cestu alebo ../(adresar vyssie) ",
              "font_height": "70", "_font_height": "velkost písma pre tlac"}
    with open('config.json', 'w') as f_read_j:
        json.dump(config, f_read_j)
    with open('config.json', 'r') as f_json:
        config_j = json.load(f_json)


def read_qr(cam=0):
    """Funkcia ktorá spustí kameru a ak nájde QR tak ho prečíta a zavolá api_fs"""
    try:
        # inicializácia kamery, prvý parameter je číslo kamery
        cap = cv2.VideoCapture(int(cam), cv2.CAP_DSHOW)
        # inicializácia cv2 QRCode detector
        detector = cv2.QRCodeDetector()
        # slučka videa s kontrolou či neobsahuje QR
        while True:
            _, img = cap.read()
            # detect and decode
            data, bbox, _ = detector.detectAndDecode(img)
            # check if there is a QRCode in the image
            if data:
                print("Tvoj ID je", data)
                cv2.destroyAllWindows()
                cap.release()
                # zavolanie aplikácie
                ent_nr.delete(0, END)
                ent_nr.insert(END, data)
                api_fs()
                break
            # zobraz okno - celá obrazovka
            cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            # okno s videom
            cv2.imshow("Naskenuj QR - bločku", img)

            # prerušenie čítania QR po stlačení klávesy
            if cv2.waitKey(1) == ord("q"):
                break
        cv2.destroyAllWindows()
    # ošetrenie chyby ak nie je kamera
    except cv2.error:
        messagebox.showinfo("Nenájdená kamera", "Nenašiel som kameru")


def print_file_txt():
    """Vytlačenie txt blokov"""
    if os.path.exists(config_j['path'] + "blocky.txt"):
        # zavolanie funkcie pre tlač
        print_text.print_to_printer(config_j['path'], int(config_j['font_height']))


def save_txt():
    """Uloží načítané bločky do txt"""

    top_text = ('SPOLU základ dane, základná sadzba: ' + str(cumulative[0]) + '\n',
                'SPOLU základ dane, znížená sadzba: ' + str(cumulative[1]) + '\n',
                'SPOLU s DPH: ' + str(cumulative[2]) + '\n',
                'SPOLU oslobodená od DPH: ' + str(cumulative[3]) + '\n',
                'SPOLU DPH: ' + str(cumulative[4]) + '\n',
                'SPOLU DPH, znížená: ' + str(cumulative[5]) + '\n',
                'DPH %: ' + str(cumulative[6]) + '\n',
                'DPH %, znížená: ' + str(cumulative[7]) + '\n')
    lines = text_bloky.get('1.0', END)
    with open(config_j['path'] + 'blocky.txt', 'w') as f:
        for tx in top_text:
            for lx in tx:
                f.write(lx)
        for line in lines:
            f.write(line)
    # messagebox.showinfo("Uložené", "Uložené")


def delete_all():
    """Vymaže všetky polia a nakumulované premenné"""
    ent_taxBaseBasic.delete(0, END)
    ent_taxBaseReduced.delete(0, END)
    ent_totalPrice.delete(0, END)
    ent_freeTaxAmount.delete(0, END)
    ent_vatAmountBasic.delete(0, END)
    ent_vatAmountReduced.delete(0, END)
    ent_vatRateBasic.delete(0, END)
    ent_vatRateReduced.delete(0, END)
    global cumulative
    cumulative = [0, 0, 0, 0, 0, 0, 0, 0]
    nr_blok[0] = 0
    text_bloky.delete('1.0', END)
    lbl_nr.config(text='0')


def api_fs1(_):
    """Pomocná app, pre fungovanie klávesy 'Enter' """
    api_fs()


def api_fs():
    """Funkcia pre načítanie bločku z api financnej správy"""
    # url api FS
    url_api_fs = "https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/find"
    # Vytvorenie objektu
    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "application/json"

    # oprava kodovanie skenera honeywell (¨ za -)
    data_correct = list(ent_nr.get())
    if ent_nr.get() != "":
        if data_correct[1] == '¨':
            data_correct[1] = '-'

    s = "".join(data_correct)
    # Vstup id bloček
    data = '{"receiptId":"' + s + '"}'
    if s in add_blok:
        messagebox.showinfo("Bloček sa opakuje!", "Pozor bloček sa opakuje!!")
    else:
        add_blok.append(s)
        # post, v tvare {"receiptId":" císlo bločku"}
        resp = requests.post(url_api_fs, headers=headers, data=str(data))
        dict_blocek = resp.json()
        if dict_blocek['returnValue'] == -1:
            # ak vráti -1 vyvolaj chybu, bloček neexistuje
            messagebox.showinfo("Chyba", "Niečo je zle, buď štátne api, alebo zly bloček")

        else:
            # print(dict_blocek)
            # najprv vymaže vstupné polia
            ent_taxBaseBasic.delete(0, END)
            ent_taxBaseReduced.delete(0, END)
            ent_totalPrice.delete(0, END)
            ent_freeTaxAmount.delete(0, END)
            ent_vatAmountBasic.delete(0, END)
            ent_vatAmountReduced.delete(0, END)
            ent_vatRateBasic.delete(0, END)
            ent_vatRateReduced.delete(0, END)

            # pripočítanie predchádzajúceho bločku do list cumulative
            cumulative[0] += dict_blocek["receipt"]['taxBaseBasic'] if dict_blocek["receipt"]['taxBaseBasic'] else 0
            cumulative[1] += dict_blocek["receipt"]['taxBaseReduced'] if dict_blocek["receipt"]['taxBaseReduced'] else 0
            cumulative[2] += dict_blocek["receipt"]['totalPrice'] if dict_blocek["receipt"]['totalPrice'] else 0
            cumulative[3] += dict_blocek["receipt"]['freeTaxAmount'] if dict_blocek["receipt"]['freeTaxAmount'] else 0
            cumulative[4] += dict_blocek["receipt"]['vatAmountBasic'] if dict_blocek["receipt"]['vatAmountBasic'] else 0
            cumulative[5] += dict_blocek["receipt"]['vatAmountReduced'] if dict_blocek["receipt"]['vatAmountReduced'] else 0
            cumulative[6] = dict_blocek["receipt"]['vatRateBasic'] if dict_blocek["receipt"]['vatRateBasic'] else 0
            cumulative[7] = dict_blocek["receipt"]['vatRateReduced'] if dict_blocek["receipt"]['vatRateReduced'] else 0

            # vloženie kumulatívnej hodnoty do polí v hlavnom okne
            ent_taxBaseBasic.insert(END, str(cumulative[0]))
            ent_taxBaseReduced.insert(END, str(cumulative[1]))
            ent_totalPrice.insert(END, str(cumulative[2]))
            ent_freeTaxAmount.insert(END, str(cumulative[3]))
            ent_vatAmountBasic.insert(END, str(cumulative[4]))
            ent_vatAmountReduced.insert(END, str(cumulative[5]))
            ent_vatRateBasic.insert(END, str(cumulative[6]))
            ent_vatRateReduced.insert(END, str(cumulative[7]))

            # Aktualizácia textového poľa z ktorého sa vytvára taktiež TXT
            text_bloky.insert(END, '\n' + '*******************************************************\n')
            text_bloky.insert(END, 'Dátum vyhotovenia bločku: ' + str(dict_blocek["receipt"]['issueDate']) + '\n', 'big')
            text_bloky.insert(END, 'Názov: ' + str(dict_blocek['receipt']['organization']['name'] + '\n'))
            text_bloky.insert(END, 'IČO: ' + str(dict_blocek["receipt"]['ico']) + '\n')
            text_bloky.insert(END, 'IČ DPH: ' + str(dict_blocek["receipt"]['icDph']) + '\n')
            text_bloky.insert(END, 'ID bločku: ' + str(ent_nr.get()) + '\n')

            # generovanie položiek
            for items in dict_blocek["receipt"]['items']:
                text_bloky.insert(END, '\n')
                for prem1 in items:
                    text_bloky.insert(END, str(items[prem1]) + ' ')
                    # print(prem1)
            text_bloky.insert(END, '\n******* Spolu: ' + str(dict_blocek["receipt"]['totalPrice']) + ' ********')
            # vymaž pole s id bločku
            ent_nr.delete(0, END)
            # pomocná premenná počet načítaných bločkov
            nr_blok[0] += 1
            # aktualizácia štítku s počtom blokov
            lbl_nr.config(text=str(nr_blok[0]))
            # vytvor txt subor
            save_txt()
            # počkaj - aby ma FS neblokla
            root.after(1000)


def about_prog():
    top = Toplevel()
    top.title("['PH'] - O programe")
    # vycentrovanie okna na stred
    screen_width_top = top.winfo_screenwidth()
    screen_height_top = top.winfo_screenheight()

    # rozmery top okna
    app_width_top = 400
    app_height_top = 400
    # vycentrovanie okna na stred
    s_x = (screen_width_top / 2) - (app_width_top / 2)
    s_y = (screen_height_top / 2) - (app_height_top / 2)
    top.geometry(str(app_width_top) + 'x' + str(app_height_top) + '+' + str(s_x) + '+' + str(s_y))

    Label(top, text="Vytvoril Peter Habovštiak", font="helvetica 10 bold").pack(pady=10, padx=10)
    Label(top, text="mail: oriesok@gmail.com").pack(pady=10, padx=10)

    txt_gnu = Text(top)
    txt_gnu.pack(pady=10, padx=10)

    statusbar = Label(top, text="['PH'] vytvoril Peťko H.  :)", bd=1, relief=SUNKEN, anchor=W)
    statusbar.pack(side=BOTTOM, fill=X)

    txt_gnu.insert(END, "<Citaj Bločky> \nCopyright (C) \n<2022> <Peter Habovštiak>\n")
    txt_gnu.insert(END, "Tento program je ABSOLÚTNE BEZ ZÁRUKY!\n")
    txt_gnu.insert(END, "Ide o slobodný softvér\na jeho šírenie je za istých podmienok vítané.")


# vytvorenie objektu hlavného okna
root = Tk()
root.title("['PH'] - Čítaj Bloky SK")
# root.iconbitmap ('PHlogo.ico')

# vycentrovanie okna na stred
screen_width_root = root.winfo_screenwidth()
screen_height_root = root.winfo_screenheight()

# rozmery hlavného okna
app_width_root = 1200
app_height_root = 700
# vycentrovanie okna na stred
x = (screen_width_root / 2) - (app_width_root / 2)
y = (screen_height_root / 2) - (app_height_root / 2)
root.geometry(str(app_width_root) + 'x' + str(app_height_root) + '+' + str(int(x)) + '+' + str(int(y)))

# Pridanie štýlu
style = ttk.Style()
style.theme_use('default')

# pridanie pätičky
statusbar_rew = Label(root, text="['PH'] vytvoril Peťko H.  :)", bd=1, relief=SUNKEN, anchor=W)
statusbar_rew.pack(side=BOTTOM, fill=X)

# menu pravé tlacitko myši
m = Menu(root, tearoff=0)
m.add_command(label="Vymaž napočítané bločky", command=delete_all)
m.add_command(label="Tlačiť napočítané bločky", command=print_file_txt)
m.add_command(label="O programe", command=about_prog)


def do_popup(event):
    try:
        m.tk_popup(event.x_root, event.y_root)
    finally:
        m.grab_release()


# definícia vstupných polí
lbl_entry = Label(root, text='Zadaj číslo z bloku, alebo naskenuj QR')
lbl_entry.pack(pady=5)
ent_nr = Entry(root)
ent_nr.pack(pady=15, ipadx=105)
ent_nr.focus()

btn_frame = LabelFrame(root, text="Možnosti")
btn_frame.pack()
btn_read = Button(btn_frame, text='Stiahni údaje', command=api_fs)
btn_read.grid(column=0, row=0, pady=10, padx=10)
btn_delete = Button(btn_frame, text='Vymaž nápočet bločkov', command=delete_all)
btn_delete.grid(column=1, row=0, pady=10, padx=10)

# zmené, doplnená automatická aktualizácia txt
# btn_save_txt = Button(btn_frame, text='Ulož bloky do TXT', command=save_txt)
# btn_save_txt.pack(pady=10, padx=10)
btn_print_txt = Button(btn_frame, text='Vytlač bločky z TXT', command=print_file_txt)
btn_print_txt.grid(column=2, row=0, pady=10, padx=10)
print(config_j['cam_read_qr'])
if config_j['cam_read_qr'] == '1':
    btn_qr_read = Button(btn_frame, text='Čítaj QR z kamery', command=lambda: read_qr(config_j['cam']))
    btn_qr_read.grid(column=3, row=0, pady=10, padx=10)

main_frame = Frame(root)
main_frame.pack()
# vloženie objektu text, so scroll tagom
text_bloky = Text(main_frame, height=22, width=60)
text_bloky.pack(pady=10, padx=5, side=LEFT)
scroll = Scrollbar(root, command=text_bloky.yview)
text_bloky.configure(yscrollcommand=scroll.set)
# nakonfigurovanie fontov pre text widget(použitý iba big)
text_bloky.tag_configure('bold_italics', font=('Arial', 12, 'bold', 'italic'))
text_bloky.tag_configure('big', font=('Verdana', 12, 'bold'))
text_bloky.tag_configure('color',
                         foreground='#476042',
                         font=('Tempus Sans ITC', 12, 'bold'))

# frame popis a input polia
frame_cumulative = LabelFrame(main_frame, text='Kumulatív bločkov')
frame_cumulative.pack(pady=10, padx=10, side=LEFT)
# popis vstupných polí
lbl_taxBaseBasic = Label(frame_cumulative, text='Základ dane, základná sadzba')
lbl_taxBaseBasic.grid(row=0, column=1, pady=10)
lbl_taxBaseReduced = Label(frame_cumulative, text='Základ dane, znížená sadzba')
lbl_taxBaseReduced.grid(row=1, column=1, pady=10)
lbl_totalPrice = Label(frame_cumulative, text='Spolu s DPH')
lbl_totalPrice.grid(row=2, column=1, pady=10)
lbl_freeTaxAmount = Label(frame_cumulative, text='Spolu oslobodená od DPH')
lbl_freeTaxAmount.grid(row=3, column=1, pady=10)
lbl_vatAmountBasic = Label(frame_cumulative, text='DPH')
lbl_vatAmountBasic.grid(row=4, column=1, pady=10)
lbl_vatAmountReduced = Label(frame_cumulative, text='DPH so zníženou sadzbou')
lbl_vatAmountReduced.grid(row=5, column=1, pady=10)
lbl_vatRateBasic = Label(frame_cumulative, text='DPH %')
lbl_vatRateBasic.grid(row=6, column=1, pady=10)
lbl_vatRateReduced = Label(frame_cumulative, text='DPH % znížená')
lbl_vatRateReduced.grid(row=7, column=1, pady=10)

# vstupné polia
ent_taxBaseBasic = Entry(frame_cumulative)
ent_taxBaseBasic.grid(row=0, column=2, pady=10, padx=10)
ent_taxBaseReduced = Entry(frame_cumulative)
ent_taxBaseReduced.grid(row=1, column=2, pady=10, padx=10)
ent_totalPrice = Entry(frame_cumulative)
ent_totalPrice.grid(row=2, column=2, pady=10, padx=10)
ent_freeTaxAmount = Entry(frame_cumulative)
ent_freeTaxAmount.grid(row=3, column=2, pady=10, padx=10)
ent_vatAmountBasic = Entry(frame_cumulative)
ent_vatAmountBasic.grid(row=4, column=2, pady=10, padx=10)
ent_vatAmountReduced = Entry(frame_cumulative)
ent_vatAmountReduced.grid(row=5, column=2, pady=10, padx=10)
ent_vatRateBasic = Entry(frame_cumulative)
ent_vatRateBasic.grid(row=6, column=2, pady=10, padx=10)
ent_vatRateReduced = Entry(frame_cumulative)
ent_vatRateReduced.grid(row=7, column=2, pady=10, padx=10)
# popis prečet napočítaných blokov
lbl_nr_blok = Label(frame_cumulative, text='Počet', font='helvetica 12 bold')
lbl_nr_blok.grid(row=0, column=0, pady=10)
lbl_nr_blok1 = Label(frame_cumulative, text='napočitaných', font='helvetica 12 bold')
lbl_nr_blok1.grid(row=1, column=0, pady=10)
lbl_nr_blok2 = Label(frame_cumulative, text='bločkov', font='helvetica 12 bold')
lbl_nr_blok2.grid(row=2, column=0, pady=10)
# štítok počet načítaných blokov
lbl_nr = Label(frame_cumulative, text='0', font='helvetica 24 bold')
lbl_nr.grid(row=3, rowspan=3, column=0, pady=10)

# zviazanie vstupného poľa s klávesov "enter"
ent_nr.bind('<Return>', api_fs1)
root.bind("<Button-3>", do_popup)
root.mainloop()
