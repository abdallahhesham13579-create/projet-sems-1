from datetime import datetime
import webbrowser
from pathlib import Path
import shutil
import subprocess
import socket
import http.client
import ssl
import re
import sys



# Date et l'heure de la génération du rapport
def current_time_fn():
    try:
     return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "erruer afficher le temps"
    




#Nom d'hôte de la machine 

def hostname_fn():

    try: return Path("/proc/sys/kernel/hostname").read_text().strip()
    except Exception:
        return "erruer afficher le nom de hote"    

       




#Version détaillée du noyau Linux

def version_fn():

    try: return Path("/proc/version").read_text().strip()
    except Exception:
        return "Erreur afficher la version:"



# Durée de fonctionnement du système (uptime)

def uptime_fn():

    try:
        raw_uptime = Path("/proc/uptime").read_text().strip()
        total_seconds = int(float(raw_uptime.split()[0]))
        total_minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except Exception:
        return "Erreur afficher le temps"

    

#Températures
   

def temperatures2_fn():

    temps2 = []
    temppath = "/sys/class/thermal/thermal_zone0/temp"
    try:
        with open(temppath, "r") as f:
            temp_str = f.read().strip()
            
            # divide by 1000 
            temp_c = int(temp_str) / 1000.0
            return f"{temp_c} °C"
            
    except Exception:
        return "Erreur afficher le temparature."



#État de l'alimentation électrique

def power_status_fn():

    power_info = []
    power_path = Path("/sys/class/power_supply")
    if not power_path.exists():
        return [("Erreur afficher l'état de l'alimentation")]

    for device in power_path.iterdir():
        status_file = device / "status"
        capacity_file = device / "capacity"
        online_file = device / "online"

        try:
            if status_file.exists():
                status = status_file.read_text().strip()
                power_info.append((device.name + " status", status))
            if capacity_file.exists():
                capacity = capacity_file.read_text().strip() + "%"
                power_info.append((device.name + " capacity", capacity))
            if online_file.exists():
                online = "Plugged in" if online_file.read_text().strip() == "1" else "Not plugged in"
                power_info.append((device.name + " online", online))
                
        except Exception:
            power_info.append((device.name, "Erreur afficher l'état"))
    
    if not power_info:
        power_info.append(("Power Info", "Not available"))
    return power_info


#État détaillé de la mémoire vive 

def memory_info_fn():
    meminfo = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split(":")
                key = parts[0]
                value = parts[1].strip().split()[0]  
                meminfo[key] = int(value)
    except Exception:
        return [("Memory Info", "Not available")]

    try:
        total = meminfo.get("MemTotal", 0)
        free = meminfo.get("MemFree", 0)
        cached = meminfo.get("Cached", 0)
        used = total - free - cached

        used_pct = used / total * 100 if total else 0
        free_pct = free / total * 100 if total else 0
        cache_pct = cached / total * 100 if total else 0

        return [
            ("Total", f"{total / 1024:.1f} MB"),
            ("Used", f"{used / 1024:.1f} MB ({used_pct:.1f}%)"),
            ("Free", f"{free / 1024:.1f} MB ({free_pct:.1f}%)"),
            ("Cached", f"{cached / 1024:.1f} MB ({cache_pct:.1f}%)")
        ]
    except Exception:
        return [("Memory Info", "Error calculating memory")]





#État des disques 

def disk_info_fn():

    disks_info = []

    try:
        with open("/proc/mounts") as f:
            mounts = [line.split()[1] for line in f if line.startswith("/dev/")]
    except Exception:
        return [("Disk Info", "Not available")]

    seen = set()
    for mount in mounts:
        if mount in seen:
            continue
        seen.add(mount)
        try:
            usage = shutil.disk_usage(mount)
            total = usage.total / (1024 ** 3)  
            used = usage.used / (1024 ** 3)
            free = usage.free / (1024 ** 3)
            used_pct = (used / total) * 100 if total else 0
            disks_info.append((
                mount,
                f"Total: {total:.1f} GB, Used: {used:.1f} GB ({used_pct:.1f}%), Free: {free:.1f} GB"
            ))
        except Exception:
            disks_info.append((mount, "Error reading usage"))
    
    if not disks_info:
        disks_info.append(("Disk Info", "No disks found"))
    
    return disks_info




#Liste des processus actifs,
def processes_fn(limit=10):
    try:

        result = subprocess.run(
            ["ps", "-eo", "pid,user,pcpu,pmem,comm", "--sort=-pcpu"],
            capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split("\n")


        headers = lines[0].split()
        processes = []

  
        for line in lines[1:limit+1]:
            parts = line.split(None, 4)
            if len(parts) == 5:
                pid, user, cpu, mem, name = parts
                processes.append({
                    "PID": pid,
                    "User": user,
                    "CPU": cpu,
                    "Memory": mem,
                    "Name": name
                })
        return processes
    except Exception :
        return [{"Error d'affichage des processus"}]

processes = processes_fn(10)



#État du réseau 
def network_info_fn():
    networks = []
    try:
        for iface in Path("/sys/class/net").iterdir():
            name = iface.name
            operstate = (iface / "operstate").read_text().strip()

            with open("/proc/net/dev") as f:
                for line in f:
                    if name + ":" in line:
                        data = line.split(":")[1].split()
                        rx_bytes, tx_bytes = int(data[0]), int(data[8])
                        networks.append({
                            "Interface": name,
                            "Status": operstate,
                            "RX (KB)": f"{rx_bytes / 1024:.1f}",
                            "TX (KB)": f"{tx_bytes / 1024:.1f}",
                        })
                        break
    except Exception as e:
        networks.append({"Error": str(e)})
    return networks



#Services web (HTTP et HTTPS)
def web_services_fn():
    services = []
    ports = [80, 443]
    localhost = "127.0.0.1"

    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((localhost, port))
        sock.close()

        if result != 0:
            services.append({
                "Port": port,
                "Status": "Closed",
                "Title": "-",
                "Favicon": "-",
                "Server": "-"
            })
            continue

        try:
            if port == 443:
                context = ssl._create_unverified_context()
                conn = http.client.HTTPSConnection(localhost, port, timeout=2, context=context)
            else:
                conn = http.client.HTTPConnection(localhost, port, timeout=2)

            conn.request("GET", "/")
            response = conn.getresponse()
            headers = dict(response.getheaders())
            data = response.read(2048).decode(errors="ignore")  

            title_match = re.search(r"<title>(.*?)</title>", data, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else "No title"


            fav_match = re.search(r'rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']+)["\']', data, re.IGNORECASE)
            favicon = fav_match.group(1).strip() if fav_match else "None"

            server = headers.get("Server", "Unknown")

            services.append({
                "Port": port,
                "Status": "Open",
                "Title": title,
                "Favicon": favicon,
                "Server": server
            })

            conn.close()

        except Exception as e:
            services.append({
                "Port": port,
                "Status": "Open",
                "Title": f"Error: {e}",
                "Favicon": "-",
                "Server": "Unknown"
            })

    return services



if __name__=="__main__": 

    template_path = "template.html"  # Path to your HTML template


    if len(sys.argv) < 3:
        print("Usage: python script.py <filename> <folder> <metric1> <metric2> ...")
        sys.exit(1)

    file_name = sys.argv[1]
    folder_path = sys.argv[2]
    user_metrics = sys.argv[3:] 


    # 3. EXECUTION LOOP
    template_string = Path(template_path).read_text()
    

    final_path = folder_path
    if not (final_path.endswith('/') or final_path.endswith('\\')):
        final_path += '/'
    final_path += file_name

    print(f"Report generated at {final_path}")

    if "time" in user_metrics:
        current_time = current_time_fn()
        final_html = template_string.replace("{{current_time}}", current_time)
    else:    
        final_html = template_string.replace("{{current_time}}", "vous avez choisi de ne pas afficher le date et l'heure.")
    if "hostname" in user_metrics:
        hostname = hostname_fn()
        final_html = final_html.replace("{{hostname}}", hostname)
    else:    
        final_html = final_html.replace("{{hostname}}", "vous avez choisi de ne pas afficher le nom d'hôte.")
    if "version" in user_metrics:
        version = version_fn()
        final_html = final_html.replace("{{version}}", version)
    else:    
        final_html = final_html.replace("{{version}}", "vous avez choisi de ne pas afficher la version.")
    if "uptime" in user_metrics:
        uptime = uptime_fn()
        final_html = final_html.replace("{{uptime}}", uptime)
    else:    
        final_html = final_html.replace("{{uptime}}", "vous avez choisi de ne pas afficher le temps de fonctionnement.")
    if "temp" in user_metrics:
        temps2 = temperatures2_fn()
        final_html = final_html.replace("{{temps2}}", temps2)
    else:    
        final_html = final_html.replace("{{temps2}}", "vous avez choisi de ne pas afficher la température.")
    if "power" in user_metrics:
        power_status = power_status_fn()
        power_html = "<br>".join([f"{name}: {value}" for name, value in power_status])
        final_html = final_html.replace("{{power_html}}", power_html)
    else:    
        final_html = final_html.replace("{{power_html}}", "vous avez choisi de ne pas afficher l'état de l'alimentation.")
    if "ram" in user_metrics:   
        memory_info = memory_info_fn()
        memory_html = "<br>".join([f"{k}: {v}" for k, v in memory_info])
        final_html = final_html.replace("{{memory_html}}", memory_html)
    else:    
        final_html = final_html.replace("{{memory_html}}", "vous avez choisi de ne pas afficher l'état de la mémoire vive.")
    if "disk" in user_metrics:   
        disk_info = disk_info_fn()
        disk_html = "<br>".join([f"{mount}: {details}" for mount, details in disk_info])
        final_html = final_html.replace("{{disk_html}}", disk_html)     
    else:    
        final_html = final_html.replace("{{disk_html}}", "vous avez choisi de ne pas afficher l'état des disques.")
    if "cpu" in user_metrics:   
        process_rows = "".join(
            f"<tr><td>{p['PID']}</td><td>{p['User']}</td><td>{p['CPU']}</td>"
            f"<td>{p['Memory']}</td><td>{p['Name']}</td></tr>"
            for p in processes
        )
        final_html = final_html.replace("{{process_rows}}", process_rows)
    else:    
        final_html = final_html.replace("{{process_rows}}", "vous avez choisi de ne pas afficher la liste des processus actifs.")
    if "net" in user_metrics:   
        network_info = network_info_fn()
        network_rows = "".join(
            f"<tr><td>{n['Interface']}</td><td>{n['Status']}</td>"
            f"<td>{n['RX (KB)']}</td><td>{n['TX (KB)']}</td></tr>"
            for n in network_info
        )
        final_html = final_html.replace("{{network_rows}}", network_rows)
    else:    
        final_html = final_html.replace("{{network_rows}}", "vous avez choisi de ne pas afficher l'état du réseau.")
    if "web" in user_metrics:   
        web_services = web_services_fn()
        web_services_rows = "".join(
            f"<tr><td>{s['Port']}</td><td>{s['Status']}</td>"
            f"<td>{s['Title']}</td><td>{s['Favicon']}</td><td>{s['Server']}</td></tr>"
            for s in web_services
        ) 
        final_html = final_html.replace("{{web_services_rows}}", web_services_rows)
    else:    
        final_html = final_html.replace("{{web_services_rows}}", "vous avez choisi de ne pas afficher les services web.")
    try:
        with open(final_path, "w", encoding="utf-8") as file:
            file.write(final_html)
        
        print(f"Report successfully generated: {final_path}")
        file_uri = Path(final_path).resolve().as_uri()
        webbrowser.open(file_uri)
        
    except Exception as e:
        print(f"Error saving or opening the report: {e}")
