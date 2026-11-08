"""Stage 536: dependency-aware parallel Pascal UNIT compilation.

The scheduler runs in a Qt worker thread, while every compiler is launched as
an isolated Python subprocess. No Qt objects or mutable compiler globals cross
process boundaries. A failed worker aborts the build before the main module is
linked. The caller may use the unchanged sequential build as a fallback when
parallelization cannot be planned safely.
"""
from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
from typing import Callable, Dict, Iterable, Mapping, Optional, Sequence


class PascalParallelBuildError(RuntimeError):
    pass


def normalize_parallel_options(options: Optional[Mapping] = None) -> dict:
    values = options if isinstance(options, Mapping) else {}
    automatic = values.get("automatic_cpu_detection", True)
    if isinstance(automatic, str):
        automatic = automatic.strip().lower() in {"1", "true", "yes", "on"}
    try:
        maximum = int(values.get("max_compiler_processes", 2))
    except (TypeError, ValueError):
        maximum = 2
    return {"automatic_cpu_detection": bool(automatic),
            "max_compiler_processes": max(1, min(4, maximum))}


def effective_parallel_processes(options: Optional[Mapping] = None,
                                 cpu_count: Optional[int] = None) -> int:
    setting = normalize_parallel_options(options)
    if not setting["automatic_cpu_detection"]:
        return setting["max_compiler_processes"]
    if cpu_count is None:
        process_count = getattr(os, "process_cpu_count", None)
        cpu_count = process_count() if callable(process_count) else os.cpu_count()
    return min(setting["max_compiler_processes"], max(1, int(cpu_count or 1)))


def validate_jobs(jobs: Sequence[dict]) -> Dict[str, dict]:
    """Validate a closed acyclic project UNIT graph; external USES are ignored.

    External/system units remain the responsibility of the existing Pascal
    resolver. Every project unit is identified by its declared unit name.
    """
    graph = {}
    outputs = set()
    for item in jobs:
        name = str(item["name"]).casefold()
        if name in graph:
            raise PascalParallelBuildError(f"Doppelter Pascal-Unit-Name: {name}")
        for output in ("object_path", "assembly_path", "pui_path"):
            key = os.path.normcase(os.path.abspath(str(item[output]))).casefold()
            if key in outputs:
                raise PascalParallelBuildError(
                    f"Gemeinsamer Ausgabepfad bei parallelen Units: {item[output]}")
            outputs.add(key)
        graph[name] = item
    indegree = {}
    for name, item in graph.items():
        deps = {str(d).casefold() for d in item.get("dependencies", ())}
        deps.discard("")
        if name in deps:
            raise PascalParallelBuildError(f"Zyklische Pascal-USES: {name}")
        indegree[name] = deps.intersection(graph)
    ready = sorted(name for name, deps in indegree.items() if not deps)
    visited = set()
    while ready:
        name = ready.pop(0)
        visited.add(name)
        for other, deps in indegree.items():
            if other not in visited and name in deps:
                deps.remove(name)
                if not deps and other not in ready:
                    ready.append(other)
        ready.sort()
    if len(visited) != len(graph):
        remaining = ", ".join(sorted(set(graph) - visited))
        raise PascalParallelBuildError(f"Zyklische Pascal-USES im Projekt: {remaining}")
    return graph


def _launch_compile(job: dict, *, python: Optional[str] = None, timeout: int = 0) -> dict:
    command = [python or sys.executable, str(Path(__file__).resolve()), "--worker"]
    try:
        child = subprocess.run(
            command, input=json.dumps(job, ensure_ascii=False),
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace", cwd=str(Path(job["path"]).parent),
            timeout=timeout or None, check=False,
            creationflags=(getattr(subprocess, "CREATE_NO_WINDOW", 0)
                           if os.name == "nt" else 0),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PascalParallelBuildError(f"{job['name']}: Compilerprozess: {exc}") from exc
    try:
        result = json.loads(child.stdout)
    except (ValueError, TypeError) as exc:
        raise PascalParallelBuildError(
            f"{job['name']}: Ungueltige Compilerantwort (Exit {child.returncode}): "
            f"{child.stderr[-2500:]} {child.stdout[-800:]}") from exc
    if child.returncode != 0 or not result.get("ok"):
        raise PascalParallelBuildError(
            f"{job['name']}: {result.get('error', child.stderr) or child.stderr}"
            f"\n{str(result.get('traceback', ''))[-2000:]}")
    obj = Path(result["object_path"])
    if not obj.is_file():
        raise PascalParallelBuildError(f"{job['name']}: COFF nicht erzeugt: {obj}")
    return result


def run_parallel_units(jobs: Sequence[dict], max_workers: int,
                       progress: Optional[Callable[[str], None]] = None,
                       runner: Optional[Callable[[dict], dict]] = None) -> dict:
    """Schedule complete dependency waves without blocking an available slot.

    At most max_workers independent compiler processes run at one time. Jobs
    dependent on a failed UNIT are never submitted. The exception is passed
    to the GUI; no EXE link step can follow it.
    """
    graph = validate_jobs(jobs)
    pending = dict(graph)
    finished = {}
    running = {}
    notify = progress if callable(progress) else lambda _message: None
    launch = runner or _launch_compile
    limit = max(1, min(4, int(max_workers)))
    with ThreadPoolExecutor(max_workers=limit, thread_name_prefix="pascal-unit") as executor:
        failure = None
        while pending or running:
            if failure is None:
                for name in sorted(tuple(pending)):
                    if len(running) >= limit:
                        break
                    deps = {str(dep).casefold()
                            for dep in pending[name].get("dependencies", ())}
                    if deps.intersection(graph).issubset(finished):
                        job = pending.pop(name)
                        notify(f"PASCAL PARALLEL START [{len(running)+1}/{limit}]: {job['name']}")
                        running[executor.submit(launch, job)] = name
            if not running:
                if failure is not None:
                    break
                if pending:
                    raise PascalParallelBuildError("Unaufgeloeste Unit-Abhaengigkeiten")
                break
            done, _ = wait(tuple(running), return_when=FIRST_COMPLETED)
            for future in done:
                name = running.pop(future)
                try:
                    outcome = future.result()
                    finished[name] = outcome
                    notify(f"PASCAL PARALLEL OK: {name}")
                except Exception as exc:
                    failure = failure or PascalParallelBuildError(f"{name}: {exc}")
                    notify(f"PASCAL PARALLEL ERROR: {name}: {exc}")
        if failure is not None:
            raise failure
    return finished


def compile_unit_in_worker(job: dict) -> dict:
    """Run inside a fresh Python interpreter, never in the Qt GUI process."""
    from c64pascal import compile_pascal_to_assembly, preprocess_pascal_source

    target = str(job["target"])
    source = str(job["source"])
    input_path = Path(job["path"])
    macros = dict(job.get("predefined_macros") or {})
    prepared = preprocess_pascal_source(
        source, filename=str(input_path), predefined_macros=macros)
    # Support a project-level plugin compiler that has not yet adopted the
    # Stage-537 keyword, while always passing it to the bundled compiler.
    import inspect
    parameters = inspect.signature(compile_pascal_to_assembly).parameters
    optimizer_kwargs = ({"optimization_level": job.get("optimization_level", 0)}
                        if "optimization_level" in parameters or
                        any(p.kind is inspect.Parameter.VAR_KEYWORD
                            for p in parameters.values()) else {})
    if "no_stack_frames" in parameters or any(
            p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters.values()):
        optimizer_kwargs["no_stack_frames"] = bool(job.get("no_stack_frames", False))
    if "linked_dll_files" in parameters:
        optimizer_kwargs["linked_dll_files"] = tuple(prepared.link_dlls)
    for keyword in ("import_cache_enabled", "import_prune_unused",
                    "import_cache_directory"):
        if keyword in parameters:
            optimizer_kwargs[keyword] = job.get(keyword)
    generated = compile_pascal_to_assembly(
        prepared.source, filename=str(input_path), target=target,
        include_paths=tuple(job.get("include_paths", ())),
        link_search_paths=tuple(job.get("link_search_paths", ())),
        output_directory=job.get("output_directory"),
        predefined_macros=dict(prepared.macros),
        linked_object_files=tuple(prepared.link_files),
        graphics_backend=job.get("graphics_backend", "Direct2D"),
        breakpoint_lines=tuple(job.get("breakpoint_lines", ())),
        stack_protector=bool(job.get("stack_protector", False)),
        **optimizer_kwargs,
    )
    if str(getattr(generated, "source_kind", "")).casefold() != "unit":
        raise PascalParallelBuildError(f"Keine Pascal-UNIT: {input_path}")
    if str(getattr(generated, "unit_name", "")).casefold() != str(job["name"]).casefold():
        raise PascalParallelBuildError(f"Unit-Name geaendert: {job['name']}")

    # The native COFF assembler lives in the existing monolithic project.
    # Importing it here does not start the GUI (__name__ != '__main__').
    from d64_dism import assemble_pe32_coff_object, assemble_pe64_coff_object
    assembly = generated.assembly
    assembly_path = Path(job["assembly_path"])
    if bool(job.get("import_externalize", False)):
        from pascal_import_manager import externalize_declarations
        assembly, import_include_path, import_include_text = externalize_declarations(
            assembly, assembly_path,
            use_preprocessor_lines=bool(job.get("import_use_preprocessor_lines", False)))
        if import_include_path is not None:
            import_include_path.parent.mkdir(parents=True, exist_ok=True)
            import_include_path.write_text(import_include_text, encoding="utf-8")
    asm_dirs = tuple(job.get("asm_include_paths", ()))
    assembler = assemble_pe64_coff_object if target == "pe64" else assemble_pe32_coff_object
    object_data = assembler(assembly, filename=str(assembly_path), include_dirs=asm_dirs)
    object_path = Path(job["object_path"])
    assembly_path.parent.mkdir(parents=True, exist_ok=True)
    object_path.parent.mkdir(parents=True, exist_ok=True)
    assembly_path.write_text(assembly, encoding="utf-8")
    if getattr(generated, "import_manifest", None) is not None:
        from pascal_import_manager import write_manifest
        write_manifest(str(assembly_path) + ".imports.json", generated.import_manifest)
    temp_object = object_path.with_name(f"{object_path.name}.{os.getpid()}.tmp")
    try:
        temp_object.write_bytes(object_data)
        os.replace(temp_object, object_path)
    finally:
        temp_object.unlink(missing_ok=True)
    return {"ok": True, "name": job["name"],
            "object_path": str(object_path), "assembly_path": str(assembly_path),
            "pui_path": str(job["pui_path"]), "object_size": len(object_data)}


def _worker_main() -> int:
    try:
        # Binary pipe UTF-8 on Windows too (sys.stdin may default to cp1252).
        request = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        # The IDE's compiler/backend can emit diagnostics with print().
        # Keep stdout as a single machine-readable JSON response.
        from contextlib import redirect_stdout
        with redirect_stdout(sys.stderr):
            result = compile_unit_in_worker(request)
    except BaseException as exc:
        result = {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                  "traceback": traceback.format_exc()[-6000:]}
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False) + "\n")
                            .encode("utf-8"))
    sys.stdout.buffer.flush()
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        raise SystemExit(_worker_main())
    raise SystemExit("Use --worker")
