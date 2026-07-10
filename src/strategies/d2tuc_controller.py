#classe del controller D2TUC - Decentralized Decoupled Traffic-Responsive Urban Controller
import numpy as np
from typing import List, Dict
from .base_controller import BaseController

class D2TUCController(BaseController):
    def __init__(self,
                 intersection_ids: List[str],
                 local_K_matr: Dict[str, List[List[float]]],
                 nominal_greens: Dict[str, List[float]],
                 min_greens: Dict[str, List[float]],
                 max_greens: Dict[str, List[float]]):
        super().__init__(intersection_ids)
        self.local_K = {int_id: np.array(K) for int_id, K in local_K_matr.items()}  # conversione in versione numpy
        self.nominal_greens = nominal_greens
        self.min_greens = min_greens
        self.max_greens = max_greens


    def compute_green_times(self, traffic_state: Dict[str, List[float]]) -> Dict[str, List[float]]:
        '''
        Il calcolo dei verdi avviene applicata in maniera decentralizzata e indipendente da incrocio a incrocio
        '''
        optimal_greens = {}

        for int_id in self.intersection_ids:
            #recupero stato del singolo incrocio
            x_local = np.array(traffic_state[int_id])

            #definisco il vettore di input per il calcolo del delta_u locale, includendo lo stato dei vicini [delta_u_i = k_i * x_i]
            delta_u_local = np.dot(self.local_K[int_id], x_local)

            #applico la legge di controllo per il singolo incrocio
            u_calculated = np.array(self.nominal_greens[int_id]) + delta_u_local

            u_min = np.array(self.min_greens[int_id])
            u_max = np.array(self.max_greens[int_id])
            u_clipped = np.clip(u_calculated, u_min, u_max)
            optimal_greens[int_id] = u_clipped.tolist()

        return optimal_greens