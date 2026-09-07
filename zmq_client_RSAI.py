
"""
Client MOTORRSAI avec ZMQ DEALER
Compatible avec le serveur ROUTER-DEALER
Inclut double système de heartbeat pour détecter les déconnexions client et serveur 

"""

import zmq
import time
import threading
from PyQt6.QtCore import pyqtSlot, QMutex
from PyQt6 import QtCore
import pathlib
import os
import uuid


class MOTORRSAI():
    """
    MOTORRSAI(IpAddress, NoMotor, server_address) 
    Classe définie par l'adresse IP du rack et le numéro d'axe
    Utilise ZMQ DEALER pour communiquer avec un serveur ROUTER
    """

    def __init__(self, IpAddress, NoMotor, parent=None):
 
        p = pathlib.Path(__file__).parent
        sepa = os.sep
        fileconf = str(p) + sepa + "confServer.ini"
        confServer = QtCore.QSettings(fileconf, QtCore.QSettings.Format.IniFormat)
        self.server_host = str(confServer.value('MAIN'+'/server_host'))
        self.serverPort = str(confServer.value('MAIN'+'/serverPort'))
        self.server_address = f"tcp://{self.server_host}:{self.serverPort}"
        #  print(f"Adresse serveur ZMQ: {self.server_address}")
        self.IpAddress = IpAddress
        self.NoMotor = NoMotor

        self.mut = QMutex()

        # Initialiser le contexte et socket ZMQ
        self.context = zmq.Context()
        self.socket = None
        self.isconnected = False
        
        #  Heartbeat pour maintenir la connexion active
        self.heartbeat_interval = 15  # Envoyer un heartbeat toutes les 15 secondes
        self.last_heartbeat = time.time()
        self.heartbeat_enabled = True

        # Gestion de la reconnexion automatique
        self.reconnect_interval = 5  # Tenter de reconnecter toutes les 5 secondes
        self.max_reconnect_attempts = 0  # 0 = infini
        self.reconnect_attempts = 0
        self.server_available = False
        
        # Démarrer le thread de heartbeat et reconnexion
        self.monitor_thread = threading.Thread(target=self._monitor_connection, daemon=True)
        self.monitor_thread.start()
        
        self._connect()
        time.sleep(0.02)
        self.update()

    def _connect(self):
        """Établit la connexion ZMQ avec pattern DEALER"""
        try:
            if self.socket:
                self.socket.close()

            # Utiliser DEALER pour se connecter au ROUTER du serveur
            self.socket = self.context.socket(zmq.DEALER)

            # Configuration des timeouts et options (optimisé pour 60+ clients)
            self.socket.setsockopt(zmq.RCVTIMEO, 5000)  # Timeout réception: 5s (augmenté)
            self.socket.setsockopt(zmq.SNDTIMEO, 5000)  # Timeout envoi: 5s (augmenté)
            self.socket.setsockopt(zmq.LINGER, 500)    # Attendre 1s à la fermeture
            self.socket.setsockopt(zmq.SNDHWM, 100)     # Queue d'envoi
            self.socket.setsockopt(zmq.RCVHWM, 100)     # Queue de réception

            # définir une identité unique pour le client
            identity = f"{str(uuid.uuid4())}_{self.IpAddress}_{self.NoMotor}".encode('utf-8')
            self.socket.setsockopt(zmq.IDENTITY, identity)

            # Connexion au serveur
            self.socket.connect(self.server_address)
            self.isconnected = True
            self.server_available = True
            self.reconnect_attempts = 0
            print(f"✅ Client DEALER connecté à {self.server_address} ({self.IpAddress}:{self.NoMotor})")

        except Exception as e:
            self.isconnected = False
            self.server_available = False
            print(f'❌ Erreur de connexion ({self.IpAddress}:{self.NoMotor}): {e}')

    def update(self):
        """Mise à jour depuis la base de données"""
        time.sleep(0.1)                                      
        self.name = self.getName()
        self.step = self.getStepValue()
        if self.step == 0:
            self.step = 1
        self.butPlus = self.getButLogPlusValue()
        self.butMoins = self.getButLogMoinsValue()
        time.sleep(0.01)  
        self.refName = []
        self.refValue = []
        try:
            for i in range(0, 6):
                r = self.getRefName(i)
                self.refName.append(r)
                time.sleep(0.02)
                rr = self.getRefValue(i)
                self.refValue.append(rr)
        except Exception as e:
            print('error update motor', e)

    def sendMessage(self, message=''):
        """
        Envoie un message via ZMQ DEALER avec gestion automatique de reconnexion
        Le DEALER envoie des messages vides comme enveloppe pour le ROUTER
        """
        retour = '1'

        # Vérifier si le serveur est disponible
        if not self.server_available:
            print(f'⚠️ Serveur non disponible, message non envoyé ({self.IpAddress}:{self.NoMotor})')
            return '1'

        self.mut.lock()
        try:
            if self.isconnected:
                try:
                    # ✅ DEALER envoie : frame vide + message
                    self.socket.send(b'', zmq.SNDMORE)
                    self.socket.send_string(message)
                    
                    # print(f"📤 Client envoi: {message}")
                    
                    # ✅ DEALER reçoit : frame vide + réponse
                    empty = self.socket.recv()
                    retour_brut = self.socket.recv_string()
                    
                    # print(f"📥 Client reçu: {retour_brut}")
                    
                    # Nettoyer la réponse
                    retour = retour_brut.strip()
                    
                    self.isconnected = True
                    self.server_available = True

                except zmq.Again:
                    print(f'⏱️ Timeout de communication ({self.IpAddress}:{self.NoMotor})')
                    self.isconnected = False
                    self.server_available = False
                    retour = '1'
   
                except zmq.ZMQError as e:
                    print(f'❌ Erreur ZMQ ({self.IpAddress}:{self.NoMotor}): {e}')
                    self.isconnected = False
                    self.server_available = False
                    retour = '1'

                except Exception as e:
                    print(f'❌ Erreur de communication ({self.IpAddress}:{self.NoMotor}): {e}')
                    self.isconnected = False
                    self.server_available = False
                    retour = '1'
            else:
                print(f'⚠️ Client non connecté ({self.IpAddress}:{self.NoMotor})')
                retour = '1'

        finally:
            self.mut.unlock()

        return retour

    def _reconnect(self):

        """Tente de reconnecter le socket ZMQ"""
        self.reconnect_attempts += 1
        max_msg = f"/{self.max_reconnect_attempts}" if self.max_reconnect_attempts > 0 else ""

        print(f'🔄 Tentative de reconnexion {self.reconnect_attempts}{max_msg}... ({self.IpAddress}:{self.NoMotor})')

        try:
            if self.socket:
                self.socket.close()
            self._connect()

            if self.isconnected:
                print(f'✅ Reconnexion réussie ! ({self.IpAddress}:{self.NoMotor})')
                return True
            else:
                print(f'❌ Reconnexion échouée ({self.IpAddress}:{self.NoMotor})')
                return False

        except Exception as e:
            print(f'❌ Échec de reconnexion ({self.IpAddress}:{self.NoMotor}): {e}')
            self.isconnected = False
            self.server_available = False
            return False

    def _monitor_connection(self):
        """
        Thread qui surveille la connexion et gère:
        1. L'envoi des hearself.muttbeats
        2. La reconnexion automatique si le serveur tombe
        """
        print(f"🔍 Thread de monitoring démarré ({self.IpAddress}:{self.NoMotor})")
        time.sleep(1)  # Attendre un peu avant de démarrer
        while self.heartbeat_enabled:
            try:
                # Attendre l'intervalle de heartbeat
                time.sleep(self.heartbeat_interval)

                # Si pas connecté, tenter de reconnecter
                if not self.isconnected or not self.server_available:
                    if self.max_reconnect_attempts == 0:
                    # Mode infini, mais avec une limite raisonnable pour éviter le spam
                        if self.reconnect_attempts < 3:  # Max 3 tentatives avant de ralentir
                            self._reconnect()
                        else:
                            print(f"⏸️ Trop de tentatives, pause de 30s ({self.IpAddress}:{self.NoMotor})")
                            time.sleep(30)  # Pause plus longue
                            self.reconnect_attempts = 0  # Reset
                    elif self.reconnect_attempts < self.max_reconnect_attempts:
                        self._reconnect()
                    else:
                        print(f"⛔ Nombre maximum de tentatives atteint ({self.IpAddress}:{self.NoMotor})")
                        break
                    
                    time.sleep(self.reconnect_interval)
                    continue

                # Si connecté, envoyer un heartbeat
                if self.isconnected:
                    try:
                        self.mut.lock()
                        # ✅ Envoyer ping
                        self.socket.send(b'', zmq.SNDMORE | zmq.DONTWAIT)
                        self.socket.send_string('ping', zmq.DONTWAIT)
                        
                        # ✅ Attendre pong
                        if self.socket.poll(1000):
                            empty = self.socket.recv()
                            response = self.socket.recv_string().strip()
                            
                            if response == 'pong':
                                self.last_heartbeat = time.time()
                                self.server_available = True
                                # print(f"💓 Heartbeat OK ({self.IpAddress}:{self.NoMotor})")
                            else:
                                print(f'⚠️ Heartbeat invalide: {response}')
                        else:
                            print(f'⚠️ Pas de réponse ({self.IpAddress}:{self.NoMotor})')
                            self.isconnected = False
                            self.server_available = False

                        self.mut.unlock()

                    except zmq.Again:
                        self.mut.unlock()
                        print(f'⏱️ Timeout heartbeat ({self.IpAddress}:{self.NoMotor})')
                        self.isconnected = False
                        self.server_available = False

                    except Exception as e:
                        self.mut.unlock()
                        print(f'❌ Erreur heartbeat ({self.IpAddress}:{self.NoMotor}): {e}')
                        self.isconnected = False
                        self.server_available = False
      
            except Exception as e:
                print(f'❌ Erreur thread monitoring ({self.IpAddress}:{self.NoMotor}): {e}')

        print(f'🛑 Thread de monitoring arrêté ({self.IpAddress}:{self.NoMotor})')

    @pyqtSlot(object)
    def position(self):
        """Retourne la position du moteur"""
        cmd = 'position'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}" 
        self._position = self.sendMessage(cmdsend)
        try:
            self._position = float(self._position)
        except Exception as e:
            print('position erro', e)
            self._position = 1
        return self._position

    def setPosition(self, pos):
        """Définit la position du moteur"""
        cmd = 'preset'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}, {pos}"
        dat = self.sendMessage(cmdsend)

    def getName(self):
        """Récupère le nom du moteur"""
        cmd = 'name'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}"
        self.name = self.sendMessage(cmdsend)
        return self.name

    def setName(self, nom):
        """Définit le nom du moteur"""
        cmd = 'setName'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}, {nom}"
        self.sendMessage(cmdsend)
        time.sleep(0.05)

    def getRefName(self, nRef):
        """Récupère le nom de la référence n°"""
        cmd = f'ref{nRef}Name'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}"
        dat = self.sendMessage(cmdsend)
        return dat

    def setRefName(self, nRef, name):
        """Définit le nom de la référence n°"""
        cmd = 'setRefName'
        nRef = nRef + 1
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}, {name}, {nRef}"
        dat = self.sendMessage(cmdsend)
        time.sleep(0.05)

    def getRefValue(self, nRef):
        """Récupère la valeur de la position de référence nRef"""
        cmd = f'ref{nRef}Pos'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}"
        try:
            dat = float(self.sendMessage(cmdsend))
        except Exception as e:
            print('error get ref value', e)
            dat = 0
        return dat

    def setRefValue(self, nReff, value):
        """Définit la valeur de la position de référence nRef"""
        cmd = 'setRefPos'
        nReff = nReff + 1
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}, {value}, {nReff}"
        dat = self.sendMessage(cmdsend)

    def getStepValue(self):
        """Valeur de 1 pas dans les unités"""
        cmd = 'step'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}"
        dat = self.sendMessage(cmdsend)
        try:
            dat = float(dat)
        except Exception as e:
            print('step value rror', e)
            dat = 1
        
        return dat
    def setStep(self,step):
        """Valeur de 1 pas dans les unités"""
        cmd = 'setStep'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd},{step}"
        dat = self.sendMessage(cmdsend)
        print('set client step')

    def getButLogPlusValue(self):
        """Récupère la butée positive"""
        cmd = 'buteePos'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}"
        dat = self.sendMessage(cmdsend)
        cmd = 'buteePos'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}"
        dat = self.sendMessage(cmdsend)
        return dat

    def setButLogPlusValue(self, butPlus):
        """Définit la butée positive """
        cmd = 'setButeePos'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}, {butPlus}"
        dat = self.sendMessage(cmdsend)

    def getButLogMoinsValue(self):
        """Récupère la butée négative"""
        cmd = 'buteeNeg'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}"
        dat = self.sendMessage(cmdsend)
        try:
            dat = float(dat)
        except Exception as e:
            print('error get ButLOgMoins', e)
            dat = 1
        return dat

    def setButLogMoinsValue(self, butMoins):
        """Définit la butée négative"""
        cmd = 'setButeeNeg'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd},{butMoins}"
        dat = self.sendMessage(cmdsend)

    def rmove(self, posrelatif, vitesse=1000):
        """
        Déplacement relatif du moteur
        posrelatif = position à déplacer en pas
        """
        cmd = 'rmove'
        pos = int(posrelatif)
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}, {pos}"
        self.sendMessage(cmdsend)

    def move(self, pos, vitesse=1000):
        """
        Déplacement absolu du moteur
        pos = position à atteindre en pas
        """
        cmd = 'move'
        pos = int(pos)
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}, {pos}"
        self.sendMessage(cmdsend)

    def setzero(self):
        """Définit la position actuelle comme zéro"""
        cmd = 'setzero'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}"
        rec = self.sendMessage(cmdsend)
        if rec != 'ok':
            print('error cmd')

    def stopMotor(self):
        """Arrête le moteur"""
        cmd = 'stop'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}"
        rec = self.sendMessage(cmdsend)
        if rec != 'ok':
            print('error cmd')

    def etatMotor(self):
        """Lit l'état du moteur"""
        cmd = 'etat'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}"
        dat = self.sendMessage(cmdsend)
   
        if not self.isconnected:
            print('Serveur non connecté')
            dat = 'notconnected'
        return dat

    def getEquipementName(self):
        """Retourne le nom de l'équipement auquel le moteur est connecté"""
        cmd = 'nomRack'
        cmdsend = f"{self.IpAddress}, {self.NoMotor}, {cmd}"
        dat = self.sendMessage(cmdsend)
        return dat

    def getConnectionStatus(self):
        """Retourne le statut de connexion détaillé"""
        return {
            'connected': self.isconnected,
            'server_available': self.server_available,
            'last_heartbeat': time.time() - self.last_heartbeat,
            'reconnect_attempts': self.reconnect_attempts
        }

    def waitForConnection(self, timeout=30):
        """
        Attend que la connexion soit établie
        Utile au démarrage si le serveur n'est pas encore lancé

        Returns:
            bool: True si connecté, False si timeout
        """
        start_time = time.time()
        print(f"⏳ Attente de connexion au serveur... ({self.IpAddress}:{self.NoMotor})")

        while time.time() - start_time < timeout:
            if self.isconnected and self.server_available:
                print(f"✅ Connexion établie ! ({self.IpAddress}:{self.NoMotor})")
                return True
            time.sleep(1)

        print(f"⏱️ Timeout: impossible de se connecter après {timeout}s ({self.IpAddress}:{self.NoMotor})")
        return False

    def closeConnexion(self):
        """Ferme proprement la connexion ZMQ"""
        self.heartbeat_enabled = False  # Arrêter le thread heartbeat
        time.sleep(0.5)  # Attendre l'arrêt du thread

        if self.socket:
            self.socket.close()
        self.context.term()
        self.isconnected = False
        print("Connexion fermée")


# Exemple d'utilisation
if __name__ == "__main__":
    # Créer plusieurs instances pour tester le multi-client
    motor1 = MOTORRSAI("10.0.1.30", "1")
    motor1.update()
    motor1.setButLogPlusValue(25555)
    # Tester quelques commandes
    #print(f"Moteur 1 - Nom: {motor1.getName()}")
    print(f"Moteur 1 - Position: {motor1.position()}")

    # Fermer les connexions
    motor1.closeConnexion()
    