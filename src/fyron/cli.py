"""Unified command-line interface for Fyron."""

from __future__ import annotations

import argparse
import json
import os
import runpy
import time
from pathlib import Path
from typing import Any

import pandas as pd

from fyron.console import configure_logging, console_message, format_duration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fyron", description="Fyron clinical data science toolkit")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug logging")
    parser.add_argument("--quiet", action="store_true", help="Suppress nonessential CLI messages")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument("--json-log", action="store_true", help="Emit JSON-formatted logs")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bars for supported commands")
    sub = parser.add_subparsers(dest="command", required=True)

    banner = sub.add_parser("banner", help="Print the Fyron terminal banner")
    banner.add_argument("--no-color", dest="banner_no_color", action="store_true", help="Disable ANSI colors")
    banner.add_argument("--no-version", action="store_true", help="Hide the version line")
    banner.add_argument("--theme", choices=("bf", "plain", "mono"), default="bf", help="Banner theme")
    banner.set_defaults(func=_cmd_banner)
    spark = sub.add_parser("spark", help="Print the Fyron easter egg banner")
    spark.add_argument("--no-color", dest="banner_no_color", action="store_true", help="Disable ANSI colors")
    spark.add_argument("--no-version", action="store_true", help="Hide the version line")
    spark.add_argument("--theme", choices=("bf", "plain", "mono"), default="bf", help="Banner theme")
    spark.set_defaults(func=_cmd_banner)
    docs = sub.add_parser("docs-build", help="Build the BF-native documentation site")
    docs.add_argument("--script", default="scripts/build_docs.py")
    docs.set_defaults(func=_cmd_docs_build)
    curate = sub.add_parser("curate", help="Start the Fyron image curation web app")
    curate.add_argument("--app-dir", help="Path to apps/image-curator when running outside a Fyron source checkout")
    curate.add_argument("--no-build", action="store_true", help="Start without rebuilding Docker images")
    curate.add_argument("--foreground", action="store_true", help="Run Docker Compose in the foreground")
    curate.add_argument("--open", action="store_true", help="Open the app URL in the default browser")
    curate.set_defaults(func=_cmd_curate)

    _add_fhir_rest_parser(sub)
    _add_fhir_build_bundle_parser(sub)
    _add_dicom_download_parser(sub)
    from fyron.documents._cli import _add_parser as _add_document_download_parser
    _add_document_download_parser(sub)
    _add_dicom_seg_parser(sub)
    _add_synthetic_dicom_parser(sub)
    _add_boa_extract_parser(sub)
    _add_boa_radiomics_parser(sub)
    _add_audit_manifest_parser(sub)
    _add_imaging_qc_parser(sub)
    _add_dataset_curate_previews_parser(sub)
    _add_dataset_nnunetv2_parser(sub)
    _add_dataset_yolo_classify_parser(sub)
    _add_dataset_yolo_detect_parser(sub)

    args = parser.parse_args(argv)
    configure_logging(
        "DEBUG" if args.verbose else "WARNING" if args.quiet else "INFO",
        color=not args.no_color,
        json=args.json_log,
    )
    args.color = not args.no_color
    started = time.perf_counter()
    args.started_at = started
    try:
        return int(args.func(args) or 0)
    finally:
        args.duration = time.perf_counter() - started


def _add_fhir_rest_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("fhir-rest", help="Extract FHIR REST resources to CSV/JSON")
    p.add_argument("--base-url", default=os.environ.get("FHIR_BASE_URL"))
    p.add_argument("--auth-url", default=os.environ.get("FHIR_AUTH_URL"))
    p.add_argument("--bearer-token", default=os.environ.get("FHIR_TOKEN"))
    p.add_argument("--resource", required=True)
    p.add_argument("--param", action="append", default=[], help="FHIR query parameter as key=value")
    p.add_argument("--params-json")
    p.add_argument("--max-pages", type=int, default=1)
    p.add_argument("--processes", type=int, default=1)
    p.add_argument("--output", required=True)
    p.add_argument("--format", choices=("csv", "json"), default="csv")
    p.add_argument("--fhir-paths")
    p.add_argument("--flatten", action="store_true")
    p.add_argument("--log-request-urls", action="store_true")
    p.add_argument("--input", help="CSV for row-wise queries")
    p.add_argument("--column-map", action="append", default=[], help="FHIR parameter to CSV column as param=column")
    p.add_argument("--include-column-map-columns", action="store_true")
    p.set_defaults(func=_cmd_fhir_rest)


def _add_fhir_build_bundle_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("fhir-build-bundle", help="Build FHIR JSON bundles from CSV tables")
    p.add_argument("--input", required=True, help="Input CSV table")
    p.add_argument("--mapping", required=True, help="FHIR mapping JSON")
    p.add_argument("--resource", required=True, choices=("Observation", "Condition", "DocumentReference", "ImagingMeasurement"))
    p.add_argument("--subject-col", required=True)
    p.add_argument("--id-col")
    p.add_argument("--study-uid-col")
    p.add_argument("--series-uid-col")
    p.add_argument("--bundle-type", choices=("collection", "transaction"), default="collection")
    p.add_argument("--transaction-method", choices=("POST", "PUT"), default="POST")
    p.add_argument("--if-none-exist")
    p.add_argument("--output", required=True)
    p.add_argument("--summary-json")
    p.add_argument("--validation-json")
    p.add_argument("--submit", action="store_true")
    p.add_argument("--base-url", default=os.environ.get("FHIR_BASE_URL"))
    p.add_argument("--bearer-token", default=os.environ.get("FHIR_TOKEN"))
    p.set_defaults(func=_cmd_fhir_build_bundle)


def _add_dicom_download_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("dicom-download", help="Download DICOMweb studies or series")
    p.add_argument("--dicom-web-url", default=os.environ.get("DICOM_WEB_URL"))
    p.add_argument("--dicom-user", default=os.environ.get("DICOM_USER"))
    p.add_argument("--dicom-password", default=os.environ.get("DICOM_PASSWORD"))
    p.add_argument("--study-uid")
    p.add_argument("--series-uid", default=None)
    p.add_argument("--csv")
    p.add_argument("--study-col", default="study_instance_uid")
    p.add_argument("--series-col", default="series_instance_uid")
    p.add_argument("--full-study", action="store_true")
    p.add_argument("--output-dir", default="dicom_out")
    p.add_argument("--output-format", default="nifti")
    p.add_argument("--compression", action="store_true")
    p.add_argument("--processes", type=int, default=1)
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--manifest", action="store_true")
    p.add_argument("--study-layout", choices=("hierarchical", "flat"), default="hierarchical")
    p.add_argument("--study-folder-name", default=None)
    p.add_argument("--study-folder-col", default=None)
    p.add_argument("--no-study-manifest", action="store_true")
    p.add_argument("--results-csv", default=None)
    p.set_defaults(func=_cmd_dicom_download)


def _add_dicom_seg_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("dicom-seg", help="Write a DICOM SEG object")
    p.add_argument("--mask", required=True)
    p.add_argument("--source-dicom", required=True)
    p.add_argument("--segments", required=True, help="JSON list of segment descriptions")
    p.add_argument("--output", required=True)
    p.add_argument("--series-description", default="Fyron DICOM SEG")
    p.add_argument("--algorithm-name", default="Fyron")
    p.add_argument("--algorithm-type", default="AUTOMATIC")
    p.add_argument("--manufacturer", default="Bits & Flames")
    p.add_argument("--validate", action="store_true", help="Validate and print a DICOM SEG summary after export")
    p.add_argument("--summary-json", help="Write DICOM SEG validation summary JSON after export")
    p.set_defaults(func=_cmd_dicom_seg)


def _add_synthetic_dicom_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("synthetic-dicom", help="Write a synthetic DICOM series from a NIfTI volume")
    p.add_argument("--volume", required=True)
    p.add_argument("--reference-dicom")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--patient-id", default="SYNTHETIC")
    p.add_argument("--series-description", default="Synthetic Fyron volume")
    p.add_argument("--manifest-csv", "--manifest", dest="manifest_csv")
    p.set_defaults(func=_cmd_synthetic_dicom)


def _add_boa_extract_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("boa-extract", help="Extract BOA cohort features")
    p.add_argument("--cohort-folder", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--include-body-regions", action="store_true")
    p.add_argument("--include-total", action="store_true")
    p.add_argument("--include-aortic-experimental", action="store_true")
    p.add_argument("--workers", "--num-workers", dest="workers", type=int, default=1)
    p.set_defaults(func=_cmd_boa_extract)


def _add_boa_radiomics_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("boa-radiomics", help="Extract BOA radiomics features")
    p.add_argument("--cohort-folder", required=True)
    p.add_argument("--segmentation", choices=("total", "body_regions"), default="total")
    p.add_argument("--output", required=True)
    p.add_argument("--workers", "--num-workers", dest="workers", type=int, default=1)
    p.set_defaults(func=_cmd_boa_radiomics)


def _add_audit_manifest_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("audit-manifest", help="Write a Fyron provenance manifest")
    p.add_argument("--title")
    p.add_argument("--input", action="append", default=[])
    p.add_argument("--output", action="append", default=[])
    p.add_argument("--parameter", "--param", dest="parameter", action="append", default=[], help="Manifest parameter as key=value")
    p.add_argument("--notes")
    p.add_argument("--write", required=True)
    p.set_defaults(func=_cmd_audit_manifest)


def _add_imaging_qc_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("imaging-qc", help="Run local imaging QC summaries")
    p.add_argument("--dicom-dir")
    p.add_argument("--nifti", action="append", default=[])
    p.add_argument("--mask")
    p.add_argument("--output", required=True)
    p.add_argument("--format", choices=("csv", "json"), default="csv")
    p.set_defaults(func=_cmd_imaging_qc)


def _add_dataset_curate_previews_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("dataset-curate-previews", help="Prepare PNG previews for Fyron Curate")
    p.add_argument("--input-dir", required=True, help="Directory with CT/MRI volumes, DICOM series, or 2-D images")
    p.add_argument("--output-dir", required=True, help="Curate-ready output image folder")
    p.add_argument("--no-recursive", action="store_true", help="Do not scan nested folders")
    p.add_argument("--no-dicom", action="store_true", help="Skip DICOM series discovery")
    p.add_argument("--no-image-files", action="store_true", help="Skip standalone NIfTI/MHA/NRRD/raster files")
    p.add_argument("--panel-width", type=int, default=384, help="Output PNG width in pixels")
    p.add_argument("--window-center", type=float, help="Optional fixed grayscale window center")
    p.add_argument("--window-width", type=float, help="Optional fixed grayscale window width")
    p.add_argument("--percentile-clip", default="1,99", help="Auto-window percentiles as low,high")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing preview PNGs")
    p.add_argument("--manifest-csv", help="Optional manifest CSV path")
    p.set_defaults(func=_cmd_dataset_curate_previews)


def _add_dataset_nnunetv2_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("dataset-nnunetv2", help="Prepare an nnU-Net v2 segmentation dataset")
    p.add_argument("--manifest", required=True, help="Input CSV or JSON manifest")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--dataset-id", required=True, type=int)
    p.add_argument("--dataset-name", required=True)
    p.add_argument("--image-col", default="image_path")
    p.add_argument("--label-col", default="label_path")
    p.add_argument("--case-id-col", default="case_id")
    p.add_argument("--split-col", default="split")
    p.add_argument("--copy-mode", choices=("copy", "symlink", "move"), default="copy")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--output-manifest", help="Optional CSV/JSON manifest of written files")
    p.set_defaults(func=_cmd_dataset_nnunetv2)


def _add_dataset_yolo_classify_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("dataset-yolo-classify", help="Prepare a YOLO classification dataset")
    p.add_argument("--manifest", required=True, help="Input CSV or JSON manifest")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--image-col", default="image_path")
    p.add_argument("--class-col", default="class")
    p.add_argument("--split-col", default="split")
    p.add_argument("--sample-id-col")
    p.add_argument("--image-format", default="png", choices=("png", "jpg", "jpeg"))
    p.add_argument("--copy-mode", choices=("copy", "symlink", "move"), default="copy")
    p.add_argument("--nifti-slice", default="middle")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--output-manifest", help="Optional CSV/JSON manifest of written files")
    p.set_defaults(func=_cmd_dataset_yolo_classify)


def _add_dataset_yolo_detect_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("dataset-yolo-detect", help="Prepare a YOLO object-detection dataset")
    p.add_argument("--manifest", required=True, help="Input CSV or JSON manifest")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--image-col", default="image_path")
    p.add_argument("--class-col", default="class")
    p.add_argument("--split-col", default="split")
    p.add_argument("--bbox-cols", default="x_min,y_min,x_max,y_max")
    p.add_argument("--image-width-col")
    p.add_argument("--image-height-col")
    p.add_argument("--sample-id-col")
    p.add_argument("--image-format", default="png", choices=("png", "jpg", "jpeg"))
    p.add_argument("--copy-mode", choices=("copy", "symlink", "move"), default="copy")
    p.add_argument("--nifti-slice", default="middle")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--output-manifest", help="Optional CSV/JSON manifest of written files")
    p.set_defaults(func=_cmd_dataset_yolo_detect)


def _cmd_banner(args: argparse.Namespace) -> int:
    from fyron.banner import print_banner

    if not args.quiet:
        print_banner(color=args.color and not args.banner_no_color, include_version=not args.no_version, theme=args.theme)
    return 0


def _cmd_docs_build(args: argparse.Namespace) -> int:
    runpy.run_path(str(Path(args.script)), run_name="__main__")
    _emit(args, "Built Fyron docs.", outputs=["site/"])
    return 0


def _cmd_curate(args: argparse.Namespace) -> int:
    from fyron.curate import start_curator

    return start_curator(
        app_dir=args.app_dir,
        build=not args.no_build,
        detached=not args.foreground,
        open_browser=args.open,
        color=args.color,
        quiet=args.quiet,
    )


def _cmd_fhir_rest(args: argparse.Namespace) -> int:
    from fyron import FHIRRestClient

    params = _parse_key_values(args.param)
    if args.params_json:
        params.update(_read_json(args.params_json))
    fhir_paths = _read_fhir_paths(args.fhir_paths)
    client = FHIRRestClient(
        base_url=args.base_url,
        auth_url=args.auth_url,
        bearer_token=args.bearer_token,
        num_processes=args.processes,
        log_request_urls=args.log_request_urls,
    )
    mode = "flatten" if args.flatten else "flatten"
    if args.input:
        df_in = pd.read_csv(args.input)
        result = client.search_df_from(
            df_in,
            resource_type=args.resource,
            column_map=_parse_key_values(args.column_map),
            params=params,
            max_pages=args.max_pages,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=args.processes > 1,
            include_column_map_columns=args.include_column_map_columns,
        )
    else:
        result = client.search_df(
            resource_type=args.resource,
            params=params,
            max_pages=args.max_pages,
            fhir_paths=fhir_paths,
            mode=mode,
            use_multiprocessing=args.processes > 1,
        )
    _write_table_result(result, args.output, args.format)
    _emit(args, f"Wrote FHIR REST output to {args.output}")
    return 0


def _cmd_fhir_build_bundle(args: argparse.Namespace) -> int:
    from fyron import FHIRRestClient
    from fyron.fhir.mapping import build_bundle_from_dataframe, read_fhir_mapping

    if args.submit and args.bundle_type != "transaction":
        raise SystemExit("--submit requires --bundle-type transaction")
    result = build_bundle_from_dataframe(
        pd.read_csv(args.input),
        args.resource,
        read_fhir_mapping(args.mapping),
        subject_col=args.subject_col,
        id_col=args.id_col,
        study_uid_col=args.study_uid_col,
        series_uid_col=args.series_uid_col,
        bundle_type=args.bundle_type,
        transaction_method=args.transaction_method,
        if_none_exist=args.if_none_exist,
    )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result["bundle"], indent=2, default=str), encoding="utf-8")
    if args.summary_json:
        Path(args.summary_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.summary_json).write_text(json.dumps(result["summary"], indent=2, default=str), encoding="utf-8")
    if args.validation_json:
        Path(args.validation_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.validation_json).write_text(json.dumps(result["validation"], indent=2, default=str), encoding="utf-8")
    if args.submit:
        if not args.base_url:
            raise SystemExit("FHIR_BASE_URL is required or pass --base-url.")
        write_result = FHIRRestClient(base_url=args.base_url, bearer_token=args.bearer_token).submit_bundle(result["bundle"])
        _emit(args, json.dumps(write_result.__dict__, indent=2, default=str), level="info")
    else:
        _emit(args, f"Wrote FHIR {args.bundle_type} Bundle with {result['summary']['entry_count']} entries to {args.output}", outputs=[args.output])
    return 0


def _cmd_dicom_download(args: argparse.Namespace) -> int:
    from fyron.dicom import DICOMDownloader

    if not args.dicom_web_url:
        raise SystemExit("DICOM_WEB_URL is required or pass --dicom-web-url.")
    downloader = DICOMDownloader(
        dicom_web_url=args.dicom_web_url,
        dicom_user=args.dicom_user,
        dicom_password=args.dicom_password,
        output_format=args.output_format,
        use_compression=args.compression,
        num_processes=args.processes,
    )
    if args.csv:
        results = downloader.download_from_dataframe(
            df=pd.read_csv(args.csv),
            output_dir=args.output_dir,
            study_uid_col=args.study_col,
            series_uid_col=args.series_col,
            download_full_study=args.full_study,
            skip_existing=args.skip_existing,
            write_manifest=args.manifest,
            study_layout=args.study_layout,
            study_folder_name_col=args.study_folder_col,
            save_study_manifest=False if args.no_study_manifest else None,
            results_csv=args.results_csv,
        )
        _emit(args, str(results))
        return 0
    if not args.study_uid:
        raise SystemExit("Provide --study-uid or --csv.")
    if args.series_uid:
        _emit(args, str(downloader.download_series(args.study_uid, args.series_uid, args.output_dir, skip_existing=args.skip_existing)), outputs=[args.output_dir])
    else:
        for result in downloader.download_study(
            args.study_uid,
            args.output_dir,
            skip_existing=args.skip_existing,
            write_manifest=args.manifest,
            study_layout=args.study_layout,
            study_folder_name=args.study_folder_name,
            save_study_manifest=False if args.no_study_manifest else None,
        ):
            _emit(args, str(result))
    return 0


def _cmd_dicom_seg(args: argparse.Namespace) -> int:
    import SimpleITK as sitk

    from fyron.dicom.seg import (
        load_source_dicom_series,
        read_segment_descriptions,
        summarize_dicom_seg,
        write_dicom_seg,
    )

    mask = sitk.GetArrayFromImage(sitk.ReadImage(args.mask))
    sources = load_source_dicom_series(args.source_dicom)
    segments = read_segment_descriptions(args.segments)
    out = write_dicom_seg(
        mask,
        sources,
        args.output,
        segments,
        series_description=args.series_description,
        manufacturer=args.manufacturer,
        algorithm_type=args.algorithm_type,
        algorithm_name=args.algorithm_name,
    )
    _emit(args, f"Wrote DICOM SEG to {out}", outputs=[out])
    if args.validate or args.summary_json:
        summary = summarize_dicom_seg(out, source_images=sources)
        if args.summary_json:
            Path(args.summary_json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        if args.validate:
            _emit(args, json.dumps(summary, indent=2), level="info")
    return 0


def _cmd_synthetic_dicom(args: argparse.Namespace) -> int:
    import SimpleITK as sitk

    from fyron.dicom.synthetic import write_synthetic_dicom_series

    volume = sitk.GetArrayFromImage(sitk.ReadImage(args.volume))
    manifest = write_synthetic_dicom_series(
        volume,
        args.output_dir,
        reference_dicom_dir=args.reference_dicom,
        patient_id=args.patient_id,
        series_description=args.series_description,
    )
    if args.manifest_csv:
        manifest.to_csv(args.manifest_csv, index=False)
    _emit(args, f"Wrote synthetic DICOM series to {args.output_dir}", outputs=[args.output_dir])
    return 0


def _cmd_boa_extract(args: argparse.Namespace) -> int:
    from fyron.boa_extraction import (
        extract_boa_features,
        extract_cohort_body_region_features,
        extract_cohort_total_features,
        extract_experimental_cohort_aortic_calcification_features,
    )

    if not any([args.include_body_regions, args.include_total, args.include_aortic_experimental]):
        frame = extract_boa_features(args.cohort_folder, num_workers=args.workers, show_progress=not args.no_progress)
    else:
        frames = []
        if args.include_body_regions:
            frames.append(extract_cohort_body_region_features(args.cohort_folder, num_workers=args.workers, show_progress=not args.no_progress))
        if args.include_total:
            frames.append(extract_cohort_total_features(args.cohort_folder, num_workers=args.workers, show_progress=not args.no_progress))
        if args.include_aortic_experimental:
            frames.append(extract_experimental_cohort_aortic_calcification_features(args.cohort_folder, num_workers=args.workers, show_progress=not args.no_progress))
        frame = _merge_on_download_id(frames)
    frame.to_csv(args.output, index=False)
    _emit(args, f"Wrote {len(frame)} BOA feature rows to {args.output}", outputs=[args.output])
    return 0


def _cmd_boa_radiomics(args: argparse.Namespace) -> int:
    from fyron.boa_radiomics import extract_boa_radiomics_features

    frame = extract_boa_radiomics_features(
        args.cohort_folder,
        segmentation_kind=args.segmentation,
        num_workers=args.workers,
        show_progress=not args.no_progress,
    )
    frame.to_csv(args.output, index=False)
    _emit(args, f"Wrote {len(frame)} BOA radiomics rows to {args.output}", outputs=[args.output])
    return 0


def _cmd_audit_manifest(args: argparse.Namespace) -> int:
    from fyron.audit import create_provenance_manifest, write_manifest

    manifest = create_provenance_manifest(
        title=args.title,
        inputs=args.input,
        outputs=args.output,
        parameters=_parse_key_values(args.parameter),
        notes=args.notes,
    )
    path = write_manifest(manifest, args.write)
    _emit(args, f"Wrote audit manifest to {path}", outputs=[path])
    return 0


def _cmd_imaging_qc(args: argparse.Namespace) -> int:
    from fyron.imaging.qc import (
        check_image_mask_alignment,
        summarize_dicom_series_geometry,
        summarize_intensity_range,
        summarize_mask_volume,
        summarize_nifti_geometry,
    )

    tables = []
    records: dict[str, Any] = {}
    if args.dicom_dir:
        table = summarize_dicom_series_geometry(args.dicom_dir)
        table.insert(0, "qc_type", "dicom_series_geometry")
        tables.append(table)
        records["dicom_series_geometry"] = table.to_dict(orient="records")
    if args.nifti:
        table = summarize_nifti_geometry(args.nifti)
        table.insert(0, "qc_type", "nifti_geometry")
        tables.append(table)
        records["nifti_geometry"] = table.to_dict(orient="records")
        records["intensity_range"] = summarize_intensity_range(args.nifti[0], mask=args.mask if args.mask else None)
    if args.mask:
        table = summarize_mask_volume(args.mask)
        table.insert(0, "qc_type", "mask_volume")
        tables.append(table)
        records["mask_volume"] = table.to_dict(orient="records")
        if args.nifti:
            records["alignment"] = check_image_mask_alignment(args.nifti[0], args.mask)
    if args.format == "json":
        Path(args.output).write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
    else:
        pd.concat(tables, ignore_index=True, sort=False).to_csv(args.output, index=False)
    _emit(args, f"Wrote QC output to {args.output}", outputs=[args.output])
    return 0


def _cmd_dataset_curate_previews(args: argparse.Namespace) -> int:
    from fyron.visualization import prepare_curate_image_previews

    result = prepare_curate_image_previews(
        args.input_dir,
        args.output_dir,
        recursive=not args.no_recursive,
        include_dicom=not args.no_dicom,
        include_image_files=not args.no_image_files,
        panel_width=args.panel_width,
        window_center=args.window_center,
        window_width=args.window_width,
        percentile_clip=_parse_float_pair(args.percentile_clip, name="--percentile-clip"),
        overwrite=args.overwrite,
        manifest_csv=args.manifest_csv,
    )
    _emit(
        args,
        f"Wrote {result['images_written']} Curate preview images.",
        outputs=[result["output_dir"], result["manifest_csv"]],
    )
    return 0


def _cmd_dataset_nnunetv2(args: argparse.Namespace) -> int:
    from fyron.datasets import prepare_nnunetv2_dataset, write_dataset_manifest

    result = prepare_nnunetv2_dataset(
        args.manifest,
        args.output_dir,
        dataset_id=args.dataset_id,
        dataset_name=args.dataset_name,
        image_col=args.image_col,
        label_col=args.label_col,
        case_id_col=args.case_id_col,
        split_col=args.split_col,
        copy_mode=args.copy_mode,
        overwrite=args.overwrite,
    )
    outputs = [args.output_dir]
    if args.output_manifest:
        outputs.append(write_dataset_manifest(result, args.output_manifest))
    _emit(args, f"Prepared nnU-Net v2 dataset with {len(result)} rows", outputs=outputs)
    return 0


def _cmd_dataset_yolo_classify(args: argparse.Namespace) -> int:
    from fyron.datasets import prepare_yolo_classification_dataset, write_dataset_manifest

    result = prepare_yolo_classification_dataset(
        args.manifest,
        args.output_dir,
        image_col=args.image_col,
        class_col=args.class_col,
        split_col=args.split_col,
        sample_id_col=args.sample_id_col,
        image_format=args.image_format,
        copy_mode=args.copy_mode,
        nifti_slice=_parse_nifti_slice(args.nifti_slice),
        overwrite=args.overwrite,
    )
    outputs = [args.output_dir]
    if args.output_manifest:
        outputs.append(write_dataset_manifest(result, args.output_manifest))
    _emit(args, f"Prepared YOLO classification dataset with {len(result)} images", outputs=outputs)
    return 0


def _cmd_dataset_yolo_detect(args: argparse.Namespace) -> int:
    from fyron.datasets import prepare_yolo_detection_dataset, write_dataset_manifest

    result = prepare_yolo_detection_dataset(
        args.manifest,
        args.output_dir,
        image_col=args.image_col,
        split_col=args.split_col,
        class_col=args.class_col,
        bbox_cols=_parse_csv_list(args.bbox_cols),
        image_width_col=args.image_width_col,
        image_height_col=args.image_height_col,
        sample_id_col=args.sample_id_col,
        image_format=args.image_format,
        copy_mode=args.copy_mode,
        nifti_slice=_parse_nifti_slice(args.nifti_slice),
        overwrite=args.overwrite,
    )
    outputs = [args.output_dir]
    if args.output_manifest:
        outputs.append(write_dataset_manifest(result, args.output_manifest))
    _emit(args, f"Prepared YOLO detection dataset with {len(result)} images", outputs=outputs)
    return 0


def _emit(args: argparse.Namespace, message: str, *, level: str = "success", outputs: list[str | Path] | None = None) -> None:
    if args.quiet:
        return
    suffix = ""
    if outputs:
        suffix = " | " + " ".join(str(path) for path in outputs)
    if hasattr(args, "started_at"):
        suffix = f"{suffix} | {format_duration(time.perf_counter() - args.started_at)}"
    console_message(f"{message}{suffix}", level=level, color=args.color)


def _parse_key_values(items: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Expected key=value, got: {item}")
        key, value = item.split("=", 1)
        out[key] = value
    return out


def _read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _parse_csv_list(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise SystemExit("Expected a comma-separated list.")
    return items


def _parse_float_pair(value: str, *, name: str) -> tuple[float, float]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if len(items) != 2:
        raise SystemExit(f"{name} must be two comma-separated numbers.")
    try:
        first, second = (float(item) for item in items)
    except ValueError as exc:
        raise SystemExit(f"{name} must be two comma-separated numbers.") from exc
    if first < 0 or second > 100 or first >= second:
        raise SystemExit(f"{name} must satisfy 0 <= low < high <= 100.")
    return first, second


def _parse_nifti_slice(value: str) -> str | int:
    lowered = str(value).strip().lower()
    if lowered in {"middle", "all"}:
        return lowered
    try:
        return int(lowered)
    except ValueError as exc:
        raise SystemExit("--nifti-slice must be 'middle', 'all', or an integer") from exc


def _read_fhir_paths(path: str | None) -> list[str | tuple[str, str]] | None:
    if not path:
        return None
    raw = _read_json(path)
    out = []
    for item in raw:
        if isinstance(item, dict):
            out.append((str(item["name"]), str(item["path"])))
        else:
            out.append(str(item))
    return out


def _write_table_result(result: Any, path: str | Path, fmt: str) -> None:
    if isinstance(result, dict):
        if fmt == "json":
            payload = {key: frame.to_dict(orient="records") for key, frame in result.items()}
            Path(path).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            return
        root = Path(path)
        root.mkdir(parents=True, exist_ok=True)
        for key, frame in result.items():
            frame.to_csv(root / f"{key}.csv", index=False)
        return
    if fmt == "json":
        result.to_json(path, orient="records", indent=2)
    else:
        result.to_csv(path, index=False)


def _merge_on_download_id(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="download_id", how="outer")
    return merged


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
