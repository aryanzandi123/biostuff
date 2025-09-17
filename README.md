# Biostuff

This repository includes utilities for visualising protein interaction pathways.

## Interactive interaction graphs

The script [`generate_interaction_graph.py`](generate_interaction_graph.py)
transforms curated JSON summaries into polished, radial pathway maps. Each
graph is rendered as an interactive HTML file that can be opened directly in a
browser for panning, zooming, node highlighting and tooltip inspection.

Key styling details:

* The query protein sits in the centre, with primary interactors forming the
  inner ring and functional outcomes gracefully fanning outwards.
* Edge colours and arrow heads reinforce the requested semantics (`--->`
  activators, `---|` inhibitors and `-----` unknown effects). Query → interactor
  edges additionally display the high-level mechanism underneath the arrow when
  it is provided in the JSON.
* Gentle shadows, curated colour palettes and curved connections keep the graph
  legible even for dense neighbourhoods.

### Usage

```bash
pip install -r requirements.txt

# VCP (p97) network
python generate_interaction_graph.py \
  --input data/vcp_interactions.json \
  --output output/vcp_interactions_graph.html \
  --title "VCP signalling landscape"

# ATXN3 network
python generate_interaction_graph.py \
  --input data/atxn3_interactions.json \
  --output output/atxn3_interactions_graph.html \
  --title "ATXN3 interaction constellation"
```

Both resulting HTML files live in the `output/` directory. Open them in any
modern browser to explore the network; the visual remains completely
self-contained and requires no additional build tooling.
