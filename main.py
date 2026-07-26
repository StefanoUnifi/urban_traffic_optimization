import csv
import os
import numpy as np

from src.strategies.tuc_controller import TUCController
from src.strategies.dtuc_controller import DTUCController
from src.strategies.d2tuc_controller import D2TUCController

from src.simulation.traffic_env import TrafficSimulationEnv
from src.utils.k_generator import calculate_k

def main():
    tls_id = "J4"  #id incrocio semaforo
    corsie_ingresso = ["Nord_in_0", "Sud_in_0", "Est_in_0", "Ovest_in_0"] #lista corsie in ingresso al semaforo

    #Configurazione parametri temporali
    nominali = {tls_id: [25.0, 25.0]}
    minimi = {tls_id: [10.0, 10.0]}
    massimi = {tls_id: [45.0, 45.0]}

    # Flussi di saturazione per le corsie in ingresso (veicoli/secondo)
    sat_flows = [0.8, 0.8, 0.8, 0.8]

    phase_map = [
        [1, 1, 0, 0],  #fase nord-sud
        [0, 0, 1, 1],  #fase est-ovest
    ]

    # Calcolo di K con funzione apposta
    q_weight = 1.0 #più aumenti, più dai importanza al recupero code
    r_weight = 0.1 #più aumenti, meno cambi improvvisi di verde

    K_matrix = calculate_k(sat_flows, phase_map, q_weight, r_weight)  #per TUC

    local_K_matricies = {tls_id: K_matrix} #per DTUC/D2TUC

    print("--- Matrice dei guadagni K calcolata via LQR ---")
    print(np.round(K_matrix, 3))
    print("-----------------------------------")

    # Inizializzazione ambiente di simulazione
    env = TrafficSimulationEnv(
        config_file="sumo_config/configuration.sumocfg",
        tls_id=tls_id,
        lanes_in=corsie_ingresso
    )

    # A seconda di quale controller usare, commenta/ decommenta la sezione corrispondente

    '''
    # Configurazione controller TUC
    controller = TUCController(
        intersection_ids=[tls_id],
        K_matr=K_matrix,
        nominal_greens=nominali,
        min_greens=minimi,
        max_greens=massimi
    )
    '''

    # Configurazione controller DTUC
    controller = DTUCController(
        intersection_ids=[tls_id],
        local_K_matr=local_K_matricies,
        nominal_greens=nominali,
        min_greens=minimi,
        max_greens=massimi
    )

    '''
    # Configurazione controller D2TUC
    controller = D2TUCController(
        intersection_ids=[tls_id],
        local_K_matr=local_K_matricies,
        nominal_greens=nominali,
        min_greens=minimi,
        max_greens=massimi
    )
    '''
    name_strat = f"{type(controller).__name__}"
    file_log_csv = f"risultati_{name_strat}.csv"

    # Inzio loop di Simulazione
    print("Apertura connessione TraCI con SUMO...")
    env.start_simulation()

    SIM_CYCLES = 50  # Eseguiamo la simulazione per 50 cicli semaforici completo
    log_data = []

    try:
        for ciclo in range(SIM_CYCLES):
            # Estrazione code da SUMO
            code_attuali = env.get_current_queues()
            coda_media = sum(code_attuali) / len(code_attuali)
            print(f"\n[Ciclo {ciclo}] Code rilevate [Nord, Sud, Est, Ovest]: {code_attuali}")

            if isinstance(controller, TUCController):
                input_traffico = code_attuali # caso TUC
            else:
                input_traffico = {tls_id: code_attuali} #caso DTUC/D2TUC

            # Calcolo verdi per controller
            verdi_ottimizzati = controller.compute_green_times(input_traffico)
            verdi_incrocio = verdi_ottimizzati[tls_id]
            print(f"[Ciclo {ciclo}] {type(controller).__name__} -> Verde N-S: {verdi_incrocio[0]:.1f}s | Verde E-O: {verdi_incrocio[1]:.1f}s")

            # Salvataggio dati per log
            log_data.append({
                "Ciclo": ciclo,
                "Coda_Nord": code_attuali[0],
                "Coda_Sud": code_attuali[1],
                "Coda_Est": code_attuali[2],
                "Coda_Ovest": code_attuali[3],
                "Coda_media": coda_media,
                "Verde_NS": verdi_incrocio[0],
                "Verde_EO": verdi_incrocio[1]
            })

            # Esecuzione in SUMO
            env.execute_traffic_cycle(verdi_incrocio[::-1])

    except Exception as e:
        print(f"Errore intercettato: {e}")
    finally:
        # Salvataggio dati di log
        if log_data:
            campi = ["Ciclo", "Coda_Nord", "Coda_Sud", "Coda_Est", "Coda_Ovest", "Coda_media", "Verde_NS", "Verde_EO"]
            try:
                with open(file_log_csv, 'w', newline='', encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=campi)
                    writer.writeheader()
                    writer.writerows(log_data)
                print(f"Dati di log salvati in '{file_log_csv}'")
            except Exception as e:
                print(f"Errore durante il salvataggio del CSV: {e}")

        env.stop_simulation()
        print("Simulazione terminata.")

    #TODO: fai parte per salvataggio dati su grafici + chiusura programma automatica

if __name__ == "__main__":
    main()