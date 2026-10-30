# Fyron Curate

React/Tailwind gallery for quickly reviewing image cohorts. Drag a folder into the app, add a selection context for the review task, accept or reject samples, and export labels or a clean folder containing only accepted images. Source uploads are kept immutable.

## Install From Fyron

For data-science use, install the Fyron extra and launch the app through the unified CLI:

```bash
uv add "fyron[curate]"
fyron curate
```

Open `http://localhost:5174`.

Docker Desktop / Docker Compose must be running because Curate starts the frontend, backend API, and PostgreSQL as local containers.

Curate is a single-user local application without shared-server authentication.
Keep the default loopback port bindings. Do not expose these containers on a
network without an independently authenticated deployment.

Uploads preserve originals: a conflicting filename returns HTTP 409; an
identical re-upload preserves the image and review history. New DICOM series
and instances are merged into the cohort metadata. A reviewed series cannot
be extended; create a new cohort to review an expanded series. Upload batches
are limited to 128 MiB total and 32 MiB per file. After an interrupted upload,
retry the same batch before exporting or adding another batch. The browser
batches large folders automatically; keep the selection and choose Create cohort
again to resume after a failure. Malformed
metadata and missing source references block exports instead of dropping data.

Useful launch options:

```bash
fyron curate --no-build
fyron curate --foreground
fyron curate --open
```

## Run From This App Folder

```bash
docker compose up --build
```

Open `http://localhost:5174`.

The API runs on `http://localhost:4000`. API and frontend ports bind only to `127.0.0.1`; PostgreSQL has no published host port. Uploaded cohorts live in the `uploaded_cohorts` Docker volume, and clean exports live in the `clean_exports` Docker volume.

## Supported Files

Curate indexes PNG, JPEG/JPG, WebP, GIF, BMP, and TIFF/TIF files. It can also read DICOM folders directly. DICOM files are grouped by study and series, and each study appears as a card with one selectable thumbnail per series.

Direct DICOM preview support is intended for common uncompressed CT, MRI, X-ray, scout, and topogram exports. Other files in an uploaded folder are skipped. If a DICOM series uses a compressed transfer syntax that cannot be decoded in the local preview service, prepare PNG previews first.

## Prepare CT/MRI Previews

For NIfTI, MHA, NRRD, or compressed DICOM exports, convert the source data into PNG previews before reviewing. Fyron provides a preview-preparation command for this:

```bash
uv add "fyron[visualization,curate]"
fyron dataset-curate-previews \
  --input-dir /data/ct_or_mri_exports \
  --output-dir curate_previews
```

The command scans nested folders by default. For each 3D volume or DICOM series it writes middle axial, coronal, and sagittal PNG slices. For 2D images such as X-rays or topograms it writes one PNG. It also creates `manifest.csv` so outputs stay traceable to their source files.

Then open Curate and add a cohort from the generated folder:

```bash
fyron curate
```

Drop `curate_previews/` into the **Add cohort** dialog.

## Workflow

1. Drop an image or DICOM folder directly, or prepare PNG previews with `fyron dataset-curate-previews` when the source data needs conversion.
2. Start the app with `fyron curate`.
3. Create a cohort by dropping a folder into the **Add cohort** dialog.
4. Add an optional **Selection context** note, for example what anatomy, scan phase, quality, or exclusion rule reviewers should use.
5. Review the gallery. DICOM studies appear as cards with selectable series thumbnails. Click an image or series to toggle accepted/rejected.
6. Adjust thumbnail size, spacing, filter, sort, search, and **Image fit** as needed. Use **Fit** for landscape-heavy or portrait-heavy cohorts so thumbnails are not cropped.
7. Use preview or **Zen mode** for one-image-at-a-time review. Keyboard shortcuts are shared across gallery preview and Zen mode: `A` accepts, `D` rejects, right arrow moves next, left arrow moves previous, and `Esc` closes the focused view.
8. Select **Export CSV** after every sample is explicitly reviewed to download labels with `filename,status`, where status is `accepted` or `rejected`.
9. Select **Create clean folder** to copy accepted images into the export volume while preserving relative paths. Accepted DICOM series also copy their original source files into `dicom_series/`.

## Data Lifecycle

Curate keeps uploaded source files immutable. Cohort metadata, review state, selection context, and gallery settings are stored in PostgreSQL. Clean-folder export copies accepted files into the `clean_exports` Docker volume; it does not delete or rewrite the upload volume. Docker volumes persist across container restarts until you remove them explicitly.

## Review Context And Labels

The selection context is study-level guidance for reviewers. It is visible in normal grid review and Zen mode so acceptance decisions stay anchored to the cohort question. Keep it short, practical, and free of PHI.

CSV labels are intended for downstream audit, modeling, or folder reconciliation. Curate only enables the complete-cohort label export after all samples have an explicit accepted or rejected status.

## License

Current Curate source, including its frontend and backend, is available under
**CC BY-NC 4.0** for noncommercial use with attribution. Share the license link
and indicate changes when redistributing or adapting the material. Commercial
use beyond existing permissions requires separate permission from the rights holder.
See the [license](https://github.com/BitsandFlames/Fyron/blob/main/LICENSE).

Previously published MIT versions, including Beta 3, retain their MIT permissions.
Third-party components retain their own licenses and notices.
