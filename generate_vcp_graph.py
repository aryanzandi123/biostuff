#!/usr/bin/env python3
"""Generate an interactive pathway graph for the VCP interaction network."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable

from pyvis.network import Network

ARROW_SYMBOLS = {
    "activates": "--->",
    "inhibits": "---|",
    "unknown": "-----",
}

EDGE_COLORS = {
    "activates": "#2E8B57",  # sea green
    "inhibits": "#C0392B",   # pomegranate red
    "unknown": "#7F8C8D",    # concrete grey
}


def normalize_arrow(value: str | None) -> str:
    """Return a lower-case arrow keyword with unknown as fallback."""
    if not value:
        return "unknown"
    value = value.lower()
    return value if value in ARROW_SYMBOLS else "unknown"


def edge_label(arrow: str, mechanism: str | None = None, *, include_mechanism: bool) -> str:
    """Format the edge label including the mechanism where requested."""
    label = ARROW_SYMBOLS.get(arrow, ARROW_SYMBOLS["unknown"])
    if include_mechanism and mechanism and mechanism.lower() != "unknown":
        label = f"{label}\n[{mechanism.title()}]"
    return label


def edge_style(arrow: str) -> Dict[str, Any]:
    """Return visual styling options for an edge."""
    color = EDGE_COLORS.get(arrow, EDGE_COLORS["unknown"])
    options: Dict[str, Any] = {
        "color": color,
        "arrows": "to",
        "smooth": {"type": "cubicBezier", "roundness": 0.25},
        "font": {"size": 16, "align": "middle"},
        "width": 2,
    }
    if arrow == "unknown":
        options["dashes"] = True
    return options


def add_nodes(net: Network, names: Iterable[str], *, shape: str, color: str, level: int, title: str) -> None:
    """Add nodes to the network if they are not present already."""
    existing = {node["id"] for node in net.nodes}
    for name in names:
        if name not in existing:
            net.add_node(
                name,
                label=name,
                shape=shape,
                color=color,
                level=level,
                title=title.replace("{name}", name),
            )
            existing.add(name)


def build_network(data: Dict[str, Any]) -> Network:
    """Create the interactive network from the supplied JSON structure."""
    main = data["main"]
    interactors = data.get("interactors", [])

    net = Network(
        height="850px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#1f1f1f",
        cdn_resources="remote",
    )

    net.set_options(
        """
        {
          "layout": {
            "hierarchical": {
              "enabled": true,
              "direction": "LR",
              "sortMethod": "hubsize",
              "levelSeparation": 220,
              "nodeSpacing": 180
            }
          },
          "physics": {
            "hierarchicalRepulsion": {
              "centralGravity": 0.0,
              "springLength": 180,
              "springConstant": 0.01,
              "nodeDistance": 220,
              "damping": 0.12
            },
            "minVelocity": 0.75
          }
        }
        """
    )

    add_nodes(net, [main], shape="ellipse", color="#1f77b4", level=0, title="Query protein: {name}")

    for interactor in interactors:
        name = interactor["primary"]
        arrow = normalize_arrow(interactor.get("arrow"))
        mechanism = interactor.get("mechanism")

        add_nodes(net, [name], shape="ellipse", color="#ff7f0e", level=1, title="Primary interactor: {name}")

        interactor_edge_label = edge_label(arrow, mechanism, include_mechanism=True)
        options = edge_style(arrow)
        net.add_edge(main, name, label=interactor_edge_label, **options)

        functions = interactor.get("functions", [])
        function_names = [entry["function"] for entry in functions]
        add_nodes(net, function_names, shape="box", color="#2ca02c", level=2, title="Interactor function: {name}")

        for entry in functions:
            func_arrow = normalize_arrow(entry.get("arrow"))
            func_label = edge_label(func_arrow, None, include_mechanism=False)
            func_options = edge_style(func_arrow)
            net.add_edge(name, entry["function"], label=func_label, **func_options)

    return net


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an interactive pathway graph for the VCP network.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/vcp_interactions.json"),
        help="Path to the VCP interaction JSON file (default: data/vcp_interactions.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/vcp_interactions_graph.html"),
        help="Destination for the generated HTML graph (default: output/vcp_interactions_graph.html)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = json.loads(args.input.read_text())
    network = build_network(data)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    network.write_html(str(args.output))
    print(f"Graph written to {args.output}")


if __name__ == "__main__":
    main()
