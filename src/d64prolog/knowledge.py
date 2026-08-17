from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from .compiler import (
    PrologClause,
    PrologCompilerError,
    PrologTerm,
    _Resolver,
    _subst,
    _term_text,
    parse_prolog,
)


@dataclass(frozen=True, order=True)
class KnowledgePredicate:
    name: str
    arity: int

    @property
    def display_name(self) -> str:
        if self.name.startswith("_") and self.arity == 1:
            return self.name
        return self.name if self.arity == 0 else f"{self.name}/{self.arity}"


@dataclass(frozen=True)
class KnowledgeQueryResult:
    predicate: KnowledgePredicate
    values: Tuple[PrologTerm, ...]
    matched: bool
    complete: bool
    alternatives: Tuple[str, ...] = ()


class PrologKnowledgeBase:
    """Read-only GUI model for one or more PROLOG knowledge files.

    It intentionally reuses the compiler parser and compile-time SLD resolver,
    so the browser follows the same unification/rule semantics as the compiler
    for the supported language subset. Runtime database mutations remain the
    responsibility of the generated native PROLOG program.
    """

    def __init__(self, clauses: Sequence[PrologClause], *, filename: str = "<Wissen>") -> None:
        self.clauses = tuple(clauses)
        self.filename = str(filename)
        self.resolver = _Resolver(self.clauses, filename=self.filename, max_solutions=1024)
        signatures = set()
        for clause in self.clauses:
            head = clause.head
            if head.kind == "atom":
                signatures.add(KnowledgePredicate(str(head.value), 0))
            elif head.kind == "compound":
                # Stage 56: hide the internal storage predicate and expose a
                # named knowledge value as a one-level GUI item ``_name``.
                if (
                    str(head.value) == "d64_knowledge_value"
                    and len(head.args) == 2
                    and head.args[0].kind == "atom"
                ):
                    signatures.add(KnowledgePredicate("_" + str(head.args[0].value), 1))
                else:
                    signatures.add(KnowledgePredicate(str(head.value), len(head.args)))
        self.predicates = tuple(sorted(signatures, key=lambda value: (value.name.casefold(), value.arity)))

    @classmethod
    def from_source(cls, source: str, *, filename: str = "<Wissen>") -> "PrologKnowledgeBase":
        clauses, _queries = parse_prolog(source, filename=filename)
        return cls(clauses, filename=filename)

    @classmethod
    def from_file(cls, path: Path) -> "PrologKnowledgeBase":
        path = Path(path)
        return cls.from_source(path.read_text(encoding="utf-8-sig"), filename=str(path))

    @classmethod
    def from_files(cls, paths: Iterable[Path]) -> "PrologKnowledgeBase":
        clauses: List[PrologClause] = []
        labels: List[str] = []
        for value in paths:
            path = Path(value)
            source = path.read_text(encoding="utf-8-sig")
            loaded, _queries = parse_prolog(source, filename=str(path))
            clauses.extend(loaded)
            labels.append(str(path))
        return cls(tuple(clauses), filename="; ".join(labels) or "<Wissen>")

    @staticmethod
    def parse_value(text: str, *, filename: str = "<Eingabe>") -> PrologTerm:
        value = str(text).strip()
        if not value:
            raise PrologCompilerError("Leere Eingabe ist kein PROLOG-Term.", filename=filename)
        clauses, queries = parse_prolog(f"?- d64_gui_value({value}).", filename=filename)
        del clauses
        if len(queries) != 1 or len(queries[0].goals) != 1:
            raise PrologCompilerError("Eingabe konnte nicht als PROLOG-Term gelesen werden.", filename=filename)
        goal = queries[0].goals[0]
        if goal.kind != "compound" or str(goal.value) != "d64_gui_value" or len(goal.args) != 1:
            raise PrologCompilerError("Eingabe konnte nicht als PROLOG-Term gelesen werden.", filename=filename)
        return goal.args[0]

    @staticmethod
    def _is_ground(term: PrologTerm) -> bool:
        if term.kind == "var":
            return False
        return all(PrologKnowledgeBase._is_ground(arg) for arg in term.args)

    @staticmethod
    def term_text(term: PrologTerm) -> str:
        return _term_text(term)

    def _goal(self, predicate: KnowledgePredicate, values: Sequence[PrologTerm]) -> Tuple[PrologTerm, Tuple[PrologTerm, ...]]:
        if len(values) > predicate.arity:
            raise PrologCompilerError(
                f"{predicate.name}/{predicate.arity} besitzt nur {predicate.arity} Argument(e).",
                filename=self.filename,
            )
        if predicate.name.startswith("_") and predicate.arity == 1:
            value_term = values[0] if values else PrologTerm("var", "D64_GUI_0")
            variables = () if values else (value_term,)
            return (
                PrologTerm(
                    "compound",
                    "d64_knowledge_value",
                    (PrologTerm("atom", predicate.name[1:]), value_term),
                ),
                variables,
            )
        args: List[PrologTerm] = list(values)
        variables: List[PrologTerm] = []
        for index in range(len(values), predicate.arity):
            variable = PrologTerm("var", f"D64_GUI_{index}")
            args.append(variable)
            variables.append(variable)
        if predicate.arity == 0:
            return PrologTerm("atom", predicate.name), ()
        return PrologTerm("compound", predicate.name, tuple(args)), tuple(variables)

    def query(self, predicate: KnowledgePredicate, values: Sequence[PrologTerm] = ()) -> KnowledgeQueryResult:
        goal, variables = self._goal(predicate, values)
        solutions = list(self.resolver.solve((goal,)))
        matched = bool(solutions)
        complete = len(values) >= predicate.arity
        alternatives: List[str] = []
        if matched and not complete and variables:
            next_variable = variables[0]
            seen = set()
            for env, _effects in solutions:
                value = _subst(next_variable, env)
                if not self._is_ground(value):
                    continue
                rendered = _term_text(value)
                key = rendered.casefold()
                if key in seen:
                    continue
                seen.add(key)
                alternatives.append(rendered)
            alternatives.sort(key=lambda value: value.casefold())
        return KnowledgeQueryResult(
            predicate=predicate,
            values=tuple(values),
            matched=matched,
            complete=complete,
            alternatives=tuple(alternatives),
        )

    def alternatives_for_level(
        self,
        predicate: KnowledgePredicate,
        prefix: Sequence[PrologTerm],
    ) -> Tuple[str, ...]:
        if len(prefix) >= predicate.arity:
            return ()
        return self.query(predicate, prefix).alternatives

    def accepts(self, predicate: KnowledgePredicate, values: Sequence[PrologTerm]) -> bool:
        return self.query(predicate, values).matched
