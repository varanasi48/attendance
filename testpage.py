import tkinter as tk
from tkinter import ttk

root = tk.Tk()

# Create a ttk Frame
frame = ttk.Frame(root)
frame.pack(fill="both", expand=True)

# Add a button inside the frame
button = ttk.Button(frame, text="Click Me")
button.pack()

root.mainloop()
