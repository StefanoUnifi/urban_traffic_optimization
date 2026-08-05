import csv
import numpy as np
import pandas as pd
import os

from src.strategies.tuc_controller import TUCController
from src.strategies.dtuc_controller import DTUCController
from src.strategies.d2tuc_controller import D2TUCController

from src.simulation.traffic_env import TrafficSimulationEnv
from src.utils.k_generator import calculate_k
from src.utils.plot_generator import PlotGenerator

def main():
    int_ids = ["J0", "J2", "J4"]  # id incroci semafori
    corsie_ingresso = {
        "J0": ["J0_nord_in_0", "J0_sud_in_0", "J0_est_in_0", "J0_ovest_in_0"],
        "J2": ["J2_nord_in_0", "J2_sud_in_0", "J2_est_in_0", "J2_ovest_in_0"],
        "J4": ["J4_nord_in_0", "J4_sud_in_0", "J4_est_in_0", "J4_ovest_in_0"]
    }  # corsie in ingresso ai semafori

    # Configurazione parametri temporali per semafori
    nominali = {i: [25.0, 25.0] for i in int_ids}
    minimi = {i: [6.0, 6.0] for i in int_ids}
    massimi = {i: [45.0, 45.0] for i in int_ids}

    # Calcolo di K con funzione apposita
    q_weight = 10.0  # più aumenti, più dai importanza al recupero code
    r_weight = 0.1   # più aumenti, meno cambi improvvisi di verde

    SIM_CYCLES = 150  # Eseguiamo la simulazione per 150 cicli semaforici

    strategies = ["TUC", "DTUC", "D2TUC"]

    for strat in strategies:
        run_sim(
            strat_name=strat,
            int_ids=int_ids,
            corsie_in=corsie_ingresso,
            nominali=nominali,
            minimi=minimi,
            massimi=massimi,
            q=q_weight,
            r=r_weight,
            n_cycles=SIM_CYCLES
        )

    # Generazione grafici
    print("\nGenerazione grafici...")
    plotter = PlotGenerator()
    strat_dataframes = {}

    for s in strategies:
        frame_name = f"risultati_{s}.csv"
        if os.path.exists(frame_name):
            strat_dataframes[s] = pd.read_csv(frame_name)

    if strat_dataframes:
        plotter.plot_net_queues(strat_dataframes)
        plotter.plot_green_times(strat_dataframes)
        plotter.plot_mean_max_bar_chart(strat_dataframes)


def run_sim(strat_name, int_ids, corsie_in, nominali, minimi, massimi, q, r, n_cycles):
    print(f"\nInizio Simulazione Strategia: {strat_name}")

    if strat_name == "TUC":
        sat_flows = [0.4] * (4 * len(int_ids))
        phase_map_single = np.array([[1, 1, 0, 0], [0, 0, 1, 1]])
        phase_map_global = np.block([
            [phase_map_single if i == j else np.zeros((2, 4)) for j in range(len(int_ids))]
            for i in range(len(int_ids))
        ])

        global_K_matrix = calculate_k(sat_flows, phase_map_global, q, r)
        controller = TUCController(
            intersection_ids=int_ids,
            K_matr=global_K_matrix,
            nominal_greens=nominali,
            min_greens=minimi,
            max_greens=massimi
        )

    elif strat_name == "DTUC":
        topologia = {
            "J0": ["J2", "J4"],  # incrocio centrale
            "J2": ["J0"],        # incrocio Est
            "J4": ["J0"]         # incrocio Ovest
        }

        local_K_matrices = {}
        for i in int_ids:
            num_neighbors = len(topologia[i])
            total_lanes = 4 * (1 + num_neighbors)  # 4 sue + 4 per ogni vicino

            sat_flows_i = [0.4] * total_lanes

            # Mappa delle fasi locale (applica i verdi solo alle 4 corsie locali dell'incrocio i)
            phase_map_single = np.array([[1, 1, 0, 0], [0, 0, 1, 1]])
            phase_map_i = np.hstack([phase_map_single, np.zeros((2, 4 * num_neighbors))])

            local_K_matrices[i] = calculate_k(sat_flows_i, phase_map_i, q, r)

        controller = DTUCController(
            intersection_ids=int_ids,
            local_K_matr=local_K_matrices,
            nominal_greens=nominali,
            min_greens=minimi,
            max_greens=massimi,
            network_topology=topologia
        )

    elif strat_name == "D2TUC":
        sat_flows_local = [0.4, 0.4, 0.4, 0.4]
        phase_map_local = [[1, 1, 0, 0], [0, 0, 1, 1]]
        local_K_single = calculate_k(sat_flows_local, phase_map_local, q, r)

        local_K_matrices = {i: local_K_single for i in int_ids}

        controller = D2TUCController(
            intersection_ids=int_ids,
            local_K_matr=local_K_matrices,
            nominal_greens=nominali,
            min_greens=minimi,
            max_greens=massimi
        )
    else:
        raise ValueError(f"Strategia sconosciuta: {strat_name}")

    # Inizializzazione ambiente di simulazione
    env = TrafficSimulationEnv(
        config_file="sumo_config/configuration.sumocfg",
        int_ids=int_ids,
        lanes_in=corsie_in
    )

    file_log_csv = f"risultati_{strat_name}.csv"
    log_data = []

    print("Apertura connessione TraCI con SUMO...")
    env.start_simulation()

    try:
        for ciclo in range(n_cycles):
            # Estrazione code da SUMO
            input_traffico = env.get_current_queues_all()

            # Calcolo verdi per controller
            verdi_ottimizzati = controller.compute_green_times(input_traffico)
            print(f"\n[Ciclo {ciclo}] --- Risultati Controllo {strat_name} ---")

            row_log = {"cycle": ciclo}
            coda_tot_ciclo = 0

            for i in int_ids:
                code_ids = input_traffico[i]
                verdi_ids = verdi_ottimizzati[i]

                coda_nodo = sum(code_ids)
                coda_tot_ciclo += coda_nodo

                print(
                    f" > {i} | Code [Nord, Sud, Est, Ovest]: {code_ids} -> Verde N-S: {verdi_ids[0]:.1f}s | Verde E-O: {verdi_ids[1]:.1f}s"
                )

                # Salvataggio dati per il log
                row_log[f"{i}_Coda_NS"] = code_ids[0] + code_ids[1]
                row_log[f"{i}_Coda_EO"] = code_ids[2] + code_ids[3]
                row_log[f"{i}_Verde_NS"] = verdi_ids[0]
                row_log[f"{i}_Verde_EO"] = verdi_ids[1]

            row_log["total_net_queue"] = coda_tot_ciclo
            log_data.append(row_log)

            # Esecuzione del ciclo in SUMO
            env.execute_traffic_cycle_all(verdi_ottimizzati)

    except Exception as e:
        print(f"Errore intercettato durante la simulazione {strat_name}: {e}")
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
        print(f"Simulazione {strat_name} terminata.")

if __name__ == "__main__":
    main()