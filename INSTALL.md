# Instrukcja Wdrożenia i Instalacji MapBike na Serwerze Ubuntu 🐧

Ta instrukcja opisuje krok po kroku proces instalacji i uruchomienia aplikacji **MapBike** na serwerze z systemem **Ubuntu 22.04 LTS / 24.04 LTS**.

---

## 📋 Wymagania Wstępne Serwera

- Serwer VPS / Dedykowany z systemem Ubuntu Server 22.04 LTS lub nowszym.
- Dostęp przez SSH z uprawnieniami `sudo`.
- Otwarty port 80 (HTTP) oraz port 443 (HTTPS w przypadku domeny).

---

# WARIANT A: Instalacja przy użyciu Docker & Docker Compose 🐳 (Rekomendowana)

Wariant z konteneryzacją zapewnia szybką instalację oraz niezależność środowiskową.

### Krok 1: Aktualizacja systemu i instalacja Dockera
Połącz się z serwerem SSH i wykonaj:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git docker.io docker-compose-v2
sudo systemctl enable --now docker
```

### Krok 2: Pobranie kodu repozytorium MapBike
```bash
cd /opt
sudo git clone https://github.com/user/mapbike.git
cd mapbike
```

### Krok 3: Budowanie i uruchomienie kontenera
Uruchom aplikację w tle za pomocą Docker Compose:
```bash
sudo docker compose up -d --build
```

### Krok 4: Sprawdzenie stanu kontenera
```bash
sudo docker compose ps
sudo docker compose logs -f
```

Aplikacja dostępna jest pod adresem:
`http://ADRES_IP_SERWERA:8000`

---

# WARIANT B: Instalacja Natywna Bez Dockera (Systemd + Nginx + Uvicorn) 🛠️

Wariant tradycyjny instalacji na systemie Ubuntu bez użycia kontenerów.

### Krok 1: Instalacja pakietów systemowych i Pythona
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx git curl
```

### Krok 2: Pobranie aplikacji do katalogu `/var/www/mapbike`
```bash
sudo mkdir -p /var/www/mapbike
sudo chown -R $USER:$USER /var/www/mapbike
cd /var/www/mapbike

git clone https://github.com/user/mapbike.git .
```

### Krok 3: Utworzenie wirtualnego środowiska Python i instalacja bibliotek
```bash
cd /var/www/mapbike/backend
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Krok 4: Utworzenie Usługi Systemd (`mapbike.service`)
Utwórz plik konfiguracji usługi systemowej:
```bash
sudo nano /etc/systemd/system/mapbike.service
```

Wklej poniższą zawartość (dostosuj ścieżki jeśli są inne):
```ini
[Unit]
Description=MapBike FastAPI Server Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/mapbike/backend
ExecStart=/var/www/mapbike/backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Zmień uprawnienia do katalogu dla użytkownika `www-data`:
```bash
sudo chown -R www-data:www-data /var/www/mapbike
```

Uruchom i włącz automatyczny start usługi:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mapbike
sudo systemctl status mapbike
```

---

### Krok 5: Konfiguracja Serwera Nginx (Reverse Proxy)

Utwórz plik konfiguracyjny Nginx dla MapBike:
```bash
sudo nano /etc/nginx/sites-available/mapbike
```

Wklej poniższą konfigurację Nginx:
```nginx
server {
    listen 80;
    server_name twoja-domena.pl ADRES_IP_SERWERA;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Włącz nową stronę i przetestuj konfigurację Nginx:
```bash
sudo ln -s /etc/systemd/system /etc/nginx/sites-enabled/mapbike
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔒 opcjonalnie: Instalacja Bezpłatnego Certyfikatu SSL Certbot (HTTPS)

Jeśli posiadasz własną domenę skierowaną na serwer IP:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d twoja-domena.pl
```

Certyfikat odnowi się automatycznie.

---

## 🔍 Weryfikacja Działania i Diagnostyka

- Sprawdzenie logów backendu w Dockerze: `sudo docker compose logs -f`
- Sprawdzenie logów usługi natywnej: `sudo journalctl -u mapbike -f`
- Przetestowanie odpowiedzi serwera: `curl -I http://127.0.0.1:8000/health`
