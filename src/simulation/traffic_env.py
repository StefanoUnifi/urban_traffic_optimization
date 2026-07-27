import os
import sys
import traci
from typing import List, Dict, Union
from traci import gui

#controllo per far trovare le librerie di SUMO da python
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

class TrafficSimulationEnv:
    def __init__(self, config_file: str, int_ids: Union[str, List[str]], lanes_in: Union[List[str], Dict[str, List[str]]], yellow_duration: float = 5.0):
        '''
        :param config_file: percorso file configuration.sumocfg
        :param int_ids: lista degli ID dei semafori da controllare
        :param lanes_in: lista degli id delle corsie in entrata o dizionario
        :param yellow_duration: durata del segnale giallo in secondi
        '''
        self.config_file = config_file

        if isinstance(int_ids, str):
            self.int_ids = [int_ids]
        else:
            self.int_ids = int_ids

        if isinstance(lanes_in, list):
            self.lanes_in = {self.int_ids[0]: lanes_in}
        else:
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

    #ricava il numero di veicoli fermi per ciascuna corsia di ogni incrocio
    def get_current_queues_all(self) -> Dict[str, List[float]]:
        queues = {}
        for int_id in self.int_ids:
            lanes = self.lanes_in.get(int_id, [])
            int_queues = []
            for lane in lanes:
                queue_length = float(traci.lane.getLastStepHaltingNumber(lane))
                int_queues.append(queue_length)
            queues[int_id] = int_queues
        return queues

    def get_current_queues(self) -> List[float]:
        queues = self.get_current_queues_all()
        return queues[self.int_ids[0]]


    def execute_traffic_cycle_all(self, green_times: Dict[str, List[float]]):
        max_green_ns = 0.0

        # fase 1 = verde nord-sud per tutti gli incroci
        for int_id in self.int_ids:
            v_ns = green_times[int_id][0]
            traci.trafficlight.setPhase(int_id, 0)
            traci.trafficlight.setPhaseDuration(int_id, v_ns)
            if v_ns > max_green_ns:
                max_green_ns = v_ns

        for _ in range(int(max_green_ns)):
            traci.simulationStep()

        # transizione 1 = giallo nord-sud per tutti gli incroci
        for int_id in self.int_ids:
            traci.trafficlight.setPhase(int_id, 1)
            traci.trafficlight.setPhaseDuration(int_id, self.yellow_duration)

        for _ in range(int(self.yellow_duration)):
            traci.simulationStep()

        # fase 2 = verde est-ovest per tutti gli incroci
        max_green_eo = 0.0
        for int_id in self.int_ids:
            v_eo = green_times[int_id][1]
            traci.trafficlight.setPhase(int_id, 2)
            traci.trafficlight.setPhaseDuration(int_id, v_eo)
            if v_eo > max_green_eo:
                max_green_eo = v_eo

        for _ in range(int(max_green_eo)):
            traci.simulationStep()

        # transizione 1 = giallo est-ovest per tutti gli incroci
        for int_id in self.int_ids:
            traci.trafficlight.setPhase(int_id, 3)  # Fase 3: Giallo E-O
            traci.trafficlight.setPhaseDuration(int_id, self.yellow_duration)

        for _ in range(int(self.yellow_duration)):
            traci.simulationStep()

    def execute_traffic_cycle(self, green_times: List[float]):
        self.execute_traffic_cycle_all({self.int_ids[0]: green_times})