# GUÍA DE INSTALACIÓN Y DESPLIEGUE EN SERVIDOR
## Sistema de Análisis y Seguimiento del Perfil Emprendedor
### Universidad Santo Tomás – Seccional Villavicencio
**Dependencia:** Dirección de Proyección Social

---

## 1. Requisitos del Sistema

### Hardware Recomendado
- **Procesador:** 2 núcleos x86-64 o superior.
- **Memoria RAM:** Mínimo 2 GB (4 GB recomendados para generación concurrente de archivos ZIP).
- **Almacenamiento:** Mínimo 10 GB de espacio libre en disco.

### Software
- **Sistema Operativo:** Windows 10/11, Windows Server 2019/2022, o Linux (Ubuntu 20.04/22.04 LTS, Debian, RedHat).
- **Entorno de Ejecución:** Python 3.10, 3.11 o 3.12 (o Docker).
- **Navegadores Compatibles:** Google Chrome, Microsoft Edge, Mozilla Firefox, Safari.

---

## 2. Opción A: Despliegue en Windows (1 Solo Clic)

El sistema incluye lanzadores automáticos que verifican dependencias, inicializan la base de datos y abren el navegador institucional:

1. Copie la carpeta `perfil-emprendedor-usta` al computador o servidor deseado.
2. Haga doble clic sobre el archivo:
   ```cmd
   iniciar_sistema.bat
   ```
   *(o haga clic derecho en `iniciar_sistema.ps1` y seleccione "Ejecutar con PowerShell")*.
3. El script iniciará el servidor web en `http://localhost:8000` y abrirá la aplicación en su navegador predeterminado.
4. Para detener la aplicación, simplemente cierre la ventana de comandos o presione `Ctrl + C`.

---

## 3. Opción B: Despliegue con Docker y Docker Compose (Recomendado para Servidores Institucionales)

Esta opción garantiza aislamiento total y funcionamiento idéntico en cualquier infraestructura:

1. Instale Docker y Docker Compose en el servidor.
2. Desde la carpeta raíz del proyecto, ejecute:
   ```bash
   docker-compose up -d --build
   ```
3. El contenedor compilará el entorno, inicializará la base de datos persistente en el volumen `./data` y levantará el servicio en el puerto `8000`.
4. Verifique el estado del contenedor:
   ```bash
   docker ps
   ```
5. El sistema estará accesible inmediatamente en `http://[IP_DEL_SERVIDOR]:8000`.

---

## 4. Opción C: Despliegue en Servidor Linux Institucional (Ubuntu/Debian + Nginx + Systemd)

### Paso 1: Clonar y configurar entorno
```bash
cd /opt
sudo git clone <repositorio> perfil-emprendedor-usta
cd perfil-emprendedor-usta

# Crear entorno virtual de Python
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Inicializar base de datos
python scripts/seed_data.py
```

### Paso 2: Crear servicio Systemd
Cree el archivo `/etc/systemd/system/usta-perfil.service`:
```ini
[Unit]
Description=Sistema Perfil Emprendedor USTA Villavicencio
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/perfil-emprendedor-usta
Environment="PATH=/opt/perfil-emprendedor-usta/venv/bin"
Environment="DATABASE_URL=sqlite:////opt/perfil-emprendedor-usta/data/usta_perfil.db"
Environment="SECRET_KEY=clave-secreta-institucional-usta-2026-produccion"
ExecStart=/opt/perfil-emprendedor-usta/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 3

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Habilite y arranque el servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable usta-perfil
sudo systemctl start usta-perfil
```

### Paso 3: Configurar Nginx y Certificado HTTPS (Let's Encrypt)
Cree el archivo `/etc/nginx/sites-available/perfil.usta.edu.co`:
```nginx
server {
    listen 80;
    server_name perfil.villavicencio.usta.edu.co;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Habilite el sitio y aplique HTTPS:
```bash
sudo ln -s /etc/nginx/sites-available/perfil.usta.edu.co /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d perfil.villavicencio.usta.edu.co
```

---

## 5. Migración a Base de Datos PostgreSQL (Opcional)

Si el Departamento de Tecnología de la Universidad Santo Tomás prefiere alojar los datos en el clúster institucional de PostgreSQL:
1. Instale el driver de postgres:
   ```bash
   pip install psycopg2-binary
   ```
2. Modifique la variable de entorno en su archivo `.env` o en el servicio:
   ```env
   DATABASE_URL=postgresql://usuario_usta:contraseña_segura@db.villavicencio.usta.edu.co:5432/perfil_emprendedor
   ```
3. Ejecute `python scripts/seed_data.py`. SQLAlchemy creará automáticamente todas las tablas, índices y restricciones en PostgreSQL sin modificar una sola línea del código fuente.
