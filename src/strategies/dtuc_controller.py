#classe del controller DTUC - Decentralized Traffic-Responsive Urban Controller
import numpy as np
from typing import List, Dict
from .base_controller import BaseController

class DTUCController(BaseController):
    def __init__(self,
                 intersection_ids: List[str],
                 local_K_matr: Dict[str, List[List[float]]],
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
        self.nominal_greens = nominal_greens
        self.min_greens = min_greens
        self.max_greens = max_greens
        self.network_topology = network_topology if network_topology is not None else {int_id: [] for int_id in intersection_ids}


    def compute_green_times(self, traffic_state: Dict[str, List[float]]) -> Dict[str, List[float]]:
        '''
        Il calcolo dei verdi avviene applicata in maniera decentralizzata
        :param traffic_state: dizionario che mappa ogni intersection_id al suo vettore x_i(k), col numero di veicoli in tutte le code locali
        '''
        optimal_greens = {}

        for int_id in self.intersection_ids:
            #recupero stato del singolo incrocio
            x_local = np.array(traffic_state[int_id])

            #recupero info da vicini (se ci sono)
            x_input = x_local

            #definisco il vettore di input per il calcolo del delta_u locale, includendo lo stato dei vicini [delta_u_i = k_i * x_i]
            delta_u_local = np.dot(self.local_K[int_id], x_input)

            #applico la legge di controllo per il singolo incrocio: u_i = u_N_i + delta_u_i
            u_calculated = np.array(self.nominal_greens[int_id]) + delta_u_local

            #stesse operazioni di clipping dei valori calcolati come nel TUCController
            u_min = np.array(self.min_greens[int_id])
            u_max = np.array(self.max_greens[int_id])
            u_clipped = np.clip(u_calculated, u_min, u_max)
            optimal_greens[int_id] = u_clipped.tolist()

        return optimal_greens