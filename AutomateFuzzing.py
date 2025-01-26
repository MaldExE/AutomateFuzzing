import os
import requests
from requests.exceptions import RequestException
import subprocess
import re
from urllib.parse import urlparse

# Fichiers et dossiers
input_file = "targets.txt"
httpx_dir = "Result-httpx"
dirsearch_dir = "Result-Dirsearch"
accessible_file = f"{httpx_dir}/accessible.txt"
inaccessible_file = f"{httpx_dir}/inaccessible.txt"

# Créer les dossiers nécessaires
os.makedirs(httpx_dir, exist_ok=True)
os.makedirs(dirsearch_dir, exist_ok=True)

def check_url_protocol(url):
    protocols = ["http://", "https://"]
    for protocol in protocols:
        try:
            response = requests.head(f"{protocol}{url}", timeout=5, allow_redirects=True)
            if response.status_code < 400:
                return protocol
        except RequestException:
            continue
    return "No access"

def clean_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# Vérification de l'accessibilité des URLs
print("Vérification de l'accessibilité des URLs :")
print("=========================================")

with open(input_file, "r") as infile, \
     open(accessible_file, "w") as accessible, \
     open(inaccessible_file, "w") as inaccessible:
    for line in infile:
        url = line.strip()
        protocol = check_url_protocol(url)
        if protocol != "No access":
            full_url = f"{protocol}{url}"
            accessible.write(full_url + "\n")
            print(f"URL accessible : {full_url}")
        else:
            inaccessible.write(url + "\n")
            print(f"URL inaccessible : {url}")

# Exécution de httpx
print("\nRésultats de httpx :")
print("====================")

status_files = {}

with open(accessible_file, "r") as f:
    urls = f.read().splitlines()

for url in urls:
    try:
        result = subprocess.run(["httpx", "-silent", "-status-code", "-u", url], capture_output=True, text=True)
        output = result.stdout.strip()
        if output:
            cleaned_output = clean_ansi_codes(output)
            print(cleaned_output)
            status_code = cleaned_output.split()[-1]
            if status_code not in status_files:
                status_files[status_code] = open(f"{httpx_dir}/{status_code}.txt", "w")
            status_files[status_code].write(url + "\n")
    except Exception as e:
        print(f"Erreur lors de l'exécution de httpx pour {url}: {e}")

# Fermer tous les fichiers ouverts
for file in status_files.values():
    file.close()

print(f"\nLes résultats de httpx ont été triés dans le dossier {httpx_dir}")

# Exécution de dirsearch
print("\nLancement de dirsearch :")
print("========================")

for status_file in os.listdir(httpx_dir):
    if status_file.endswith(".txt") and status_file != "accessible.txt" and status_file != "inaccessible.txt":
        status_code = os.path.splitext(status_file)[0]
        file_path = os.path.join(httpx_dir, status_file)
        
        with open(file_path, "r") as f:
            urls = f.read().splitlines()

        for url in urls:
            # Extraire le domaine de l'URL
            domain = urlparse(url).netloc
            domain_dir = os.path.join(dirsearch_dir, domain)
            os.makedirs(domain_dir, exist_ok=True)

            output_file = os.path.join(domain_dir, f"{status_code}.txt")
            try:
                print(f"Scanning: {url}")
                subprocess.run([
                    "dirsearch", "-u", url, "-e", "php,html,js", "-o", output_file, "-q"
                ], check=True)
                print(f"Résultats sauvegardés dans {output_file}")
            except subprocess.CalledProcessError as e:
                print(f"Erreur lors de l'exécution de dirsearch pour {url}: {e}")
            except Exception as e:
                print(f"Erreur inattendue pour {url}: {e}")

print(f"\nLes résultats de dirsearch ont été sauvegardés dans le dossier {dirsearch_dir}")
