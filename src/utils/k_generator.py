import numpy as np
import scipy

def calculate_k(
        saturation_flows: list[float],
        phase_mapping: list[list[int]],
        q_weight: float,
        r_weight: float,
        leakage_factor: float = 0.98  # fattore di decadimento (gamma < 1)
) -> np.ndarray:
    """
    Calcola la matrice dei guadagni K per un incrocio con LQR
    :param saturation_flows: Flussi di saturazione per ogni corsia in ingresso (S_i)
    :param phase_mapping: Matrice binaria dove le righe indicano la fase semaforica e le colonne le corsie abilitate (1=attiva, 0=non attiva)
    :param q_weight: Peso della penalizzazione delle code nel costo LQR (Q = q_weight * I)
    :param r_weight: Peso della penalizzazione sulla variazione di verde (R = r_weight * I)
    :param leakage_factor: Parametro di stabilità dinamica (deve essere < 1.0)
    :return: matrice di guadagno K (di dimensioni = num_fasi * num_corsie)
    """

    S = np.array(saturation_flows)
    P = np.array(phase_mapping)

    num_lanes = len(S)
    num_phases = len(P)

    #Calcolo matrice di controllo B
    B = np.zeros((num_lanes, num_phases))
    for i in range(num_phases):
        for j in range(num_lanes):
            if P[i][j] == 1:
                B[j, i] = -S[j]

    #Calcolo matrice di stato A (leakage_factor < 1 rende il sistema stabilizzabile per Riccati)
    A = np.eye(num_lanes) * leakage_factor

    #Calcolo matrici di peso Q (stato) e R (controllo)
    Q = np.eye(num_lanes) * q_weight
    R = np.eye(num_phases) * r_weight

    #Risoluzione equazione di Riccati per ottenere matrice P
    P_matrix = scipy.linalg.solve_discrete_are(A, B, Q, R)

    #Calcolo del guadagno K = -(R + B(trasposta) * P * B)[invertita] * B(trasposta) * P * A
    K = -np.linalg.inv(R + B.T @ P_matrix @ B) @ B.T @ P_matrix @ A

    return K