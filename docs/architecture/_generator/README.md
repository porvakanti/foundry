# Diagram generator

The five architecture diagrams are generated, not hand-drawn, so they stay consistent with each
other and can be regenerated when the architecture moves. This folder is self-contained: copy it
into another repository and it works there.

## Run it

```bash
pip install -r requirements.txt
python build.py                 # writes SVG + 2x PNG into ../diagrams
DIAGRAM_OUT=/some/path python build.py
```

The build is reproducible: the same inputs produce byte-identical SVGs, so a rebuild only shows a
diff when something actually changed.

## Files

| File | What it is |
| --- | --- |
| `gcpkit.py` | The drawing kit. Containers, service icons, connectors, step markers, legends. |
| `d01_logical.py` … `d05_sequence.py` | One script per diagram. Pure layout: coordinates and content. |
| `build.py` | Runs every `dNN_*.py`, then exports 2x PNGs if cairosvg is present. |

## Icons

`gcpkit._icon_root()` resolves the icon set in this order:

1. `$DIAGRAM_ICONS`, if it points at a directory
2. the `resources/` folder shipped with the `diagrams` pip package
3. a vendored `./icons` folder

Icons are referenced by relative path (`gcp/compute/run.png`, `azure/identity/azure-active-directory.png`),
so if Vodafone holds a licensed Google Cloud icon pack, point `DIAGRAM_ICONS` at it and nothing in
the layout code changes. Icon bytes are base64-embedded into the SVG, so the output travels as a
single file.

## The conventions the kit enforces

These are what make the output read like a cloud vendor's reference architecture rather than a
box diagram. Keep to them when adding a diagram.

- **Containment carries the meaning.** `cloud()` for the provider boundary, `project()` for a
  project, `group()` for anything else. A dashed red group is a security perimeter; a dashed grey
  one is a logical grouping.
- **Services are icons with labels, never boxes.** `icon()` draws the product icon with its name
  beneath. Boxes are for containers and for text panels only.
- **Connectors are typed by colour** and the diagram carries a legend saying what each colour
  means. Do not introduce a new colour without adding it to the legend.
- **Numbered steps** (`step()`) mark a request path, and the narrative that explains them sits on
  the same canvas.
- **Colour-code the review surface** when a diagram will be read by an approver: what is new
  versus what is inherited from an already-approved platform.
- **List items use `litem()`, which draws a small dot.** Do not use a dash, hyphen or box-drawing
  character as a bullet: rendered at diagram scale they read as stray long hyphens, and reviewers
  correctly flag them as machine-generated.
- **Leave 18px between a group's subtitle and its first child.** The subtitle sits at `y+34`; a
  child placed at `y+28` will overlap it. This is the single most common layout bug.

## Adding a diagram

Copy the closest `dNN_*.py`, change `OUT`, lay it out, run `build.py`. Check the rendered PNG
before committing: the kit does not detect overlapping text, so read the output rather than
trusting the code.
