from tkinter import *
from ttkbootstrap.constants import *
import ttkbootstrap as tb

root = tb.Window(themename="cyborg")

# root = Tk()
root.title("TTK Bootstrap!")
root.iconbitmap("images/bitcoin.ico")
root.geometry("500x350")


# Functions
def checker():
    if var1.get() == 1:
        my_label.config(text="Checked!")
    else:
        my_label.config(text="Unchecked!")


# Label
my_label = Label(text="Click the button to change my color!", font=("Helvetica", 18))
my_label.pack(pady=(40, 10))

# Check button
var1 = IntVar()
my_check = tb.Checkbutton(
    bootstyle="primary",
    text="Check me out!",
    variable=var1,
    onvalue=1,
    offvalue=0,
    command=checker,
)
my_check.pack(pady=10)

# Tool button
var2 = IntVar()
my_check2 = tb.Checkbutton(
    bootstyle="danger, toolbutton",
    text="Toolbutton Check!",
    variable=var2,
    onvalue=1,
    offvalue=0,
    command=checker,
)
my_check2.pack(pady=10)

# Outline tool button
var3 = IntVar()
my_check3 = tb.Checkbutton(
    bootstyle="danger, toolbutton, outline",
    text="Outline Toolbutton Check!",
    variable=var3,
    onvalue=1,
    offvalue=0,
    command=checker,
)
my_check3.pack(pady=10)

# Round toggle
var4 = IntVar()
my_check4 = tb.Checkbutton(
    bootstyle="success, round-toggle",
    text="Round Toggle!",
    variable=var4,
    onvalue=1,
    offvalue=0,
    command=checker,
)
my_check4.pack(pady=10)

# Square toggle
var5 = IntVar()
my_check5 = tb.Checkbutton(
    bootstyle="warning, square-toggle",
    text="Square Toggle!",
    variable=var5,
    onvalue=1,
    offvalue=0,
    command=checker,
)
my_check5.pack(pady=10)

root.mainloop()
