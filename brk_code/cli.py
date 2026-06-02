"""BRK-Code CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .ast_analyzer import (
    analyze_project,
    build_ast_semantic_graph,
    build_symbol_table,
    build_dependency_graph,
)
from .checksum import compute_semantic_checksum
from .constants import (
    CODEC_ZLIB,
    CONTRACT_TASKS,
    CREATED_BY,
    DECODER,
    FORMAT_VERSION,
    HARD_CONSTRAINTS,
    MAGIC,
    MODEL_FAMILY,
    MODEL_ID,
    PROFILE_NAME,
)
from .container import BRKCodeContainer
from .dependency import build_function_contracts, build_test_map
from .html_report import export_html
from .jsonl_export import export_jsonl
from .learning_tasks import generate_learning_tasks
from .scanner import scan_source_directory, build_repo_graph
from .security import scan_security
from .sparse_source_residual import build_sparse_source_residual
from .sqlite_export import export_sqlite
from .util import format_size


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="brk-code",
        description=(
            "BRK-Code: AI-learning-optimized semantic code container. "
            "BRK-Code is NOT a universal lossless source-code compressor. "
            "BRK-Code does not break Shannon's theorem."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    # scan
    scan_p = sub.add_parser("scan", help="Scan a Python project and create .brk-code container")
    scan_p.add_argument("source_dir", type=str, help="Path to Python project directory")
    scan_p.add_argument("output", type=str, help="Output .brk file path")
    scan_p.add_argument("--sqlite", type=str, help="Export SQLite database path")
    scan_p.add_argument("--html", type=str, help="Export HTML report path")
    scan_p.add_argument("--jsonl", type=str, help="Export JSONL learning tasks path")
    scan_p.add_argument("--include-snippets", action="store_true", help="Include minimal source snippets")
    scan_p.add_argument("--max-snippet-lines", type=int, default=20, help="Max lines per snippet")
    scan_p.add_argument("--quiet", action="store_true", help="Suppress informational output")

    # inspect
    insp_p = sub.add_parser("inspect", help="Inspect a .brk-code container")
    insp_p.add_argument("input", type=str, help="Path to .brk file")

    # verify
    ver_p = sub.add_parser("verify", help="Verify a .brk-code container")
    ver_p.add_argument("input", type=str, help="Path to .brk file")

    # export-html
    ehtml_p = sub.add_parser("export-html", help="Export HTML report from .brk-code")
    ehtml_p.add_argument("input", type=str, help="Path to .brk file")
    ehtml_p.add_argument("output", type=str, help="Output HTML file path")

    # export-jsonl
    ejsonl_p = sub.add_parser("export-jsonl", help="Export JSONL learning tasks from .brk-code")
    ejsonl_p.add_argument("input", type=str, help="Path to .brk file")
    ejsonl_p.add_argument("output", type=str, help="Output JSONL file path")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "scan":
            _cmd_scan(args)
        elif args.command == "inspect":
            _cmd_inspect(args)
        elif args.command == "verify":
            _cmd_verify(args)
        elif args.command == "export-html":
            _cmd_export_html(args)
        elif args.command == "export-jsonl":
            _cmd_export_jsonl(args)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_scan(args: argparse.Namespace) -> None:
    """Execute the scan command."""
    source_dir = Path(args.source_dir)
    output_path = Path(args.output)

    if not source_dir.is_dir():
        print(f"Error: Source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    quiet = args.quiet

    # 1. Scan files
    if not quiet:
        print(f"Scanning: {source_dir}")
    files, directories = scan_source_directory(source_dir)
    root_name = source_dir.name
    repo_graph = build_repo_graph(source_dir, root_name, files, directories)

    # 2. AST analysis
    if not quiet:
        print(f"Analyzing {len(files)} Python files...")
    ast_result = analyze_project(source_dir, files)
    ast_semantic_graph = build_ast_semantic_graph(ast_result)
    symbol_table = build_symbol_table(ast_result)
    dependency_graph = build_dependency_graph(ast_result)

    # 3. Security scan
    if not quiet:
        print("Running security scan...")
    security_report = scan_security(source_dir, files)

    # 4. Function contracts
    function_contracts = build_function_contracts(ast_result, security_report.get("findings", []))

    # 5. Test map
    test_map = build_test_map(ast_result)

    # 6. Learning tasks
    if not quiet:
        print("Generating learning tasks...")
    learning_tasks = generate_learning_tasks(ast_result, security_report)

    # 7. Sparse source residual
    sparse = build_sparse_source_residual(
        source_dir, ast_result,
        include_snippets=args.include_snippets,
        max_snippet_lines=args.max_snippet_lines,
    )

    # 8. Build header
    now = datetime.now(timezone.utc).isoformat()
    header = {
        "magic": "BRKC1",
        "format_version": FORMAT_VERSION,
        "profile": PROFILE_NAME,
        "created_by": CREATED_BY,
        "created_at": now,
        "flags": {
            "lossless": False,
            "bit_exact_reconstruction": False,
            "semantic_equivalent": True,
            "ai_learning_optimized": True,
        },
        "source_root_name": root_name,
        "file_count": len(files),
        "python_file_count": len(files),  # Only Python files scanned
    }

    # 9. Model binding
    model_binding = {
        "model_family": MODEL_FAMILY,
        "model_id": MODEL_ID,
        "version": FORMAT_VERSION,
        "weights_hash": None,
        "decoder": DECODER,
        "note": "Analytic local AST-based code understanding model. No neural weights.",
    }

    # 10. Contract
    contract = {
        "mode": "brk-code",
        "domain": "python_repository",
        "lossless": False,
        "bit_exact_reconstruction": False,
        "semantic_equivalent": True,
        "ai_learning_optimized": True,
        "tasks": CONTRACT_TASKS,
        "hard_constraints": HARD_CONSTRAINTS,
    }

    # 11. Task outputs
    task_outputs = {
        "file_count": len(files),
        "function_count": len(ast_result.functions),
        "class_count": len(ast_result.classes),
        "import_count": len(dependency_graph.get("imports", [])),
        "security_findings_count": len(security_report.get("findings", [])),
        "secrets_redacted": security_report.get("secrets_redacted", 0),
        "learning_task_count": len(learning_tasks),
        "symbol_count": len(ast_result.symbols),
        "test_count": len(test_map.get("tests", [])),
    }

    # 12. Semantic checksum
    semantic_checksum = compute_semantic_checksum(
        contract=contract,
        repo_graph=repo_graph,
        ast_semantic_graph=ast_semantic_graph,
        symbol_table=symbol_table,
        dependency_graph=dependency_graph,
        task_outputs=task_outputs,
        flags=header["flags"],
    )

    # 13. Build container
    container_data = {
        "header": header,
        "model_binding": model_binding,
        "contract": contract,
        "repo_graph": repo_graph,
        "ast_semantic_graph": ast_semantic_graph,
        "symbol_table": symbol_table,
        "dependency_graph": dependency_graph,
        "function_contracts": function_contracts,
        "test_map": test_map,
        "security_report": security_report,
        "learning_tasks": learning_tasks,
        "sparse_source_residual": sparse,
        "task_outputs": task_outputs,
        "semantic_checksum": semantic_checksum,
    }

    container = BRKCodeContainer(container_data)
    container.write(output_path)

    output_size = output_path.stat().st_size

    if not quiet:
        print(f"\nBRK-Code scan complete.")
        print(f"Output: {output_path}")
        print(f"Output size: {format_size(output_size)}")
        print(f"Files: {len(files)}")
        print(f"Functions: {len(ast_result.functions)}")
        print(f"Classes: {len(ast_result.classes)}")
        print(f"Security findings: {len(security_report.get('findings', []))}")
        print(f"Secrets redacted: {security_report.get('secrets_redacted', 0)}")
        print(f"Learning tasks: {len(learning_tasks)}")
        print(f"Lossless: false")
        print(f"Bit-exact reconstruction: false")
        print(f"Semantic equivalent: true")
        print(f"AI learning optimized: true")

    # Optional exports
    if args.sqlite:
        if not quiet:
            print(f"Exporting SQLite: {args.sqlite}")
        export_sqlite(container, Path(args.sqlite))

    if args.html:
        if not quiet:
            print(f"Exporting HTML: {args.html}")
        export_html(container, Path(args.html))

    if args.jsonl:
        if not quiet:
            print(f"Exporting JSONL: {args.jsonl}")
        export_jsonl(container, Path(args.jsonl))


def _cmd_inspect(args: argparse.Namespace) -> None:
    """Execute the inspect command."""
    container = BRKCodeContainer.read(Path(args.input))
    data = container.data
    header = data.get("header", {})
    flags = header.get("flags", {})
    task_out = data.get("task_outputs", {})
    sec = data.get("security_report", {})

    print(f"Profile: {header.get('profile', 'unknown')}")
    print(f"Format version: {header.get('format_version', 'unknown')}")
    print(f"Source root: {header.get('source_root_name', 'unknown')}")
    print(f"Created at: {header.get('created_at', 'unknown')}")
    print(f"File count: {task_out.get('file_count', 0)}")
    print(f"Python file count: {header.get('python_file_count', 0)}")
    print(f"Function count: {task_out.get('function_count', 0)}")
    print(f"Class count: {task_out.get('class_count', 0)}")
    print(f"Import count: {task_out.get('import_count', 0)}")
    print(f"Security findings: {task_out.get('security_findings_count', 0)}")
    print(f"Secrets redacted: {sec.get('secrets_redacted', 0)}")
    print(f"Learning task count: {task_out.get('learning_task_count', 0)}")
    print(f"Lossless: {flags.get('lossless', 'N/A')}")
    print(f"Bit-exact reconstruction: {flags.get('bit_exact_reconstruction', 'N/A')}")
    print(f"Semantic equivalent: {flags.get('semantic_equivalent', 'N/A')}")
    print(f"AI learning optimized: {flags.get('ai_learning_optimized', 'N/A')}")


def _cmd_verify(args: argparse.Namespace) -> None:
    """Execute the verify command."""
    container = BRKCodeContainer.read(Path(args.input))
    data = container.data
    header = data.get("header", {})
    flags = header.get("flags", {})
    contract = data.get("contract", {})
    stored_checksum = data.get("semantic_checksum", {})

    errors: list[str] = []

    # Check magic
    if header.get("magic") != "BRKC1":
        errors.append("Invalid magic in header.")

    # Check flags
    if flags.get("lossless") != False:
        errors.append("lossless must be false.")
    if flags.get("bit_exact_reconstruction") != False:
        errors.append("bit_exact_reconstruction must be false.")
    if flags.get("semantic_equivalent") != True:
        errors.append("semantic_equivalent must be true.")
    if flags.get("ai_learning_optimized") != True:
        errors.append("ai_learning_optimized must be true.")

    # Check contract
    if contract.get("lossless") != False:
        errors.append("contract.lossless must be false.")
    if contract.get("semantic_equivalent") != True:
        errors.append("contract.semantic_equivalent must be true.")
    if contract.get("ai_learning_optimized") != True:
        errors.append("contract.ai_learning_optimized must be true.")

    # Verify semantic checksum
    recomputed = compute_semantic_checksum(
        contract=contract,
        repo_graph=data.get("repo_graph", {}),
        ast_semantic_graph=data.get("ast_semantic_graph", {}),
        symbol_table=data.get("symbol_table", {}),
        dependency_graph=data.get("dependency_graph", {}),
        task_outputs=data.get("task_outputs", {}),
        flags=flags,
    )
    if recomputed["digest"] != stored_checksum.get("digest", ""):
        errors.append("Semantic checksum mismatch.")

    if errors:
        print("Verification FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Verification passed.")
        print(f"Semantic checksum valid: true")
        print(f"Lossless: false")
        print(f"Bit-exact reconstruction: false")
        print(f"Semantic equivalent: true")
        print(f"AI learning optimized: true")


def _cmd_export_html(args: argparse.Namespace) -> None:
    """Execute the export-html command."""
    container = BRKCodeContainer.read(Path(args.input))
    export_html(container, Path(args.output))
    print(f"HTML report exported: {args.output}")


def _cmd_export_jsonl(args: argparse.Namespace) -> None:
    """Execute the export-jsonl command."""
    container = BRKCodeContainer.read(Path(args.input))
    export_jsonl(container, Path(args.output))
    task_count = len(container.data.get("learning_tasks", []))
    print(f"JSONL exported: {args.output} ({task_count} tasks)")
