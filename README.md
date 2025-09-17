# Biostuff

This repository includes utilities for visualising protein interaction pathways.

## VCP interaction graph

The file [`data/vcp_interactions.json`](data/vcp_interactions.json) describes the
VCP (p97) interaction network, including the primary interactors and their
relevant downstream functions.

Run the script below to generate an interactive, publication-ready pathway
visualisation that follows the requested arrow conventions (`--->` for
activation, `---|` for inhibition and `-----` for unknown/neutral effects). The
VCP → interactor edges also annotate the interaction mechanism underneath the
arrow label when the JSON provides one.

```bash
pip install -r requirements.txt
python generate_vcp_graph.py --input data/vcp_interactions.json --output output/vcp_interactions_graph.html
```

Open the resulting HTML file (`output/vcp_interactions_graph.html`) in a web
browser to explore the graph. Nodes are grouped into three tiers:

1. The query protein (VCP) in blue on the left.
2. Primary interactors in orange in the middle.
3. Functional outcomes in green on the right.

Edge colours reinforce the arrow semantics (green for activation, red for
inhibition and grey for unknown). Tooltips on nodes describe their roles, and
the hierarchical left-to-right layout keeps the pathway structure easy to read
while still allowing you to pan and zoom for closer inspection.
