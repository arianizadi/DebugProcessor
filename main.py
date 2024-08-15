import re
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import datetime

from matplotlib.ticker import FuncFormatter


def parse_log_file(file_path):
    timestamp_pattern = re.compile(
        r"-------------(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})-------------"
    )
    variable_pattern = re.compile(r"^([^:]+):\s*(.+)$")

    data = defaultdict(lambda: defaultdict(dict))
    current_timestamp = None

    with open(file_path, "r") as file:
        for line in file:
            timestamp_match = timestamp_pattern.match(line)
            if timestamp_match:
                current_timestamp = timestamp_match.group(1)
                continue

            if current_timestamp:
                variable_match = variable_pattern.match(line.strip())
                if variable_match:
                    key, value = variable_match.groups()
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                    data[current_timestamp][key] = value

    return dict(data)


def identify_changing_variables(data):
    all_variables = set()
    for timestamp in data:
        all_variables.update(data[timestamp].keys())

    changing_variables = set()
    static_variables = {}

    for var in all_variables:
        values = [
            data[timestamp].get(var) for timestamp in data if var in data[timestamp]
        ]
        if len(set(values)) > 1:
            changing_variables.add(var)
        else:
            static_variables[var] = values[0]

    return changing_variables, static_variables


def create_gui(data, changing_variables, static_variables):
    root = tk.Tk()
    root.title("Log Data Analyzer")
    root.geometry("1200x800")

    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    left_frame = ttk.Frame(main_frame, width=300)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

    static_text = scrolledtext.ScrolledText(
        left_frame, wrap=tk.WORD, width=40, height=40, font=("Arial", 12)
    )
    static_text.pack(fill=tk.BOTH, expand=True)
    static_text.insert(tk.INSERT, "Static Variables:\n\n")
    for var, value in static_variables.items():
        static_text.insert(tk.END, f"{var}: {value}\n")

    right_frame = ttk.Frame(main_frame)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    if changing_variables:
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        timestamps = [
            datetime.datetime.strptime(ts, "%Y-%m-%d_%H-%M-%S") for ts in data.keys()
        ]

        def format_y_axis(value, pos):
            return f"{value:.2f}"

        for var in changing_variables:
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=var)

            fig, ax = plt.subplots(figsize=(12, 7))

            values = [data[ts].get(var, float("nan")) for ts in data.keys()]
            ax.plot(timestamps, values)
            ax.set_ylabel(var, fontsize=10)
            ax.set_xlabel("Time", fontsize=10)
            ax.tick_params(axis="both", which="major", labelsize=8)
            ax.grid(True)

            ax.yaxis.set_major_formatter(FuncFormatter(format_y_axis))

            ax.xaxis.set_major_formatter(
                plt.matplotlib.dates.DateFormatter("%Y-%m-%d\n%H:%M:%S")
            )
            for label in ax.get_xticklabels():
                label.set_rotation(45)
                label.set_ha("right")

            plt.tight_layout(pad=5.0, rect=[0.05, 0.05, 0.95, 0.95])

            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    else:
        no_change_label = ttk.Label(
            right_frame,
            text="No changing variables detected in the log file.",
            font=("Arial", 12),
        )
        no_change_label.pack(expand=True)

    root.mainloop()


if __name__ == "__main__":
    log_file_path = "log.log"

    print("Parsing log file...")
    parsed_data = parse_log_file(log_file_path)

    print("Identifying changing and static variables...")
    changing_vars, static_vars = identify_changing_variables(parsed_data)

    print(f"Number of changing variables: {len(changing_vars)}")
    print(f"Number of static variables: {len(static_vars)}")

    if not changing_vars:
        print("Warning: No changing variables detected in the log file.")
    else:
        print("Changing variables:", changing_vars)

    print("Launching GUI...")
    create_gui(parsed_data, changing_vars, static_vars)
