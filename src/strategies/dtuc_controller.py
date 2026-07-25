#classe del controller DTUC - Decentralized Traffic-Responsive Urban Controller
import numpy as np
from typing import List, Dict, Union
from .base_controller import BaseController

class DTUCController(BaseController):
    def __init__(self,
                 intersection_ids: List[str],
                 local_K_matr: Dict[str, Union[List[List[float]], np.ndarray]],
                 nominal_greens: Dict[str, List[float]],
                 min_greens: Dict[str, List[float]],
                 max_greens: Dict[str, List[float]],
                 network_topology: Dict[str, List[str]] = None):
        '''
        :param local_K_matr: dizionario che mappa ogni intersection_id alla sua matrice dei guadagni K_i locale
        :param network_topology: dizionario che definisce i vicini di ogni incrocio con intersection_id come chiave e una lista di intersection_id dei vicini come valore
        '''
        super().__init__(intersection_ids)
        self.local_K = {int_id: np.array(K) for int_id, K in local_K_matr.items()}  # conversione in versione numpy
        self.nominal_greens = {k: np.array(v) for k, v in nominal_greens.items()}
        self.min_greens = {k: np.array(v) for k, v in min_greens.items()}
        self.max_greens = {k: np.array(v) for k, v in max_greens.items()}
        self.network_topology = network_topology if network_topology is not None else {int_id: [] for int_id in intersection_ids}


    def compute_green_times(self, traffic_state: Dict[str, Union[List[float], np.ndarray]]) -> Dict[str, List[float]]:
        '''
        Il calcolo dei verdi avviene applicata in maniera decentralizzata: u_i(k) = u_nom_i + K_i * x_input_i(k)
        :param traffic_state: dizionario che mappa ogni intersection_id al suo vettore x_i(k), col numero di veicoli in tutte le code locali
        '''
        optimal_greens = {}

        for int_id in self.intersection_ids:
            #recupero stato del singolo incrocio
            x_local = np.asarray(traffic_state[int_id])

            neighbors = self.network_topology.get(int_id, [])
            #recupero info da vicini (se ci sono)
            if neighbors:
                neighbor_states = [np.asarray(traffic_state[n_id]) for n_id in neighbors]
                x_input = np.concatenate([x_local] + neighbor_states)
            else:
                x_input = x_local

            K_i = self.local_K[int_id]

            #calcolo del delta_u locale [delta_u_i = K_i * x_i]
            delta_u_local = np.dot(K_i, x_input)

            #applico la legge di controllo per il singolo incrocio: u_i = u_N_i + delta_u_i
            u_calculated = self.nominal_greens[int_id] + delta_u_local

            #stesse operazioni di clipping dei valori calcolati come nel TUCController
            u_min = np.array(self.min_greens[int_id])
            u_max = np.array(self.max_greens[int_id])
            u_clipped = np.clip(u_calculated, u_min, u_max)
            optimal_greens[int_id] = u_clipped.tolist()

        return optimal_greens