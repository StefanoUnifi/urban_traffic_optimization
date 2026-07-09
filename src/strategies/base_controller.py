from abc import ABC, abstractmethod
from typing import List, Dict, Any

#classe astratta per i controllori semaforici
class BaseController(ABC):
    def __init__(self, intersection_ids: List[str]):
        self.intersection_ids = intersection_ids
        #intersection_ids è una lista delle intersezioni gestite dal sistema

    @abstractmethod
    def compute_green_times(self, traffic_state: Any) -> Dict[str, List[float]]:
        """
        Metodo astratto che calcola i tempi dei verdi per il ciclo successivo, per ciascun controllore.
        :param traffic_state: rappresenta lo stato corrente delle code (gestito come array o dizionario a seconda della decentrallizzazione).
        :return: un dizionario contente ogni intersection_id con i relativi tempi di verde.
        """
        pass