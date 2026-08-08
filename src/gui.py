"""
gui.py
Builds and runs the Tkinter interface: layout, widgets, and event wiring.
All heavy lifting (plotting, EDA stats, file I/O) is delegated to the other
src modules so this file stays focused on presentation and control flow.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src import plots as plots_module
from src import file_handler
from src import eda as eda_module
from src import customize as customize_module
from src import utils

APP_TITLE = "Seaborn EDA Dashboard"
BG_COLOR = "#1a1a2e"
PANEL_COLOR = "#252542"
ACCENT_COLOR = "#e94560"
ACCENT_COLOR2 = "#4f8ef7"
TEXT_COLOR = "#eaeaf5"
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_SECTION = ("Segoe UI", 11, "bold")
FONT_NORMAL = ("Segoe UI", 10)

NONE_OPTION = "None"


class EDADashboardApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1240x800")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(1050, 700)

        # Application state
        self.df = None
        self.dataset_path = None
        self.dataset_name = tk.StringVar(value="No dataset loaded")
        self.rows_var = tk.StringVar(value="Rows: -")
        self.cols_var = tk.StringVar(value="Columns: -")
        self.style = customize_module.ChartStyle()
        self.current_fig = None

        self.x_col_var = tk.StringVar()
        self.y_col_var = tk.StringVar()
        self.hue_col_var = tk.StringVar(value=NONE_OPTION)
        self.single_col_var = tk.StringVar()

        self._build_layout()

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------
    def _build_layout(self):
        self._build_header()

        body = tk.Frame(self.root, bg=BG_COLOR)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        left = tk.Frame(body, bg=BG_COLOR, width=310)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        self._build_dataset_panel(left)
        self._build_column_selector(left)
        self._build_plot_buttons(left)
        self._build_actions_panel(left)

        right = tk.Frame(body, bg=BG_COLOR)
        right.pack(side="left", fill="both", expand=True)

        self._build_chart_area(right)
        self._build_bottom_row(right)

    def _section_frame(self, parent, title):
        frame = tk.LabelFrame(
            parent, text=title, bg=PANEL_COLOR, fg=TEXT_COLOR,
            font=FONT_SECTION, bd=1, relief="groove", labelanchor="n"
        )
        frame.pack(fill="x", pady=6)
        return frame

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG_COLOR)
        header.pack(fill="x", padx=12, pady=(12, 0))
        tk.Label(
            header, text="📊 SEABORN EDA DASHBOARD",
            bg=BG_COLOR, fg=ACCENT_COLOR2, font=FONT_HEADER
        ).pack(side="left")

    def _build_dataset_panel(self, parent):
        frame = self._section_frame(parent, "📂 Load CSV Dataset")

        tk.Button(
            frame, text="Load CSV", command=self.on_load_csv,
            bg=ACCENT_COLOR2, fg="white", font=FONT_NORMAL, relief="flat", pady=4
        ).pack(fill="x", padx=8, pady=(6, 4))

        tk.Label(frame, textvariable=self.dataset_name, bg=PANEL_COLOR,
                 fg=TEXT_COLOR, font=FONT_NORMAL, wraplength=270, justify="left"
                 ).pack(anchor="w", padx=8)
        tk.Label(frame, textvariable=self.rows_var, bg=PANEL_COLOR,
                 fg=TEXT_COLOR, font=FONT_NORMAL).pack(anchor="w", padx=8)
        tk.Label(frame, textvariable=self.cols_var, bg=PANEL_COLOR,
                 fg=TEXT_COLOR, font=FONT_NORMAL).pack(anchor="w", padx=8, pady=(0, 6))

    def _build_column_selector(self, parent):
        frame = self._section_frame(parent, "🧭 Columns")

        tk.Label(frame, text="X-axis", bg=PANEL_COLOR, fg=TEXT_COLOR,
                 font=FONT_NORMAL).pack(anchor="w", padx=8, pady=(6, 0))
        self.x_combo = ttk.Combobox(frame, textvariable=self.x_col_var, state="readonly")
        self.x_combo.pack(fill="x", padx=8, pady=(0, 6))

        tk.Label(frame, text="Y-axis", bg=PANEL_COLOR, fg=TEXT_COLOR,
                 font=FONT_NORMAL).pack(anchor="w", padx=8)
        self.y_combo = ttk.Combobox(frame, textvariable=self.y_col_var, state="readonly")
        self.y_combo.pack(fill="x", padx=8, pady=(0, 6))

        tk.Label(frame, text="Hue (optional)", bg=PANEL_COLOR, fg=TEXT_COLOR,
                 font=FONT_NORMAL).pack(anchor="w", padx=8)
        self.hue_combo = ttk.Combobox(frame, textvariable=self.hue_col_var, state="readonly")
        self.hue_combo.pack(fill="x", padx=8, pady=(0, 6))

        tk.Label(frame, text="Single column (hist / count)", bg=PANEL_COLOR, fg=TEXT_COLOR,
                 font=FONT_NORMAL).pack(anchor="w", padx=8)
        self.single_combo = ttk.Combobox(frame, textvariable=self.single_col_var, state="readonly")
        self.single_combo.pack(fill="x", padx=8, pady=(0, 8))

        style_row = tk.Frame(frame, bg=PANEL_COLOR)
        style_row.pack(fill="x", padx=8, pady=(0, 8))
        tk.Label(style_row, text="Palette", bg=PANEL_COLOR, fg=TEXT_COLOR,
                 font=FONT_NORMAL).pack(anchor="w")
        palette_box = ttk.Combobox(style_row, values=customize_module.VALID_PALETTES, state="readonly")
        palette_box.set(self.style.palette)
        palette_box.pack(fill="x", pady=(0, 4))
        palette_box.bind("<<ComboboxSelected>>",
                          lambda e: customize_module.change_palette(self.style, palette_box.get()))

        tk.Label(style_row, text="Theme", bg=PANEL_COLOR, fg=TEXT_COLOR,
                 font=FONT_NORMAL).pack(anchor="w")
        theme_box = ttk.Combobox(style_row, values=customize_module.VALID_STYLES, state="readonly")
        theme_box.set(self.style.style)
        theme_box.pack(fill="x")
        theme_box.bind("<<ComboboxSelected>>",
                        lambda e: customize_module.change_style(self.style, theme_box.get()))

    def _build_plot_buttons(self, parent):
        frame = self._section_frame(parent, "📈 Visualizations")

        buttons = [
            ("🔵 Scatter Plot", self.on_scatter),
            ("📈 Line Plot", self.on_line),
            ("📊 Bar Plot", self.on_bar),
            ("📦 Box Plot", self.on_box),
            ("🎻 Violin Plot", self.on_violin),
            ("🔥 Correlation Heatmap", self.on_heatmap),
            ("🔢 Count Plot", self.on_count),
            ("🔍 Pair Plot", self.on_pairplot),
        ]
        grid = tk.Frame(frame, bg=PANEL_COLOR)
        grid.pack(fill="x", padx=8, pady=6)
        for i, (label, cmd) in enumerate(buttons):
            r, c = divmod(i, 2)
            tk.Button(
                grid, text=label, command=cmd, anchor="w",
                bg="#33335c", fg=TEXT_COLOR, font=("Segoe UI", 9),
                relief="flat", pady=4, wraplength=130, justify="left"
            ).grid(row=r, column=c, sticky="ew", padx=2, pady=2)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

    def _build_actions_panel(self, parent):
        frame = self._section_frame(parent, "⚙ Actions")

        tk.Button(
            frame, text="💾 Save Visualization", command=self.on_save_chart,
            bg="#33335c", fg=TEXT_COLOR, font=FONT_NORMAL, relief="flat", pady=4
        ).pack(fill="x", padx=8, pady=2)

        tk.Button(
            frame, text="📄 Generate EDA Report", command=self.on_generate_report,
            bg="#33335c", fg=TEXT_COLOR, font=FONT_NORMAL, relief="flat", pady=4
        ).pack(fill="x", padx=8, pady=2)

        tk.Button(
            frame, text="🚪 Exit", command=self.root.quit,
            bg="#c0392b", fg="white", font=FONT_NORMAL, relief="flat", pady=4
        ).pack(fill="x", padx=8, pady=(2, 8))

    def _build_chart_area(self, parent):
        self.chart_frame = tk.LabelFrame(
            parent, text="Visualization Preview", bg=PANEL_COLOR, fg=TEXT_COLOR,
            font=FONT_SECTION, bd=1, relief="groove", labelanchor="n", height=460
        )
        self.chart_frame.pack(fill="both", expand=True, pady=(0, 8))
        self.chart_frame.pack_propagate(False)

        self.placeholder_label = tk.Label(
            self.chart_frame, text="Load a dataset and pick a visualization to begin.",
            bg=PANEL_COLOR, fg=TEXT_COLOR, font=FONT_NORMAL
        )
        self.placeholder_label.pack(expand=True)

    def _build_bottom_row(self, parent):
        row = tk.Frame(parent, bg=BG_COLOR)
        row.pack(fill="both", expand=False)

        summary_frame = self._section_frame(row, "📋 Dataset Summary")
        summary_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.summary_text = tk.Text(
            summary_frame, height=8, bg="#12121f", fg=TEXT_COLOR, font=("Consolas", 9),
            relief="flat", wrap="word"
        )
        self.summary_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.summary_text.insert("1.0", "Load a dataset to see Mean, Median, Std, Skew, and outliers here.")
        self.summary_text.config(state="disabled")

        outlier_frame = self._section_frame(row, "🚨 Outlier Detection")
        outlier_frame.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.outlier_text = tk.Text(
            outlier_frame, height=8, bg="#12121f", fg=TEXT_COLOR, font=("Consolas", 9),
            relief="flat", wrap="word"
        )
        self.outlier_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.outlier_text.insert("1.0", "IQR-based outlier counts will appear here.")
        self.outlier_text.config(state="disabled")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def on_load_csv(self):
        path = filedialog.askopenfilename(
            title="Select a CSV file", filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return

        df, error = file_handler.load_csv(path)
        if error:
            utils.show_message("error", "Failed to Load Dataset", error)
            return

        self.df = df
        self.dataset_path = path
        self.dataset_name.set(f"Dataset: {os.path.basename(path)}")
        self.rows_var.set(f"Rows: {df.shape[0]}")
        self.cols_var.set(f"Columns: {df.shape[1]}")

        all_cols = utils.get_all_columns(df)
        numeric_cols = utils.get_numeric_columns(df)
        cat_cols = utils.get_categorical_columns(df)

        self.x_combo["values"] = all_cols
        self.y_combo["values"] = numeric_cols
        self.hue_combo["values"] = [NONE_OPTION] + cat_cols
        self.single_combo["values"] = all_cols

        if all_cols:
            self.x_col_var.set(all_cols[0])
            self.single_col_var.set(numeric_cols[0] if numeric_cols else all_cols[0])
        if numeric_cols:
            self.y_col_var.set(numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0])
        self.hue_col_var.set(NONE_OPTION)

        self._refresh_summary()
        utils.show_message("info", "Dataset Loaded",
                            f"Loaded {df.shape[0]} rows and {df.shape[1]} columns.")

    def _refresh_summary(self):
        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", eda_module.format_summary_text(self.df))
        self.summary_text.config(state="disabled")

        self.outlier_text.config(state="normal")
        self.outlier_text.delete("1.0", "end")
        self.outlier_text.insert("1.0", eda_module.format_outlier_text(self.df))
        self.outlier_text.config(state="disabled")

    def _validate_ready(self, need_y=True):
        valid, msg = utils.validate_dataset(self.df)
        if not valid:
            utils.show_message("warning", "No Data", msg)
            return False
        if need_y and (not self.x_col_var.get() or not self.y_col_var.get()):
            utils.show_message("warning", "Select Columns",
                                "Please choose both an X-axis and Y-axis column.")
            return False
        return True

    def _render_figure(self, fig):
        utils.clear_frame(self.chart_frame)
        self.current_fig = fig
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _hue(self):
        h = self.hue_col_var.get()
        return None if h == NONE_OPTION or not h else h

    def on_scatter(self):
        if not self._validate_ready():
            return
        try:
            fig = plots_module.scatter_plot(self.df, self.x_col_var.get(), self.y_col_var.get(),
                                             self._hue(), self.style)
            self._render_figure(fig)
        except Exception as e:  # noqa: BLE001
            utils.show_message("error", "Plot Error", str(e))

    def on_line(self):
        if not self._validate_ready():
            return
        try:
            fig = plots_module.line_plot(self.df, self.x_col_var.get(), self.y_col_var.get(),
                                          self._hue(), self.style)
            self._render_figure(fig)
        except Exception as e:  # noqa: BLE001
            utils.show_message("error", "Plot Error", str(e))

    def on_bar(self):
        if not self._validate_ready():
            return
        try:
            fig = plots_module.bar_plot(self.df, self.x_col_var.get(), self.y_col_var.get(),
                                         self._hue(), self.style)
            self._render_figure(fig)
        except Exception as e:  # noqa: BLE001
            utils.show_message("error", "Plot Error", str(e))

    def on_box(self):
        if not self._validate_ready():
            return
        try:
            fig = plots_module.box_plot(self.df, self.x_col_var.get(), self.y_col_var.get(), self.style)
            self._render_figure(fig)
        except Exception as e:  # noqa: BLE001
            utils.show_message("error", "Plot Error", str(e))

    def on_violin(self):
        if not self._validate_ready():
            return
        try:
            fig = plots_module.violin_plot(self.df, self.x_col_var.get(), self.y_col_var.get(), self.style)
            self._render_figure(fig)
        except Exception as e:  # noqa: BLE001
            utils.show_message("error", "Plot Error", str(e))

    def on_heatmap(self):
        valid, msg = utils.validate_dataset(self.df)
        if not valid:
            utils.show_message("warning", "No Data", msg)
            return
        try:
            fig = plots_module.correlation_heatmap(self.df, self.style)
            self._render_figure(fig)
        except Exception as e:  # noqa: BLE001
            utils.show_message("error", "Plot Error", str(e))

    def on_count(self):
        valid, msg = utils.validate_dataset(self.df)
        if not valid:
            utils.show_message("warning", "No Data", msg)
            return
        col = self.single_col_var.get() or self.x_col_var.get()
        if not col:
            utils.show_message("warning", "Select Column", "Please choose a column for the count plot.")
            return
        try:
            fig = plots_module.count_plot(self.df, col, self.style)
            self._render_figure(fig)
        except Exception as e:  # noqa: BLE001
            utils.show_message("error", "Plot Error", str(e))

    def on_pairplot(self):
        valid, msg = utils.validate_dataset(self.df)
        if not valid:
            utils.show_message("warning", "No Data", msg)
            return
        try:
            fig = plots_module.pair_plot(self.df, self.style)
            self._render_figure(fig)
        except Exception as e:  # noqa: BLE001
            utils.show_message("error", "Plot Error", str(e))

    def on_save_chart(self):
        if self.current_fig is None:
            utils.show_message("warning", "No Chart", "Generate a visualization first before saving.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Visualization As", defaultextension=".png",
            filetypes=[("PNG image", "*.png")], initialdir="visualizations"
        )
        if not path:
            return

        success, message = file_handler.save_visualization(self.current_fig, path)
        utils.show_message("info" if success else "error", "Save Visualization", message)

    def on_generate_report(self):
        valid, msg = utils.validate_dataset(self.df)
        if not valid:
            utils.show_message("warning", "No Data", msg)
            return

        path = filedialog.asksaveasfilename(
            title="Save EDA Report As", defaultextension=".txt",
            filetypes=[("Text file", "*.txt")], initialdir="reports",
            initialfile="eda_report.txt"
        )
        if not path:
            return

        name = os.path.basename(self.dataset_path) if self.dataset_path else "Unknown dataset"
        success, message = file_handler.generate_eda_report(self.df, name, path)
        utils.show_message("info" if success else "error", "Generate EDA Report", message)


def start_app():
    root = tk.Tk()
    app = EDADashboardApp(root)
    root.mainloop()
