import socket
import threading

class Intermedia2:
    def _init_(self):  # INIT CORRECTO
        self.ip_propia = '192.168.40.101'
        self.puerto_hojas = 9001
        self.ip_raiz = '192.168.40.100'
        self.puerto_raiz = 9000
        self.conexion_raiz = None
    
    def conectar_raiz(self):
        try:
            self.conexion_raiz = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conexion_raiz.connect((self.ip_raiz, self.puerto_raiz))
            print("✅ Conectado a raíz")
            return True
        except Exception as e:
            print("❌ Error conectando a raíz:", e)
            return False
    
    def manejar_hoja(self, cliente, addr):
        print(f"Hoja conectada: {addr[0]}")
        
        try:
            while True:
                datos = cliente.recv(1024).decode()
                if datos:
                    print(f"Datos de hoja: {datos}")
                    if self.conexion_raiz:
                        self.conexion_raiz.send(datos.encode())
        except:
            pass
        
        cliente.close()
        print(f"Hoja desconectada: {addr[0]}")
    
    def iniciar_servidor(self):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind((self.ip_propia, self.puerto_hojas))
        servidor.listen(5)
        
        print(f"Intermedia2 lista en {self.ip_propia}:{self.puerto_hojas}")
        
        while True:
            cliente, addr = servidor.accept()
            hilo = threading.Thread(target=self.manejar_hoja, args=(cliente, addr))
            hilo.daemon = True
            hilo.start()
    
    def iniciar(self):
        if self.conectar_raiz():
            self.iniciar_servidor()

# ✅ BLOQUE MAIN CORRECTO
if __name__ == "__main__":
    print("=== INTERMEDIA 1 ===")
    intermedia = Intermedia2()
    intermedia.iniciar()