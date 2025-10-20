import socket
import threading
import time
import json
import serial

# =============================================================================
# CLASE BASE PARA LA TOPOLOGÍA EN ANILLO
# =============================================================================

class NodoAnillo:
    def _init_(self, ip_propia, ip_siguiente, tiene_arduino=False):
        self.ip = ip_propia
        self.ip_siguiente = ip_siguiente
        self.tiene_arduino = tiene_arduino
        self.puerto = 13000
        self.token = False
        self.arduino = None
        self.conexion_activa = None
        self.servidor_activo = True
        self.nodo_siguiente_caido = False
        
    def conectar_arduino(self):
        if self.tiene_arduino:
            try:
                self.arduino = serial.Serial('COM3', 9600, timeout=1)
                time.sleep(2)
                print("✅ Arduino conectado")
                return True
            except:
                print("❌ Arduino no disponible, simulando...")
                return False
    
    def conectar_siguiente_nodo(self):
        """Conectar al siguiente nodo en el anillo"""
        intentos = 0
        while intentos < 3:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((self.ip_siguiente, self.puerto))
                self.conexion_activa = sock
                self.nodo_siguiente_caido = False
                print(f"✅ Conectado al siguiente nodo: {self.ip_siguiente}")
                return True
            except Exception as e:
                intentos += 1
                print(f"❌ Intento {intentos}/3 - No se pudo conectar a {self.ip_siguiente}: {e}")
                time.sleep(2)
        
        self.nodo_siguiente_caido = True
        print(f"🚨 Nodo siguiente {self.ip_siguiente} considerado caído")
        return False
    
    def enviar_token(self, mensaje_token=""):
        """Enviar token al siguiente nodo"""
        if not self.token:
            print("❌ No tengo el token para enviar")
            return False
            
        if self.nodo_siguiente_caido:
            print(f"⚠  Nodo siguiente {self.ip_siguiente} está caído, no se puede enviar token")
            return False
            
        try:
            mensaje = {
                'tipo': 'TOKEN',
                'origen': self.ip,
                'destino': self.ip_siguiente,
                'mensaje': mensaje_token,
                'timestamp': time.time()
            }
            self.conexion_activa.send(json.dumps(mensaje).encode())
            self.token = False
            print(f"📤 Token enviado a {self.ip_siguiente}: {mensaje_token}")
            return True
        except Exception as e:
            print(f"❌ Error enviando token: {e}")
            self.nodo_siguiente_caido = True
            return False
    
    def manejar_conexion(self, cliente, addr):
        """Manejar conexiones entrantes (recibir token)"""
        try:
            while True:
                datos = cliente.recv(1024).decode()
                if not datos:
                    break
                    
                mensaje = json.loads(datos)
                
                if mensaje['tipo'] == 'TOKEN':
                    print(f"🎟  TOKEN recibido de {mensaje['origen']}")
                    self.token = True
                    
                    # Procesar mensaje del token si lo hay
                    if mensaje['mensaje']:
                        print(f"💬 Mensaje en token: {mensaje['mensaje']}")
                        
                        # Si es un comando para Arduino y este nodo lo tiene
                        if mensaje['mensaje'].startswith("ARDUINO:") and self.tiene_arduino:
                            comando = mensaje['mensaje'].split(":")[1]
                            self.procesar_comando_arduino(comando)
                    
                    # Mantener el token por un tiempo
                    time.sleep(10)
                    
                    # Pasar el token al siguiente nodo
                    self.enviar_token()
                    
        except Exception as e:
            print(f"❌ Error manejando conexión: {e}")
        finally:
            cliente.close()
    
    def procesar_comando_arduino(self, comando):
        """Procesar comando para el Arduino"""
        print(f"🎯 Ejecutando en Arduino: {comando}")
        
        if self.arduino:
            try:
                self.arduino.write(f"{comando}\n".encode())
                time.sleep(0.5)
                if self.arduino.in_waiting > 0:
                    respuesta = self.arduino.readline().decode().strip()
                    print(f"🔄 Arduino: {respuesta}")
            except Exception as e:
                print(f"❌ Error con Arduino: {e}")
        else:
            print(f"🔧 Simulación: Arduino ejecuta {comando}")
    
    def iniciar_servidor(self):
        """Iniciar servidor para recibir token"""
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((self.ip, self.puerto))
        servidor.listen(5)
        
        print(f"🎯 {self.ip} escuchando en puerto {self.puerto}")
        
        while self.servidor_activo:
            try:
                cliente, addr = servidor.accept()
                print(f"🔗 Conexión entrante de {addr[0]}")
                threading.Thread(target=self.manejar_conexion, args=(cliente, addr), daemon=True).start()
            except:
                break
        
        servidor.close()
    
    def simular_caida(self, duracion=10):
        """Simular caída de este nodo"""
        print(f"🔄 Simulando caída por {duracion} segundos...")
        self.servidor_activo = False
        if self.conexion_activa:
            self.conexion_activa.close()
        
        time.sleep(duracion)
        
        print("🔄 Reanudando operación...")
        self.servidor_activo = True
        self.conectar_siguiente_nodo()
        threading.Thread(target=self.iniciar_servidor, daemon=True).start()
    
    def mostrar_estado(self):
        """Mostrar estado del nodo"""
        print(f"\n📊 ESTADO ANILLO {self.ip}")
        print(f"🎟  Token: {'✅ SÍ' if self.token else '❌ NO'}")
        print(f"🔗 Siguiente nodo: {self.ip_siguiente}")
        print(f"📡 Estado siguiente nodo: {'✅ ACTIVO' if not self.nodo_siguiente_caido else '❌ CAÍDO'}")
        print(f"🤖 Arduino: {'✅ CONECTADO' if self.tiene_arduino else '❌ NO'}")
    
    def iniciar_anillo(self):
        """Iniciar participación en el anillo"""
        print(f"=== NODO ANILLO {self.ip} ===")
        print(f"🔗 Conectando a: {self.ip_siguiente}")
        
        if self.tiene_arduino:
            self.conectar_arduino()
        
        # Iniciar servidor
        threading.Thread(target=self.iniciar_servidor, daemon=True).start()
        time.sleep(2)
        
        # Conectar al siguiente nodo
        self.conectar_siguiente_nodo()
        
        # Si es el primer nodo, iniciar con el token
        if self.ip == '192.168.40.101':
            print("🚀 Nodo inicial - poseyendo token inicial")
            time.sleep(5)
            self.token = True
            self.enviar_token("Token inicial del anillo")
        
        return True

# =============================================================================
# CLASES ESPECÍFICAS PARA CADA NODO DEL ANILLO
# =============================================================================

class PC1(NodoAnillo):
    def _init_(self):
        # PC1 -> PC2 -> PC3 -> PC4 -> PC1
        super()._init_('192.168.40.101', '192.168.40.102')
    
    def interfaz_usuario(self):
        while True:
            print("\n💡 Comandos: ESTADO, CAIDA <segundos>, MENSAJE <texto>, SALIR")
            entrada = input("PC1> ").strip()
            
            if not entrada:
                continue
                
            partes = entrada.split()
            comando = partes[0].upper()
            
            if comando == "SALIR":
                break
            elif comando == "ESTADO":
                self.mostrar_estado()
            elif comando == "CAIDA" and len(partes) >= 2:
                try:
                    segundos = int(partes[1])
                    threading.Thread(target=self.simular_caida, args=(segundos,), daemon=True).start()
                except:
                    print(" Tiempo inválido")
            elif comando == "MENSAJE" and len(partes) >= 2:
                if self.token:
                    mensaje = " ".join(partes[1:])
                    self.enviar_token(f"Mensaje de PC1: {mensaje}")
                else:
                    print(" No tengo el token para enviar mensaje")
            else:
                print(" Comando no válido")

class PC2(NodoAnillo):
    def _init_(self):
        super()._init_('192.168.40.102', '192.168.40.103')
    
    def interfaz_usuario(self):
        while True:
            print("\n💡 Comandos: ESTADO, CAIDA <segundos>, MENSAJE <texto>, SALIR")
            entrada = input("PC2> ").strip()
            
            if not entrada:
                continue
                
            partes = entrada.split()
            comando = partes[0].upper()
            
            if comando == "SALIR":
                break
            elif comando == "ESTADO":
                self.mostrar_estado()
            elif comando == "CAIDA" and len(partes) >= 2:
                try:
                    segundos = int(partes[1])
                    threading.Thread(target=self.simular_caida, args=(segundos,), daemon=True).start()
                except:
                    print(" Tiempo inválido")
            elif comando == "MENSAJE" and len(partes) >= 2:
                if self.token:
                    mensaje = " ".join(partes[1:])
                    self.enviar_token(f"Mensaje de PC2: {mensaje}")
                else:
                    print(" No tengo el token para enviar mensaje")
            else:
                print(" Comando no válido")

class PC3(NodoAnillo):
    def _init_(self):
        super()._init_('192.168.40.103', '192.168.40.104', tiene_arduino=True)
    
    def interfaz_usuario(self):
        while True:
            print("\n💡 Comandos: ESTADO, CAIDA <segundos>, ARDUINO <comando>, SALIR")
            entrada = input("PC3> ").strip()
            
            if not entrada:
                continue
                
            partes = entrada.split()
            comando = partes[0].upper()
            
            if comando == "SALIR":
                break
            elif comando == "ESTADO":
                self.mostrar_estado()
            elif comando == "CAIDA" and len(partes) >= 2:
                try:
                    segundos = int(partes[1])
                    threading.Thread(target=self.simular_caida, args=(segundos,), daemon=True).start()
                except:
                    print(" Tiempo inválido")
            elif comando == "ARDUINO" and len(partes) >= 2:
                if self.token:
                    accion = " ".join(partes[1:])
                    self.enviar_token(f"ARDUINO:{accion}")
                else:
                    print(" No tengo el token para controlar Arduino")
            else:
                print(" Comando no válido")

class PC4(NodoAnillo):
    def _init_(self):
        super()._init_('192.168.40.104', '192.168.40.101')
    
    def interfaz_usuario(self):
        while True:
            print("\n💡 Comandos: ESTADO, CAIDA <segundos>, MENSAJE <texto>, SALIR")
            entrada = input("PC4> ").strip()
            
            if not entrada:
                continue
                
            partes = entrada.split()
            comando = partes[0].upper()
            
            if comando == "SALIR":
                break
            elif comando == "ESTADO":
                self.mostrar_estado()
            elif comando == "CAIDA" and len(partes) >= 2:
                try:
                    segundos = int(partes[1])
                    threading.Thread(target=self.simular_caida, args=(segundos,), daemon=True).start()
                except:
                    print(" Tiempo inválido")
            elif comando == "MENSAJE" and len(partes) >= 2:
                if self.token:
                    mensaje = " ".join(partes[1:])
                    self.enviar_token(f"Mensaje de PC4: {mensaje}")
                else:
                    print(" No tengo el token para enviar mensaje")
            else:
                print(" Comando no válido")

# =============================================================================
# PROGRAMA PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("           TOPOLOGÍA ANILLO -  TOKEN")
    print("=" * 60)
    print(" Estructura: PC1 → PC2 → PC3 → PC4 → PC1")
    print("  El nodo con token puede comunicarse con Arduino")
    print(" Arduino conectado en PC3")
    print(" Comando CAIDA para simular fallos")
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
    
    if nodo.iniciar_anillo():
        nodo.interfaz_usuario()