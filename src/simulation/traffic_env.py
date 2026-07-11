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
    def __init__(self, config_file: str, tls_id: str, lanes_in: List[str]):
        '''
        :param config_file: percorso file configuration.sumocfg
        :param tls_id: ID semaforo da controllare su NETEDIT
        :param lanes_in: lista degli id delle corsie in entrata
        '''
        self.config_file = config_file
        self.tls_id = tls_id
        self.lanes_in = lanes_in

    #avvia sim
    def start_simulation(self):
        sumo_binary = "sumo-gui" if gui else "sumo"
        sumo_cmd = [sumo_binary, "-c", self.config_file]
        traci.start(sumo_cmd)

    #ferma sim
    def stop_simulation(self):
        traci.close()

    #avanza sim di un secondo
    def step(self):
        traci.simulationStep()

    #ricava il numero di veicoli fermi per ciascuna corsia (che sarà il vettore di stato x(k))
    def get_current_queues(self) -> List[float]:
        queues = []
        for lane in self.lanes_in:
            halted_vehicles = traci.lane.getLastStepHaltingNumber(lane)
            queues.append(float(halted_vehicles))
        return queues
