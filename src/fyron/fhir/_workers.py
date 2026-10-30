"""Parent-owned token leases and monitored worker pools."""

import logging
import math
import multiprocessing as mp
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from multiprocessing.connection import wait

from ._device_auth import DeviceAuthError, _BearerAuth
from .._diagnostics import event

logger = logging.getLogger("fyron.fhir.rest")
_auth = None
_events = None
_job = None


def positive_timeout(value, name):
    if value is True or value is False:
        raise ValueError(f"{name} must be finite and positive.")
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be finite and positive.") from None
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and positive.")
    return result


def stage(value):
    if _events is not None and _job is not None:
        _events.put((_job, value, time.monotonic()))


def worker_auth():
    return _auth


class PipeAuth(_BearerAuth):
    def __init__(self, connection, timeout, authorization_endpoint):
        self.connection = connection
        self.timeout = timeout
        self.authorization_endpoint = authorization_endpoint
        self.token = None
        self.generation = None
        self.until = 0

    def get_token(self, rejected=None):
        if rejected is None and self.token and time.monotonic() < self.until:
            return self.token
        stage("authentication")
        try:
            self.connection.send(
                (
                    self.generation if rejected is not None else None,
                    time.monotonic() + self.timeout,
                )
            )
            if not self.connection.poll(self.timeout):
                self.connection.close()
                raise DeviceAuthError("Worker token wait exceeded its deadline.")
            ok, payload = self.connection.recv()
        except (EOFError, OSError):
            raise DeviceAuthError("Worker token coordinator disconnected.") from None
        if not ok:
            raise DeviceAuthError("Parent token renewal failed.")
        self.token, self.generation, self.until = payload
        stage("http")
        return self.token


def _initialize(channels, slot, events, timeout, endpoint):
    from multiprocessing.util import Finalize
    from .rest import _close_worker_session
    _close_worker_session()
    Finalize(None, _close_worker_session, exitpriority=10)
    global _auth, _events
    _events = events
    _auth = None
    if channels is not None:
        with slot.get_lock():
            index = slot.value
            slot.value += 1
        for number, connection in enumerate(channels):
            if number != index:
                connection.close()
        if index >= len(channels):
            raise RuntimeError("Authentication worker cannot be replaced.")
        _auth = PipeAuth(channels[index], timeout, endpoint)


def _execute(item):
    global _job
    number, function, args = item
    _job = number
    stage("started")
    try:
        result = function(args)
        stage("delivery")
        return number, result
    finally:
        _job = None


class TokenBroker:
    def __init__(self, auth):
        self.auth = auth
        self.generation = 0
        self.last_token = None
        self.lock = threading.Lock()

    def lease(self, rejected, deadline=None):
        with self.lock:
            return self._lease(rejected, deadline)

    def _lease(self, rejected, deadline):
        from .auth import TokenAuth

        getter = (
            self.auth._get_token
            if isinstance(self.auth, TokenAuth)
            else self.auth.get_token
        )
        force = rejected is not None and rejected == self.generation
        before = (
            getattr(self.auth, "_renew_at", None),
            getattr(self.auth, "state", {}).get("issued_at"),
            getattr(self.auth, "_issued_at", None),
        )
        if deadline is not None and time.monotonic() >= deadline:
            raise DeviceAuthError("Worker authentication deadline exceeded.")
        self.auth._worker_deadline = deadline or time.monotonic() + getattr(
            self.auth, "_worker_timeout", 120
        )
        try:
            token = getter(rejected=self.last_token if force else None)
        finally:
            self.auth._worker_deadline = None
        after = (
            getattr(self.auth, "_renew_at", None),
            getattr(self.auth, "state", {}).get("issued_at"),
            getattr(self.auth, "_issued_at", None),
        )
        if force or token != self.last_token or before != after:
            self.generation += 1
        self.last_token = token
        if len(token.encode("utf-8")) > 16384:
            raise DeviceAuthError(
                "Access token exceeds worker transport limit (16 KiB)."
            )
        now = time.monotonic()
        until = now + 30
        renewal = getattr(self.auth, "_renew_at", None)
        if renewal is not None:
            until = renewal
        state = getattr(self.auth, "state", {})
        if state.get("lifetime") is not None:
            until = now + max(
                0, state["issued_at"] + 0.75 * state["lifetime"] - time.time()
            )
        if isinstance(self.auth, TokenAuth):
            import jwt

            try:
                claims = jwt.decode(token, options={"verify_signature": False})
                if "iat" in claims and "exp" in claims:
                    until = now + max(
                        0,
                        claims["iat"]
                        + 0.75 * (claims["exp"] - claims["iat"])
                        - time.time(),
                    )
            except (jwt.PyJWTError, TypeError, ValueError):
                pass
            if self.auth._refresh_delta is not None:
                until = min(
                    until,
                    now
                    + max(
                        0,
                        (self.auth.auth_time + self.auth._refresh_delta).timestamp()
                        - time.time(),
                    ),
                )
        return token, self.generation, until


@contextmanager
def managed_pool(auth, processes, auth_timeout):
    """Give each spawned worker one private pipe and one cached token lease."""
    ctx = mp.get_context("spawn")
    events = ctx.Queue()
    pairs = [ctx.Pipe() for _ in range(processes)] if auth is not None else []
    # Transfer descriptors during spawn, not through a resource-sharer socket.
    channels = [child for _, child in pairs] if pairs else None
    slot = ctx.Value("i", 0) if pairs else None
    stop = threading.Event()
    broker = TokenBroker(auth) if auth is not None else None

    def serve():
        connections = [parent for parent, _ in pairs]
        pending = []
        # The dispatcher keeps draining pipes while renewal is serialized.
        with ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="fyron-token-renewal"
        ) as executor:
            while not stop.is_set():
                if not connections:
                    stop.wait(0.05)
                for conn in wait(connections, timeout=0.05) if connections else []:
                    try:
                        rejected, deadline = conn.recv()
                        pending.append(
                            (conn, executor.submit(broker.lease, rejected, deadline))
                        )
                    except (EOFError, OSError):
                        connections.remove(conn)
                for conn, future in pending[:]:
                    if future.done():
                        try:
                            payload = (True, future.result())
                        except Exception:  # noqa: BLE001 - never send provider exceptions or secrets over IPC.
                            payload = (False, None)
                        try:
                            conn.send(payload)
                        except (EOFError, OSError):
                            pass
                        pending.remove((conn, future))
            for _, future in pending:
                future.cancel()

    thread = (
        threading.Thread(target=serve, name="fyron-token-dispatcher")
        if broker
        else None
    )
    pool = None
    thread_started = False
    completed_normally = False
    old_deadline = getattr(auth, "_worker_deadline", None)
    old_timeout = getattr(auth, "_worker_timeout", None)
    if auth is not None:
        auth._worker_timeout = auth_timeout
    try:
        pool = ctx.Pool(
            processes,
            initializer=_initialize,
            initargs=(
                channels,
                slot,
                events,
                auth_timeout,
                getattr(auth, "authorization_endpoint", None),
            ),
        )
        if thread:
            thread.start()
            thread_started = True
        yield pool, events
        completed_normally = True
    finally:
        stop.set()
        cancel = getattr(auth, "_cancel", None)
        if cancel is not None:
            cancel.set()
        if pool is not None:
            if completed_normally:
                pool.close()
            else:
                pool.terminate()
            pool.join()
        if thread_started:
            thread.join()
        if cancel is not None:
            cancel.clear()
        if auth is not None:
            auth._worker_deadline = old_deadline
            if old_timeout is None:
                del auth._worker_timeout
            else:
                auth._worker_timeout = old_timeout
        for pair in pairs:
            for conn in pair:
                conn.close()
        for q in (events,):
            if q is not None:
                if hasattr(q, "cancel_join_thread"):
                    q.cancel_join_thread()
                q.close()


def monitored_results(pool, events, function, args, timeout):
    """Fail on dead workers or elapsed execution deadlines, never skip jobs."""
    from .rest import FHIRRequestError

    workers = list(pool._pool)
    active = {}
    completed = set()
    iterator = pool.imap_unordered(
        _execute, ((i, function, item) for i, item in enumerate(args))
    )
    last_warning = time.monotonic()
    while len(completed) < len(args):
        while True:
            try:
                number, state, timestamp = events.get_nowait()
            except queue.Empty:
                break
            if number not in completed:
                start = active.get(number, (timestamp, state))[0]
                active[number] = start, state
        dead = [p for p in workers if p.exitcode is not None]
        if dead:
            raise FHIRRequestError(
                f"Parallel worker exited; {len(args) - len(completed)} queries unfinished."
            )
        now = time.monotonic()
        for number, (start, state) in active.items():
            if timeout is not None and now - start > timeout:
                raise FHIRRequestError(
                    f"Query job {number} exceeded deadline in {state}; {len(args) - len(completed)} queries unfinished."
                )
        if now - last_warning >= 30:
            for number, (start, state) in active.items():
                if now - start >= 30:
                    event(logger, "fhir", state, level=logging.WARNING,
                          job=number, elapsed_s=now - start,
                          unfinished=len(args) - len(completed))
            last_warning = now
        try:
            number, result = iterator.next(timeout=0.1)
        except mp.TimeoutError:
            continue
        except Exception:  # noqa: BLE001 - remote exceptions may contain clinical query values.
            raise FHIRRequestError(
                f"Parallel query failed; {len(args) - len(completed)} queries unfinished."
            ) from None
        completed.add(number)
        active.pop(number, None)
        yield result
