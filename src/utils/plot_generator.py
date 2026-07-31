import matplotlib.pyplot as plt
import os
import pandas as pd

#stile dei grafici
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14
})

class PlotGenerator:
    def __init__(self, output_dir="results/plots"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def plot_net_queues(self, strat_dict):
        """
        Confronta l'andamento della coda totale della rete nel tempo tra i vari controllori.
        :param strat_dict: dizionario di DataFrame [nome del controllore: dati del controllore]
        """
        plt.figure(figsize=(9, 5))

        colors = {'TUC': 'blue', 'DTUC': 'red', 'D2TUC': 'green'}
        for name, df in strat_dict.items():
            plt.plot(df['cycle'], df['total_net_queue'], label=name, color=colors.get(name, None), linewidth=2)

        plt.xlabel("Ciclo semaforico (k)")
        plt.ylabel("Coda totale della rete (veicoli)")
        plt.title("Coda totale della rete nel tempo")
        plt.legend(loc='upper right', frameon=True)
        plt.tight_layout()

        filepath = os.path.join(self.output_dir, "net_queues.png")
        plt.savefig(filepath, dpi=300)
        plt.close()
        print(f"[PlotGenerator] Grafico salvato in: {filepath}")

    def plot_green_times(self, strat_dict, int_id="J0"):
        """
        Confronta l'andamento dei tempi di verde per le varie fasi dell'incrocio J0 tra i controllori
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        colors = {'TUC': 'blue', 'DTUC': 'red', 'D2TUC': 'green'}
        linestyles = {'TUC': '-', 'DTUC': '--', 'D2TUC': '-.'}

        for name, df in strat_dict.items():
            color = colors.get(name, None)
            ls = linestyles.get(name, '-')

            col_ns = f"{int_id}_Verde_NS"
            col_eo = f"{int_id}_Verde_EO"

            if col_ns in df.columns:
                ax1.plot(df['cycle'], df[col_ns], label=f"{name}", color=color, linestyle=ls, linewidth=2)

            if col_eo in df.columns:
                ax2.plot(df['cycle'], df[col_eo], label=f"{name}", color=color, linestyle=ls, linewidth=2)

        #configurazione plot fase ns
        ax1.axhline(y=6, color='r', linestyle=':', alpha=0.6, label='Verde Minimo (6s)')
        ax1.axhline(y=45, color='g', linestyle=':', alpha=0.6, label='Verde Massimo (45s)')
        ax1.set_ylabel("Tempo di verde (s)")
        ax1.set_title(f"Allocazione verde - Fase Nord-Sud ({int_id})")
        ax1.legend(loc='upper right', frameon=True, ncol=2)
        ax1.grid(True, linestyle='--', alpha=0.6)

        #configurazione plot fase eo
        ax2.axhline(y=6, color='r', linestyle=':', alpha=0.6, label='Verde Minimo (6s)')
        ax2.axhline(y=45, color='g', linestyle=':', alpha=0.6, label='Verde Massimo (45s)')
        ax2.set_xlabel("Ciclo semaforico (k)")
        ax2.set_ylabel("Tempo di verde (s)")
        ax2.set_title(f"Allocazione verde - Fase Est-Ovest ({int_id})")
        ax2.legend(loc='upper right', frameon=True, ncol=2)
        ax2.grid(True, linestyle='--', alpha=0.6)

        plt.suptitle(f"Confronto tempi di verde sull'incrocio {int_id}", fontsize=14, y=0.98)
        plt.tight_layout()

        filepath = os.path.join(self.output_dir, f"green_times_comparison_{int_id}.png")
        plt.savefig(filepath, dpi=300)
        plt.close()
        print(f"[PlotGenerator] Grafico salvato in: {filepath}")

    def plot_mean_max_bar_chart(self, strat_dict):
        """
        Genera un grafico a barre per confrontare le code medie e massime tra i controllori.
        """
        data = []
        for name, df in strat_dict.items():
            data.append({
                'Controllore': name,
                'Coda Media': df['total_net_queue'].mean(),
                'Coda Massima': df['total_net_queue'].max()
            })

        df_summary = pd.DataFrame(data)

        fig, ax = plt.subplots(figsize=(9, 5))
        df_summary.plot(x='Controllore', y=['Coda Media', 'Coda Massima'], kind='bar', ax=ax, width=0.6, rot=0)
        plt.ylabel("Numero di veicoli")
        plt.title("Confronto coda media e massima tra controllori")
        plt.tight_layout()

        filepath = os.path.join(self.output_dir, "mean_max_bar_chart.png")
        plt.savefig(filepath, dpi=300)
        plt.close()
        print(f"[PlotGenerator] Grafico salvato in: {filepath}")