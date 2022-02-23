from tkinter import *
import sys
from tkinter.filedialog import askdirectory

root = Tk()
root.geometry('+%d+%d'%(350,10))
FONT = "Roboto"

#Left area
leftArea = Frame(root, width=1280, height=720, bg="white")
leftArea.grid(columnspan=2, rowspan=5, column=0)

#Right area
rightArea = Frame(root, width=1280, height=720, bg="blue")
rightArea.grid(columnspan=2, rowspan=5, column=2)


#StatusBox
statusBox = sys.stdout

#Instructions
instructions = Label(root, text="Enter the game name", font=FONT)
instructions.grid(columnspan=3, column=0, row=1)

def openFolder():
    browseTxt.set("Loading...")
    folder = askdirectory(parent=root, initialdir="C:/Users", title="Choose a directory")
    folder = folder + "/"
    browseTxt.set("Browse")

#Browser Button
browseTxt = StringVar()
browseBtn = Button(root, textvariable=browseTxt, command=lambda:openFolder(), font=FONT)
browseTxt.set("Browse")
browseBtn.grid(column=1, row=2)


root.mainloop()
