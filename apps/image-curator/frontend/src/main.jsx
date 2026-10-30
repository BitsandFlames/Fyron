import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  Copy,
  Download,
  FolderUp,
  ImageIcon,
  Info,
  LayoutDashboard,
  Loader2,
  Maximize2,
  Menu,
  Plus,
  RotateCcw,
  Search,
  SlidersHorizontal,
  X
} from "./icons.jsx";
import "./styles.css";
import { splitUploadBatches } from "./upload-batches.js";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:4000/api";
const supportedExtensions = [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"];
const dicomExtensions = [".dcm", ".dicom", ".ima"];
const acceptedImageTypes = "image/png,image/jpeg,image/webp,image/gif,image/bmp,image/tiff,.png,.jpg,.jpeg,.webp,.gif,.bmp,.tif,.tiff,.dcm,.dicom,.ima";

function getPathExt(fileOrPath) {
  const name = (typeof fileOrPath === "string" ? fileOrPath : fileOrPath.name).toLowerCase();
  const fileName = name.split("/").pop() || name;
  const dotIndex = fileName.lastIndexOf(".");
  return dotIndex > -1 ? fileName.slice(dotIndex) : "";
}

function isSupportedImageFile(fileOrPath) {
  return supportedExtensions.includes(getPathExt(fileOrPath));
}

function isDicomCandidate(fileOrPath) {
  const name = (typeof fileOrPath === "string" ? fileOrPath : fileOrPath.name).toLowerCase();
  const fileName = name.split("/").pop() || name;
  const ext = getPathExt(fileOrPath);
  return dicomExtensions.includes(ext) || !fileName.includes(".");
}

function isSupportedFile(fileOrPath) {
  return isSupportedImageFile(fileOrPath) || isDicomCandidate(fileOrPath);
}

function readFileFromEntry(entry) {
  return new Promise((resolve, reject) => {
    entry.file(resolve, reject);
  });
}

function readDirectoryBatch(reader) {
  return new Promise((resolve, reject) => {
    reader.readEntries(resolve, reject);
  });
}

async function readAllDirectoryEntries(directoryEntry) {
  const reader = directoryEntry.createReader();
  const entries = [];
  while (true) {
    const batch = await readDirectoryBatch(reader);
    if (!batch.length) break;
    entries.push(...batch);
  }
  return entries;
}

async function collectDroppedImageEntries(dataTransfer) {
  const items = Array.from(dataTransfer.items || []);
  const entries = [];

  async function visitEntry(entry) {
    if (!entry) return;
    if (entry.isFile) {
      const file = await readFileFromEntry(entry);
      const relativePath = entry.fullPath ? entry.fullPath.replace(/^\/+/, "") : file.name;
      if (isSupportedFile(relativePath)) {
        entries.push({ file, relativePath });
      }
      return;
    }
    if (entry.isDirectory) {
      const children = await readAllDirectoryEntries(entry);
      for (const child of children) {
        await visitEntry(child);
      }
    }
  }

  const supportsEntries = items.some((item) => typeof item.webkitGetAsEntry === "function");
  if (supportsEntries) {
    for (const item of items) {
      await visitEntry(item.webkitGetAsEntry());
    }
    return entries;
  }

  return Array.from(dataTransfer.files || [])
    .filter(isSupportedFile)
    .map((file) => ({ file, relativePath: file.webkitRelativePath || file.name }));
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `Request failed with ${response.status}`);
  }
  return response.json();
}

function formatBytes(value) {
  if (!value) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function makeToastId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function App() {
  const [cohorts, setCohorts] = useState([]);
  const [activeCohortId, setActiveCohortId] = useState(null);
  const [images, setImages] = useState([]);
  const [dicomStudies, setDicomStudies] = useState([]);
  const [counts, setCounts] = useState({ accepted: 0, rejected: 0 });
  const [reviewedImageIds, setReviewedImageIds] = useState([]);
  const [settings, setSettings] = useState({ imageSize: 180, gapSize: 12, imageFit: "cover", sortKey: "relativePath", sortDirection: "asc" });
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const pendingUpload = useRef(null);
  const [exporting, setExporting] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [addCohortOpen, setAddCohortOpen] = useState(false);
  const [contextEditorOpen, setContextEditorOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [zenOpen, setZenOpen] = useState(false);
  const [focusedImageId, setFocusedImageId] = useState(null);
  const [detailImageId, setDetailImageId] = useState(null);
  const [undoStack, setUndoStack] = useState([]);
  const [sessionReviewed, setSessionReviewed] = useState(0);
  const [selectedImageIds, setSelectedImageIds] = useState([]);
  const [health, setHealth] = useState(null);

  const activeCohort = useMemo(() => cohorts.find((cohort) => cohort.id === activeCohortId) || null, [cohorts, activeCohortId]);
  const dicomPreviewImages = useMemo(() => dicomStudies.flatMap((study) => (study.series || []).map((series) => ({
    id: series.thumbnailImageId,
    originalName: series.seriesDescription || "DICOM series",
    relativePath: series.thumbnailRelativePath || series.seriesUid,
    mimeType: "image/bmp",
    sizeBytes: 0,
    width: series.width,
    height: series.height,
    reviewState: series.reviewState || "ACCEPTED"
  }))), [dicomStudies]);
  const focusedImage = useMemo(() => images.find((image) => image.id === focusedImageId) || images[0] || null, [focusedImageId, images]);
  const detailImage = useMemo(() => images.find((image) => image.id === detailImageId) || dicomPreviewImages.find((image) => image.id === detailImageId) || null, [detailImageId, dicomPreviewImages, images]);
  const selectedImages = useMemo(() => images.filter((image) => selectedImageIds.includes(image.id)), [images, selectedImageIds]);
  const lastExport = activeCohort?.exports?.[0] || null;

  const loadCohorts = useCallback(async () => {
    const data = await api("/cohorts");
    setCohorts(data);
  }, []);

  const pushToast = useCallback((toast) => {
    const id = makeToastId();
    const nextToast = { id, tone: "info", timeout: 4200, ...toast };
    setToasts((current) => [nextToast, ...current].slice(0, 4));
    if (nextToast.timeout) {
      window.setTimeout(() => {
        setToasts((current) => current.filter((item) => item.id !== id));
      }, nextToast.timeout);
    }
    return id;
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((current) => current.filter((item) => item.id !== id));
  }, []);

  const loadImages = useCallback(async () => {
    if (!activeCohortId) return;
    setBusy(true);
    try {
      const params = new URLSearchParams({
        filter,
        search,
        sortKey: settings.sortKey,
        sortDirection: settings.sortDirection
      });
      const [data, dicomData] = await Promise.all([
        api(`/cohorts/${activeCohortId}/images?${params}`),
        api(`/cohorts/${activeCohortId}/dicom-studies`)
      ]);
      setImages(data.images);
      setDicomStudies(dicomData.studies || []);
      setCounts(data.counts);
      setReviewedImageIds(data.reviewedImageIds || []);
      if (data.cohort.settings) {
        setSettings((current) => ({ ...current, ...data.cohort.settings }));
      }
    } finally {
      setBusy(false);
    }
  }, [activeCohortId, filter, search, settings.sortDirection, settings.sortKey]);

  useEffect(() => {
    loadCohorts().catch((err) => pushToast({ tone: "error", title: "Backend connection failed", message: err.message, timeout: 7000 }));
    api("/health").then(setHealth).catch((err) => pushToast({ tone: "error", title: "Health check failed", message: err.message, timeout: 7000 }));
  }, [loadCohorts, pushToast]);

  useEffect(() => {
    if (!activeCohortId) {
      setImages([]);
      setDicomStudies([]);
      setCounts({ accepted: 0, rejected: 0 });
      setReviewedImageIds([]);
      setFocusedImageId(null);
      setDetailImageId(null);
      setSelectedImageIds([]);
      return;
    }
    loadImages().catch((err) => pushToast({ tone: "error", title: "Could not load gallery", message: err.message, timeout: 7000 }));
  }, [activeCohortId, loadImages, pushToast]);

  useEffect(() => {
    if (!images.length) {
      setFocusedImageId(null);
      setSelectedImageIds([]);
      return;
    }
    setFocusedImageId((current) => images.some((image) => image.id === current) ? current : images[0].id);
    setSelectedImageIds((current) => current.filter((id) => images.some((image) => image.id === id)));
  }, [images]);

  useEffect(() => {
    function handleKeyDown(event) {
      const tagName = event.target?.tagName?.toLowerCase();
      if (tagName === "input" || tagName === "textarea" || tagName === "select" || addCohortOpen || contextEditorOpen || settingsOpen) return;
      if (!activeCohortId || !images.length) return;
      if ((event.key === " " || event.key === "Enter") && event.target?.closest("button, a") && !event.target?.closest("[data-review-image]")) return;
      if (detailImageId && !zenOpen) {
        if (event.key === "ArrowRight") {
          event.preventDefault();
          moveDetailFocus(1);
        } else if (event.key === "ArrowLeft") {
          event.preventDefault();
          moveDetailFocus(-1);
        } else if (event.key.toLowerCase() === "a" && detailImage) {
          event.preventDefault();
          setReviewState(detailImage, "ACCEPTED");
        } else if ((event.key.toLowerCase() === "d" || event.key.toLowerCase() === "r") && detailImage) {
          event.preventDefault();
          setReviewState(detailImage, "REJECTED");
        } else if (event.key === "Escape") {
          event.preventDefault();
          setDetailImageId(null);
        }
        return;
      }
      if (zenOpen) {
        if (event.key === "ArrowRight") {
          event.preventDefault();
          moveFocus(1);
        } else if (event.key === "ArrowLeft") {
          event.preventDefault();
          moveFocus(-1);
        } else if (event.key.toLowerCase() === "a" && focusedImage) {
          event.preventDefault();
          setReviewState(focusedImage, "ACCEPTED");
        } else if (event.key.toLowerCase() === "d" && focusedImage) {
          event.preventDefault();
          setReviewState(focusedImage, "REJECTED");
        } else if (event.key === "Escape") {
          event.preventDefault();
          setZenOpen(false);
        }
        return;
      }
      if (event.key === "ArrowRight" || event.key === "ArrowDown") {
        event.preventDefault();
        moveFocus(1);
      } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
        event.preventDefault();
        moveFocus(-1);
      } else if (event.key.toLowerCase() === "a" && focusedImage) {
        event.preventDefault();
        setReviewState(focusedImage, "ACCEPTED");
      } else if ((event.key.toLowerCase() === "d" || event.key.toLowerCase() === "r") && focusedImage) {
        event.preventDefault();
        setReviewState(focusedImage, "REJECTED");
      } else if (event.key.toLowerCase() === "u") {
        event.preventDefault();
        undoLastReview();
      } else if ((event.key === " " || event.key === "Enter") && focusedImage) {
        event.preventDefault();
        setDetailImageId(focusedImage.id);
      } else if (event.key === "Escape") {
        setDetailImageId(null);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeCohortId, addCohortOpen, contextEditorOpen, detailImage, detailImageId, focusedImage, images.length, settingsOpen, undoStack, zenOpen]);

  async function persistSettings(nextSettings) {
    setSettings(nextSettings);
    if (!activeCohortId) return;
    setSavingSettings(true);
    try {
      await api(`/cohorts/${activeCohortId}/settings`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(nextSettings)
      });
    } catch (err) {
      pushToast({ tone: "error", title: "Settings were not saved", message: err.message, timeout: 6500 });
    } finally {
      setSavingSettings(false);
    }
  }

  async function uploadFiles(entries, cohortName, selectionContext = "") {
    setUploading(true);
    try {
      const batches = splitUploadBatches(entries);
      const previous = pendingUpload.current;
      const sameSelection = previous && previous.name === cohortName && previous.context === selectionContext
        && entries.length === previous.entries.length
        && entries.every((entry, index) => entry.file === previous.entries[index].file && entry.relativePath === previous.entries[index].relativePath);
      if (!sameSelection) {
        const cohort = await api("/cohorts", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: cohortName, selectionContext })
        });
        pendingUpload.current = { cohort, entries, name: cohortName, context: selectionContext, nextBatch: 0, skipped: 0 };
      }
      const pending = pendingUpload.current;
      const { cohort } = pending;
      for (; pending.nextBatch < batches.length; pending.nextBatch += 1) {
        const batch = batches[pending.nextBatch];
        const formData = new FormData();
        for (const { file } of batch) formData.append("files", file, file.name);
        formData.append("relativePaths", JSON.stringify(batch.map((entry) => entry.relativePath)));
        const result = await api(`/cohorts/${cohort.id}/images`, { method: "POST", body: formData });
        pending.skipped += result.skipped;
      }
      await loadCohorts();
      setActiveCohortId(cohort.id);
      setAddCohortOpen(false);
      pushToast({
        tone: "success",
        title: "Cohort ready",
        message: `All ${entries.length} selected files processed. Skipped ${pending.skipped}.`
      });
      pendingUpload.current = null;
    } catch (err) {
      pushToast({ tone: "error", title: "Upload failed", message: `${err.message} Keep this selection and choose Create cohort again to retry.`, timeout: 10000 });
    } finally {
      setUploading(false);
    }
  }

  async function updateCohortMetadata(nextMetadata) {
    if (!activeCohortId) return;
    setSavingSettings(true);
    try {
      const updated = await api(`/cohorts/${activeCohortId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(nextMetadata)
      });
      setCohorts((current) => current.map((cohort) => cohort.id === updated.id ? updated : cohort));
      setContextEditorOpen(false);
      pushToast({ tone: "success", title: "Selection context saved", message: "Review instructions were updated." });
    } catch (err) {
      pushToast({ tone: "error", title: "Selection context not saved", message: err.message, timeout: 6500 });
    } finally {
      setSavingSettings(false);
    }
  }

  async function setReviewState(image, nextState, { remember = true } = {}) {
    if (!image) return;
    const previousState = image.reviewState;
    const stateChanged = previousState !== nextState;
    if (stateChanged) {
      setImages((current) => current.map((item) => item.id === image.id ? { ...item, reviewState: nextState } : item));
      setDicomStudies((current) => current.map((study) => ({
        ...study,
        series: (study.series || []).map((series) => (
          series.thumbnailImageId === image.id ? { ...series, reviewState: nextState } : series
        ))
      })));
      setCounts((current) => ({
        accepted: current.accepted + (nextState === "ACCEPTED" ? 1 : -1),
        rejected: current.rejected + (nextState === "REJECTED" ? 1 : -1)
      }));
    }
    setReviewedImageIds((current) => current.includes(image.id) ? current : [...current, image.id]);
    if (remember && stateChanged) {
      setUndoStack((current) => [{ imageId: image.id, previousState, nextState, label: image.originalName }, ...current].slice(0, 25));
    }
    if (remember) {
      setSessionReviewed((current) => current + 1);
    }
    try {
      await api(`/images/${image.id}/review-state`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewState: nextState })
      });
    } catch (err) {
      pushToast({ tone: "error", title: "Review state was restored", message: err.message, timeout: 6500 });
      await loadImages();
    }
  }

  async function toggleReview(image) {
    await setReviewState(image, image.reviewState === "ACCEPTED" ? "REJECTED" : "ACCEPTED");
  }

  async function toggleDicomSeries(series) {
    const image = images.find((item) => item.id === series.thumbnailImageId) || {
      id: series.thumbnailImageId,
      reviewState: series.reviewState || "ACCEPTED",
      originalName: series.seriesDescription || "DICOM series",
      relativePath: series.thumbnailRelativePath || series.seriesUid
    };
    await toggleReview(image);
  }

  async function undoLastReview() {
    const [last, ...rest] = undoStack;
    if (!last) return;
    const image = images.find((item) => item.id === last.imageId);
    setUndoStack(rest);
    if (image) {
      await setReviewState(image, last.previousState, { remember: false });
      pushToast({ tone: "info", title: "Review undone", message: `${last.label} restored to ${last.previousState.toLowerCase()}.` });
    }
  }

  async function applyBatchReview(nextState) {
    if (!selectedImages.length) return;
    for (const image of selectedImages) {
      await setReviewState(image, nextState);
    }
    pushToast({ tone: "success", title: "Batch review updated", message: `${selectedImages.length} images set to ${nextState.toLowerCase()}.` });
    setSelectedImageIds([]);
  }

  function moveFocus(step) {
    if (!images.length) return;
    const currentIndex = Math.max(0, images.findIndex((image) => image.id === (focusedImageId || images[0].id)));
    const nextIndex = Math.min(images.length - 1, Math.max(0, currentIndex + step));
    setFocusedImageId(images[nextIndex].id);
  }

  function moveDetailFocus(step) {
    if (!images.length) return;
    const currentIndex = Math.max(0, images.findIndex((image) => image.id === (detailImageId || focusedImageId || images[0].id)));
    const nextIndex = Math.min(images.length - 1, Math.max(0, currentIndex + step));
    setFocusedImageId(images[nextIndex].id);
    setDetailImageId(images[nextIndex].id);
  }

  function toggleSelectedImage(image) {
    setSelectedImageIds((current) => current.includes(image.id) ? current.filter((id) => id !== image.id) : [...current, image.id]);
  }

  async function exportCleanFolder() {
    if (!activeCohortId) return;
    setBusy(true);
    setExporting(true);
    try {
      const result = await api(`/cohorts/${activeCohortId}/export-clean`, { method: "POST" });
      pushToast({
        tone: "success",
        title: "Clean folder created",
        message: `${result.acceptedCount} accepted images exported to ${result.exportRoot}.`,
        timeout: 9000
      });
      await loadCohorts();
    } catch (err) {
      pushToast({ tone: "error", title: "Export failed", message: err.message, timeout: 7000 });
    } finally {
      setBusy(false);
      setExporting(false);
    }
  }

  async function exportReviewLabelsCsv() {
    if (!activeCohortId) return;
    setBusy(true);
    try {
      const response = await fetch(`${API_BASE_URL}/cohorts/${activeCohortId}/review-labels.csv`);
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.error || `Request failed with ${response.status}`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${activeCohort?.name || "cohort"}-review-labels.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      pushToast({ tone: "success", title: "CSV labels exported", message: "Downloaded filename/status labels for the reviewed cohort." });
    } catch (err) {
      pushToast({ tone: "error", title: "CSV export blocked", message: err.message, timeout: 7000 });
    } finally {
      setBusy(false);
    }
  }

  async function copyExportPath(path) {
    if (!path) return;
    try {
      await navigator.clipboard.writeText(path);
      pushToast({ tone: "success", title: "Export path copied", message: path });
    } catch (err) {
      pushToast({ tone: "error", title: "Could not copy path", message: err.message, timeout: 6500 });
    }
  }

  const total = counts.accepted + counts.rejected;
  const reviewedCount = reviewedImageIds.length;
  const canExportReviewLabels = total > 0 && reviewedCount >= total;
  const activity = uploading
    ? "Uploading cohort"
    : exporting
      ? "Creating clean folder"
      : busy
        ? "Loading gallery"
        : savingSettings
          ? "Saving settings"
          : "";

  return (
    <main className="min-h-screen bg-[var(--bf-page-bg)] text-[var(--bf-text)]">
      <StandardNavbar
        search={search}
        onSearch={setSearch}
        onOpenSettings={() => setSettingsOpen(true)}
        onOpenAddCohort={() => setAddCohortOpen(true)}
        onDashboard={() => setActiveCohortId(null)}
        inDashboard={!activeCohortId}
        mobileMenuOpen={mobileMenuOpen}
        onToggleMobileMenu={() => setMobileMenuOpen((current) => !current)}
      />
      <MobileMenu
        open={mobileMenuOpen}
        search={search}
        onSearch={setSearch}
        onDashboard={() => {
          setActiveCohortId(null);
          setMobileMenuOpen(false);
        }}
        onAddCohort={() => {
          setAddCohortOpen(true);
          setMobileMenuOpen(false);
        }}
        onOpenSettings={() => {
          setSettingsOpen(true);
          setMobileMenuOpen(false);
        }}
      />
      <ActivityRail label={activity} />

      <div className="bf-workspace">
        {activeCohort ? (
          <PageHeader
            title={activeCohort.name}
            counts={counts}
            total={total}
            reviewedCount={reviewedCount}
            busy={busy}
            canExport={Boolean(activeCohortId)}
            canExportReviewLabels={canExportReviewLabels}
            onExport={exportCleanFolder}
            onExportReviewLabels={exportReviewLabelsCsv}
            cohorts={cohorts}
            activeCohortId={activeCohortId}
            onSelectCohort={setActiveCohortId}
            filter={filter}
            onFilter={setFilter}
            onAddCohort={() => setAddCohortOpen(true)}
            sessionReviewed={sessionReviewed}
            undoCount={undoStack.length}
            onUndo={undoLastReview}
            selectedCount={selectedImages.length}
            onBatchAccept={() => applyBatchReview("ACCEPTED")}
            onBatchReject={() => applyBatchReview("REJECTED")}
            lastExport={lastExport}
            onCopyExportPath={copyExportPath}
            onOpenZen={() => setZenOpen(true)}
          />
        ) : (
          <DashboardHeader onAddCohort={() => setAddCohortOpen(true)} />
        )}

        {activeCohort ? (
          <section className="bf-review-content">
            <SelectionContextPanel
              context={activeCohort.selectionContext}
              onEdit={() => setContextEditorOpen(true)}
            />
            <MobileSearch search={search} onSearch={setSearch} />
            <DicomStudyCards
              studies={dicomStudies}
              imageFit={settings.imageFit}
              onToggleSeries={toggleDicomSeries}
              onOpenSeries={(series) => setDetailImageId(series.thumbnailImageId)}
            />

            <Gallery
              images={images}
              imageSize={settings.imageSize}
              gapSize={settings.gapSize}
              imageFit={settings.imageFit}
              busy={busy}
              filter={filter}
              search={search}
              onToggle={toggleReview}
              focusedImageId={focusedImageId}
              selectedImageIds={selectedImageIds}
              onFocusImage={setFocusedImageId}
              onOpenDetail={(image) => setDetailImageId(image.id)}
              onToggleSelected={toggleSelectedImage}
            />
          </section>
        ) : (
          <CohortDashboard cohorts={cohorts} onOpenCohort={setActiveCohortId} onAddCohort={() => setAddCohortOpen(true)} />
        )}
      </div>

      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)}>
        <HealthPanel health={health} />
        <Controls settings={settings} onChange={persistSettings} />
        <CohortPanel cohorts={cohorts} activeCohortId={activeCohortId} onSelect={setActiveCohortId} />
      </SettingsDrawer>
      <ImageDetailModal
        image={detailImage}
        images={images}
        onClose={() => setDetailImageId(null)}
        onNext={() => moveDetailFocus(1)}
        onPrevious={() => moveDetailFocus(-1)}
        onAccept={() => detailImage && setReviewState(detailImage, "ACCEPTED")}
        onReject={() => detailImage && setReviewState(detailImage, "REJECTED")}
      />
      <ZenReviewModal
        open={zenOpen}
        image={focusedImage}
        images={images}
        selectionContext={activeCohort?.selectionContext}
        onClose={() => setZenOpen(false)}
        onNext={() => moveFocus(1)}
        onPrevious={() => moveFocus(-1)}
        onAccept={() => focusedImage && setReviewState(focusedImage, "ACCEPTED")}
        onReject={() => focusedImage && setReviewState(focusedImage, "REJECTED")}
      />
      <AddCohortDialog
        open={addCohortOpen}
        uploading={uploading}
        onClose={() => setAddCohortOpen(false)}
        onCreate={uploadFiles}
      />
      <SelectionContextDialog
        open={contextEditorOpen}
        cohort={activeCohort}
        saving={savingSettings}
        onClose={() => setContextEditorOpen(false)}
        onSave={updateCohortMetadata}
      />
      <ToastViewport toasts={toasts} onDismiss={dismissToast} />
    </main>
  );
}

function StandardNavbar({ search, onSearch, onOpenSettings, onOpenAddCohort, onDashboard, inDashboard, mobileMenuOpen, onToggleMobileMenu }) {
  const navItems = [
    {
      key: "dashboard",
      label: "Dashboard",
      description: "All image cohorts",
      icon: <LayoutDashboard className="size-4" />,
      current: inDashboard,
      onClick: onDashboard
    },
    {
      key: "curate",
      label: "Gallery view",
      description: "Select accepted and rejected images",
      icon: <ImageIcon className="size-4" />,
      current: !inDashboard,
      disabled: inDashboard
    },
    {
      key: "add",
      label: "Add cohort",
      description: "Drop image or DICOM folders",
      icon: <Plus className="size-4" />,
      onClick: onOpenAddCohort
    }
  ];
  const activeNavItem = navItems.find((item) => item.current) || navItems[0];

  return (
    <header className="abr-navbar">
      <nav className="abr-navbar-inner mx-auto max-w-[112rem]" aria-label="Main">
        <div className="abr-navbar-left">
          <BrandWordmark onClick={onDashboard} />
          <span className="abr-brand-divider" aria-hidden />
          <CurateNavDropdown activeItem={activeNavItem} items={navItems} />
        </div>

        <div className="abr-navbar-right">
          <label className="relative hidden w-full max-w-[18rem] xl:block">
            <span className="sr-only">Search</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--bf-text-muted)]" />
            <input
              type="search"
              aria-label="Search"
              className="bf-input pl-9"
              placeholder="Search image path"
              value={search}
              onChange={(event) => onSearch(event.target.value)}
            />
          </label>
          <button className="bf-button-clinical bf-navbar-add" type="button" onClick={onOpenAddCohort}>
            <Plus className="size-4" />
            Add cohort
          </button>
          <button className="bf-icon-button" type="button" aria-label="Open gallery settings" onClick={onOpenSettings}>
            <SlidersHorizontal className="size-4" />
          </button>
          <button className="bf-icon-button bf-mobile-menu-toggle" type="button" aria-label={mobileMenuOpen ? "Close menu" : "Open menu"} onClick={onToggleMobileMenu}>
            {mobileMenuOpen ? <X className="size-4" /> : <Menu className="size-4" />}
          </button>
        </div>
      </nav>
    </header>
  );
}

function ForgeMenu({ trigger, children, align = "right", label }) {
  const [open, setOpen] = useState(false);
  const menuRef = React.useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    function handlePointerDown(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) setOpen(false);
    }
    function handleKeyDown(event) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <div className="abr-menu" ref={menuRef}>
      <button
        type="button"
        className="abr-menu-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={label}
        onClick={() => setOpen((current) => !current)}
      >
        {trigger}
      </button>
      {open && (
        <div className="abr-menu-panel" role="menu" data-align={align} onClick={() => setOpen(false)}>
          {children}
        </div>
      )}
    </div>
  );
}

function ForgeMenuItem({ icon, children, onClick, current = false, disabled = false }) {
  return (
    <button
      type="button"
      role="menuitem"
      className={`abr-menu-item${current ? " is-current" : ""}${disabled ? " is-disabled" : ""}`}
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      aria-disabled={disabled || undefined}
    >
      {icon}
      <span>{children}</span>
    </button>
  );
}

function CurateNavDropdown({ activeItem, items }) {
  return (
    <ForgeMenu
      align="left"
      label="Curate workspace navigation"
      trigger={
        <span className="abr-nav-menu-trigger">
          {activeItem.icon}
          <span>{activeItem.label}</span>
          <ChevronDown className="size-4" aria-hidden />
        </span>
      }
    >
      <div className="abr-menu-header">
        <span className="abr-menu-kicker">Workspace</span>
        <strong>Curate modules</strong>
      </div>
      {items.map((item) => (
        <ForgeMenuItem
          key={item.key}
          icon={item.icon}
          current={item.current}
          disabled={item.disabled}
          onClick={item.onClick}
        >
          <span className="abr-menu-item-copy">
            <span>{item.label}</span>
            {item.description && <small>{item.description}</small>}
          </span>
        </ForgeMenuItem>
      ))}
    </ForgeMenu>
  );
}

function MobileMenu({ open, search, onSearch, onDashboard, onAddCohort, onOpenSettings }) {
  return (
    <div className={`sticky top-[var(--bf-nav-height)] z-30 border-b border-[var(--bf-divider)] bg-[var(--bf-page-bg)]/96 px-4 pb-3 backdrop-blur-xl transition md:hidden ${open ? "block" : "hidden"}`}>
      <div className="mx-auto flex max-w-[112rem] flex-col gap-2">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--bf-text-muted)]" />
          <input className="bf-input pl-9" placeholder="Search image path" value={search} onChange={(event) => onSearch(event.target.value)} />
        </div>
        <div className="grid grid-cols-3 gap-2">
          <button className="bf-button-secondary" type="button" onClick={onDashboard}>Dashboard</button>
          <button className="bf-button-clinical" type="button" onClick={onAddCohort}>Add</button>
          <button className="bf-button-secondary" type="button" onClick={onOpenSettings}>Settings</button>
        </div>
      </div>
    </div>
  );
}

function ActivityRail({ label }) {
  return (
    <div className={`sticky top-[var(--bf-nav-height)] z-30 border-b border-[var(--bf-divider)] bg-[var(--bf-page-bg)]/92 backdrop-blur-xl transition ${label ? "max-h-12 opacity-100" : "max-h-0 overflow-hidden opacity-0"}`}>
      <div className="mx-auto flex h-10 max-w-[112rem] items-center gap-3 px-4 text-xs font-semibold text-[var(--bf-text-muted)] sm:px-6">
        <Loader2 className="size-4 animate-spin text-ember" />
        <span>{label}</span>
        <span className="h-px flex-1 overflow-hidden rounded bg-[var(--bf-field-bg)]">
          <span className="block h-full w-1/3 animate-[bf-progress_1.2s_ease-in-out_infinite] rounded bg-ember/70" />
        </span>
      </div>
    </div>
  );
}

function SettingsDrawer({ open, onClose, children }) {
  return (
    <div className={`fixed inset-0 z-50 transition ${open ? "pointer-events-auto" : "pointer-events-none"}`} aria-hidden={!open} inert={!open ? "" : undefined}>
      <button
        type="button"
        className={`absolute inset-0 bg-black/55 backdrop-blur-sm transition-opacity duration-200 ${open ? "opacity-100" : "opacity-0"}`}
        onClick={onClose}
        aria-label="Dismiss gallery settings"
      />
      <aside
        className={`absolute right-0 top-0 flex h-full w-full max-w-md flex-col gap-3 overflow-auto border-l border-[var(--bf-card-border)] bg-[var(--bf-page-bg)] p-4 shadow-[var(--bf-modal-shadow)] transition duration-200 sm:p-5 ${open ? "translate-x-0 opacity-100" : "translate-x-6 opacity-0"}`}
        role="dialog"
        aria-modal="true"
        aria-label="Gallery settings"
      >
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="bf-eyebrow-accent">Workspace</p>
            <h2 className="font-display text-xl font-bold tracking-tight text-[var(--bf-text)]">Gallery settings</h2>
          </div>
          <button className="bf-icon-button" type="button" aria-label="Close gallery settings" onClick={onClose}>
            <X className="size-4" />
          </button>
        </div>
        {children}
      </aside>
    </div>
  );
}

function HealthPanel({ health }) {
  return (
    <div className="bf-panel p-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="bf-eyebrow-accent">System health</p>
          <h2 className="font-display text-lg font-semibold tracking-normal">{health?.service || "Curate API"}</h2>
        </div>
        <span className={`rounded px-2 py-1 text-xs font-semibold ${health?.ok ? "bg-emerald-500/15 text-emerald-300" : "bg-red-500/15 text-red-300"}`}>
          {health?.ok ? "online" : "checking"}
        </span>
      </div>
      <p className="mt-3 truncate text-xs text-[var(--bf-text-muted)]">Uploads: {health?.uploadRoot || "not reported"}</p>
      <p className="mt-1 truncate text-xs text-[var(--bf-text-muted)]">Exports: {health?.exportRoot || "not reported"}</p>
      <p className="mt-3 text-xs text-[var(--bf-text-muted)]">
        <a className="underline" href="/LICENSE" target="_blank" rel="noopener noreferrer">CC BY-NC 4.0</a>
        {" · "}<a className="underline" href="/NOTICE" target="_blank" rel="noopener noreferrer">Notices</a>
      </p>
    </div>
  );
}

function BrandWordmark({ onClick }) {
  return (
    <button className="abr-brand" type="button" aria-label="Curate dashboard" onClick={onClick}>
      <img className="abr-brand-wordmark" src="/brand/logo-modern-light.png" alt="Bits & Flames" width={95} height={48} />
      <span className="abr-brand-product-divider" aria-hidden="true">|</span>
      <span className="abr-brand-name">Curate</span>
    </button>
  );
}



function ImageDetailModal({ image, images, onClose, onNext, onPrevious, onAccept, onReject }) {
  if (!image) return null;
  const currentIndex = images.findIndex((item) => item.id === image.id);
  return (
    <div className="fixed inset-0 z-[65] bg-black/75 p-3 backdrop-blur-md sm:p-6" role="dialog" aria-modal="true" aria-label="Image detail">
      <div className="mx-auto flex h-full max-w-6xl flex-col overflow-hidden rounded-md border border-[var(--bf-card-border)] bg-[var(--bf-page-bg)] shadow-[var(--bf-modal-shadow)]">
        <div className="flex items-center justify-between gap-3 border-b border-[var(--bf-divider)] p-3">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">{image.originalName}</p>
            <p className="truncate text-xs text-[var(--bf-text-muted)]">{image.relativePath}</p>
          </div>
          <button className="bf-icon-button" type="button" aria-label="Close image detail" onClick={onClose}>
            <X className="size-4" />
          </button>
        </div>
        <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_18rem]">
          <div className="min-h-0 bg-black">
            <img className="h-full w-full object-contain" src={`${API_BASE_URL}/files/${image.id}`} alt={image.relativePath} />
          </div>
          <aside className="space-y-4 overflow-auto border-t border-[var(--bf-divider)] p-4 lg:border-l lg:border-t-0">
            <div>
              <p className="bf-eyebrow-accent">Review state</p>
              <p className={`mt-1 font-display text-xl font-bold ${image.reviewState === "REJECTED" ? "text-red-300" : "text-emerald-300"}`}>{image.reviewState.toLowerCase()}</p>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Metric label="Size" value={formatBytes(image.sizeBytes)} tone="gold" />
              <Metric label="Dims" value={image.width && image.height ? `${image.width}x${image.height}` : "n/a"} tone="blue" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button className="bf-button-secondary" type="button" disabled={currentIndex <= 0} onClick={onPrevious}>Previous</button>
              <button className="bf-button-secondary" type="button" disabled={currentIndex >= images.length - 1} onClick={onNext}>Next</button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button className="bf-button-secondary" type="button" onClick={onAccept}><Check className="size-4" /> Accept</button>
              <button className="bf-button-primary" type="button" onClick={onReject}><X className="size-4" /> Reject</button>
            </div>
            <p className="text-xs leading-5 text-[var(--bf-text-muted)]">Shortcuts: A accepts, D rejects, arrows move between files, Esc closes.</p>
          </aside>
        </div>
      </div>
    </div>
  );
}

function PageHeader({ title, counts, total, reviewedCount, busy, canExport, canExportReviewLabels,
  onExport, onExportReviewLabels, cohorts, activeCohortId, onSelectCohort, filter, onFilter,
  undoCount, onUndo, selectedCount, onBatchAccept, onBatchReject, lastExport, onCopyExportPath, onOpenZen }) {
  const reviewedPercent = total ? Math.min(100, Math.round((reviewedCount / total) * 100)) : 0;
  return (
    <div className="bf-page-header">
      <div className="bf-title-row">
        <h1>{title}</h1>
        <div className="bf-keyboard-hints" aria-label="Review shortcuts">
          <span><kbd>A</kbd> accept</span><span><kbd>D</kbd> reject</span>
          <span><kbd>← →</kbd> navigate</span><span><kbd>Space</kbd> preview</span><span><kbd>U</kbd> undo</span>
        </div>
      </div>
      <div className="bf-review-bar">
        <ReviewToolbar cohorts={cohorts} activeCohortId={activeCohortId} onSelectCohort={onSelectCohort} filter={filter} onFilter={onFilter} />
        <div className="bf-review-progress">
          <span>{reviewedCount}/{total} reviewed</span>
          <div role="progressbar" aria-label="Review progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={reviewedPercent}>
            <span style={{ width: `${reviewedPercent}%` }} />
          </div>
        </div>
        <div className="bf-review-counts">
          <HeaderMetric label="Accepted" value={counts.accepted} tone="green" />
          <HeaderMetric label="Rejected" value={counts.rejected} tone="coral" />
          <HeaderMetric label="Total" value={total} tone="neutral" />
        </div>
        {selectedCount > 0 && <div className="bf-batch-actions">
          <button className="bf-button-secondary" type="button" onClick={onBatchAccept}><Check />{selectedCount} accept</button>
          <button className="bf-button-secondary" type="button" onClick={onBatchReject}><X />Reject selected</button>
        </div>}
        <div className="bf-review-actions">
          <button className="bf-icon-button" disabled={!undoCount} onClick={onUndo} type="button" aria-label="Undo last review" title="Undo (U)"><RotateCcw /></button>
          {lastExport?.exportRoot && <button className="bf-icon-button" type="button" onClick={() => onCopyExportPath(lastExport.exportRoot)} aria-label="Copy export path" title="Copy export path"><Copy /></button>}
          <button className="bf-button-secondary" disabled={!total} onClick={onOpenZen} type="button"><Maximize2 />Zen</button>
          <button className="bf-button-secondary" disabled={!canExportReviewLabels || busy} onClick={onExportReviewLabels} type="button" title={canExportReviewLabels ? "Download filename/status CSV" : "Review every image once before exporting labels"}><Download />CSV</button>
          <button className="bf-button-primary" disabled={!canExport || busy} onClick={onExport} type="button"><Download />Clean folder</button>
        </div>
      </div>
    </div>
  );
}

function HeaderMetric({ label, value, tone }) {
  return <span className={`bf-count bf-count-${tone}`}><strong>{value}</strong> {label.toLowerCase()}</span>;
}

function ZenReviewModal({ open, image, images, selectionContext, onClose, onNext, onPrevious, onAccept, onReject }) {
  if (!open || !image) return null;
  const currentIndex = images.findIndex((item) => item.id === image.id);
  const displayIndex = currentIndex >= 0 ? currentIndex + 1 : 1;
  return (
    <div className="bf-zen fixed inset-0 z-[70] flex flex-col bg-black text-white" role="dialog" aria-modal="true" aria-label="Zen image review">
      <header className="bf-zen-header">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">{image.originalName}</p>
          {image.relativePath !== image.originalName && <p className="truncate text-xs text-white/55">{image.relativePath}</p>}
          {selectionContext && (
            <p className="mt-1 max-w-4xl text-xs leading-5 text-amber-100/85">
              <span className="font-bold uppercase tracking-[0.14em] text-amber-300/90">Context</span> {selectionContext}
            </p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className={`rounded px-3 py-1 text-xs font-bold uppercase tracking-[0.12em] ${image.reviewState === "REJECTED" ? "bg-red-500 text-white" : "bg-emerald-500 text-white"}`}>
            {image.reviewState.toLowerCase()}
          </span>
          <button className="bf-icon-button text-white/70 hover:text-white" type="button" aria-label="Close zen mode" onClick={onClose}>
            <X className="size-4" />
          </button>
        </div>
      </header>
      <main className="relative min-h-0 flex-1 bg-black">
        <img className="h-full w-full object-contain" src={`${API_BASE_URL}/files/${image.id}`} alt={image.relativePath} />
        <button
          className="bf-zen-arrow bf-zen-previous"
          type="button"
          aria-label="Previous image"
          disabled={currentIndex <= 0}
          onClick={onPrevious}
        >
          <ArrowLeft />
        </button>
        <button
          className="bf-zen-arrow bf-zen-next"
          type="button"
          aria-label="Next image"
          disabled={currentIndex >= images.length - 1}
          onClick={onNext}
        >
          <ArrowRight />
        </button>
      </main>
      <footer className="bf-zen-footer">
        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-white/65">
          <span className="bf-shortcut border-white/15 bg-white/10 text-white/75">{displayIndex} / {images.length}</span>
          <span className="bf-shortcut border-white/15 bg-white/10 text-white/75">A accept</span>
          <span className="bf-shortcut border-white/15 bg-white/10 text-white/75">D reject</span>
          <span className="bf-shortcut border-white/15 bg-white/10 text-white/75">← previous</span>
          <span className="bf-shortcut border-white/15 bg-white/10 text-white/75">→ next</span>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:flex">
          <button className="bf-button-secondary border-emerald-400/40 bg-emerald-500/10 text-emerald-100" type="button" onClick={onAccept}>
            <Check className="size-4" /> Accept
          </button>
          <button className="bf-button-secondary border-red-400/40 bg-red-500/10 text-red-100" type="button" onClick={onReject}>
            <X className="size-4" /> Reject
          </button>
        </div>
      </footer>
    </div>
  );
}

function SelectionContextPanel({ context, onEdit }) {
  return (
    <section className="bf-selection-context" aria-label="Selection context">
      <div className="min-w-0">
        <span className="bf-eyebrow-accent">Selection context</span>
        <p>{context || "Add what reviewers should look for in this cohort."}</p>
      </div>
      <button className="bf-icon-button" type="button" onClick={onEdit} aria-label={context ? "Edit context" : "Add selection context"} title={context ? "Edit context" : "Add selection context"}><Info /></button>
    </section>
  );
}

function SelectionContextDialog({ open, cohort, saving, onClose, onSave }) {
  const [name, setName] = useState("");
  const [selectionContext, setSelectionContext] = useState("");

  useEffect(() => {
    if (open && cohort) {
      setName(cohort.name || "");
      setSelectionContext(cohort.selectionContext || "");
    }
  }, [cohort, open]);

  if (!open || !cohort) return null;

  function submit(event) {
    event.preventDefault();
    onSave({ name: name.trim(), selectionContext });
  }

  return (
    <div className="fixed inset-0 z-[75] transition" aria-hidden={!open} inert={!open ? "" : undefined}>
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-label="Dismiss selection context dialog"
      />
      <form
        className="absolute left-1/2 top-1/2 bf-dialog w-[min(36rem,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 rounded-md border border-[var(--bf-card-border)] bg-[var(--bf-page-bg)] p-5 shadow-[var(--bf-modal-shadow)]"
        role="dialog"
        aria-modal="true"
        aria-label="Edit selection context"
        onSubmit={submit}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="bf-eyebrow-accent">Study context</p>
            <h2 className="font-display text-xl font-bold tracking-tight text-[var(--bf-text)]">Selection context</h2>
            <p className="mt-1 text-sm text-[var(--bf-text-muted)]">Describe what reviewers should look for in this cohort.</p>
          </div>
          <button className="bf-icon-button" type="button" aria-label="Close selection context dialog" onClick={onClose} disabled={saving}>
            <X className="size-4" />
          </button>
        </div>

        <label className="bf-label mt-3">
          Cohort name
          <input className="bf-input mt-2" value={name} onChange={(event) => setName(event.target.value)} />
        </label>

        <label className="bf-label mt-3">
          Selection context
          <textarea
            className="bf-input mt-2 min-h-24 resize-y leading-6"
            maxLength={2000}
            value={selectionContext}
            onChange={(event) => setSelectionContext(event.target.value)}
            placeholder="Example: Select contrast-enhanced thorax CT samples with diagnostic axial lung-window coverage."
          />
        </label>
        <p className="mt-2 text-xs text-[var(--bf-text-subtle)]">{selectionContext.length}/2000 characters</p>

        <div className="mt-3 flex flex-wrap justify-end gap-2">
          <button className="bf-button-secondary" type="button" onClick={onClose} disabled={saving}>Cancel</button>
          <button className="bf-button-primary" type="submit" disabled={saving}>
            {saving ? <Loader2 className="size-4 animate-spin" /> : <Check className="size-4" />}
            Save context
          </button>
        </div>
      </form>
    </div>
  );
}



function DashboardHeader({ onAddCohort }) {
  return (
    <div className="bf-dashboard-header">
      <div><h1>Image cohorts</h1><p>Create a cohort, review images, and export your selection.</p></div>
      <button className="bf-button-primary bf-mobile-add" type="button" onClick={onAddCohort}><Plus />Add cohort</button>
    </div>
  );
}

function CohortDashboard({ cohorts, onOpenCohort, onAddCohort }) {
  if (!cohorts.length) return (
    <section className="bf-empty-cohorts">
      <FolderUp className="size-8 text-ember" />
      <h2>Add your first cohort</h2><p>Drop a folder of images or DICOM studies to start reviewing.</p>
      <button className="bf-button-primary" type="button" onClick={onAddCohort}><Plus />Add cohort</button>
    </section>
  );
  return <section className="bf-cohorts" aria-label="Cohorts">{cohorts.map(cohort => (
    <button key={cohort.id} type="button" className="bf-cohort-card" onClick={() => onOpenCohort(cohort.id)}>
      <div className="flex items-center justify-between gap-2"><LayoutDashboard className="text-ember" /><span className="bf-eyebrow-accent">{cohort.status.toLowerCase()}</span></div>
      <h2 title={cohort.name}>{cohort.name}</h2>
      <div className="bf-cohort-meta"><span>{cohort.imageCount} images</span><span>{cohort.exports?.length || 0} exports</span><span>{new Date(cohort.createdAt).toLocaleDateString()}</span></div>
      {cohort.selectionContext && <p className="line-clamp-2">{cohort.selectionContext}</p>}
      {cohort.exports?.[0] && <p>Last export {new Date(cohort.exports[0].createdAt).toLocaleDateString()}</p>}
    </button>
  ))}</section>;
}

function ReviewToolbar({ cohorts, activeCohortId, onSelectCohort, filter, onFilter }) {
  return (
    <div className="bf-review-toolbar">
      <CohortMenu cohorts={cohorts} activeCohortId={activeCohortId} onSelectCohort={onSelectCohort} />
      <div className="bf-filter-buttons">
        {["all", "accepted", "rejected"].map((item) => (
          <button
            key={item}
            type="button"
            className={`bf-chip ${filter === item ? "bf-chip-active" : ""}`}
            onClick={() => onFilter(item)}
            aria-pressed={filter === item}
          >
            {item}
          </button>
        ))}
      </div>
    </div>
  );
}

function CohortMenu({ cohorts, activeCohortId, onSelectCohort }) {
  const activeCohort = cohorts.find((cohort) => cohort.id === activeCohortId);
  return (
    <ForgeMenu
      align="left"
      label="Select cohort"
      trigger={
        <span className="bf-select-trigger">
          <span className="min-w-0">

            <span className="block truncate">{activeCohort?.name || "No cohort"}</span>
          </span>
          <ChevronDown className="size-4 shrink-0 text-[var(--bf-text-muted)]" aria-hidden />
        </span>
      }
    >
      <div className="abr-menu-header">
        <span className="abr-menu-kicker">Review data</span>
        <strong>Select cohort</strong>
      </div>
      <ForgeMenuItem
        icon={<LayoutDashboard className="size-4" />}
        current={!activeCohortId}
        onClick={() => onSelectCohort(null)}
      >
        No cohort
      </ForgeMenuItem>
      {cohorts.map((cohort) => (
        <ForgeMenuItem
          key={cohort.id}
          icon={cohort.id === activeCohortId ? <Check className="size-4" /> : <ImageIcon className="size-4" />}
          current={cohort.id === activeCohortId}
          onClick={() => onSelectCohort(cohort.id)}
        >
          <span className="abr-menu-item-copy">
            <span>{cohort.name}</span>
            <small>{cohort.imageCount} images</small>
          </span>
        </ForgeMenuItem>
      ))}
    </ForgeMenu>
  );
}

function AddCohortDialog({ open, uploading, onClose, onCreate }) {
  const [name, setName] = useState("");
  const [selectionContext, setSelectionContext] = useState("");
  const [entries, setEntries] = useState([]);
  const [localError, setLocalError] = useState("");
  const totalBytes = useMemo(() => entries.reduce((sum, entry) => sum + (entry.file?.size || 0), 0), [entries]);
  const imageCount = useMemo(() => entries.filter((entry) => isSupportedImageFile(entry.relativePath)).length, [entries]);
  const dicomCount = useMemo(() => entries.filter((entry) => isDicomCandidate(entry.relativePath) && !isSupportedImageFile(entry.relativePath)).length, [entries]);

  useEffect(() => {
    if (!open) {
      setName("");
      setSelectionContext("");
      setEntries([]);
      setLocalError("");
    }
  }, [open]);

  async function acceptEntries(nextEntries) {
    if (!nextEntries.length) {
      setLocalError("No supported image or DICOM files found. Drop PNG/JPEG/WebP/GIF/BMP/TIFF files or a DICOM folder.");
      return;
    }
    setLocalError("");
    setEntries(nextEntries);
    if (!name.trim()) {
      const firstPath = nextEntries[0].relativePath;
      setName(firstPath.split("/")[0] || `Cohort ${new Date().toLocaleString()}`);
    }
  }

  async function handleDialogDrop(event) {
    event.preventDefault();
    const nextEntries = await collectDroppedImageEntries(event.dataTransfer);
    await acceptEntries(nextEntries);
  }

  async function handleDialogFileInput(event) {
    const nextEntries = Array.from(event.target.files || [])
      .filter((file) => isSupportedFile(file.webkitRelativePath || file.name))
      .map((file) => ({ file, relativePath: file.webkitRelativePath || file.name }));
    await acceptEntries(nextEntries);
    event.target.value = "";
  }

  async function submit(event) {
    event.preventDefault();
    if (!name.trim()) {
      setLocalError("Please name the cohort.");
      return;
    }
    if (!entries.length) {
      setLocalError("Drop or select a folder first.");
      return;
    }
    await onCreate(entries, name.trim(), selectionContext);
  }

  return (
    <div className={`fixed inset-0 z-50 transition ${open ? "pointer-events-auto" : "pointer-events-none"}`} aria-hidden={!open} inert={!open ? "" : undefined}>
      <button
        type="button"
        className={`absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-200 ${open ? "opacity-100" : "opacity-0"}`}
        onClick={() => {
          if (!uploading) onClose();
        }}
        aria-label="Dismiss add cohort dialog"
      />
      <form
        className={`absolute left-1/2 top-1/2 bf-dialog w-[min(36rem,calc(100vw-2rem))] -translate-x-1/2 rounded-md border border-[var(--bf-card-border)] bg-[var(--bf-page-bg)] p-5 shadow-[var(--bf-modal-shadow)] transition duration-200 ${open ? "-translate-y-1/2 opacity-100" : "-translate-y-[46%] opacity-0"}`}
        role="dialog"
        aria-modal="true"
        aria-label="Add cohort"
        onSubmit={submit}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="bf-eyebrow-accent">New cohort</p>
            <h2 className="font-display text-xl font-bold tracking-tight text-[var(--bf-text)]">Add cohort</h2>
            <p className="mt-1 text-sm text-[var(--bf-text-muted)]">Name the cohort and drop an image or DICOM folder.</p>
          </div>
          <button className="bf-icon-button" type="button" aria-label="Close add cohort dialog" onClick={onClose} disabled={uploading}>
            <X className="size-4" />
          </button>
        </div>

        <label className="bf-label mt-3">
          Cohort name
          <input className="bf-input mt-2" value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Chest X-ray review 2026" autoFocus={open} />
        </label>

        <label className="bf-label mt-3">
          Selection context
          <textarea
            className="bf-input mt-2 min-h-20 resize-y leading-6"
            maxLength={2000}
            value={selectionContext}
            onChange={(event) => setSelectionContext(event.target.value)}
            placeholder="Example: Select contrast-enhanced thorax CT samples with diagnostic axial lung-window coverage."
          />
        </label>

        <label
          className="mt-3 flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-ember/35 bg-[var(--bf-card-bg)] p-6 text-center transition hover:border-ember/70 hover:bg-[var(--bf-surface-hover)]"
          onDragOver={(event) => event.preventDefault()}
          onDrop={handleDialogDrop}
        >
          <input className="hidden" type="file" multiple webkitdirectory="" directory="" accept={acceptedImageTypes} onChange={handleDialogFileInput} />
          {uploading ? <Loader2 className="mb-3 size-8 animate-spin text-ember" /> : <FolderUp className="mb-3 size-8 text-ember" />}
          <p className="font-display text-lg font-semibold tracking-normal">
            {uploading ? "Uploading cohort" : entries.length ? `${entries.length} files ready` : "Drop image or DICOM folder"}
          </p>
          <p className="mt-1 max-w-xl text-sm text-[var(--bf-text-muted)]">
            {entries.length
              ? `${formatBytes(totalBytes)} selected · ${imageCount} images · ${dicomCount} DICOM candidates`
              : "PNG, JPEG, WebP, GIF, BMP, TIFF, and uncompressed DICOM folders are supported."}
          </p>
          <p className="mt-1 max-w-xl text-xs text-[var(--bf-text-subtle)]">
            DICOM files are grouped into study cards with one selectable thumbnail per series.
          </p>
          {uploading && (
            <span className="mt-4 h-1.5 w-full max-w-sm overflow-hidden rounded bg-[var(--bf-field-bg)]">
              <span className="block h-full w-1/3 animate-[bf-progress_1.2s_ease-in-out_infinite] rounded bg-ember/70" />
            </span>
          )}
        </label>

        {localError && <p className="mt-3 rounded border border-red-500/30 bg-red-950/30 px-3 py-2 text-sm font-semibold text-red-300">{localError}</p>}

        <div className="mt-3 flex flex-wrap justify-end gap-2">
          <button className="bf-button-secondary" type="button" onClick={onClose} disabled={uploading}>Cancel</button>
          <button className="bf-button-primary" type="submit" disabled={uploading}>
            {uploading ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
            Create cohort
          </button>
        </div>
      </form>
    </div>
  );
}

function MobileSearch({ search, onSearch }) {
  return (
    <div className="bf-mobile-search xl:hidden">
      <div className="relative min-w-0 flex-1">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--bf-text-muted)]" />
        <input
          className="bf-input pl-9"
          placeholder="Search relative path"
          value={search}
          onChange={(event) => onSearch(event.target.value)}
        />
      </div>
    </div>
  );
}

function DropZone({ onDrop, onFileInput, uploading }) {
  return (
    <label
      className="group flex cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-ember/35 bg-[var(--bf-card-bg)] p-8 text-center shadow-[var(--bf-card-shadow)] transition hover:border-ember/70 hover:bg-[var(--bf-surface-hover)]"
      onDragOver={(event) => event.preventDefault()}
      onDrop={onDrop}
    >
      <input className="hidden" type="file" multiple webkitdirectory="" directory="" accept={acceptedImageTypes} onChange={onFileInput} />
      <div className="mb-3 rounded border border-ember/25 bg-ember/10 p-3 text-ember transition">
        {uploading ? <Loader2 className="size-6 animate-spin" /> : <FolderUp className="size-6" />}
      </div>
      <p className="font-display text-lg font-semibold tracking-normal">Drop an image folder</p>
      <p className="mt-1 max-w-xl text-sm text-[var(--bf-text-muted)]">Images are indexed directly; DICOM folders are grouped by study with one selectable thumbnail per series.</p>
    </label>
  );
}

function DicomStudyCards({ studies, imageFit, onToggleSeries, onOpenSeries }) {
  if (!studies.length) return null;
  const totalSeries = studies.reduce((sum, study) => sum + (study.series?.length || 0), 0);
  return (
    <section className="bf-panel p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <p className="bf-eyebrow-accent">DICOM studies</p>
          <h2 className="font-display text-lg font-semibold tracking-normal">
            {studies.length} studies · {totalSeries} series
          </h2>
        </div>
        <p className="text-xs leading-5 text-[var(--bf-text-muted)]">Click a series thumbnail to accept or reject it. Open uses the generated preview.</p>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-3 xl:grid-cols-2">
        {studies.map((study) => (
          <article key={study.studyUid} className="rounded-md border border-[var(--bf-field-border)] bg-[var(--bf-field-bg)] p-3">
            <div className="mb-3 min-w-0">
              <h3 className="truncate text-sm font-semibold text-[var(--bf-text)]">{study.studyDescription || shortIdentifier(study.studyUid)}</h3>
              <p className="truncate text-[11px] text-[var(--bf-text-muted)]">{study.studyUid}</p>
            </div>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
              {(study.series || []).map((series) => {
                const rejected = series.reviewState === "REJECTED";
                return (
                  <article key={series.seriesUid} className={`bf-image-card ${rejected ? "is-rejected" : ""}`}>
                    <button type="button" className="bf-image-review" onClick={() => onToggleSeries(series)}
                      title={series.seriesDescription || series.seriesUid}
                      aria-label={`${series.seriesDescription || series.seriesUid}: ${rejected ? "rejected" : "accepted"}. Toggle review state`}>
                      <div className="aspect-[4/3] overflow-hidden bg-black">
                        <img className={`h-full w-full ${imageFit === "contain" ? "object-contain" : "object-cover"}`}
                          src={`${API_BASE_URL}/files/${series.thumbnailImageId}`} alt={series.seriesDescription || series.seriesUid} loading="lazy" />
                      </div>
                      <div className="bf-image-caption"><p>{series.seriesDescription || "DICOM series"}</p>
                        <small>{[series.modality, `${series.imageCount} slices`].filter(Boolean).join(" · ")}</small>
                      </div>
                      <span className={`bf-review-badge ${rejected ? "is-rejected" : ""}`} aria-hidden="true">{rejected ? <X /> : <Check />}</span>
                    </button>
                    <div className="bf-image-actions"><button type="button" className="bf-tile-action"
                      aria-label={`Preview ${series.seriesDescription || series.seriesUid}`} onClick={() => onOpenSeries(series)}><Maximize2 /></button></div>
                  </article>
                );
              })}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function shortIdentifier(value) {
  const text = String(value || "unknown");
  return text.length > 22 ? `${text.slice(0, 10)}...${text.slice(-8)}` : text;
}

function Gallery({ images, imageSize, gapSize, imageFit, busy, filter, search, onToggle, focusedImageId, selectedImageIds, onFocusImage, onOpenDetail, onToggleSelected }) {
  if (busy && !images.length) {
    return <GallerySkeleton imageSize={imageSize} gapSize={gapSize} />;
  }
  if (!images.length) {
    const emptyText = search
      ? "No images match the current search."
      : filter !== "all"
        ? `No ${filter} images in this cohort.`
        : "Upload a cohort or adjust the filter/search controls.";
    return (
      <div className="rounded-md border border-[var(--bf-card-border)] bg-[var(--bf-card-bg)] p-10 text-center shadow-[var(--bf-card-shadow)]">
        <ImageIcon className="mx-auto mb-3 size-8 text-ember" />
        <p className="font-display text-lg font-semibold tracking-normal">No images in view</p>
        <p className="mt-1 text-sm text-[var(--bf-text-muted)]">{emptyText}</p>
      </div>
    );
  }
  return (
    <div
      className="bf-gallery"
      style={{
        gridTemplateColumns: `repeat(auto-fill, minmax(min(100%, ${imageSize}px), 1fr))`,
        gap: `${gapSize}px`
      }}
    >
      {images.map((image) => (
        <article key={image.id} className={`bf-image-card ${image.id === focusedImageId ? "is-focused" : ""} ${image.reviewState === "REJECTED" ? "is-rejected" : ""}`}>
          <button type="button" data-review-image className="bf-image-review" aria-label={`${image.originalName}: ${image.reviewState.toLowerCase()}. Toggle review state`} title={image.relativePath}
            onClick={() => { onFocusImage(image.id); onToggle(image); }} onFocus={() => onFocusImage(image.id)}>
            <div className="aspect-square overflow-hidden bg-black"><GalleryImage image={image} imageFit={imageFit} /></div>
            <div className="bf-image-caption">
              <p>{image.originalName}</p>
              {image.relativePath !== image.originalName && <small>{image.relativePath}</small>}
            </div>
            <span className={`bf-review-badge ${image.reviewState === "REJECTED" ? "is-rejected" : ""}`} aria-hidden="true">{image.reviewState === "REJECTED" ? <X /> : <Check />}</span>
          </button>
          <div className="bf-image-actions">
            <button type="button" className="bf-tile-action" aria-label={`Select ${image.originalName}`} aria-pressed={selectedImageIds.includes(image.id)} title="Select for batch review"
              onClick={() => { onFocusImage(image.id); onToggleSelected(image); }}>{selectedImageIds.includes(image.id) ? <Check /> : <Plus />}</button>
            <button type="button" className="bf-tile-action" aria-label={`Preview ${image.originalName}`} title="Open preview"
              onClick={() => { onFocusImage(image.id); onOpenDetail(image); }}><Maximize2 /></button>
          </div>
        </article>
      ))}
    </div>
  );
}

function GalleryImage({ image, imageFit }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center bg-[var(--bf-surface-subtle)] p-4 text-center">
        <ImageIcon className="mb-2 size-8 text-[var(--bf-text-subtle)]" />
        <p className="max-w-full truncate text-xs font-semibold text-[var(--bf-text-muted)]">Preview unavailable</p>
      </div>
    );
  }
  return (
    <img
      className={`h-full w-full transition duration-200 ${imageFit === "contain" ? "object-contain" : "object-cover"}`}
      src={`${API_BASE_URL}/files/${image.id}`}
      alt={image.relativePath}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}

function GallerySkeleton({ imageSize, gapSize }) {
  return (
    <div
      className="bf-gallery"
      style={{
        gridTemplateColumns: `repeat(auto-fill, minmax(min(100%, ${imageSize}px), 1fr))`,
        gap: `${gapSize}px`
      }}
      aria-label="Loading gallery"
    >
      {Array.from({ length: 12 }).map((_, index) => (
        <div key={index} className="overflow-hidden rounded-md border border-[var(--bf-card-border)] bg-[var(--bf-card-bg)] shadow-[var(--bf-card-shadow)]">
          <div className="aspect-square animate-pulse bg-[linear-gradient(110deg,rgba(255,255,255,0.04),rgba(255,106,26,0.14),rgba(255,255,255,0.04))] bg-[length:220%_100%]" />
          <div className="space-y-2 border-t border-[var(--bf-divider)] p-2">
            <div className="h-3 w-2/3 rounded bg-white/10" />
            <div className="h-2.5 w-full rounded bg-white/5" />
            <div className="h-2.5 w-1/2 rounded bg-white/5" />
          </div>
        </div>
      ))}
    </div>
  );
}

function Controls({ settings, onChange }) {
  function update(patch) {
    onChange({ ...settings, ...patch });
  }
  return (
    <div className="bf-panel p-3">
      <div className="mb-4 flex items-center gap-2">
        <SlidersHorizontal className="size-4 text-ember" />
        <h2 className="font-display text-lg font-semibold tracking-normal">Gallery controls</h2>
      </div>
      <label className="bf-label">
        Image size
        <input className="w-full accent-ember" type="range" min="96" max="420" value={settings.imageSize} onChange={(event) => update({ imageSize: Number(event.target.value) })} />
        <span className="text-xs text-[var(--bf-text-muted)]">{settings.imageSize}px</span>
      </label>
      <label className="bf-label mt-3">
        Spacing
        <input className="w-full accent-ember" type="range" min="4" max="32" value={settings.gapSize} onChange={(event) => update({ gapSize: Number(event.target.value) })} />
        <span className="text-xs text-[var(--bf-text-muted)]">{settings.gapSize}px</span>
      </label>
      <div className="mt-3">
        <span className="bf-label">Image fit</span>
        <div className="mt-2 grid grid-cols-2 gap-2">
          <button
            className={`bf-button-secondary ${settings.imageFit !== "contain" ? "border-ember/45 bg-ember/10 text-[var(--bf-text)]" : ""}`}
            type="button"
            onClick={() => update({ imageFit: "cover" })}
            aria-pressed={settings.imageFit !== "contain"}
          >
            <Maximize2 className="size-4" /> Crop
          </button>
          <button
            className={`bf-button-secondary ${settings.imageFit === "contain" ? "border-ember/45 bg-ember/10 text-[var(--bf-text)]" : ""}`}
            type="button"
            onClick={() => update({ imageFit: "contain" })}
            aria-pressed={settings.imageFit === "contain"}
          >
            <ImageIcon className="size-4" /> Fit
          </button>
        </div>
      </div>
      <label className="bf-label mt-3">
        Sort by
        <span className="relative mt-2 block">
        <select className="bf-select" value={settings.sortKey} onChange={(event) => update({ sortKey: event.target.value })}>
          <option value="relativePath">Path</option>
          <option value="originalName">Name</option>
          <option value="sizeBytes">File size</option>
          <option value="createdAt">Created</option>
          <option value="updatedAt">Updated</option>
          <option value="reviewState">Review state</option>
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-[var(--bf-text-muted)]" />
        </span>
      </label>
      <label className="bf-label mt-3">
        Direction
        <span className="relative mt-2 block">
        <select className="bf-select" value={settings.sortDirection} onChange={(event) => update({ sortDirection: event.target.value })}>
          <option value="asc">Ascending</option>
          <option value="desc">Descending</option>
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-[var(--bf-text-muted)]" />
        </span>
      </label>
    </div>
  );
}

function CohortPanel({ cohorts, activeCohortId, onSelect }) {
  return (
    <div className="bf-panel p-3">
      <h2 className="mb-3 bf-eyebrow-accent">Cohorts</h2>
      <div className="space-y-2">
        {cohorts.map((cohort) => (
          <button
            key={cohort.id}
            className={`w-full rounded border px-3 py-3 text-left transition ${cohort.id === activeCohortId ? "border-ember/45 bg-ember/10 shadow-[var(--bf-card-shadow)]" : "border-[var(--bf-field-border)] bg-[var(--bf-field-bg)] hover:bg-[var(--bf-surface-hover)]"}`}
            onClick={() => onSelect(cohort.id)}
          >
            <p className="truncate text-sm font-semibold">{cohort.name}</p>
            <p className="mt-1 text-xs text-[var(--bf-text-muted)]">{cohort.imageCount} images - {cohort.status.toLowerCase()}</p>
          </button>
        ))}
        {!cohorts.length && <p className="text-sm text-[var(--bf-text-muted)]">No cohorts yet.</p>}
      </div>
    </div>
  );
}

function Metric({ label, value, tone }) {
  const tones = {
    blue: "text-sky-300",
    coral: "text-red-300",
    gold: "text-amber-300"
  };
  return (
    <div className="min-w-24 rounded-md border border-[var(--bf-field-border)] bg-[var(--bf-field-bg)] px-3 py-2">
      <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--bf-text-muted)]">{label}</p>
      <p className={`font-display text-lg font-bold tracking-normal ${tones[tone]}`}>{value}</p>
    </div>
  );
}

function ToastViewport({ toasts, onDismiss }) {
  if (!toasts.length) return null;
  return (
    <div className="fixed right-4 top-16 z-[70] flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2" role="status" aria-live="polite">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onDismiss={() => onDismiss(toast.id)} />
      ))}
    </div>
  );
}

function Toast({ toast, onDismiss }) {
  const tone = toast.tone || "info";
  const icons = {
    success: <CheckCircle2 className="size-4 text-emerald-300" />,
    error: <AlertCircle className="size-4 text-red-300" />,
    loading: <Loader2 className="size-4 animate-spin text-ember" />,
    info: <Info className="size-4 text-sky-300" />
  };
  const tones = {
    success: "border-emerald-400/25 bg-emerald-950/30",
    error: "border-red-400/30 bg-red-950/35",
    loading: "border-ember/30 bg-ember/10",
    info: "border-sky-400/25 bg-sky-950/25"
  };
  return (
    <div className={`flex items-start gap-3 rounded-md border p-3 shadow-[var(--bf-modal-shadow)] backdrop-blur-xl ${tones[tone] || tones.info}`}>
      <div className="mt-0.5 shrink-0">{icons[tone] || icons.info}</div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-[var(--bf-text)]">{toast.title}</p>
        {toast.message && <p className="mt-0.5 break-words text-xs leading-5 text-[var(--bf-text-muted)]">{toast.message}</p>}
      </div>
      <button className="bf-icon-button h-8 w-8 shrink-0" type="button" aria-label="Dismiss notification" onClick={onDismiss}>
        <X className="size-4" />
      </button>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
