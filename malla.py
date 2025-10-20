import socket
import threading
import time
import json
import serial

# =============================================================================
# CLASE BASE PARA TODOS LOS NODOS (EVITA IMPORTACIÓN)
# =============================================================================

class NodoMalla:
    def _init_(self, ip_propia, vecinos):
        self.ip = ip_propia
        self.vecinos = vecinos
        self.nodos_conectados = {}
        self.nodos_caidos = set()
        self.puerto = 11000
        self.arduino = None
        
    def conectar_vecino(self, ip_vecino):
        """Conectar a un vecino de la malla"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip_vecino, self.puerto))
            self.nodos_conectados[ip_vecino] = sock
            print(f"✅ Conectado a {ip_vecino}")
            return sock
        except Exception as e:
            print(f"❌ No se pudo conectar a {ip_vecino}: {e}")
            self.nodos_caidos.add(ip_vecino)
            return None
    
    def enviar_mensaje(self, destino, mensaje):
        """Enviar mensaje a través de la malla"""
        if destino in self.nodos_conectados:
            try:
                mensaje_completo = json.dumps({
                    'origen': self.ip,
                    'destino': destino,
                    'mensaje': mensaje,
                    'timestamp': time.time()
                })
                self.nodos_conectados[destino].send(mensaje_completo.encode())
                print(f"📤 Enviado directo a {destino}: {mensaje}")
                return True
            except:
                print(f"❌ Error enviando a {destino}")
                self.nodos_caidos.add(destino)
                return False
        else:
            print(f"❌ {destino} no está conectado directamente")
            return False
    
    def manejar_conexion(self, cliente, addr):
        """Manejar mensajes entrantes"""
        try:
            while True:
                datos = cliente.recv(1024).decode()
                if not datos:
                    break
                    
                mensaje = json.loads(datos)
                print(f"📨 De {mensaje['origen']} para {mensaje['destino']}: {mensaje['mensaje']}")
                
                # Si el mensaje es para este nodo
                if mensaje['destino'] == self.ip:
                    self.procesar_mensaje_local(mensaje['mensaje'])
                else:
                    print("🔄 Mensaje no para este nodo")
                    
        except Exception as e:
            print(f"❌ Error manejando conexión: {e}")
        finally:
            cliente.close()
    
    def procesar_mensaje_local(self, mensaje):
        """Procesar mensaje destinado a este nodo"""
        if mensaje.startswith("ARDUINO:"):
            comando = mensaje.split(":")[1]
            print(f"🎯 Comando Arduino: {comando}")
        else:
            print(f"💬 Mensaje: {mensaje}")
    
    def iniciar_servidor(self):
        """Iniciar servidor para recibir conexiones"""
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((self.ip, self.puerto))
        servidor.listen(5)
        
        print(f"🎯 {self.ip} escuchando en puerto {self.puerto}")
        
        while True:
            try:
                cliente, addr = servidor.accept()
                print(f"🔗 Nueva conexión de {addr[0]}")
                threading.Thread(target=self.manejar_conexion, args=(cliente, addr)).start()
            except Exception as e:
                print(f"❌ Error aceptando conexión: {e}")
    
    def conectar_malla(self):
        """Conectar con todos los vecinos"""
        print(f"🔗 Conectando a vecinos: {self.vecinos}")
        for vecino in self.vecinos:
            if vecino not in self.nodos_caidos:
                self.conectar_vecino(vecino)
    
    def mostrar_estado(self):
        """Mostrar estado de la malla"""
        print(f"\n📊 ESTADO {self.ip}")
        print(f"✅ Conectados: {list(self.nodos_conectados.keys())}")
        print(f"❌ Caídos: {list(self.nodos_caidos)}")
        print(f"🌐 Vecinos: {self.vecinos}")

# =============================================================================
# CLASE PC1 - SIN DEPENDENCIAS EXTERNAS
# =============================================================================

class PC1(NodoMalla):
    def _init_(self):
        super()._init_('192.168.40.101', ['192.168.40.102', '192.168.40.103', '192.168.40.104'])
    
    def iniciar(self):
        print("=== PC1 - MALLA ===")
        print("🔗 Vecinos: PC2 (40.102), PC3 (40.103), PC3 (40.104)")
        
        hilo_servidor = threading.Thread(target=self.iniciar_servidor)
        hilo_servidor.daemon = True
        hilo_servidor.start()
        
        time.sleep(2)
        self.conectar_malla()
        self.interfaz_usuario()
    
    def interfaz_usuario(self):
        while True:
            print("\n💡 Comandos: ENVIAR <destino> <mensaje>, ESTADO, TEST, SALIR")
            entrada = input("PC1> ").strip()
            
            if not entrada:
                continue
                
            partes = entrada.split()
            comando = partes[0].upper()
            
            if comando == "SALIR":
                break
            elif comando == "ESTADO":
                self.mostrar_estado()
            elif comando == "TEST":
                for vecino in ['192.168.40.102', '192.168.40.103', '192.168.40.104']:
                    if vecino in self.nodos_conectados:
                        self.enviar_mensaje(vecino, f"TEST desde PC1")
            elif comando == "ENVIAR" and len(partes) >= 3:
                destino = partes[1]
                mensaje = " ".join(partes[2:])
                self.enviar_mensaje(destino, mensaje)
            else:
                print("❌ Comando no válido")

# =============================================================================
# CLASE PC2 - SIN DEPENDENCIAS EXTERNAS
# =============================================================================

class PC2(NodoMalla):
    def _init_(self):
        super()._init_('192.168.40.102', ['192.168.40.103'])
    
    def iniciar(self):
        print("=== PC2 - MALLA ===")
        print("🔗 Vecinos: PC2 (40.103)")
        
        hilo_servidor = threading.Thread(target=self.iniciar_servidor)
        hilo_servidor.daemon = True
        hilo_servidor.start()
        
        time.sleep(2)
        self.conectar_malla()
        self.interfaz_usuario()
    
    def interfaz_usuario(self):
        while True:
            print("\n💡 Comandos: ENVIAR <destino> <mensaje>, ESTADO, TEST, SALIR")
            entrada = input("PC2> ").strip()
            
            if not entrada:
                continue
                
            partes = entrada.split()
            comando = partes[0].upper()
            
            if comando == "SALIR":
                break
            elif comando == "ESTADO":
                self.mostrar_estado()
            elif comando == "TEST":
                for vecino in ['192.168.40.103']:
                    if vecino in self.nodos_conectados:
                        self.enviar_mensaje(vecino, f"TEST desde PC2")
            elif comando == "ENVIAR" and len(partes) >= 3:
                destino = partes[1]
                mensaje = " ".join(partes[2:])
                self.enviar_mensaje(destino, mensaje)

# =============================================================================
# CLASE PC3 - CON ARDUINO
# =============================================================================

class PC3(NodoMalla):
    def _init_(self):
        super()._init_('192.168.40.103', ['192.168.40.101', '192.168.40.104'])
        self.arduino = None
    
    def conectar_arduino(self):
        try:
            self.arduino = serial.Serial('COM3', 9600, timeout=1)
            time.sleep(2)
            print("✅ Arduino conectado en PC3")
            return True
        except:
            print("❌ Arduino no disponible, simulando...")
            return False
    
    def procesar_mensaje_local(self, mensaje):
        """Procesar mensaje destinado a este nodo"""
        if mensaje.startswith("ARDUINO:"):
            comando = mensaje.split(":")[1]
            print(f"🎯 Ejecutando en Arduino: {comando}")
            
            if self.arduino:
                self.arduino.write(f"{comando}\n".encode())
                time.sleep(0.5)
                if self.arduino.in_waiting > 0:
                    respuesta = self.arduino.readline().decode().strip()
                    print(f"🔄 Arduino: {respuesta}")
            else:
                print(f"🔧 Simulación: Arduino {comando}")
        else:
            print(f"💬 Mensaje: {mensaje}")
    
    def iniciar(self):
        print("=== PC3 - MALLA (CON ARDUINO) ===")
        print("🔗 Vecinos: PC1 (40.101), PC4 (40.104)")
        
        self.conectar_arduino()
        
        hilo_servidor = threading.Thread(target=self.iniciar_servidor)
        hilo_servidor.daemon = True
        hilo_servidor.start()
        
        time.sleep(2)
        self.conectar_malla()
        self.interfaz_usuario()
    
    def interfaz_usuario(self):
        while True:
            print("\n💡 Comandos: ENVIAR <destino> <mensaje>, ARDUINO <cmd>, ESTADO, SALIR")
            entrada = input("PC3> ").strip()
            
            if not entrada:
                continue
                
            partes = entrada.split()
            comando = partes[0].upper()
            
            if comando == "SALIR":
                break
            elif comando == "ESTADO":
                self.mostrar_estado()
            elif comando == "ARDUINO" and len(partes) >= 2:
                accion = " ".join(partes[1:])
                self.procesar_mensaje_local(f"ARDUINO:{accion}")
            elif comando == "ENVIAR" and len(partes) >= 3:
                destino = partes[1]
                mensaje = " ".join(partes[2:])
                self.enviar_mensaje(destino, mensaje)

# =============================================================================
# CLASE PC4
# =============================================================================

class PC4(NodoMalla):
    def _init_(self):
        super()._init_('192.168.40.104', ['192.168.40.102', '192.168.40.103'])
    
    def iniciar(self):
        print("=== PC4 - MALLA ===")
        print("🔗 Vecinos: PC2 (40.102), PC3 (40.103)")
        
        hilo_servidor = threading.Thread(target=self.iniciar_servidor)
        hilo_servidor.daemon = True
        hilo_servidor.start()
        
        time.sleep(2)
        self.conectar_malla()
        self.interfaz_usuario()
    
    def interfaz_usuario(self):
        while True:
            print("\n💡 Comandos: ENVIAR <destino> <mensaje>, ESTADO, TEST, SALIR")
            entrada = input("PC4> ").strip()
            
            if not entrada:
                continue
                
            partes = entrada.split()
            comando = partes[0].upper()
            
            if comando == "SALIR":
                break
            elif comando == "ESTADO":
                self.mostrar_estado()
            elif comando == "TEST":
                for vecino in ['192.168.40.101', '192.168.40.102', '192.168.40.103']:
                    if vecino in self.nodos_conectados:
                        self.enviar_mensaje(vecino, f"TEST desde PC4")
            elif comando == "ENVIAR" and len(partes) >= 3:
                destino = partes[1]
                mensaje = " ".join(partes[2:])
                self.enviar_mensaje(destino, mensaje)

# =============================================================================
# SELECCIÓN DE MÁQUINA AL EJECUTAR
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("           TOPOLOGÍA MALLA - SELECCIÓN DE NODO")
    print("=" * 60)
    print("1. PC1 (192.168.40.101) - Conecta a PC2 y PC3")
    print("2. PC2 (192.168.40.102) - Conecta a PC1 y PC4") 
    print("3. PC3 (192.168.40.103) - Con Arduino, conecta a PC1 y PC4")
    print("4. PC4 (192.168.40.104) - Conecta a PC2 y PC3")
    print("=" * 60)
    
    while True:
        opcion = input("Selecciona el número de tu PC (1-4): ").strip()
        
        if opcion == "1":
            nodo = PC1()
            break
        elif opcion == "2":
            nodo = PC2()
            break
        elif opcion == "3":
            nodo = PC3()
            break
        elif opcion == "4":
            nodo = PC4()
            break
        else:
            print("❌ Opción no válida. Usa 1, 2, 3 o 4")
    
    nodo.iniciar()