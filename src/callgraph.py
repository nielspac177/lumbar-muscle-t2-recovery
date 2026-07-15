"""Generate a function call graph of the analysis code by static analysis.

Parses every module in src/ with the `ast` module, collects function
definitions, and records edges where one function calls another function
defined anywhere in the package. Renders the graph with networkx + matplotlib
and also emits a Mermaid version for the documentation.

Outputs: docs/callgraph.png, docs/callgraph.svg, docs/callgraph.mmd
Run:     python src/callgraph.py
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

SRC = Path(__file__).resolve().parent
MODULE_COLORS = {
    "data_loading": "#0072B2",
    "cleaning": "#009E73",
    "cohort": "#E69F00",
    "analysis": "#CC79A7",
    "figures": "#56B4E9",
    "pipeline": "#D55E00",
    "make_schematic": "#999999",
    "callgraph": "#999999",
}


def collect_defs(files):
    """Map every function name to the module that defines it."""
    owner = {}
    trees = {}
    for f in files:
        mod = f.stem
        tree = ast.parse(f.read_text())
        trees[mod] = tree
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                owner[node.name] = mod
    return owner, trees


def build_graph(trees, owner):
    """Add an edge caller -> callee for each call to a package-defined function."""
    g = nx.DiGraph()
    for mod, tree in trees.items():
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            caller = f"{mod}.{node.name}"
            g.add_node(caller, module=mod)
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    fn = sub.func
                    name = getattr(fn, "id", None) or getattr(fn, "attr", None)
                    if name in owner:
                        callee = f"{owner[name]}.{name}"
                        g.add_node(callee, module=owner[name])
                        g.add_edge(caller, callee)
    return g


def render(g, out_base="docs/callgraph"):
    os.makedirs(os.path.dirname(out_base), exist_ok=True)
    pos = nx.kamada_kawai_layout(g)
    colors = [MODULE_COLORS.get(g.nodes[n]["module"], "#777") for n in g.nodes]
    fig, ax = plt.subplots(figsize=(15, 10))
    nx.draw_networkx_edges(g, pos, ax=ax, edge_color="#999", arrows=True,
                           arrowsize=14, width=1.1, connectionstyle="arc3,rad=0.06")
    nx.draw_networkx_nodes(g, pos, ax=ax, node_color=colors, node_size=420, alpha=0.95)
    for n, (x, y) in pos.items():
        ax.text(x, y - 0.045, n, fontsize=7.2, ha="center", va="top",
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    # legend by module
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=c,
                      markersize=9, label=m) for m, c in MODULE_COLORS.items()
               if any(g.nodes[n]["module"] == m for n in g.nodes)]
    ax.legend(handles=handles, title="module", loc="upper left", fontsize=8, frameon=False)
    ax.axis("off")
    ax.set_title("Analysis pipeline — function call graph", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"{out_base}.png", dpi=300, bbox_inches="tight")
    fig.savefig(f"{out_base}.svg", bbox_inches="tight")

    lines = ["flowchart LR"]
    for u, v in g.edges:
        lines.append(f'    {u.replace(".", "_")}["{u}"] --> {v.replace(".", "_")}["{v}"]')
    Path(f"{out_base}.mmd").write_text("\n".join(lines) + "\n")
    print(f"wrote {out_base}.png, .svg, .mmd  ({g.number_of_nodes()} nodes, {g.number_of_edges()} edges)")


def main():
    files = [f for f in SRC.glob("*.py") if f.name != "__init__.py"]
    owner, trees = collect_defs(files)
    g = build_graph(trees, owner)
    render(g)


if __name__ == "__main__":
    main()
