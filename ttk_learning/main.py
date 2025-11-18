from tkinter import *
from ttkbootstrap.constants import *
import ttkbootstrap as tb

root = tb.Window(themename="cyborg")

# root = Tk()
root.title("TTK Bootstrap!")
root.iconbitmap("images/bitcoin.ico")
root.geometry("500x350")

# Function to change label text
counter = 0


def changer():
    global counter
    counter += 1
    if counter % 2 == 0:
        my_label.config(text="Hello, TTK Bootstrap!")
    else:
        my_label.config(text="Goodbye TTK Bootstrap!")


# Create a label
my_label = tb.Label(
    root, text="Hello, TTK Bootstrap!", font=("Helvetica", 28), bootstyle="light"
)
my_label.pack(pady=50)

# Create a button
my_button = tb.Button(root, text="Click Me!", bootstyle="primary", command=changer)
my_button.pack(pady=20)

root.mainloop()
