#!/usr/bin/env python3
# SOCKET para hacer la conexión cliente-servidor, OS para interactuar con los archivos
# SHLEX para trabajar con los comandos ingresados y TIME para tener mayor control y visualizacion del tiempo
import socket, os, shlex, time

# Define el tamaño de cada bloque de datos que se enviará o recibirá (64 KB)
TAMANIO_BLOQUE = 64 * 1024

# Recibe datos desde el servidor hasta encontrar un salto de línea, devuelve la línea como texto decodificado
# y lo usamos para leer comandos o respuestas desde el servidor
def recibir_linea(conexion):
    buffer = bytearray()
    while True:
        salto = buffer.find(b"\n")
        if salto != -1:
            return buffer[:salto].decode().rstrip("\r")
        datos = conexion.recv(4096)
        if not datos:
            return buffer.decode() if buffer else ""
        buffer.extend(datos)

# Se le entregan los parámetros para descargar un archivo, antes de codificarlo y enviarlo se arma el comando
# a enviar utilizando GET. Luego, recibe la respuesta con el tamaño del archivo.
# Muestra el progreso de descarga
def descargar(conexion, archivo_remoto, archivo_local=None):
    archivo_local = archivo_local or archivo_remoto
    conexion.sendall(f"GET {archivo_remoto}\n".encode())
    respuesta = recibir_linea(conexion)
    if not respuesta or respuesta.startswith("ERR"):
        print("\033[1;31mError:\033[0m", respuesta or "Servidor cerró conexión"); return
    if not respuesta.startswith("OK "):
        print("Respuesta:", respuesta); return
    try: tamanio = int(respuesta.split()[1])
    except: print("Respuesta:", respuesta); return

    recibidos, tiempo_inicio = 0, time.time()
    with open(archivo_local, "wb") as archivo:
        while recibidos < tamanio:
            datos = conexion.recv(min(TAMANIO_BLOQUE, tamanio - recibidos))
            if not datos: break
            archivo.write(datos); recibidos += len(datos)
            if time.time() - tiempo_inicio > 0.5:
                porcentaje = (recibidos / tamanio) * 100
                print(f"\033[0;32m  Progreso: {recibidos}/{tamanio} bytes ({porcentaje:.1f}%)\033[0m", end="\r")
                tiempo_inicio = time.time()
    print(f"\033[0;32m  Progreso: {recibidos}/{tamanio} bytes (100.0%)\033[0m")
    print()
    if recibidos != tamanio:
        print("\033[1;31mDescarga incompleta\033[0m"); os.remove(archivo_local); return
    print(f"\033[1;34mDescargado en '{archivo_local}' ({tamanio} bytes)\033[0m")

# Se le entrega la ruta local del archivo que se quiere subir y se calcula el tamaño
# Usa los parámetros para concatenar con GET, posteriormente codificar y enviar al servidor
# Muestra el progreso de carga
def cargar(conexion, ruta_local, nombre_remoto=None):
    if not os.path.isfile(ruta_local):
        print(f"\033[1;31mNo existe el archivo: {ruta_local}\033[0m"); return
    tamanio = os.path.getsize(ruta_local)
    nombre_remoto = nombre_remoto or os.path.basename(ruta_local)
    conexion.sendall(f"PUT {nombre_remoto} {tamanio}\n".encode())

    enviados, tiempo_inicio = 0, time.time()
    with open(ruta_local, "rb") as archivo:
        while bloque := archivo.read(TAMANIO_BLOQUE):
            conexion.sendall(bloque); enviados += len(bloque)
            if time.time() - tiempo_inicio > 0.5:
                porcentaje = (enviados / tamanio) * 100
                print(f"  Progreso: {enviados}/{tamanio} bytes ({porcentaje:.1f}%)", end="\r")
                tiempo_inicio = time.time()
    print(f"\033[0;32m  Progreso: {enviados}/{tamanio} bytes (100.0%)\033[0m")
    print()
    print(f"\033[0;32mArchivo '{ruta_local}' subido como '{nombre_remoto}' ({tamanio} bytes)\033[0m" if recibir_linea(conexion).startswith("OK") else "Error")


# Muestra los comandos disponibles, es un bucle que queda a la espera de los comandos del usuario
# Usa shlex para dividir la entrada por partes, separando e identificando las palabras
# Antes de cargar/descargar hay que conectarse al servidor
def main():
    #print("CLIENTE\nComandos: \nconectarse <host> <puerto> \ndescargar <nombre> [carpeta_contenedor/nombre] \ncargar [carpeta_contenedor/nombre] \nsalir")
    print("\033[1;36m####################CLIENTE####################\033[0m")
    print("\033[1;33m > Comandos:\033[0m")
    print("\033[0;32m  conectarse <ip_host> <puerto>\033[0m")
    print("\033[0;32m  descargar <nombre_remoto> [nombre_para_local]\033[0m")
    print("\033[0;32m  cargar <nombre_local> [nombre_para_remoto]\033[0m")
    print("\033[0;31m  salir\033[0m")

    conexion = None
    while True:
        try: partes = shlex.split(input("comando> "))
        except (EOFError, KeyboardInterrupt): print(); break
        if not partes: continue
        comando = partes[0].lower()

        if comando == "salir": break
        elif comando == "conectarse" and len(partes) == 3:
            host, puerto = partes[1], int(partes[2])
            if conexion: conexion.close()
            try:
                conexion = socket.create_connection((host, puerto), timeout=10)
                conexion.settimeout(None)
                print(f"\033[0;32mConectado a {host}:{puerto}\033[0m")
            except Exception as error:
                print(f"\033[1;31mNo se pudo conectar: {error}\033[0m"); conexion = None
        elif comando in ("descargar", "cargar") and conexion:
            if comando == "descargar" and len(partes) in (2, 3):
                descargar(conexion, partes[1], partes[2] if len(partes) == 3 else None)
            elif comando == "cargar" and len(partes) in (2, 3):
                cargar(conexion, partes[1], partes[2] if len(partes) == 3 else None)
            else:
                print(f"Uso: {comando} <archivo> [nombre]")
        else:
            print("\033[1;31mComando inválido o no conectado\033[0m")

    if conexion: conexion.close()

# ejecuta el main si el archivo se corre directamente
if __name__ == "__main__":
    main()