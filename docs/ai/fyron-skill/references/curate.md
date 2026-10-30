# Fyron Curate Agent Notes

Curate is Fyron's local image cohort review app. Use it when the user needs to quickly review folders, reject bad images, and create a clean accepted folder.

Install and start:

```bash
uv add "fyron[curate]"
fyron curate
```

Prepare CT/MRI/X-ray previews first:

```bash
fyron dataset-curate-previews --input-dir imaging_exports/ --output-dir curate_previews/
fyron curate
```

Supported review inputs:

- PNG, JPEG/JPG, WebP, GIF, BMP, and supported TIFF previews.
- Nested image folders with relative paths preserved.
- DICOM directories, grouped by study and series in the app.
- CT/MRI/X-ray/topogram folders converted to PNG preview folders through `dataset-curate-previews`.

Curate behavior:

- Source uploads stay immutable.
- Review state is stored in PostgreSQL.
- Clean export copies accepted files and preserves relative structure.
- DICOM study/series review can export selected original series files.

Assistant rules:

- Prefer clean-folder export over physical deletion.
- Explain that Docker Desktop / Docker Compose is required.
- Do not promise regulatory audit behavior.
- For medical volumes, recommend preview generation unless the user specifically wants direct DICOM folder review.

