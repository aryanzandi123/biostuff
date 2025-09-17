#!/usr/bin/env python3
"""Generate a polished interactive protein interaction network."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pyvis.network import Network

ARROW_SYMBOLS: Dict[str, str] = {
    "activates": "--->",
    "inhibits": "---|",
    "unknown": "-----",
}

EDGE_COLORS: Dict[str, str] = {
    "activates": "#2a9d8f",
    "inhibits": "#e76f51",
    "unknown": "#8d99ae",
}

ARROW_TYPES: Dict[str, Dict[str, Any]] = {
    "activates": {"to": {"enabled": True, "type": "arrow", "scaleFactor": 0.9}},
    "inhibits": {"to": {"enabled": True, "type": "bar", "scaleFactor": 0.9}},
    "unknown": {"to": {"enabled": True, "type": "circle", "scaleFactor": 0.75}},
}

ARROW_VERBS: Dict[str, str] = {
    "activates": "activates",
    "inhibits": "inhibits",
    "unknown": "modulates",
}


def normalize_arrow(value: str | None) -> str:
    """Return a supported arrow keyword with "unknown" as the fallback."""
    if not value:
        return "unknown"
    value = value.lower().strip()
    return value if value in ARROW_SYMBOLS else "unknown"


def format_mechanism(mechanism: str | None) -> str | None:
    if not mechanism:
        return None
    mechanism = mechanism.strip()
    if not mechanism or mechanism.lower() == "unknown":
        return None
    return mechanism.title()


def arrow_label(arrow: str, mechanism: str | None, include_mechanism: bool) -> str:
    label = ARROW_SYMBOLS.get(arrow, ARROW_SYMBOLS["unknown"])
    if include_mechanism and mechanism:
        label = f"{label}\n[{mechanism}]"
    return label


def arrow_title(source: str, target: str, arrow: str, mechanism: str | None) -> str:
    verb = ARROW_VERBS.get(arrow, "modulates")
    description = f"<b>{source}</b> {verb} <b>{target}</b>"
    if mechanism:
        description += f"<br/><span style='color:#4a4a4a'>Mechanism: {mechanism}</span>"
    return description


def extract_payload(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the {"main", "interactors"} payload regardless of wrapper."""
    if "main" in raw and "interactors" in raw:
        return raw
    if "final_json" in raw and isinstance(raw["final_json"], dict):
        candidate = raw["final_json"]
        if "main" in candidate and "interactors" in candidate:
            return candidate
    if "ctx_json" in raw and isinstance(raw["ctx_json"], dict):
        ctx = raw["ctx_json"]
        if "final_json" in ctx and isinstance(ctx["final_json"], dict):
            candidate = ctx["final_json"]
            if "main" in candidate and "interactors" in candidate:
                return candidate
    raise ValueError("Input JSON does not include a recognisable interaction payload.")


def polar_to_cartesian(radius: float, angle_deg: float) -> Tuple[float, float]:
    angle_rad = math.radians(angle_deg)
    x = radius * math.cos(angle_rad)
    y = radius * math.sin(angle_rad)
    return x, y


def interactor_offsets(count: int, max_offset: float) -> List[float]:
    if count <= 0:
        return []
    if count == 1 or max_offset <= 0:
        return [0.0]
    step = min(28.0, max(12.0, (2.0 * max_offset) / (count - 1)))
    start = -step * (count - 1) / 2.0
    offsets = [start + idx * step for idx in range(count)]
    clipped = [max(-max_offset, min(max_offset, offset)) for offset in offsets]
    return clipped


def build_network(payload: Dict[str, Any], *, title: str, include_mechanism: bool) -> Network:
    main = payload["main"]
    interactors: List[Dict[str, Any]] = payload.get("interactors", [])

    net = Network(
        height="900px",
        width="100%",
        directed=True,
        bgcolor="#f4f7fb",
        font_color="#1c1c1c",
        cdn_resources="remote",
    )
    net.toggle_physics(False)
    net.set_options(
        """
        {
          "interaction": {
            "hover": true,
            "tooltipDelay": 150,
            "dragNodes": false,
            "multiselect": false,
            "zoomView": true
          },
          "layout": {
            "improvedLayout": false
          },
          "nodes": {
            "shadow": {
              "enabled": true,
              "size": 18,
              "x": 0,
              "y": 3
            }
          },
          "edges": {
            "shadow": {
              "enabled": true,
              "size": 8,
              "x": 0,
              "y": 0
            },
            "smooth": false,
            "selectionWidth": 2
          },
          "physics": {
            "enabled": false
          }
        }
        """
    )

    net.heading = title

    query_style = {
        "shape": "circle",
        "size": 58,
        "color": {"background": "#264653", "border": "#0d1b2a"},
        "font": {"size": 30, "color": "#ffffff", "face": "Inter"},
        "borderWidth": 3,
    }
    interactor_style = {
        "shape": "circle",
        "size": 34,
        "color": {"background": "#2a9d8f", "border": "#1b7f6a"},
        "font": {"size": 22, "color": "#ffffff", "face": "Inter"},
        "borderWidth": 2,
    }
    function_style = {
        "shape": "box",
        "size": 20,
        "color": {"background": "#e9c46a", "border": "#c59b2a"},
        "font": {"size": 20, "color": "#1c1c1c", "face": "Inter"},
        "borderWidth": 2,
        "shapeProperties": {"borderRadius": 6},
        "widthConstraint": {"maximum": 280},
    }

    net.add_node(
        main,
        label=main,
        title=f"<b>{main}</b><br/>Query protein",
        x=0,
        y=0,
        physics=False,
        fixed={"x": True, "y": True},
        **query_style,
    )

    if not interactors:
        return net

    interactor_radius = 320.0
    function_radius = 550.0
    function_radius_variation = 80.0
    angle_step = 360.0 / len(interactors)
    start_angle = -90.0

    for idx, interactor in enumerate(interactors):
        name = interactor.get("primary", f"Interactor {idx + 1}")
        arrow = normalize_arrow(interactor.get("arrow"))
        mechanism = format_mechanism(interactor.get("mechanism"))

        angle = start_angle + idx * angle_step
        x, y = polar_to_cartesian(interactor_radius, angle)

        net.add_node(
            name,
            label=name,
            title=(
                f"<b>{name}</b><br/>{main} {ARROW_VERBS.get(arrow, 'modulates')} this interactor"
                + (f"<br/>Mechanism: {mechanism}" if mechanism else "")
            ),
            x=x,
            y=y,
            physics=False,
            fixed={"x": True, "y": True},
            **interactor_style,
        )

        edge_label = arrow_label(arrow, mechanism, include_mechanism)
        edge_title = arrow_title(main, name, arrow, mechanism)
        net.add_edge(
            main,
            name,
            label=edge_label,
            color=EDGE_COLORS.get(arrow, EDGE_COLORS["unknown"]),
            arrows=ARROW_TYPES.get(arrow, ARROW_TYPES["unknown"]),
            width=4,
            font={"size": 20, "face": "Inter", "color": "#2f2f2f"},
            title=edge_title,
        )

        functions: List[Dict[str, Any]] = interactor.get("functions", [])
        if not functions:
            continue

        max_offset = angle_step * 0.4
        offsets = interactor_offsets(len(functions), max_offset)

        for func_idx, (function, offset) in enumerate(zip(functions, offsets)):
            func_name = function.get("function", f"Function {func_idx + 1}")
            func_arrow = normalize_arrow(function.get("arrow"))

            radius_adjustment = (
                function_radius_variation * (abs(offset) / max_offset) if max_offset else 0.0
            )
            func_radius = function_radius + radius_adjustment
            fx, fy = polar_to_cartesian(func_radius, angle + offset)

            if not any(node["id"] == func_name for node in net.nodes):
                net.add_node(
                    func_name,
                    label=func_name,
                    title=(
                        f"<b>{func_name}</b><br/>{name} {ARROW_VERBS.get(func_arrow, 'modulates')} this function"
                    ),
                    x=fx,
                    y=fy,
                    physics=False,
                    fixed={"x": True, "y": True},
                    **function_style,
                )

            func_edge_label = arrow_label(func_arrow, None, False)
            func_edge_title = arrow_title(name, func_name, func_arrow, None)
            if abs(offset) < 1e-6:
                smooth: Any | bool = False
            elif offset > 0:
                smooth = {"type": "curvedCW", "roundness": 0.15}
            else:
                smooth = {"type": "curvedCCW", "roundness": 0.15}

            net.add_edge(
                name,
                func_name,
                label=func_edge_label,
                color=EDGE_COLORS.get(func_arrow, EDGE_COLORS["unknown"]),
                arrows=ARROW_TYPES.get(func_arrow, ARROW_TYPES["unknown"]),
                width=3,
                font={"size": 18, "face": "Inter", "color": "#2f2f2f"},
                title=func_edge_title,
                smooth=smooth,
            )

    return net


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an interactive, presentation-ready protein interaction graph.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/vcp_interactions.json"),
        help="Path to the interaction JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/vcp_interactions_graph.html"),
        help="Destination for the generated HTML graph.",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Optional custom heading for the rendered graph.",
    )
    parser.add_argument(
        "--no-mechanism-labels",
        dest="mechanism_labels",
        action="store_false",
        help="Hide mechanism annotations on query → interactor edges.",
    )
    parser.set_defaults(mechanism_labels=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw = json.loads(args.input.read_text())
    payload = extract_payload(raw)
    title = args.title or f"{payload['main']} interaction landscape"

    network = build_network(payload, title=title, include_mechanism=args.mechanism_labels)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    network.write_html(str(args.output), notebook=False)
    print(f"Graph written to {args.output}")


if __name__ == "__main__":
    main()
