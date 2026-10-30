"""LLM agent utilities for DataFrame and document workflows."""

from __future__ import annotations

from .._diagnostics import event, safe_error, batch_report, error_event, task_outcome
from .._http import guard_redirects

import base64
import json
import logging
import os
import pathlib
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class LLMRequestError(RuntimeError):
    """Raised when an LLM request fails."""


@dataclass
class LLMConfig:
    provider: str
    base_url: str
    api_key: Optional[str]
    model: str
    timeout: int


class LLMAgent:
    """Simple LLM agent for DataFrame and document directory workflows.

    Parameters
    ----------
    provider:
        Provider mode: ``openai``, ``anyllm``, or ``custom``. Defaults to
        ``LLM_PROVIDER`` or ``openai``.
    base_url:
        Provider base URL or custom endpoint. Defaults to ``LLM_BASE_URL``.
    api_key:
        Optional API key. Defaults to ``LLM_API_KEY`` and is sent as a bearer
        token when present.
    model:
        Model name for the provider. Defaults to ``LLM_MODEL``.
    timeout:
        Request timeout in seconds. Defaults to ``LLM_TIMEOUT`` or 30.
    extra_headers:
        Additional HTTP headers merged into the session.
    auth_required:
        Whether an API key is required. Defaults to true for ``openai`` and
        ``anyllm`` and false for ``custom``.
    verify_ssl:
        Whether HTTPS certificate verification is enabled for requests.

    Providers
    ---------
    - openai: uses Responses API at /v1/responses
    - anyllm: uses OpenAI-compatible Chat Completions at /v1/chat/completions
    - custom: uses `base_url` as a full endpoint and expects JSON {"text": "..."}

    Environment variables
    ---------------------
    LLM_PROVIDER, LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TIMEOUT
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        auth_required: Optional[bool] = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize an LLM agent using environment or explicit configuration.

        Parameters
        ----------
        provider:
            Provider mode: ``openai``, ``anyllm``, or ``custom``. Defaults to
            ``LLM_PROVIDER`` or ``openai``.
        base_url:
            Provider base URL or custom endpoint. Defaults to ``LLM_BASE_URL``.
        api_key:
            Optional API key. Defaults to ``LLM_API_KEY`` and is sent as a
            bearer token when present.
        model:
            Model name for the provider. Defaults to ``LLM_MODEL``.
        timeout:
            Request timeout in seconds. Defaults to ``LLM_TIMEOUT`` or 30.
        extra_headers:
            Additional HTTP headers merged into the session.
        auth_required:
            Whether an API key is required. Defaults to true for ``openai`` and
            ``anyllm`` and false for ``custom``.
        verify_ssl:
            Whether HTTPS certificate verification is enabled for requests.
        """
        self.config = LLMConfig(
            provider=(provider or os.environ.get("LLM_PROVIDER", "openai")).lower(),
            base_url=base_url or os.environ.get("LLM_BASE_URL", "https://api.openai.com"),
            api_key=api_key or os.environ.get("LLM_API_KEY"),
            model=model or os.environ.get("LLM_MODEL", "gpt-4.1-mini"),
            timeout=int(timeout or os.environ.get("LLM_TIMEOUT", "30")),
        )
        self.session = guard_redirects(requests.Session())
        self.verify_ssl = verify_ssl
        headers = extra_headers.copy() if extra_headers else {}
        if auth_required is None:
            auth_required = self.config.provider in {"openai", "anyllm"}
        if auth_required and not self.config.api_key:
            raise ValueError("api_key is required for this provider.")
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        headers.setdefault("Content-Type", "application/json")
        self.session.headers.update(headers)
        event(logger, "llm", "activity", level=logging.DEBUG)

    def prompt(
        self,
        user_prompt: str,
        *,
        image_path: Optional[str] = None,
        file_path: Optional[str] = None,
        mode: str = "text",
    ) -> str:
        """Send a single prompt and return the model response."""
        if mode == "text":
            return self._request(user_prompt)
        return self._request_multimodal(
            user_prompt=user_prompt,
            image_path=image_path,
            file_path=file_path,
            mode=mode,
        )

    def chat(
        self,
        user_prompt: str,
        *,
        image_path: Optional[str] = None,
        file_path: Optional[str] = None,
        mode: str = "text",
    ) -> str:
        """Alias for prompt (kept for convenience)."""
        return self.prompt(
            user_prompt=user_prompt,
            image_path=image_path,
            file_path=file_path,
            mode=mode,
        )

    @batch_report("llm")
    def run_on_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str,
        prompt: str,
        output_col: str = "llm_output",
        format_func: Optional[Callable[[str, Dict[str, Any]], str]] = None,
        image_col: Optional[str] = None,
        file_col: Optional[str] = None,
        mode: str = "text",
    ) -> pd.DataFrame:
        """Run a prompt over a DataFrame column and append results.

        Parameters
        ----------
        df:
            Input DataFrame.
        text_col:
            Column containing text to analyze.
        prompt:
            Prompt template. If format_func is not provided, text is appended.
        output_col:
            Name of output column.
        format_func:
            Optional function (text, row_dict) -> prompt string.
        image_col:
            Optional column with image file paths or URLs.
        file_col:
            Optional column with PDF file paths (OpenAI Responses only).
        mode:
            "text", "image", "pdf", or "auto".
        """
        if text_col not in df.columns:
            raise ValueError(f"Column '{text_col}' not found in DataFrame.")
        if image_col and image_col not in df.columns:
            raise ValueError(f"Column '{image_col}' not found in DataFrame.")
        if file_col and file_col not in df.columns:
            raise ValueError(f"Column '{file_col}' not found in DataFrame.")
        if not df.columns.is_unique:
            raise ValueError("DataFrame columns must be unique.")

        event(logger, "llm", "activity", level=logging.DEBUG)
        results: List[str] = []
        for row in df.itertuples(index=False, name=None):
            row_dict = dict(zip(df.columns, row))
            text = str(row_dict.get(text_col, ""))
            if format_func:
                user_prompt = format_func(text, row_dict)
            else:
                user_prompt = f"{prompt}\n\n{text}"
            failed = False
            try:
                if mode == "text":
                    results.append(self._request(user_prompt))
                else:
                    image_path = str(row_dict.get(image_col)) if image_col else None
                    file_path = str(row_dict.get(file_col)) if file_col else None
                    results.append(
                        self._request_multimodal(
                            user_prompt=user_prompt,
                            image_path=image_path,
                            file_path=file_path,
                            mode=mode,
                        )
                    )
            except Exception as exc:
                error_event(logger, "llm", exc)
                results.append(f"ERROR: {safe_error(exc)}")
                failed = True
            task_outcome(failed=failed)
        out = df.copy()
        out[output_col] = results
        return out

    @batch_report("llm")
    def run_on_documents(
        self,
        documents: List[str],
        prompt: str,
        output_csv: Optional[str] = None,
        mode: str = "text",
    ) -> pd.DataFrame:
        """Run a prompt over a list of documents (paths or raw strings).

        Parameters
        ----------
        documents:
            List of file paths or raw text strings.
        prompt:
            Prompt to apply to each document.
        output_csv:
            Optional path to write results as CSV.
        mode:
            "text", "image", "pdf", or "auto".
        """
        rows: List[Dict[str, Any]] = []
        event(logger, "llm", "activity", level=logging.DEBUG)
        for idx, doc in enumerate(documents):
            failed = False
            path = pathlib.Path(doc)
            text = None
            image_path = None
            file_path = None
            if path.exists():
                if mode == "auto":
                    if path.suffix.lower() == ".pdf":
                        file_path = str(path)
                    elif path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
                        image_path = str(path)
                    else:
                        text = path.read_text(errors="ignore")
                elif mode == "pdf":
                    file_path = str(path)
                elif mode == "image":
                    image_path = str(path)
                else:
                    text = path.read_text(errors="ignore")
            else:
                text = doc

            try:
                if mode == "text":
                    user_prompt = f"{prompt}\n\n{text or ''}"
                    output = self._request(user_prompt)
                else:
                    user_prompt = f"{prompt}\n\n{text or ''}" if text else prompt
                    output = self._request_multimodal(
                        user_prompt=user_prompt,
                        image_path=image_path,
                        file_path=file_path,
                        mode=mode,
                    )
            except Exception as exc:
                error_event(logger, "llm", exc)
                output = f"ERROR: {safe_error(exc)}"
                failed = True

            task_outcome(failed=failed)

            rows.append(
                {
                    "document_index": idx,
                    "document": doc,
                    "output": output,
                }
            )

        df = pd.DataFrame(rows)
        if output_csv:
            df.to_csv(output_csv, index=False)
        return df

    def prompt_documents(
        self,
        documents: List[str],
        prompt: str,
        output_csv: Optional[str] = None,
        mode: str = "text",
    ) -> pd.DataFrame:
        """Short alias for run_on_documents."""
        return self.run_on_documents(
            documents=documents,
            prompt=prompt,
            output_csv=output_csv,
            mode=mode,
        )

    def prompt_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str,
        prompt: str,
        output_col: str = "llm_output",
        output_csv: Optional[str] = None,
        format_func: Optional[Callable[[str, Dict[str, Any]], str]] = None,
        image_col: Optional[str] = None,
        file_col: Optional[str] = None,
        mode: str = "text",
    ) -> pd.DataFrame:
        """Run a prompt over a DataFrame column and optionally save results."""
        out = self.run_on_dataframe(
            df=df,
            text_col=text_col,
            prompt=prompt,
            output_col=output_col,
            format_func=format_func,
            image_col=image_col,
            file_col=file_col,
            mode=mode,
        )
        if output_csv:
            out.to_csv(output_csv, index=False)
        return out

    def prompt_df(
        self,
        df: pd.DataFrame,
        text_col: str,
        prompt: str,
        output_col: str = "llm_output",
        output_csv: Optional[str] = None,
        format_func: Optional[Callable[[str, Dict[str, Any]], str]] = None,
        image_col: Optional[str] = None,
        file_col: Optional[str] = None,
        mode: str = "text",
    ) -> pd.DataFrame:
        """Short alias for prompt_dataframe."""
        return self.prompt_dataframe(
            df=df,
            text_col=text_col,
            prompt=prompt,
            output_col=output_col,
            output_csv=output_csv,
            format_func=format_func,
            image_col=image_col,
            file_col=file_col,
            mode=mode,
        )

    def run_prompt_on_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str,
        prompt: str,
        output_col: str = "llm_output",
        output_csv: Optional[str] = None,
        format_func: Optional[Callable[[str, Dict[str, Any]], str]] = None,
        image_col: Optional[str] = None,
        file_col: Optional[str] = None,
        mode: str = "text",
    ) -> pd.DataFrame:
        """Backward-compatible alias for prompt_dataframe."""
        return self.prompt_dataframe(
            df=df,
            text_col=text_col,
            prompt=prompt,
            output_col=output_col,
            output_csv=output_csv,
            format_func=format_func,
            image_col=image_col,
            file_col=file_col,
            mode=mode,
        )

    def describe_python_file(
        self,
        file_path: str | pathlib.Path,
        output_md: str | pathlib.Path,
        prompt: Optional[str] = None,
    ) -> str:
        """Generate a scientific-methods style description of a Python file.

        Parameters
        ----------
        file_path:
            Path to the Python file to analyze.
        output_md:
            Path to write the markdown summary.
        prompt:
            Optional prompt override.
        """
        path = pathlib.Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if path.suffix.lower() != ".py":
            raise ValueError("describe_python_file expects a .py file.")
        text = path.read_text(errors="ignore")
        default_prompt = (
            "You are writing a Methods section for a scientific paper. "
            "Explain what this Python module does, its inputs/outputs, "
            "key processing steps, and any assumptions. Use concise, "
            "formal scientific language and bullet points where helpful."
        )
        user_prompt = f"{prompt or default_prompt}\n\n```python\n{text}\n```"
        output = self._request(user_prompt)
        out_path = pathlib.Path(output_md)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output)
        return output

    @batch_report("llm")
    def run_on_directory(
        self,
        input_dir: str | pathlib.Path,
        prompt: str,
        glob: str = "*.txt",
        mode: str = "text",
    ) -> Dict[str, str]:
        """Run a prompt over all files in a directory.

        Returns a mapping of filename -> model output.
        """
        base = pathlib.Path(input_dir)
        results: Dict[str, str] = {}
        paths = sorted(path for path in base.glob(glob) if path.is_file())
        if len({path.name for path in paths}) != len(paths):
            raise ValueError("Duplicate filenames would overwrite directory results; process subdirectories separately.")
        event(logger, "llm", "activity", level=logging.DEBUG)
        for path in paths:
            failed = False
            try:
                if mode == "auto":
                    if path.suffix.lower() == ".pdf":
                        results[path.name] = self._request_multimodal(
                            user_prompt=prompt,
                            image_path=None,
                            file_path=str(path),
                            mode="pdf",
                        )
                        continue
                    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
                        results[path.name] = self._request_multimodal(
                            user_prompt=prompt,
                            image_path=str(path),
                            file_path=None,
                            mode="image",
                        )
                        continue
                text = path.read_text(errors="ignore")
                user_prompt = f"{prompt}\n\n{text}"
                if mode in {"text", "auto"}:
                    results[path.name] = self._request(user_prompt)
                else:
                    results[path.name] = self._request_multimodal(
                        user_prompt=user_prompt,
                        image_path=str(path) if mode == "image" else None,
                        file_path=str(path) if mode == "pdf" else None,
                        mode=mode,
                    )
            except Exception as exc:
                error_event(logger, "llm", exc)
                results[path.name] = f"ERROR: {safe_error(exc)}"
                failed = True
            finally:
                if path.name in results:
                    task_outcome(failed=failed)
        return results

    def prompt_directory(
        self,
        input_dir: str | pathlib.Path,
        prompt: str,
        glob: str = "*.txt",
        mode: str = "text",
    ) -> Dict[str, str]:
        """Short alias for run_on_directory."""
        return self.run_on_directory(
            input_dir=input_dir,
            prompt=prompt,
            glob=glob,
            mode=mode,
        )

    def _request(self, user_prompt: str) -> str:
        """Route a text-only request to the configured provider."""
        try:
            if self.config.provider == "openai":
                return self._request_openai_responses(user_prompt)
            if self.config.provider == "anyllm":
                return self._request_chat_completions(user_prompt)
            if self.config.provider == "custom":
                return self._request_custom(user_prompt)
            raise ValueError(f"Unknown provider: {self.config.provider}")
        except Exception as exc:
            error_event(logger, "llm", exc)
            raise LLMRequestError(safe_error(exc)) from None

    def _request_multimodal(
        self,
        user_prompt: str,
        image_path: Optional[str],
        file_path: Optional[str],
        mode: str,
    ) -> str:
        """Route a multimodal request to the configured provider."""
        try:
            if self.config.provider == "openai":
                return self._request_openai_multimodal(user_prompt, image_path, file_path, mode)
            if self.config.provider == "anyllm":
                return self._request_anyllm_image(user_prompt, image_path, mode)
            if self.config.provider == "custom":
                return self._request_custom_multimodal(user_prompt, image_path, file_path, mode)
            raise ValueError(f"Unknown provider: {self.config.provider}")
        except Exception as exc:
            error_event(logger, "llm", exc)
            raise LLMRequestError(safe_error(exc)) from None

    def _request_openai_responses(self, user_prompt: str) -> str:
        """Send a text-only request to OpenAI Responses API."""
        url = self.config.base_url.rstrip("/") + "/v1/responses"
        payload = {
            "model": self.config.model,
            "input": [
                {"role": "user", "content": user_prompt},
            ],
        }
        resp = self.session.post(
            url, data=json.dumps(payload), timeout=self.config.timeout, verify=self.verify_ssl
        )
        resp.raise_for_status()
        data = resp.json()
        return _extract_responses_text(data)

    def _request_chat_completions(self, user_prompt: str) -> str:
        """Send a text-only request to Chat Completions API."""
        url = self.config.base_url.rstrip("/") + "/v1/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }
        resp = self.session.post(
            url, data=json.dumps(payload), timeout=self.config.timeout, verify=self.verify_ssl
        )
        resp.raise_for_status()
        data = resp.json()
        return _extract_chat_text(data)

    def _request_custom(self, user_prompt: str) -> str:
        """Send a text-only request to a custom endpoint."""
        url = self.config.base_url
        payload = {"text": user_prompt, "model": self.config.model}
        resp = self.session.post(
            url, data=json.dumps(payload), timeout=self.config.timeout, verify=self.verify_ssl
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data.get("text", ""))

    def _request_openai_multimodal(
        self,
        user_prompt: str,
        image_path: Optional[str],
        file_path: Optional[str],
        mode: str,
    ) -> str:
        """Send a multimodal request to OpenAI Responses API."""
        url = self.config.base_url.rstrip("/") + "/v1/responses"
        content: List[Dict[str, Any]] = [{"type": "input_text", "text": user_prompt}]

        if mode in {"image", "auto"} and image_path:
            image_data = _load_image_data_url(image_path)
            content.append({"type": "input_image", "image_url": image_data})
        if mode in {"pdf", "auto"} and file_path:
            filename, file_data = _load_file_base64(file_path)
            content.append({"type": "input_file", "filename": filename, "file_data": file_data})

        payload = {"model": self.config.model, "input": [{"role": "user", "content": content}]}
        resp = self.session.post(
            url, data=json.dumps(payload), timeout=self.config.timeout, verify=self.verify_ssl
        )
        resp.raise_for_status()
        data = resp.json()
        return _extract_responses_text(data)

    def _request_anyllm_image(
        self,
        user_prompt: str,
        image_path: Optional[str],
        mode: str,
    ) -> str:
        """Send an image prompt to an OpenAI-compatible Chat Completions endpoint."""
        if mode not in {"image", "auto"} or not image_path:
            raise ValueError("anyllm provider supports image mode only.")
        url = self.config.base_url.rstrip("/") + "/v1/chat/completions"
        image_data = _load_image_data_url(image_path)
        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": image_data}},
                    ],
                }
            ],
        }
        resp = self.session.post(
            url, data=json.dumps(payload), timeout=self.config.timeout, verify=self.verify_ssl
        )
        resp.raise_for_status()
        data = resp.json()
        return _extract_chat_text(data)

    def _request_custom_multimodal(
        self,
        user_prompt: str,
        image_path: Optional[str],
        file_path: Optional[str],
        mode: str,
    ) -> str:
        """Send a multimodal request to a custom endpoint."""
        url = self.config.base_url
        payload: Dict[str, Any] = {"text": user_prompt, "model": self.config.model}
        if mode in {"image", "auto"} and image_path:
            payload["image_base64"] = _load_file_base64(image_path)[1]
        if mode in {"pdf", "auto"} and file_path:
            payload["file_base64"] = _load_file_base64(file_path)[1]
            payload["filename"] = _load_file_base64(file_path)[0]
        resp = self.session.post(
            url, data=json.dumps(payload), timeout=self.config.timeout, verify=self.verify_ssl
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data.get("text", ""))


def _extract_chat_text(data: Dict[str, Any]) -> str:
    """Extract text content from chat-completions response JSON."""
    choices = data.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    return str(message.get("content", ""))


def _extract_responses_text(data: Dict[str, Any]) -> str:
    """Extract text content from responses API output JSON."""
    output = data.get("output", [])
    if not output:
        return ""
    # Responses output is a list of items; collect all text parts
    texts: List[str] = []
    for item in output:
        for content in item.get("content", []) or []:
            if content.get("type") == "output_text":
                texts.append(content.get("text", ""))
    return "\n".join(texts).strip()


def _load_file_base64(path_or_url: str) -> Tuple[str, str]:
    """Load a local file and return (filename, base64)."""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        raise ValueError("URL inputs are not supported for file_base64. Download locally first.")
    path = pathlib.Path(path_or_url)
    data = path.read_bytes()
    return path.name, base64.b64encode(data).decode("utf-8")


def _load_image_data_url(path_or_url: str) -> str:
    """Return a data URL for a local image or pass through URL."""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    path = pathlib.Path(path_or_url)
    ext = path.suffix.lower().lstrip(".") or "png"
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/{ext};base64,{data}"
