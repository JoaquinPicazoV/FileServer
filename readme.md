# 📁 Proyecto de Transferencia de Archivos en Red (Cliente-Servidor en Python)

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
### 3. Ejecutar "client.py".
```bash
python client.py
```
```bash
python3 client.py
```
### 3. Usar el comando "conectarse" entregando la IP del host en la red y el puerto (definidos en "server.py")
```bash
conectarse 192.168.18.217 5000
```
### 3. Empezar a interactuar con los comandos existentes que otorga el programa.


