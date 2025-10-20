import socket
import threading

# Configuración
SERVER_IP = '192.168.10.100'  # IP del servidor
SERVER_PORT = 5000

def recibir_mensajes(sock):
    while True:
        try:
            mensaje = sock.recv(1024).decode()
            if mensaje:
                print("\n" + mensaje, end="")
                print("> ", end="", flush=True)
        except:
            print("\n❌ Desconectado del servidor")
            break

try:
    # Conectar al servidor
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    
    print(f"✅ Conectado al servidor {SERVER_IP}")
    print("Comandos: ON, OFF, ESTADO, SALIR")
    print("-" * 30)
    
    # Hilo para recibir mensajes
    hilo = threading.Thread(target=recibir_mensajes, args=(sock,))
    hilo.daemon = True
    hilo.start()
    
    # Enviar comandos
    while True:
        comando = input("> ").strip()
        
        if comando.upper() == "SALIR":
            break
        elif comando.upper() in ["ON", "OFF", "ESTADO"]:
            sock.send(comando.encode())
        else:
            print("❌ Comando no válido. Usa: ON, OFF, ESTADO, SALIR")
            
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    try:
        sock.close()
    except:
        pass
    print("👋 Desconectado")