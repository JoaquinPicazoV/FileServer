#!/usr/bin/env python3
import os, socket, threading, re, sys
from typing import Tuple

# Configuramos los parametros principales
ANFITRION = os.environ.get("HOST", "0.0.0.0")
PUERTO = int(os.environ.get("PORT", "5000"))
CARPETA_BASE = os.environ.get("FILES_DIR", "/data")
MAXIMO_SUBIDA = int(os.environ.get("MAX_UPLOAD_BYTES", "5242880"))
TAMANIO_BLOQUE = 64 * 1024

# se valida que sean nombres validos para archivos y no simbolos raros
VALIDO_NOMBRE = re.compile(r"^[a-zA-Z0-9._-]{1,255}$")

# crea la carpeta si es que no existiera por algun motivo en los directorios
def asegurar_carpeta():
    os.makedirs(CARPETA_BASE, exist_ok=True)

# Valida el nombre del archivo con los carácteres y numerosque definimos anteriormente
# asegura que se trabaje dentro de la carpeta/directorio asignado para los archivos
#y evita que se modifiquen otros directorios que no sea el destinado para archivos
def ruta_segura(nombre: str) -> str:
    if not VALIDO_NOMBRE.match(nombre):
        raise ValueError("\033[1;33mNombre de archivo inválido. Usa solo letras, números, ., _, -\033[0m")
    ruta = os.path.normpath(os.path.join(CARPETA_BASE, nombre))
    base = os.path.abspath(CARPETA_BASE)
    if not os.path.abspath(ruta).startswith(base + os.sep) and os.path.abspath(ruta) != base:
        raise ValueError("\033[1;33mRuta fuera del directorio permitido\033[0m")
    return ruta

# lee los datos del socket hasta que se encuentra el salto de linea ya que esto permite separar los mensajes
#devuelve la linea decodificada y su principal funcion es leer comandos del cliente
def recibir_linea(sock, buffer: bytearray) -> Tuple[str, bytearray]:
    while True:
        salto = buffer.find(b"\n")
        if salto != -1:
            linea = buffer[:salto]
            restante = buffer[salto+1:]
            try:
                return linea.decode("utf-8").rstrip("\r"), restante
            except UnicodeDecodeError:
                return "", bytearray()
        datos = sock.recv(4096)
        if not datos:
            try: return buffer.decode("utf-8"), bytearray()
            except: return "", bytearray()
        buffer.extend(datos)

#envia la linea de texto al cliente con un salto de linea para delimitar el mensaje
def enviar_linea(sock, texto: str):
    sock.sendall((texto + "\n").encode("utf-8"))

# verifica si el archivo existe, sino avisa. Envia al cliente el tamaño del archivo
# ademas divide en bloques el contenido y lo envía.
def manejar_descarga(sock, nombre: str):
    ruta = ruta_segura(nombre)
    if not os.path.isfile(ruta):
        enviar_linea(sock, "\033[1;33mERROR 404 No existe el archivo\033[0m"); return
    tamanio = os.path.getsize(ruta)
    enviar_linea(sock, f"OK {tamanio}")
    with open(ruta, "rb") as archivo:
        while bloque := archivo.read(TAMANIO_BLOQUE):
            sock.sendall(bloque)

# verifica que el tamaño sea menor al limite asignado, lo recibe en bloques y lo guarda
def manejar_subida(sock, nombre: str, tamanio: int):
    if tamanio < 0:
        enviar_linea(sock, "\033[1;33mERROR 400 Tamaño inválido, no puede ser menor a 0\033[0m"); return
    if tamanio > MAXIMO_SUBIDA:
        enviar_linea(sock, "\033[1;33mTamaño inválido, usa uno más pequeño.\033[0m"); return
    ruta = ruta_segura(nombre)
    recibidos = 0
    try:
        with open(ruta, "wb") as archivo:
            while recibidos < tamanio:
                datos = sock.recv(min(TAMANIO_BLOQUE, tamanio - recibidos))
                if not datos: break
                archivo.write(datos); recibidos += len(datos)
        if recibidos != tamanio:
            os.remove(ruta)
            enviar_linea(sock, "\033[1;33mERROR 499 Incompleto\033[0m"); return
        enviar_linea(sock, "OK")
    except:
        try: os.remove(ruta)
        except: pass
        enviar_linea(sock, "\033[1;33mError del servidor\033[0m")

# maneja la comunicacion con el cliente usando la lectura de GET y PUT. cada cliente
# va a tener un hilo
def hilo_cliente(conexion, direccion):
    print("\033[92m" + f"[+] Conectado {direccion}" + "\033[0m")
    buffer = bytearray()
    try:
        while True:
            linea, buffer = recibir_linea(conexion, buffer)
            if not linea: break
            partes = linea.strip().split()
            if not partes: continue
            comando = partes[0].upper()

            if comando == "GET" and len(partes) == 2:
                try: manejar_descarga(conexion, partes[1])
                except ValueError as e: enviar_linea(conexion, f"\033[1;33mERROR 400 {e}\033[0m")

                except: enviar_linea(conexion, "Error del servidor")
            elif comando == "PUT" and len(partes) == 3:
                try: tamanio = int(partes[2])
                except: enviar_linea(conexion, "\033[1;33mTamaño inválido, usa uno más pequeño.\033[0m"); continue
                try: manejar_subida(conexion, partes[1], tamanio)
                except ValueError as e: enviar_linea(conexion, f"\033[1;33mERROR 400 {e}\033[0m")
                except: enviar_linea(conexion, "Error del servidor")
            else:
                enviar_linea(conexion, "\033[1;33mERROR 400 Comando Desconocido\033[0m")
    finally:
        conexion.close()
        print("\033[91m" + f"[-] Desconectado {direccion}" + "\033[0m")

# crea el socket y establece conexion con el cliente, tira un hilo para cada cliente
def main():
    asegurar_carpeta()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((ANFITRION, PUERTO))
        servidor.listen(64)
        print("\033[92m" + f"Servidor escuchando en {ANFITRION}:{PUERTO} | Directorio de archivos: {CARPETA_BASE} | Límite subida: {MAXIMO_SUBIDA} bytes (5,24 MB)" + "\033[0m")

        while True:
            conexion, direccion = servidor.accept()
            threading.Thread(target=hilo_cliente, args=(conexion, direccion), daemon=True).start()

# ejecuta el servidor si se ejecuta directamente
if __name__ == "__main__":
    main()