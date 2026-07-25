#classe del controller D2TUC - Decentralized Decoupled Traffic-Responsive Urban Controller
import numpy as np
from typing import List, Dict, Union
from .base_controller import BaseController

class D2TUCController(BaseController):
    def __init__(self,
                 intersection_ids: List[str],
                 local_K_matr: Dict[str, Union[List[List[float]], np.ndarray]],
                 nominal_greens: Dict[str, List[float]],
                 min_greens: Dict[str, List[float]],
                 max_greens: Dict[str, List[float]]):
        super().__init__(intersection_ids)
        self.local_K = {int_id: np.array(K) for int_id, K in local_K_matr.items()}  # conversione in versione numpy
        self.nominal_greens = {k: np.array(v) for k, v in nominal_greens.items()}
        self.min_greens = {k: np.array(v) for k, v in min_greens.items()}
        self.max_greens = {k: np.array(v) for k, v in max_greens.items()}


    def compute_green_times(self, traffic_state: Dict[str, Union[List[float], np.ndarray]]) -> Dict[str, List[float]]:
        '''
        Il calcolo dei verdi avviene applicata in maniera decentralizzata e indipendente da incrocio a incrocio: u_i(k) = u_nom_i + K_i * x_i(k)
        '''
        optimal_greens = {}

        for int_id in self.intersection_ids:
            #recupero stato del singolo incrocio
            x_local = np.asarray(traffic_state[int_id])
            K_i = np.array(self.local_K[int_id])

            #calcolo del delta_u locale, includendo lo stato dei vicini [delta_u_i = K_i * x_i]
            delta_u_local = np.dot(K_i, x_local)

            #applico la legge di controllo per il singolo incrocio
            u_calculated = self.nominal_greens[int_id] + delta_u_local

            u_min = np.array(self.min_greens[int_id])
            u_max = np.array(self.max_greens[int_id])
            u_clipped = np.clip(u_calculated, u_min, u_max)
            optimal_greens[int_id] = u_clipped.tolist()

        return optimal_greens