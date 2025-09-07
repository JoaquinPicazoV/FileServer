# 📁 Proyecto de Transferencia de Archivos en Red (Cliente-Servidor en Python) usando 🐳DOCKER

Este proyecto implementa un sistema de transferencia de archivos entre un servidor y cliente usando sockets TCP. Está diseñado para funcionar en una red local, permitiendo subir y descargar archivos. Ideal para equipo Linux (ej: Ubuntu).

---
# Pasos para ejecución solo utilizando los archivos en python (SIN DOCKER)
## 🧱 Requisitos

- Python instalado en el servidor y en los clientes
- Red local compartida entre el servidor y los clientes
- Dos archivos: `server.py` y `client.py`

## 🚀 Ejecución del servidor solo usando servidor.py

### SERVIDOR:
### 1. Clonar el repositorio en tu ubuntu.
```bash
git clone {url}
```
### 2. Colocar la IP del dispositivo que será host para el servidor en la red y el puerto a la escucha.
```bash
ANFITRION = os.environ.get("HOST", "192.168.18.217")
```
```bash
PUERTO = int(os.environ.get("PORT", "5000"))
```
### 3. Elegir la ruta del directorio en la cual se almacenarán los archivos. Es importante que ese directorio exista en la ubicación dada y se tenga permisos para leer y modificar.
```bash
CARPETA_BASE = os.environ.get("FILES_DIR", "/data")
```
### 4. Ingresar al directorio del archivo "server.py" y ejecutar.
```bash
python3 server.py
```
### 5. Esperar conexiones e interacción de clientes.

### CLIENTE:
### 1. Clonar el repositorio en tu computadora.
```bash
git clone {url}
```
### 2. Ejecutar "client.py".
```bash
python client.py
```
```bash
python3 client.py
```
### 3. Usar el comando "conectarse" entregando la IP del host en la red y el puerto (definidos en "server.py"), por ejemplo:
```bash
conectarse 192.168.18.217 5000
```
### 4. Empezar a interactuar con los comandos existentes que otorga el programa.

---

# 🐳 Pasos para ejecución para DOCKERIZAR EL SERVIDOR
### 1. Clonar repositorio desde ubuntu
```bash
git clone https://github.com/JoaquinPicazoV/FileServer.git
```

### 2. Instalar y actualizar elementos clave en ubuntu
```bash
sudo apt install docker-compose
```
```bash
sudo apt update
```
```bash
sudo apt install python3-setuptools
```

### 3. Entrar al proyecto clonado y dockerizar el proyecto completo en la raiz del proyecto
```bash
sudo docker-compose up --build
```

### 4. Dockerizar y ejecutar solo el servidor (queda a la espera de conexiones)
```bash
sudo docker-compose up --build server
```

---

# ⚙️📦 Pasos para ejecución para conectar cliente con IMAGEN DOCKER (WINDOWS)
### 1. Descargar la imagen para el cliente
```bash
docker pull joaquinpicazo/client:v0
```
### 2. Conectarse al servidor usando la imagen
```bash
docker run -it --rm -v C:{path_windows}:/app/archivos joaquinpicazo/client:v0
```
### Por ejemplo:
```bash
docker run -it --rm -v C:\Users\pepe\Desktop\universidad:/app/archivos joaquinpicazo/client:v0
```

### 3. Usar los comandos con la sintaxis correcta
### {ip_ubuntu_host} = ip de la máquina que hostea servidor docker
```bash
conectarse {ip_ubuntu_host} 5000
```
### {nombre_archivo} = nombre del archivo del servidor  -  archivos/{nombre_archivo} = Nombre archivo para guardarlo en carpeta local montada en contenedor
```bash
descargar {nombre_archivo} archivos/{nombre_archivo}
```
### archivos/{nombre_archivo} = Nombre archivo local para enviarlo desde carpeta local montada en contenedor
```bash
cargar archivos/{nombre_archivo}
```
