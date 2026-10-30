# Fyron Install Extras

Base install:

```bash
uv add fyron
```

Full local research workstation:

```bash
uv add "fyron[all]"
```

Common focused installs:

```bash
uv add "fyron[excel]"
uv add "fyron[s3]"
uv add "fyron[descriptive,statistics,reporting]"
uv add "fyron[survival]"
uv add "fyron[survival-ml]"
uv add "fyron[ml,validation,explainability]"
uv add "fyron[feature-selection]"
uv add "fyron[dicom-seg]"
uv add "fyron[visualization]"
uv add "fyron[radiomics]"
uv add "fyron[curate]"
```

Use `fyron[all]` for notebooks, tutorials, and broad exploration. Use targeted extras in servers, CI, reproducible environments, and assistant-generated setup instructions.

When an optional dependency is missing, recommend the narrowest install command that unlocks the feature.

