"""
plots.py
All plotting logic lives here, isolated from the GUI. Every function takes
a pandas DataFrame plus a ChartStyle and returns a matplotlib Figure, which
gui.py embeds into the Tkinter canvas. Seaborn is used for the statistical
heavy-lifting (KDE, regression lines, box/violin internals); matplotlib
Figure/Axes objects are what actually get embedded and saved.
"""

import matplotlib
matplotlib.use("Agg")  # safe default backend; gui.py swaps in TkAgg when embedding

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def _prep(style):
    """Apply the current seaborn theme before drawing a new figure."""
    sns.set_theme(style=style.style, context=style.context, palette=style.palette)


def scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, hue_col: str, style) -> plt.Figure:
    _prep(style)
    fig, ax = plt.subplots(figsize=(6.2, 4.4), dpi=100)
    sns.scatterplot(
        data=df, x=x_col, y=y_col,
        hue=hue_col if hue_col and hue_col != "None" else None,
        marker=style.marker, ax=ax, s=45, alpha=0.8,
    )
    ax.set_title(f"Scatter Plot: {y_col} vs {x_col}")
    fig.tight_layout()
    return fig


def line_plot(df: pd.DataFrame, x_col: str, y_col: str, hue_col: str, style) -> plt.Figure:
    _prep(style)
    fig, ax = plt.subplots(figsize=(6.2, 4.4), dpi=100)
    sns.lineplot(
        data=df, x=x_col, y=y_col,
        hue=hue_col if hue_col and hue_col != "None" else None,
        marker=style.marker, ax=ax,
    )
    ax.set_title(f"Line Plot: {y_col} over {x_col}")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def bar_plot(df: pd.DataFrame, x_col: str, y_col: str, hue_col: str, style) -> plt.Figure:
    _prep(style)
    fig, ax = plt.subplots(figsize=(6.2, 4.4), dpi=100)
    plot_df = df.copy()
    # Cap category count so wide categorical columns stay readable.
    top_categories = plot_df[x_col].value_counts().index[:20]
    plot_df = plot_df[plot_df[x_col].isin(top_categories)]

    sns.barplot(
        data=plot_df, x=x_col, y=y_col,
        hue=hue_col if hue_col and hue_col != "None" else None,
        ax=ax, errorbar="sd",
    )
    ax.set_title(f"Bar Plot: mean {y_col} by {x_col}")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def box_plot(df: pd.DataFrame, x_col: str, y_col: str, style) -> plt.Figure:
    _prep(style)
    fig, ax = plt.subplots(figsize=(6.2, 4.4), dpi=100)
    plot_df = df.copy()
    if x_col and x_col != "None":
        top_categories = plot_df[x_col].value_counts().index[:15]
        plot_df = plot_df[plot_df[x_col].isin(top_categories)]
        sns.boxplot(data=plot_df, x=x_col, y=y_col, ax=ax)
        ax.tick_params(axis="x", rotation=45)
        ax.set_title(f"Box Plot: {y_col} by {x_col}")
    else:
        sns.boxplot(data=plot_df, y=y_col, ax=ax)
        ax.set_title(f"Box Plot: {y_col}")
    fig.tight_layout()
    return fig


def violin_plot(df: pd.DataFrame, x_col: str, y_col: str, style) -> plt.Figure:
    _prep(style)
    fig, ax = plt.subplots(figsize=(6.2, 4.4), dpi=100)
    plot_df = df.copy()
    if x_col and x_col != "None":
        top_categories = plot_df[x_col].value_counts().index[:12]
        plot_df = plot_df[plot_df[x_col].isin(top_categories)]
        sns.violinplot(data=plot_df, x=x_col, y=y_col, ax=ax)
        ax.tick_params(axis="x", rotation=45)
        ax.set_title(f"Violin Plot: {y_col} by {x_col}")
    else:
        sns.violinplot(data=plot_df, y=y_col, ax=ax)
        ax.set_title(f"Violin Plot: {y_col}")
    fig.tight_layout()
    return fig


def correlation_heatmap(df: pd.DataFrame, style) -> plt.Figure:
    _prep(style)
    numeric_df = df.select_dtypes(include="number")
    fig, ax = plt.subplots(figsize=(6.2, 5.2), dpi=100)
    corr = numeric_df.corr(numeric_only=True)
    sns.heatmap(
        corr, annot=True, fmt=".2f", cmap=style.palette, ax=ax,
        square=True, linewidths=0.5, cbar_kws={"shrink": 0.8},
    )
    ax.set_title("Correlation Heatmap")
    fig.tight_layout()
    return fig


def count_plot(df: pd.DataFrame, col: str, style) -> plt.Figure:
    _prep(style)
    fig, ax = plt.subplots(figsize=(6.2, 4.4), dpi=100)
    plot_df = df.copy()
    top_categories = plot_df[col].value_counts().index[:15]
    plot_df = plot_df[plot_df[col].isin(top_categories)]
    order = plot_df[col].value_counts().index
    sns.countplot(data=plot_df, x=col, order=order, ax=ax)
    ax.set_title(f"Count Plot: {col}")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def pair_plot(df: pd.DataFrame, style, max_cols: int = 4):
    """
    Pair plot across numeric columns. Returns a seaborn PairGrid's
    underlying Figure. Capped at max_cols numeric columns to keep
    render time and figure size reasonable.
    """
    _prep(style)
    numeric_df = df.select_dtypes(include="number")
    cols = numeric_df.columns.tolist()[:max_cols]
    if len(cols) < 2:
        raise ValueError("Need at least 2 numeric columns for a pair plot.")

    grid = sns.pairplot(df[cols].dropna(), diag_kind="kde", height=1.8)
    grid.figure.suptitle("Pair Plot", y=1.02)
    return grid.figure


def distribution_plot(df: pd.DataFrame, col: str, style) -> plt.Figure:
    """Histogram + KDE overlay — used for the 'distribution' concept in EDA."""
    _prep(style)
    fig, ax = plt.subplots(figsize=(6.2, 4.4), dpi=100)
    sns.histplot(df[col].dropna(), kde=True, ax=ax)
    ax.set_title(f"Distribution: {col}")
    fig.tight_layout()
    return fig
