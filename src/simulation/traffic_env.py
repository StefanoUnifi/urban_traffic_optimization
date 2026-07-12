import os
import sys
import traci
from typing import List
from traci import gui

#controllo per far trovare le librerie di SUMO da python
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

class TrafficSimulationEnv:
    def __init__(self, config_file: str, tls_id: str, lanes_in: List[str], yellow_duration: float = 3.0):
        '''
        :param config_file: percorso file configuration.sumocfg
        :param tls_id: ID semaforo da controllare su NETEDIT
        :param lanes_in: lista degli id delle corsie in entrata
        :param yellow_duration: durata del segnale giallo in secondi
        '''
        self.config_file = config_file
        self.tls_id = tls_id
        self.lanes_in = lanes_in
        self.yellow_duration = yellow_duration

    #avvia sim
    def start_simulation(self):
        sumo_binary = "sumo-gui" if gui else "sumo"
        sumo_cmd = [sumo_binary, "-c", self.config_file]
        traci.start(sumo_cmd)

    #ferma sim
    def stop_simulation(self):
        traci.close()

    #ricava il numero di veicoli fermi per ciascuna corsia (che sarà il vettore di stato x(k))
    def get_current_queues(self) -> List[float]:
        queues = []
        for lane in self.lanes_in:
            halted_vehicles = traci.lane.getLastStepHaltingNumber(lane)
            queues.append(float(halted_vehicles))
        return queues

    def execute_traffic_cycle(self, green_times: List[float]):
        '''
        Esegue un ciclo di semaforo con i tempi di verde specificati dal modello usato.
        :param green_times: lista dei tempi di verde per ciascuna fase del semaforo
        '''
        # Fase 1: verde Nord-Sud
        traci.trafficlight.setPhase(self.tls_id, 0)
        traci.trafficlight.setPhaseDuration(self.tls_id, green_times[0])
        for _ in range(int(green_times[0])):
            traci.simulationStep()

        # Transizione 1: giallo Nord-Sud
        traci.trafficlight.setPhase(self.tls_id, 1)
        traci.trafficlight.setPhaseDuration(self.tls_id, self.yellow_duration)
        for _ in range(int(self.yellow_duration)):
            traci.simulationStep()

        # Fase 2: verde Est-Ovest
        traci.trafficlight.setPhase(self.tls_id, 2)
        traci.trafficlight.setPhaseDuration(self.tls_id, green_times[1])
        for _ in range(int(green_times[1])):
            traci.simulationStep()

        # Transizione 2: giallo Est-Ovest
        traci.trafficlight.setPhase(self.tls_id, 3)
        traci.trafficlight.setPhaseDuration(self.tls_id, self.yellow_duration)
        for _ in range(int(self.yellow_duration)):
            traci.simulationStep()