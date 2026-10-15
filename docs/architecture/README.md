# Agent Marketplace: architecture and governance pack

Everything required for the AI Portfolio Board, the Security assessment, the Privacy assessment
and Vodafone Group review. Read in this order.

| # | Artefact | Audience | What it is for |
| --- | --- | --- | --- |
| 1 | `HLD-agent-marketplace.md` | All reviewers | The submission. Scope, architecture, security, data, AI usage, well-architected review, open items. |
| 2 | `diagrams/01-logical-architecture.svg` | Board, architects | The nine domain services and where the boundaries sit. Read before the deployment view. |
| 3 | `diagrams/02-deployment-architecture.svg` | Architects, security | What is actually deployed, in which project, behind which control. Colour-coded by review surface. |
| 4 | `diagrams/03-data-flow.svg` | Security, privacy | Ten numbered flows with data, classification, purpose and retention per flow. |
| 5 | `diagrams/04-catalogue-data-lifecycle.svg` | Architects, data governance | How agent information enters the catalogue and how it reaches the UI. |
| 6 | `diagrams/05-sequence-flows.svg` | Security | Three request sequences end to end. Proves the frontend has no data path. |
| 7 | `DPIA-agent-marketplace.md` | Privacy | Personal data inventory, lawful basis, pseudonymisation, retention, subject rights, risk register. |
| 8 | `security-control-matrix.md` | Security | Control by control: inherited from AIB, or new for this use case. Includes declared gaps. |
| 9 | `api-contract.md` | Security, architects | The frontend-to-backend contract. Shows the tier split is a real boundary. |
| 10 | `schema/bigquery-ddl.sql` | Data governance, privacy | The executable schema, with purpose and retention declared per table and column. |

PNG exports of every diagram sit beside the SVGs, at 2x, for pasting into the board pack.

## The one-line argument

The marketplace is a catalogue and a front door, not a runtime. No supplier, contract,
purchase-order, invoice, price or spend data enters it on any path. That exclusion is what makes
the risk profile low, and it is an architectural property rather than a policy promise: there is
no connection, credential or network path to those systems.

## Review surface

The web tier, the backend service, the data model and the service perimeter are new. The
orchestration boundary, Responsible AI screening, model serving and the identity chain are
existing approved AIB components whose controls this use case inherits. Diagram 02 colour-codes
which is which; `security-control-matrix.md` sets it out control by control.

## What still needs an owner

Nine items are marked CONFIRM in the HLD and collected in its section 10. Four of them block the
assessment: region, the gateway interface and prompt-logging policy, lawful basis, and the EU AI
Act classification.

## Regenerating the diagrams

The diagrams are generated, not hand-drawn, so they stay consistent when the architecture moves.
Sources are the `n*.py` / `g*.py` scripts used to produce them, built on a small SVG kit that
follows Google Cloud diagramming conventions and the official product icon set. Ask the AI Domain
team for the generator if a change is needed.
