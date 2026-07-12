from src.strategies.tuc_controller import TUCController
from src.strategies.dtuc_controller import DTUCController
from src.strategies.d2tuc_controller import D2TUCController

from src.simulation.traffic_env import TrafficSimulationEnv

def main():
    tls_id = "J4"  #id incrocio semaforo
    corsie_ingresso = ["Nord_in_0", "Sud_in_0", "Est_in_0", "Ovest_in_0"] #lista corsie in ingresso al semaforo

    #Configurazione Parametri Temporali per il TUC (2 Fasi: Nord-Sud / Est-Ovest)
    nominali = {tls_id: [30.0, 30.0]}
    minimi = {tls_id: [10.0, 10.0]}
    massimi = {tls_id: [60.0, 60.0]}

    # Matrice K per le 4 corsie di input e le 2 fasi di output (per TUC)
    K_matrix = [
        [0.4, 0.4, -0.3, -0.3],  # Impatto sulla Fase 1 (Nord-Sud)
        [-0.3, -0.3, 0.4, 0.4]  # Impatto sulla Fase 2 (Est-Ovest)
    ]

    local_K_matricies = {tls_id: [
        [0.8, 0.8, -0.1, -0.1],
        [-0.1, -0.1, 0.8, 0.8]
    ]}  # Per DTUC/D2TUC

    # Inizializzazione ambiente di simulazione
    env = TrafficSimulationEnv(
        config_file="sumo_config/configuration.sumocfg",
        tls_id=tls_id,
        lanes_in=corsie_ingresso
    )

    # A seconda di quale controller usare, commenta/ decommenta la sezione corrispondente

    # Configurazione controller TUC
    controller = TUCController(
        intersection_ids=[tls_id],
        K_matr=K_matrix,
        nominal_greens=nominali,
        min_greens=minimi,
        max_greens=massimi
    )


    # Configurazione controller DTUC
    '''
    controller = DTUCController(
        intersection_ids=[tls_id],
        local_K_matr=local_K_matricies,
        nominal_greens=nominali,
        min_greens=minimi,
        max_greens=massimi
    )
    
    # Configurazione controller D2TUC
    controller = D2TUCController(
        intersection_ids=[tls_id],
        local_K_matr=local_K_matricies,
        nominal_greens=nominali,
        min_greens=minimi,
        max_greens=massimi
    )
    '''

    # Inzio loop di Simulazione
    print("Apertura connessione TraCI con SUMO...")
    env.start_simulation()

    SIM_CYCLES = 100  # Eseguiamo la simulazione per 50 cicli semaforici completo

    try:
        for ciclo in range(SIM_CYCLES):
            # Estrazione code da SUMO
            code_attuali = env.get_current_queues()
            print(f"\n[Ciclo {ciclo}] Code rilevate [Nord, Sud, Est, Ovest]: {code_attuali}")

            if isinstance(controller, TUCController):
                input_traffico = code_attuali # caso TUC
            else:
                input_traffico = {tls_id: code_attuali} #caso DTUC/D2TUC

            # Calcolo verdi per controller
            verdi_ottimizzati = controller.compute_green_times(input_traffico)
            verdi_incrocio = verdi_ottimizzati[tls_id]
            print(f"[Ciclo {ciclo}] {type(controller).__name__} -> Verde N-S: {verdi_incrocio[0]:.1f}s | Verde E-O: {verdi_incrocio[1]:.1f}s")
            # Esecuzione in SUMO
            env.execute_traffic_cycle(verdi_incrocio)

    except Exception as e:
        print(f"Errore intercettato: {e}")
    finally:
        env.stop_simulation()
        print("Simulazione terminata.")

if __name__ == "__main__":
    main()