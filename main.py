import csv
import os
import numpy as np

from src.strategies.tuc_controller import TUCController
from src.strategies.dtuc_controller import DTUCController
from src.strategies.d2tuc_controller import D2TUCController

from src.simulation.traffic_env import TrafficSimulationEnv
from src.utils.k_generator import calculate_k

def main():
    int_ids = ["J0","J2","J4"]  #id incroci semafori
    corsie_ingresso = {
        "J0": ["J0_nord_in_0", "J0_sud_in_0", "J0_est_in_0", "J0_ovest_in_0"],
        "J2": ["J2_nord_in_0", "J2_sud_in_0", "J2_est_in_0", "J2_ovest_in_0"],
        "J4": ["J4_nord_in_0", "J4_sud_in_0", "J4_est_in_0", "J4_ovest_in_0"]
    } #corsie in ingresso ai semafori

    #Configurazione parametri temporali per semafori
    nominali = {i: [25.0, 25.0] for i in int_ids}
    minimi = {i: [10.0, 10.0] for i in int_ids}
    massimi = {i: [45.0, 45.0] for i in int_ids}

    # Flussi di saturazione per le corsie in ingresso (veicoli/secondo)
    sat_flows = [0.8, 0.8, 0.8, 0.8]

    phase_map = [
        [1, 1, 0, 0],  #fase nord-sud
        [0, 0, 1, 1],  #fase est-ovest
    ]

    # Calcolo di K con funzione apposta
    q_weight = 1.0 #più aumenti, più dai importanza al recupero code
    r_weight = 0.5 #più aumenti, meno cambi improvvisi di verde

    global_K_matrix = calculate_k(sat_flows, phase_map, q_weight, r_weight)  #matrice globale per TUC

    local_K_matricies = {i: global_K_matrix for i in int_ids} #dizionario di matrici locali per DTUC/D2TUC

    print("--- Matrice dei guadagni K calcolata via LQR ---")
    print(np.round(global_K_matrix, 3))
    print("-----------------------------------")

    # Inizializzazione ambiente di simulazione
    env = TrafficSimulationEnv(
        config_file="sumo_config/configuration.sumocfg",
        int_ids=int_ids,
        lanes_in=corsie_ingresso
    )

    # A seconda di quale controller usare, commenta/ decommenta la sezione corrispondente

    '''
    # Configurazione controller TUC
    controller = TUCController(
        intersection_ids=int_ids,
        K_matr=global_K_matrix,
        nominal_greens=nominali,
        min_greens=minimi,
        max_greens=massimi
    )
    '''
    '''
    # Configurazione controller DTUC
    controller = DTUCController(
        intersection_ids=int_ids,
        local_K_matr=local_K_matricies,
        nominal_greens=nominali,
        min_greens=minimi,
        max_greens=massimi
    )
'''

    # Configurazione controller D2TUC
    controller = D2TUCController(
        intersection_ids=int_ids,
        local_K_matr=local_K_matricies,
        nominal_greens=nominali,
        min_greens=minimi,
        max_greens=massimi
    )

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
            input_traffico = env.get_current_queues_all()

            # Calcolo verdi per controller
            verdi_ottimizzati = controller.compute_green_times(input_traffico)
            print(f"\n[Ciclo {ciclo}] --- Risultati Controllo {name_strat} ---")

            row_log = {"Ciclo": ciclo}
            for i in int_ids:
                code_ids = input_traffico[i]
                verdi_ids = verdi_ottimizzati[i]
                print(
                    f" > {i} | Code [Nord, Sud, Est, Ovest]: {code_ids} -> Verde N-S: {verdi_ids[0]:.1f}s | Verde E-O: {verdi_ids[1]:.1f}s")

                # Salvataggio dati per il log
                row_log[f"{i}_Coda_NS"] = code_ids[0] + code_ids[1]
                row_log[f"{i}_Coda_EO"] = code_ids[2] + code_ids[3]
                row_log[f"{i}_Verde_NS"] = verdi_ids[0]
                row_log[f"{i}_Verde_EO"] = verdi_ids[1]

            log_data.append(row_log)

            # Esecuzione del ciclo in SUMO
            env.execute_traffic_cycle_all(verdi_ottimizzati)

    except Exception as e:
        print(f"Errore intercettato: {e}")
    finally:
        # Salvataggio dati di log
        if log_data:
            campi = list(log_data[0].keys())
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