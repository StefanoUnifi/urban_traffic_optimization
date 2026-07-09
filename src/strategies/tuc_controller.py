#classe del controller TUC - Traffic-Responsive Urban Controller
import numpy as np
from typing import Dict, List
from .base_controller import BaseController

class TUCController(BaseController):
    def __init__(self,
                 intersection_ids: List[str],
                 K_matr: List[List[float]],
                 nominal_greens: Dict[str, List[float]],
                 min_greens: Dict[str, List[float]],
                 max_greens: Dict[str, List[float]]):
        '''
        :param K_matr: matrice dei guadagni K
        :param nominal_greens: dizionario dei tempi dei verdi predefiniti
        :param min_greens: dizionario dei tempi di verde minimi
        :param max_greens: dizionario dei tempi di verde massimi
        '''
        super().__init__(intersection_ids)
        self.K = np.array(K_matr) #conversione in versione numpy per velocizzare calcoli matriciali
        self.nominal_greens = nominal_greens
        self.min_greens = min_greens
        self.max_greens = max_greens


    def compute_green_times(self, global_traffic_state: List[float]) -> Dict[str, List[float]]:
        '''
        Per il calcolo dei verdi viene applicata la legge di controllo u(k) = u_nom + K * x(k)
        :param global_traffic_state: vettore x(k), col numero di veicoli in tutte le code
        :return: dizionario con tempi di verdi ottimali per ogni incrocio
        '''
        x = np.array(global_traffic_state)

        #vettore che contiene le variazioni dei tempi di verde per tutte le fasi di tutti gli incroci
        #calcolo del delta con prodotto matriciale
        delta_u = np.dot(self.K, x)

        #vettore che contiene i valori dei verdi ottimali per ogni singolo incrocio
        optimal_greens = {}
        i = 0  #indice del vettore delta_u

        # Calcolo dei tempi di verde ottimali per ogni incrocio (anche se è 1 solo)
        for int_id in self.intersection_ids:
            num_phase = len(self.nominal_greens[int_id])

            #ricavo del delta del singolo incrocio
            int_delta = delta_u[i : i + num_phase]
            i += num_phase

            #legge di controllo per u(k) [= u_calculated]
            u_calculated = np.array(self.nominal_greens[int_id]) + int_delta

            #ricavo dei valori minimi/massimi di verde per l'incrocio e 'limito' i valori calcolati
            u_min = np.array(self.min_greens[int_id])
            u_max = np.array(self.max_greens[int_id])
            u_clipped = np.clip(u_calculated, u_min, u_max)

            optimal_greens[int_id] = u_clipped.tolist()

        return optimal_greens