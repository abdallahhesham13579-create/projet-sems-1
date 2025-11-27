import platform
import datetime
import socket
import subprocess
import sys
import os
import shutil
import ctypes
import tkinter as tk
from tkinter import ttk
from PROJ1 import (
    web_services_fn,
    power_status_fn,
    memory_info_fn,
    disk_info_fn,
    processes_fn,
    hostname_fn,
    current_time_fn,
    uptime_fn,
    version_fn,
    temperatures2_fn
)



class SystemDashboard(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("System Monitor Dashboard")
        self.geometry("900x600")

        self.text = tk.Text(self, font=("Arial", 11), background="#0b132b", foreground="#ffffff")
        self.text.pack(fill="both", expand=True)
        self.text.tag_configure("header", font=("Arial", 16, "bold"),background="#0b132b", foreground="#ffffff")
        self.text.configure(tabs=("150p", "450p", "600p"))
        self.static_info()
        self.update_dashboard()



    def static_info(self):
        #Nom d'hôte de la machine 
        self.text.insert(tk.END, "Nom d'hôte:"+ "\n", "header")
        hostname=hostname_fn()
        self.text.insert(tk.END, f"{hostname}"+ "\n", "p")

        # Version du système d'exploitation
        self.text.insert(tk.END, "Version:"+ "\n", "header") 
        version=version_fn()
        self.text.insert(tk.END, f"{version}\n", "p")
        

        # Date et l'heure de la génération du rapport
        current_time = current_time_fn()
        self.text.insert(tk.END, "Date et l'heure précises de la génération du rapport :" + "\n" , "header")
        self.text.insert(tk.END, f"{current_time}\n", "p")
        self.text.mark_set("dynamic_start", "insert")
        self.text.mark_gravity("dynamic_start", tk.LEFT)



    def update_dashboard(self):
        self.text.delete("dynamic_start", tk.END)

        # Durée de fonctionnement du système (uptime)
        current_uptime = uptime_fn()
        self.text.insert(tk.END, "Durée de fonctionnement " + "\n" , "header")
        self.text.insert(tk.END, f"{current_uptime}\n", "p")


        # Temperatures
        self.text.insert(tk.END, "Températures\n" , "header")
        current_temps = temperatures2_fn()
        self.text.insert(tk.END, f"CPU : {current_temps}\n")
        self.text.insert(tk.END, "\n")

        # État de l'alimentation électrique 
        self.text.insert(tk.END, "État de l'alimentation électrique\n" , "header")
        for name, val in power_status_fn():
            self.text.insert(tk.END, f"{name}: {val}\n")
        self.text.insert(tk.END, "\n")


        mem_data = list(memory_info_fn())
        disk_data = list(disk_info_fn())
        self.text.insert(tk.END, "Mémoire Vive\tÉtat des Disques\n", "header")
        max_len = max(len(mem_data), len(disk_data))
        for i in range(max_len):

                if i < len(mem_data):
                    left_text = f"{mem_data[i][0]}: {mem_data[i][1]}"
                else:
                    left_text = "" 
                
                if i < len(disk_data):
                    mount, info = disk_data[i]
                    right_text = f"{mount}: {info}"
                else:
                    right_text = "" 

                self.text.insert(tk.END, f"{left_text}\t{right_text}\n", "p")

        self.text.insert(tk.END, "\n")



        self.text.insert(tk.END, "Liste des processus \n", "header")
        for p in processes_fn():
            self.text.insert(tk.END, f"{p}\n")

        # Web services
        self.text.insert(tk.END, "Web Services (Ports 80 / 443)\n" , "header")
        for s in web_services_fn():
            self.text.insert(tk.END, f"{s}\n")
        self.text.insert(tk.END, "\n")    

        
        self.after(1000, self.update_dashboard)

    

if __name__ == "__main__":
    if "--gui" in sys.argv:
        print("Launching Graphical Dashboard...")
        app = SystemDashboard()
        app.mainloop()
    else:
        print("Erreur: pour afficher le gui écrivez: python3 dashboard.py --gui")