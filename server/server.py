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
    if not VALIDO_NOMBRE.match(nombre):  # Rechaza nombres que no cumpla con la expresión regular
        raise ValueError("\033[1;33mNombre de archivo inválido. Usa solo letras, números, ., _, -\033[0m")
    ruta = os.path.normpath(os.path.join(CARPETA_BASE, nombre)) # Construye y normaliza la ruta
    base = os.path.abspath(CARPETA_BASE)                        # Ruta absoluta de la base.
    # Verifica que la ruta final quede dentro de CARPETA_BASE
    if not os.path.abspath(ruta).startswith(base + os.sep) and os.path.abspath(ruta) != base:
        raise ValueError("\033[1;33mRuta fuera del directorio permitido\033[0m")
    return ruta

# lee los datos del socket hasta que se encuentra el salto de linea ya que esto permite separar los mensajes
#devuelve la linea decodificada y su principal funcion es leer comandos del cliente
def recibir_linea(sock, buffer: bytearray) -> Tuple[str, bytearray]:
    while True:
        salto = buffer.find(b"\n")                 # Busca el salto de línea en el buffer
        if salto != -1:
            linea = buffer[:salto]          # Extrae la línea hasta el salto
            restante = buffer[salto+1:]     # Deja el resto en buffer
            try:
                return linea.decode("utf-8").rstrip("\r"), restante # Decodifica UTF-8, quita \r final si venía
            except UnicodeDecodeError:
                return "", bytearray()
        datos = sock.recv(4096)          # Lee más datos del socket
        if not datos:                   # Conexión cerrada
            try: return buffer.decode("utf-8"), bytearray() # Devuelve lo que queda en buffer
            except: return "", bytearray() # Si no se puede decodificar, devuelve cadena vacía
        buffer.extend(datos) # Añade los datos leídos al buffer

#envia la linea de texto al cliente con un salto de linea para delimitar el mensaje
def enviar_linea(sock, texto: str):
    sock.sendall((texto + "\n").encode("utf-8"))  # Envía la línea con salto de línea

# verifica si el archivo existe, sino avisa. Envia al cliente el tamaño del archivo
# ademas divide en bloques el contenido y lo envía.
def manejar_descarga(sock, nombre: str):
    ruta = ruta_segura(nombre)          # Obtiene la ruta segura del archivo
    if not os.path.isfile(ruta):        # Verifica si el archivo existe
        enviar_linea(sock, "\033[1;33mERROR 404 No existe el archivo\033[0m"); return
    tamanio = os.path.getsize(ruta) # Obtiene el tamaño del archivo
    enviar_linea(sock, f"OK {tamanio}") # Envía "OK" y el tamaño del archivo
    with open(ruta, "rb") as archivo: # Abre el archivo en binario
        while bloque := archivo.read(TAMANIO_BLOQUE): # Lee y envía en bloques
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
        with open(ruta, "wb") as archivo:  # Abre el archivo en binario
            while recibidos < tamanio: # Lee hasta completar el tamaño
                datos = sock.recv(min(TAMANIO_BLOQUE, tamanio - recibidos)) # No leer más de lo que falta.
                if not datos: break # Conexión cerrada antes de tiempo
                archivo.write(datos); recibidos += len(datos) # Escribe y cuenta bytes recibidos
        if recibidos != tamanio: # Verifica si se recibió todo
            os.remove(ruta) # Borra el archivo incompleto
            enviar_linea(sock, "\033[1;33mERROR 499 Incompleto\033[0m"); return
        enviar_linea(sock, "OK")
    except:
        try: os.remove(ruta)
        except: pass
        enviar_linea(sock, "\033[1;33mError del servidor\033[0m")

# maneja la comunicacion con el cliente usando la lectura de GET y PUT. cada cliente
# va a tener un hilo
def hilo_cliente(conexion, direccion):
    print("\033[92m" + f"[+] Conectado {direccion}" + "\033[0m") # Mensaje de conexión
    buffer = bytearray() # Buffer para datos recibidos
    try:
        while True:
            linea, buffer = recibir_linea(conexion, buffer) # Lee una línea
            if not linea: break # Conexión cerrada
            partes = linea.strip().split() # Divide la línea en partes
            if not partes: continue # Línea vacía, ignora
            comando = partes[0].upper() # Comando en mayúsculas

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
    asegurar_carpeta() # Asegura que la carpeta base exista
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor: # Crea el socket TCP
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reutiliza la dirección
        servidor.bind((ANFITRION, PUERTO)) # Asocia IP:puerto
        servidor.listen(64) # Escucha conexiones entrantes; backlog de 64 conexiones pendientes
        print("\033[92m" + f"Servidor escuchando en {ANFITRION}:{PUERTO} | Directorio de archivos: {CARPETA_BASE} | Límite subida: {MAXIMO_SUBIDA} bytes (5,24 MB)" + "\033[0m")

        while True:
            conexion, direccion = servidor.accept() # Espera una conexión
            # Crea un hilo para manejar al cliente
            threading.Thread(target=hilo_cliente, args=(conexion, direccion), daemon=True).start()

# ejecuta el servidor si se ejecuta directamente
if __name__ == "__main__":
    main()