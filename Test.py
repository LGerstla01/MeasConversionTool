import tkinter as tk

def on_enter(event):
 read_text()

def read_text():
    text = text_widget.get("1.0", "end-1c")  # Text aus dem Text-Widget auslesen
    print("Eingabetaste wurde gedrückt. Text:", text)

root = tk.Tk()

text_widget = tk.Text(root)
text_widget.pack()

text_widget.bind("<KeyRelease-Return>", on_enter, add="+")  # Binden der Eingabetaste an die Funktion und Unterdrücken des Standardverhaltens

root.mainloop()