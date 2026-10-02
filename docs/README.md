# docs/

Reference material and decision records that support the catalog but don't
belong in the root [`README.md`](../README.md) or `CLAUDE.md`.

There is no index of the files here, deliberately. The directory listing
is the index, and it cannot fall behind the way a hand-kept list does.
What each location means:

| Location | What lives there | How it ages |
|---|---|---|
| `catalog.md` | Auto-generated catalog inventory: every material, every property, every source citation, every confidence level. Regenerate with `uv run python scripts/generate_catalog_doc.py`; never hand-edit. | Mechanically, on every regeneration. Cannot drift from the code it summarizes. |
| [`adr/`](adr/) | One architecture decision per file, `NNNN-kebab-title.md`, with `Status` / `Context` / `Decision` / `Consequences`. | Not at all. A record is superseded by a later one, never rewritten, so it states what was true when it was accepted. |

## Adding to this directory

- Recording a **decision** and the reasoning behind it: write an ADR.
- Explaining **why** the catalog is shaped as it is, where that reasoning
  is too broad for one docstring or one `CLAUDE.md` bullet: extend
  `catalog.md`'s neighbors, or open an issue if it's really a proposal.
- Anything that is neither, such as a dated investigation, a sourcing
  attempt that didn't pan out, or a superseded plan: it belongs in a
  GitHub issue, not in this directory.

Name a file so the listing reads as its own index. An ADR states its
decision in its filename, not just its number.

**Do not restate the catalog in prose.** A material's properties, units,
sources, and confidence levels belong in the catalog files under
`src/emergent_matter_materials/catalog/`, where they are validator-enforced
and reviewed with the change that moves them. `catalog.md` is the one
generated exception: it's a rendering of that data, never hand-authored.

The test before adding a paragraph: **would this need editing if someone
corrected a `PropertyValue`?** If yes, it belongs in the catalog files
instead.

A document that reads as a proposal is a sign the decision hasn't been
recorded yet. Convert it into an ADR once the decision is made.
