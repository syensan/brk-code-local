"""AST-based Python code analyzer for BRK-Code."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ASTAnalysisError
from .util import is_test_file


@dataclass
class ClassInfo:
    name: str
    file: str
    line: int
    docstring: str | None
    methods: list[str] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)


@dataclass
class FunctionInfo:
    name: str
    qualified_name: str
    file: str
    line: int
    end_line: int
    args: list[str]
    returns: str | None
    docstring: str | None
    calls: list[str]
    decorators: list[str]
    raises: list[str]
    is_async: bool
    complexity_estimate: int


@dataclass
class ModuleInfo:
    file: str
    docstring: str | None
    imports: list[str]
    from_imports: list[tuple[str, str]]  # (module, name)


@dataclass
class SymbolInfo:
    name: str
    qualified_name: str
    kind: str  # "function", "method", "class", "variable"
    file: str
    line: int
    signature: str


@dataclass
class ImportInfo:
    from_file: str
    module: str
    kind: str  # "stdlib_or_external", "local"


@dataclass
class ASTResult:
    modules: list[ModuleInfo]
    classes: list[ClassInfo]
    functions: list[FunctionInfo]
    symbols: list[SymbolInfo]
    imports: list[ImportInfo]
    dependency_edges: list[tuple[str, str]]
    errors: list[dict[str, Any]]


class ASTAnalyzer:
    """Analyze Python source files using the ast module."""

    def __init__(self, local_modules: set[str] | None = None) -> None:
        self._local_modules = local_modules or set()

    def analyze_file(self, file_path: Path, rel_path: str) -> ASTResult:
        """Analyze a single Python file."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            raise ASTAnalysisError(f"Cannot read {file_path}: {e}") from e

        try:
            tree = ast.parse(source, filename=rel_path)
        except SyntaxError as e:
            return ASTResult(
                modules=[], classes=[], functions=[], symbols=[],
                imports=[], dependency_edges=[],
                errors=[{"file": rel_path, "error": f"SyntaxError: {e}", "line": e.lineno}],
            )

        return self._walk_tree(tree, rel_path)

    def _walk_tree(self, tree: ast.Module, rel_path: str) -> ASTResult:
        modules: list[ModuleInfo] = []
        classes: list[ClassInfo] = []
        functions: list[FunctionInfo] = []
        symbols: list[SymbolInfo] = []
        imports: list[ImportInfo] = []
        edges: list[tuple[str, str]] = []
        errors: list[dict[str, Any]] = []

        # Module-level
        module_doc = ast.get_docstring(tree)
        module_imports: list[str] = []
        module_from_imports: list[tuple[str, str]] = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    module_imports.append(mod)
                    kind = "local" if mod in self._local_modules else "stdlib_or_external"
                    imports.append(ImportInfo(from_file=rel_path, module=mod, kind=kind))
                    if kind == "local":
                        edges.append((rel_path, mod + ".py"))

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod = node.module.split(".")[0]
                    module_imports.append(mod)
                    for alias in node.names:
                        module_from_imports.append((mod, alias.name))
                    kind = "local" if mod in self._local_modules else "stdlib_or_external"
                    imports.append(ImportInfo(from_file=rel_path, module=mod, kind=kind))
                    if kind == "local":
                        edges.append((rel_path, mod + ".py"))

            elif isinstance(node, ast.ClassDef):
                ci = self._extract_class(node, rel_path)
                classes.append(ci)
                symbols.append(SymbolInfo(
                    name=ci.name,
                    qualified_name=f"{rel_path}.{ci.name}",
                    kind="class",
                    file=rel_path,
                    line=ci.line,
                    signature=ci.name,
                ))
                # Process methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        fi = self._extract_function(item, rel_path, class_name=ci.name)
                        functions.append(fi)
                        ci.methods.append(fi.name)
                        symbols.append(SymbolInfo(
                            name=fi.name,
                            qualified_name=fi.qualified_name,
                            kind="method",
                            file=rel_path,
                            line=fi.line,
                            signature=self._make_signature(fi),
                        ))

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fi = self._extract_function(node, rel_path)
                functions.append(fi)
                symbols.append(SymbolInfo(
                    name=fi.name,
                    qualified_name=fi.qualified_name,
                    kind="function",
                    file=rel_path,
                    line=fi.line,
                    signature=self._make_signature(fi),
                ))

        modules.append(ModuleInfo(
            file=rel_path,
            docstring=module_doc,
            imports=module_imports,
            from_imports=module_from_imports,
        ))

        return ASTResult(
            modules=modules, classes=classes, functions=functions,
            symbols=symbols, imports=imports, dependency_edges=edges,
            errors=errors,
        )

    def _extract_class(self, node: ast.ClassDef, rel_path: str) -> ClassInfo:
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(self._get_attr_str(base))

        return ClassInfo(
            name=node.name,
            file=rel_path,
            line=node.lineno,
            docstring=ast.get_docstring(node),
            methods=[],
            bases=bases,
        )

    def _extract_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        rel_path: str,
        class_name: str | None = None,
    ) -> FunctionInfo:
        # Arguments
        args: list[str] = []
        for arg in node.args.args:
            args.append(arg.arg)

        # Return annotation
        returns: str | None = None
        if node.returns:
            returns = ast.unparse(node.returns) if hasattr(ast, "unparse") else None

        # Docstring
        docstring = ast.get_docstring(node)

        # Calls within the function
        calls: list[str] = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_name = self._get_call_name(child)
                if call_name and call_name not in calls:
                    calls.append(call_name)

        # Decorators
        decorators: list[str] = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(self._get_attr_str(dec))

        # Raises
        raises: list[str] = []
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                if child.exc and isinstance(child.exc, ast.Call):
                    if isinstance(child.exc.func, ast.Name):
                        exc_name = child.exc.func.id
                        if exc_name not in raises:
                            raises.append(exc_name)
                elif child.exc and isinstance(child.exc, ast.Name):
                    if child.exc.id not in raises:
                        raises.append(child.exc.id)

        # Complexity estimate (simplified cyclomatic)
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        # Qualified name
        if class_name:
            qualified = f"{rel_path}.{class_name}.{node.name}"
        else:
            qualified = f"{rel_path}.{node.name}"

        # End line
        end_line = node.end_lineno if node.end_lineno else node.lineno

        return FunctionInfo(
            name=node.name,
            qualified_name=qualified,
            file=rel_path,
            line=node.lineno,
            end_line=end_line,
            args=args,
            returns=returns,
            docstring=docstring,
            calls=calls,
            decorators=decorators,
            raises=raises,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            complexity_estimate=complexity,
        )

    def _get_call_name(self, node: ast.Call) -> str | None:
        """Extract a readable name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return self._get_attr_str(node.func)
        return None

    def _get_attr_str(self, node: ast.Attribute) -> str:
        """Convert an Attribute node to a string like 'obj.attr'."""
        parts: list[str] = []
        current: ast.expr = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        parts.reverse()
        return ".".join(parts)

    def _make_signature(self, fi: FunctionInfo) -> str:
        """Create a human-readable function signature."""
        args_str = ", ".join(fi.args)
        prefix = "async " if fi.is_async else ""
        ret = f" -> {fi.returns}" if fi.returns else ""
        return f"{prefix}{fi.name}({args_str}){ret}"


def analyze_project(
    source_dir: Path,
    files: list[Any],  # list of ScannedFile
) -> ASTResult:
    """Analyze all Python files in a project.

    Returns combined ASTResult with all modules, classes, functions, etc.
    """
    # Determine local module names for dependency classification
    local_modules: set[str] = set()
    for f in files:
        stem = Path(f.path).stem
        local_modules.add(stem)

    analyzer = ASTAnalyzer(local_modules=local_modules)

    all_modules: list[ModuleInfo] = []
    all_classes: list[ClassInfo] = []
    all_functions: list[FunctionInfo] = []
    all_symbols: list[SymbolInfo] = []
    all_imports: list[ImportInfo] = []
    all_edges: list[tuple[str, str]] = []
    all_errors: list[dict[str, Any]] = []

    for f in files:
        file_path = source_dir / f.path
        if not file_path.exists():
            continue
        result = analyzer.analyze_file(file_path, f.path)
        all_modules.extend(result.modules)
        all_classes.extend(result.classes)
        all_functions.extend(result.functions)
        all_symbols.extend(result.symbols)
        all_imports.extend(result.imports)
        all_edges.extend(result.dependency_edges)
        all_errors.extend(result.errors)

    return ASTResult(
        modules=all_modules,
        classes=all_classes,
        functions=all_functions,
        symbols=all_symbols,
        imports=all_imports,
        dependency_edges=all_edges,
        errors=all_errors,
    )


def build_ast_semantic_graph(result: ASTResult) -> dict:
    """Build the ast_semantic_graph section."""
    return {
        "modules": [
            {
                "file": m.file,
                "docstring": m.docstring,
                "imports": m.imports,
                "from_imports": [[fi[0], fi[1]] for fi in m.from_imports],
            }
            for m in result.modules
        ],
        "classes": [
            {
                "name": c.name,
                "file": c.file,
                "line": c.line,
                "docstring": c.docstring,
                "methods": c.methods,
                "bases": c.bases,
            }
            for c in result.classes
        ],
        "functions": [
            {
                "name": f.name,
                "qualified_name": f.qualified_name,
                "file": f.file,
                "line": f.line,
                "end_line": f.end_line,
                "args": f.args,
                "returns": f.returns,
                "docstring": f.docstring,
                "calls": f.calls,
                "decorators": f.decorators,
                "raises": f.raises,
                "is_async": f.is_async,
                "complexity_estimate": f.complexity_estimate,
            }
            for f in result.functions
        ],
    }


def build_symbol_table(result: ASTResult) -> dict:
    """Build the symbol_table section."""
    return {
        "symbols": [
            {
                "name": s.name,
                "qualified_name": s.qualified_name,
                "kind": s.kind,
                "file": s.file,
                "line": s.line,
                "signature": s.signature,
            }
            for s in result.symbols
        ],
    }


def build_dependency_graph(result: ASTResult) -> dict:
    """Build the dependency_graph section."""
    # Deduplicate imports
    seen_imports: set[tuple[str, str, str]] = set()
    unique_imports: list[dict] = []
    for imp in result.imports:
        key = (imp.from_file, imp.module, imp.kind)
        if key not in seen_imports:
            seen_imports.add(key)
            unique_imports.append({
                "from_file": imp.from_file,
                "module": imp.module,
                "kind": imp.kind,
            })

    # Deduplicate edges
    unique_edges: list[list[str]] = []
    seen_edges: set[tuple[str, str]] = set()
    for a, b in result.dependency_edges:
        key = (a, b)
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append([a, b])

    return {
        "imports": unique_imports,
        "edges": unique_edges,
    }
