from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


INVALID = 0xFFFFFFFF
NODE_VAR = 1
NODE_ATOM = 2
NODE_INT = 3
NODE_STRING = 4
NODE_NIL = 5
NODE_LIST = 6
NODE_STRUCT = 7
NODE_LINK = 8
NODE_FLOAT = 9

# One VirtualAlloc arena (currently 0x240000 bytes). All transient/dynamic term handles are 32-bit
# node indexes, so the logic representation is identical for PE32 and PE32+.
ARENA_SIZE = 0x240000
HEAP_OFF = 0x00000
HEAP_SIZE = 0x40000
DYN_HEAP_OFF = 0x40000
DYN_HEAP_SIZE = 0x40000
TRAIL_OFF = 0x80000
TRAIL_SIZE = 0x10000
CHOICE_OFF = 0x90000
CHOICE_SIZE = 0x10000
ATOM_POOL_OFF = 0xA0000
ATOM_POOL_SIZE = 0x10000
INPUT_OFF = 0xB0000
INPUT_SIZE = 0x1000
TOKEN_OFF = 0xB1000
TOKEN_SIZE = 0x1000
QNAME_OFF = 0xB2000
QNAME_SIZE = 0x2000
SCRATCH_OFF = 0xB4000
SCRATCH_SIZE = 0x8000
OUTPUT_OFF = 0xC0000
OUTPUT_SIZE = 0x10000
DYN_ALT_OFF = 0x100000
DYN_ALT_SIZE = DYN_HEAP_SIZE
FILE_BUFFER_OFF = 0x140000
FILE_BUFFER_SIZE = 0x100000

DATABASE_MAX = 32
DATABASE_FILENAME_SIZE = 260
DATABASE_KIND_KNOWLEDGE = 1
DATABASE_KIND_RECORD = 2
DATABASE_KIND_SYSTEM = 3
DATABASE_MODE_READ_ONLY = 0
DATABASE_MODE_READ_WRITE = 1

BUILD_VAR_OFF = SCRATCH_OFF + 0x0000        # 256 dwords
QUERY_NODE_OFF = SCRATCH_OFF + 0x0400       # 64 dwords
QUERY_NAME_OFF = SCRATCH_OFF + 0x0500       # 64 pointers
DYN_ATOM_TABLE_OFF = SCRATCH_OFF + 0x0800   # 512 pointers max
DYN_DB_OFF = SCRATCH_OFF + 0x1800           # 512 x 16-byte entries
DYN_DB_OWNER_OFF = SCRATCH_OFF + 0x5800     # 512 x dword Database-ID owners
DB_PARSER_NAME_POOL_OFF = SCRATCH_OFF + 0x6000
DB_PARSER_NAME_POOL_SIZE = 0x1000
DB_SAVE_VAR_OFF = SCRATCH_OFF + 0x7000       # canonical variable handles while saving

# Stage 51: external-database metadata lives in the unused 0xBC000..0xC0000
# arena gap instead of being emitted as ~9.5 KiB of zero bytes into PE32.
DB_META_OFF = SCRATCH_OFF + SCRATCH_SIZE            # 0xBC000
DB_ACTIVE_OFF = DB_META_OFF + 0x0000                # 32 dwords
DB_IDS_OFF = DB_META_OFF + 0x0080                   # 32 dwords
DB_MODES_OFF = DB_META_OFF + 0x0100                 # 32 dwords
DB_KINDS_OFF = DB_META_OFF + 0x0180                 # 32 dwords
DB_MODIFIED_OFF = DB_META_OFF + 0x0200              # 32 dwords
DB_FILENAMES_OFF = DB_META_OFF + 0x0280             # 32 * 260 bytes
DB_TEMP_PATH_OFF = DB_FILENAMES_OFF + DATABASE_MAX * DATABASE_FILENAME_SIZE
DB_OLD_PATH_OFF = DB_TEMP_PATH_OFF + DATABASE_FILENAME_SIZE
DB_META_END = DB_OLD_PATH_OFF + DATABASE_FILENAME_SIZE
# Stage 58: temporary materialization buffer for external ``_name = A + B``
# string expressions. It uses the still-free tail of the DB metadata gap and
# therefore does not add a zero-filled block to the PE image.
KNOWLEDGE_CONCAT_OFF = (DB_META_END + 0xFF) & ~0xFF
KNOWLEDGE_CONCAT_SIZE = 0x1800
DYN_COPY_SRC_OFF = SCRATCH_OFF + 0x3800     # reserved

assert DB_META_END <= KNOWLEDGE_CONCAT_OFF
assert KNOWLEDGE_CONCAT_OFF + KNOWLEDGE_CONCAT_SIZE <= OUTPUT_OFF, "PROLOG knowledge concat buffer overlaps output arena"
DYN_COPY_DST_OFF = SCRATCH_OFF + 0x3C00
DYN_CLONE_SRC_OFF = SCRATCH_OFF + 0x4400
DYN_CLONE_DST_OFF = SCRATCH_OFF + 0x4800
PARSER_VAR_NODE_OFF = SCRATCH_OFF + 0x4000
PARSER_VAR_NAME_OFF = SCRATCH_OFF + 0x4100
GC_ROOT_OFF = SCRATCH_OFF + 0x5000          # 512 transient handles during copying GC

HEAP_NODE_COUNT = HEAP_SIZE // 16
DYN_NODE_COUNT = DYN_HEAP_SIZE // 16
TRAIL_COUNT = TRAIL_SIZE // 4
CHOICE_COUNT = CHOICE_SIZE // 16
DYN_ATOM_COUNT_MAX = 512
DYN_DB_COUNT_MAX = 512
QUERY_VAR_MAX = 64
BUILD_VAR_MAX = 256

BUILTIN_NAMES = (
    "[]", ".", ",", ";", ":-", "true", "false", "fail", "!", "=", "\\=", "==", "is",
    "<", "=<", ">", ">=", "+", "-", "*", "/", "mod",
    "write", "writeln", "nl", "var", "nonvar", "atom", "integer", "float", "number", "string",
    "assert", "asserta", "assertz", "retract", "repl", "halt", "quit",
    "gc", "garbage_collect", "verbose",
    "database_open", "database_close", "database_save", "database_save_as",
    "database_select", "current_database", "database_assert", "database_asserta",
    "database_assertz", "database_retract", "database_modified", "with_database",
    "read_only", "read_write", "knowledge", "record", "system",
)


class _A:
    def __init__(self) -> None:
        self.lines: List[str] = []

    def e(self, text: str = "") -> None:
        self.lines.append(text)

    def l(self, name: str) -> None:
        self.lines.append(name + ":")

    def render(self) -> str:
        return "\n".join(self.lines).rstrip() + "\n"


@dataclass
class _Arch:
    is64: bool

    @property
    def ptr(self) -> int:
        return 8 if self.is64 else 4

    @property
    def bp(self) -> str:
        return "rbp" if self.is64 else "ebp"

    @property
    def sp(self) -> str:
        return "rsp" if self.is64 else "esp"

    @property
    def bx(self) -> str:
        return "rbx" if self.is64 else "ebx"

    @property
    def si(self) -> str:
        return "rsi" if self.is64 else "esi"

    @property
    def di(self) -> str:
        return "rdi" if self.is64 else "edi"

    @property
    def cx(self) -> str:
        return "rcx" if self.is64 else "ecx"

    @property
    def dx(self) -> str:
        return "rdx" if self.is64 else "edx"

    @property
    def ax(self) -> str:
        return "rax" if self.is64 else "eax"

    def mem_ptr(self, expr: str) -> str:
        return ("qword" if self.is64 else "dword") + f" ptr [{expr}]"

    def push_reg32(self, reg32: str) -> str:
        if not self.is64:
            return f"push {reg32}"
        aliases = {"eax":"rax","ebx":"rbx","ecx":"rcx","edx":"rdx","esi":"rsi","edi":"rdi"}
        return f"push {aliases.get(reg32, reg32)}"

    def cleanup(self, count: int) -> str:
        return f"add {self.sp}, {count * self.ptr}"

    def arg(self, index: int, width: str = "dword") -> str:
        # index 0 is first argument after prologue push bp / mov bp,sp.
        return f"{width} ptr [{self.bp}+{2*self.ptr + index*self.ptr}]"


class PrologRuntimeEmitter:
    """Emit a small native Prolog runtime for d64_dism's internal assemblers.

    Runtime model:
      * 16-byte term cells addressed by 32-bit handles
      * transient heap + persistent dynamic heap
      * explicit trail stack for bindings
      * explicit choice-point stack storing heap/trail snapshots
      * recursive runtime unifier and DFS solver
      * static clauses compiled into native builder routines
      * dynamic assert/retract database for runtime facts
      * Console REPL parser for atoms, variables, integers, IEEE-754 doubles, strings, compounds,
        conjunctions and lists.
    """

    def __init__(self, clauses, queries, *, target: str, mode: str, filename: str, verbose: bool = False) -> None:
        self.clauses = tuple(clauses)
        self.queries = tuple(queries)
        self.filename = filename
        self.arch = _Arch(str(target).casefold() == "pe64")
        self.is_gui = str(mode).casefold() == "gui"
        self.verbose = bool(verbose)
        self.atom_ids: Dict[str, int] = {}
        self.atom_labels: Dict[str, str] = {}
        self.qvar_labels: Dict[Tuple[int, str], str] = {}
        self._collect_atoms()
        self.pred_groups: Dict[Tuple[str, int], List[Tuple[int, object]]] = {}
        for idx, clause in enumerate(self.clauses):
            key = self._predicate_key(clause.head)
            self.pred_groups.setdefault(key, []).append((idx, clause))

    # ------------------------------------------------------------------
    # Python-side term inspection / metadata
    # ------------------------------------------------------------------
    @staticmethod
    def _predicate_key(term) -> Tuple[str, int]:
        if term.kind == "atom":
            return str(term.value), 0
        if term.kind == "compound":
            if str(term.value) == "." and len(term.args) == 2:
                return ".", 2
            return str(term.value), len(term.args)
        return "", -1

    def _walk(self, term) -> Iterable[object]:
        yield term
        for arg in getattr(term, "args", ()):
            yield from self._walk(arg)

    def _collect_atoms(self) -> None:
        values: List[str] = list(BUILTIN_NAMES) + ["d64_knowledge_value"]
        for clause in self.clauses:
            for term in self._walk(clause.head):
                if term.kind in {"atom", "string"}:
                    values.append(str(term.value))
                if term.kind == "compound":
                    values.append(str(term.value))
            for goal in clause.body:
                for term in self._walk(goal):
                    if term.kind in {"atom", "string"}:
                        values.append(str(term.value))
                    if term.kind == "compound":
                        values.append(str(term.value))
        for query in self.queries:
            for goal in query.goals:
                for term in self._walk(goal):
                    if term.kind in {"atom", "string"}:
                        values.append(str(term.value))
                    if term.kind == "compound":
                        values.append(str(term.value))
        for value in values:
            key = value
            if key not in self.atom_ids:
                self.atom_ids[key] = len(self.atom_ids) + 1
        for key, atom_id in self.atom_ids.items():
            self.atom_labels[key] = f"__prolog_atom_{atom_id}"

    def atom_id(self, value: str) -> int:
        key = str(value)
        return self.atom_ids[key]

    def _variables(self, terms: Sequence[object], *, public_only: bool = False) -> Tuple[Dict[str, int], List[str]]:
        mapping: Dict[str, int] = {}
        public: List[str] = []
        def visit(term) -> None:
            if term.kind == "var":
                name = str(term.value)
                if name not in mapping:
                    if len(mapping) >= BUILD_VAR_MAX:
                        raise ValueError("too many Prolog variables")
                    mapping[name] = len(mapping)
                    if (
                        not name.startswith("__anon_")
                        and not name.startswith("__fresh_")
                        and not name.startswith("__knowledge_")
                    ):
                        public.append(name)
            for arg in getattr(term, "args", ()):
                visit(arg)
        for t in terms:
            visit(t)
        return mapping, public if public_only else list(mapping)

    # ------------------------------------------------------------------
    # Assembly utility
    # ------------------------------------------------------------------
    def _prologue(self, a: _A, *, save: Sequence[str] = ()) -> None:
        ar = self.arch
        a.e(f"    push {ar.bp}")
        a.e(f"    mov {ar.bp}, {ar.sp}")
        for reg in save:
            a.e(f"    push {reg}")

    def _epilogue(self, a: _A, *, save: Sequence[str] = ()) -> None:
        ar = self.arch
        for reg in reversed(tuple(save)):
            a.e(f"    pop {reg}")
        a.e(f"    mov {ar.sp}, {ar.bp}")
        a.e(f"    pop {ar.bp}")
        a.e("    ret")

    def _call1_imm(self, a: _A, fn: str, value: int) -> None:
        a.e(f"    push {value}")
        a.e(f"    call {fn}")
        a.e(f"    {self.arch.cleanup(1)}")

    def _call1_eax(self, a: _A, fn: str) -> None:
        a.e(f"    {self.arch.push_reg32('eax')}")
        a.e(f"    call {fn}")
        a.e(f"    {self.arch.cleanup(1)}")

    def _call2_regs(self, a: _A, fn: str, first: str, second: str) -> None:
        # push reverse: second, first
        a.e(f"    {self.arch.push_reg32(second)}")
        a.e(f"    {self.arch.push_reg32(first)}")
        a.e(f"    call {fn}")
        a.e(f"    {self.arch.cleanup(2)}")

    def _arena_to(self, a: _A, reg: str, offset: int) -> None:
        ar = self.arch
        a.e(f"    mov {reg}, {ar.mem_ptr('__prolog_arena')}")
        if offset:
            a.e(f"    add {reg}, {offset}")

    # ------------------------------------------------------------------
    # Static builder generation
    # ------------------------------------------------------------------
    def _emit_term_builder(self, a: _A, term, varmap: Dict[str, int]) -> None:
        ar = self.arch
        if term.kind == "var":
            self._call1_imm(a, "__rt_make_var", varmap[str(term.value)])
            return
        if term.kind == "number":
            self._call1_imm(a, "__rt_make_int", int(term.value))
            return
        if term.kind == "float":
            low, high = struct.unpack("<II", struct.pack("<d", float(term.value)))
            a.e(f"    push {high}")
            a.e(f"    push {low}")
            a.e("    call __rt_make_float_bits")
            a.e(f"    {ar.cleanup(2)}")
            return
        if term.kind == "string":
            self._call1_imm(a, "__rt_make_string", self.atom_id(str(term.value)))
            return
        if term.kind == "atom":
            if str(term.value) == "[]":
                a.e("    call __rt_make_nil")
            else:
                self._call1_imm(a, "__rt_make_atom", self.atom_id(str(term.value)))
            return
        if term.kind != "compound":
            raise ValueError(f"unsupported term kind {term.kind}")
        if str(term.value) == "." and len(term.args) == 2:
            # tail first, then head; make_list(head, tail)
            self._emit_term_builder(a, term.args[1], varmap)
            a.e(f"    {ar.push_reg32('eax')}")
            self._emit_term_builder(a, term.args[0], varmap)
            a.e(f"    pop {ar.cx}")
            self._call2_regs(a, "__rt_make_list", "eax", "ecx")
            return

        # Build argument link chain in reverse. Keep the current chain on the
        # CPU stack; nested builders are balanced and therefore safe.
        a.e(f"    push {INVALID}")
        for arg in reversed(term.args):
            self._emit_term_builder(a, arg, varmap)
            a.e(f"    pop {ar.cx}")
            self._call2_regs(a, "__rt_make_link", "eax", "ecx")
            a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    pop {ar.cx}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    push {len(term.args)}")
        a.e(f"    push {self.atom_id(str(term.value))}")
        a.e("    call __rt_make_struct")
        a.e(f"    {ar.cleanup(3)}")

    def _emit_clause_builders(self, a: _A) -> None:
        ar = self.arch
        for idx, clause in enumerate(self.clauses):
            varmap, _ = self._variables((clause.head,) + tuple(clause.body))
            a.l(f"__prolog_clause_{idx}_build")
            self._prologue(a, save=(ar.bx,))
            a.e("    mov ebx, edx")  # rest goal chain
            self._call1_imm(a, "__rt_build_vars_reset", len(varmap))
            self._emit_term_builder(a, clause.head, varmap)
            a.e(f"    {ar.push_reg32('eax')}")  # save head
            for goal in reversed(clause.body):
                self._emit_term_builder(a, goal, varmap)
                # make goal link(term, current chain)
                a.e("    mov ecx, dword ptr [__prolog_build_barrier]")
                a.e(f"    {ar.push_reg32('ecx')}")
                a.e(f"    {ar.push_reg32('ebx')}")
                a.e(f"    {ar.push_reg32('eax')}")
                a.e("    call __rt_make_goal_link")
                a.e(f"    {ar.cleanup(3)}")
                a.e("    mov ebx, eax")
            a.e(f"    pop {ar.ax}")
            a.e("    mov ecx, ebx")
            self._epilogue(a, save=(ar.bx,))
            a.e()

    def _emit_query_builders(self, a: _A) -> List[Tuple[str, object]]:
        ar = self.arch
        specs: List[Tuple[str, object]] = []
        queries = list(self.queries)
        if not queries:
            # runtime main/0 if present; otherwise console drops into REPL.
            if any(self._predicate_key(c.head) == ("main", 0) for c in self.clauses):
                atom_cls = type(self.clauses[0].head) if self.clauses else None
                if atom_cls is not None:
                    main_term = atom_cls("atom", "main")
                    query_cls = None
                    # use a tiny duck-typed object instead of importing compiler types
                    class Q:
                        goals = (main_term,)
                        line = 0
                    queries = [Q()]
        for qi, query in enumerate(queries):
            name = f"__prolog_query_{qi}_build"
            specs.append((name, query))
            varmap, public = self._variables(tuple(query.goals), public_only=True)
            a.l(name)
            self._prologue(a, save=(ar.bx,))
            self._call1_imm(a, "__rt_build_vars_reset", len(varmap))
            a.e(f"    mov ebx, {INVALID}")
            for goal in reversed(query.goals):
                self._emit_term_builder(a, goal, varmap)
                a.e(f"    {ar.push_reg32('ebx')}")
                a.e(f"    {ar.push_reg32('eax')}")
                a.e("    call __rt_make_link")
                a.e(f"    {ar.cleanup(2)}")
                a.e("    mov ebx, eax")
            a.e(f"    mov dword ptr [__prolog_query_var_count], {len(public)}")
            for vi, public_name in enumerate(public):
                var_id = varmap[public_name]
                # query node = build_var_map[var_id]
                self._arena_to(a, ar.di, BUILD_VAR_OFF)
                a.e(f"    mov ecx, {var_id}")
                a.e(f"    mov eax, dword ptr [{ar.di}+{ar.cx}*4]")
                self._arena_to(a, ar.di, QUERY_NODE_OFF)
                a.e(f"    mov dword ptr [{ar.di}+{vi*4}], eax")
                label = f"__prolog_q{qi}_var_{vi}"
                self.qvar_labels[(qi, public_name)] = label
                self._arena_to(a, ar.di, QUERY_NAME_OFF)
                if ar.is64:
                    a.e(f"    mov rax, {label}")
                    a.e(f"    mov qword ptr [{ar.di}+{vi*8}], rax")
                else:
                    a.e(f"    mov eax, {label}")
                    a.e(f"    mov dword ptr [{ar.di}+{vi*4}], eax")
            a.e("    mov eax, ebx")
            self._epilogue(a, save=(ar.bx,))
            a.e()
        return specs

    # ------------------------------------------------------------------
    # Runtime core
    # ------------------------------------------------------------------
    def _emit_runtime_core(self, a: _A) -> None:
        ar = self.arch
        ptrmem = "qword" if ar.is64 else "dword"

        # node pointer: input EAX index, output DI pointer, preserves EAX
        a.l("__rt_node_ptr")
        self._arena_to(a, ar.di, HEAP_OFF)
        a.e("    mov ecx, eax")
        a.e(f"    shl {ar.cx}, 4")
        a.e(f"    add {ar.di}, {ar.cx}")
        a.e("    ret")
        a.e()
        a.l("__rt_dyn_ptr")
        a.e(f"    mov {ar.di}, {ar.mem_ptr('__prolog_dyn_base')}")
        a.e("    mov ecx, eax")
        a.e(f"    shl {ar.cx}, 4")
        a.e(f"    add {ar.di}, {ar.cx}")
        a.e("    ret")
        a.e()

        a.l("__rt_fatal")
        a.e("    push 2")
        a.e("    call ExitProcess")
        a.e("    ret")
        a.e()

        a.l("__rt_new_node")
        a.e("    mov eax, dword ptr [__prolog_heap_top]")
        a.e(f"    cmp eax, {HEAP_NODE_COUNT}")
        a.e("    jb __rt_new_node_ok")
        a.e("    call __rt_fatal")
        a.l("__rt_new_node_ok")
        a.e("    inc dword ptr [__prolog_heap_top]")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov dword ptr [{ar.di}], 0")
        a.e(f"    mov dword ptr [{ar.di}+4], 0")
        a.e(f"    mov dword ptr [{ar.di}+8], {INVALID}")
        a.e(f"    mov dword ptr [{ar.di}+12], {INVALID}")
        a.e("    ret")
        a.e()

        a.l("__rt_new_dyn_node")
        a.e("    mov eax, dword ptr [__prolog_dyn_heap_top]")
        a.e(f"    cmp eax, {DYN_NODE_COUNT}")
        a.e("    jb __rt_new_dyn_node_ok")
        a.e("    call __rt_fatal")
        a.l("__rt_new_dyn_node_ok")
        a.e("    inc dword ptr [__prolog_dyn_heap_top]")
        a.e("    call __rt_dyn_ptr")
        a.e(f"    mov dword ptr [{ar.di}], 0")
        a.e(f"    mov dword ptr [{ar.di}+4], 0")
        a.e(f"    mov dword ptr [{ar.di}+8], {INVALID}")
        a.e(f"    mov dword ptr [{ar.di}+12], {INVALID}")
        a.e("    ret")
        a.e()

        # reset build var map
        a.l("__rt_build_vars_reset")
        self._prologue(a, save=(ar.di,))
        a.e(f"    mov ecx, {ar.arg(0)}")
        self._arena_to(a, ar.di, BUILD_VAR_OFF)
        a.e("    xor eax, eax")
        a.l("__rt_build_vars_reset_loop")
        a.e("    cmp eax, ecx")
        a.e("    jae __rt_build_vars_reset_done")
        a.e(f"    mov dword ptr [{ar.di}+{ar.ax}*4], {INVALID}")
        a.e("    inc eax")
        a.e("    jmp __rt_build_vars_reset_loop")
        a.l("__rt_build_vars_reset_done")
        self._epilogue(a, save=(ar.di,))
        a.e()

        # make variable using builder map
        a.l("__rt_make_var")
        self._prologue(a, save=(ar.bx, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        self._arena_to(a, ar.di, BUILD_VAR_OFF)
        a.e(f"    mov eax, dword ptr [{ar.di}+{ar.bx}*4]")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    jne __rt_make_var_done")
        a.e("    call __rt_new_node")
        # EAX index, DI node pointer
        a.e(f"    mov dword ptr [{ar.di}], {NODE_VAR}")
        a.e(f"    mov dword ptr [{ar.di}+4], eax")
        a.e("    mov ecx, eax")
        self._arena_to(a, ar.di, BUILD_VAR_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.bx}*4], ecx")
        a.e("    mov eax, ecx")
        a.l("__rt_make_var_done")
        self._epilogue(a, save=(ar.bx, ar.di))
        a.e()

        # simple node constructors
        for fn, tag in (("atom", NODE_ATOM), ("int", NODE_INT), ("string", NODE_STRING)):
            a.l(f"__rt_make_{fn}")
            self._prologue(a, save=(ar.bx,))
            a.e(f"    mov ebx, {ar.arg(0)}")
            a.e("    call __rt_new_node")
            a.e(f"    mov dword ptr [{ar.di}], {tag}")
            a.e(f"    mov dword ptr [{ar.di}+4], ebx")
            self._epilogue(a, save=(ar.bx,))
            a.e()

        # Float terms store one IEEE-754 binary64 payload in +4..+11.
        a.l("__rt_make_float_bits")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e(f"    mov ebx, {ar.arg(0)}")  # low dword
        a.e(f"    mov esi, {ar.arg(1)}")  # high dword
        a.e("    call __rt_new_node")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_FLOAT}")
        a.e(f"    mov dword ptr [{ar.di}+4], ebx")
        a.e(f"    mov dword ptr [{ar.di}+8], esi")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # x87 ST0 -> newly allocated FLOAT term.
        a.l("__rt_make_float_from_st0")
        a.e("    call __rt_new_node")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_FLOAT}")
        a.e(f"    fstp qword ptr [{ar.di}+4]")
        a.e("    ret")
        a.e()
        if ar.is64:
            # Win64 strtod returns a double in XMM0.
            a.l("__rt_make_float_from_xmm0")
            a.e("    call __rt_new_node")
            a.e(f"    mov dword ptr [{ar.di}], {NODE_FLOAT}")
            a.e(f"    movsd qword ptr [{ar.di}+4], xmm0")
            a.e("    ret")
            a.e()
        a.l("__rt_make_nil")
        a.e("    call __rt_new_node")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_NIL}")
        a.e("    ret")
        a.e()

        # make list(head,tail)
        a.l("__rt_make_list")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        a.e("    call __rt_new_node")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_LIST}")
        a.e(f"    mov dword ptr [{ar.di}+8], ebx")
        a.e(f"    mov dword ptr [{ar.di}+12], esi")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # generic link(term,next)
        a.l("__rt_make_link")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        a.e("    call __rt_new_node")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_LINK}")
        a.e(f"    mov dword ptr [{ar.di}+8], ebx")
        a.e(f"    mov dword ptr [{ar.di}+12], esi")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # Goal links use the otherwise-unused +4 dword for the lexical cut
        # barrier (choice_top snapshot at clause entry).  Continuations keep
        # their own barrier, so a cut in an outer continuation is not mistaken
        # for a cut inside a nested predicate.
        a.l("__rt_make_goal_link")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        a.e(f"    mov ecx, {ar.arg(2)}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_make_link")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    pop {ar.cx}")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov dword ptr [{ar.di}+4], ecx")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # struct(functor,arity,first-link)
        a.l("__rt_make_struct")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        a.e(f"    mov ecx, {ar.arg(2)}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_new_node")
        a.e(f"    pop {ar.cx}")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e(f"    mov dword ptr [{ar.di}+4], ebx")
        a.e(f"    mov dword ptr [{ar.di}+8], esi")
        a.e(f"    mov dword ptr [{ar.di}+12], ecx")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # dereference VAR chains; input/output EAX
        a.l("__rt_deref")
        a.l("__rt_deref_loop")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_VAR}")
        a.e("    jne __rt_deref_done")
        a.e(f"    mov ecx, dword ptr [{ar.di}+4]")
        a.e("    cmp ecx, eax")
        a.e("    je __rt_deref_done")
        a.e("    mov eax, ecx")
        a.e("    jmp __rt_deref_loop")
        a.l("__rt_deref_done")
        a.e("    ret")
        a.e()

        # Trail helpers ---------------------------------------------------
        a.l("__rt_trail_push")
        self._prologue(a, save=(ar.bx, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e("    mov eax, dword ptr [__prolog_trail_top]")
        a.e(f"    cmp eax, {TRAIL_COUNT}")
        a.e("    jb __rt_trail_push_ok")
        a.e("    call __rt_fatal")
        a.l("__rt_trail_push_ok")
        self._arena_to(a, ar.di, TRAIL_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.ax}*4], ebx")
        a.e("    inc dword ptr [__prolog_trail_top]")
        self._epilogue(a, save=(ar.bx, ar.di))
        a.e()

        a.l("__rt_untrail_to")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.l("__rt_untrail_loop")
        a.e("    mov eax, dword ptr [__prolog_trail_top]")
        a.e("    cmp eax, ebx")
        a.e("    jbe __rt_untrail_done")
        a.e("    dec eax")
        a.e("    mov dword ptr [__prolog_trail_top], eax")
        self._arena_to(a, ar.di, TRAIL_OFF)
        a.e(f"    mov esi, dword ptr [{ar.di}+{ar.ax}*4]")
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov dword ptr [{ar.di}+4], esi")
        a.e("    jmp __rt_untrail_loop")
        a.l("__rt_untrail_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # occurs(var, term) -> 1 iff the dereferenced term contains var.
        a.l("__rt_occurs")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov eax, {ar.arg(1)}")
        a.e("    call __rt_deref")
        a.e("    mov esi, eax")
        a.e("    cmp eax, ebx")
        a.e("    je __rt_occurs_yes")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov ecx, dword ptr [{ar.di}]")
        a.e(f"    cmp ecx, {NODE_LIST}")
        a.e("    je __rt_occurs_list")
        a.e(f"    cmp ecx, {NODE_STRUCT}")
        a.e("    je __rt_occurs_struct")
        a.e("    xor eax, eax")
        a.e("    jmp __rt_occurs_done")
        a.l("__rt_occurs_list")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_occurs")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    pop {ar.dx}")
        a.e("    test eax, eax")
        a.e("    jne __rt_occurs_yes")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_occurs")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    jmp __rt_occurs_done")
        a.l("__rt_occurs_struct")
        a.e(f"    mov esi, dword ptr [{ar.di}+8]")
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")
        a.l("__rt_occurs_struct_loop")
        a.e("    test esi, esi")
        a.e("    je __rt_occurs_no")
        a.e(f"    cmp edx, {INVALID}")
        a.e("    je __rt_occurs_no")
        a.e("    mov eax, edx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_occurs")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    pop {ar.dx}")
        a.e("    test eax, eax")
        a.e("    jne __rt_occurs_yes")
        a.e("    dec esi")
        a.e("    jmp __rt_occurs_struct_loop")
        a.l("__rt_occurs_no")
        a.e("    xor eax, eax")
        a.e("    jmp __rt_occurs_done")
        a.l("__rt_occurs_yes")
        a.e("    mov eax, 1")
        a.l("__rt_occurs_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        a.l("__rt_bind_var")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_occurs")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    jne __rt_bind_var_occurs_fail")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_trail_push")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov dword ptr [{ar.di}+4], esi")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_bind_var_done")
        a.l("__rt_bind_var_occurs_fail")
        a.e("    xor eax, eax")
        a.l("__rt_bind_var_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Choice point stack ---------------------------------------------
        a.l("__rt_choice_push")
        self._prologue(a, save=(ar.di,))
        a.e("    mov eax, dword ptr [__prolog_choice_top]")
        a.e(f"    cmp eax, {CHOICE_COUNT}")
        a.e("    jb __rt_choice_push_ok")
        a.e("    call __rt_fatal")
        a.l("__rt_choice_push_ok")
        self._arena_to(a, ar.di, CHOICE_OFF)
        a.e("    mov ecx, eax")
        a.e("    shl ecx, 4")
        a.e(f"    add {ar.di}, {ar.cx}")
        a.e("    mov ecx, dword ptr [__prolog_heap_top]")
        a.e(f"    mov dword ptr [{ar.di}], ecx")
        a.e("    mov ecx, dword ptr [__prolog_trail_top]")
        a.e(f"    mov dword ptr [{ar.di}+4], ecx")
        a.e("    inc dword ptr [__prolog_choice_top]")
        self._epilogue(a, save=(ar.di,))
        a.e()

        a.l("__rt_choice_restore_pop")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e("    mov eax, dword ptr [__prolog_choice_top]")
        a.e("    test eax, eax")
        a.e("    je __rt_choice_restore_done")
        a.e("    dec eax")
        a.e("    mov dword ptr [__prolog_choice_top], eax")
        self._arena_to(a, ar.di, CHOICE_OFF)
        a.e("    mov ecx, eax")
        a.e("    shl ecx, 4")
        a.e(f"    add {ar.di}, {ar.cx}")
        a.e(f"    mov ebx, dword ptr [{ar.di}]")
        a.e(f"    mov esi, dword ptr [{ar.di}+4]")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_untrail_to")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov dword ptr [__prolog_heap_top], ebx")
        a.l("__rt_choice_restore_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Restore the snapshot stored at an exact choice slot and set top to
        # that slot.  This still works after ! has pruned choice_top because
        # the snapshot bytes themselves remain in the arena.
        a.l("__rt_choice_restore_slot")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    cmp ebx, {CHOICE_COUNT}")
        a.e("    jae __rt_choice_restore_slot_done")
        self._arena_to(a, ar.di, CHOICE_OFF)
        a.e("    mov ecx, ebx")
        a.e("    shl ecx, 4")
        a.e(f"    add {ar.di}, {ar.cx}")
        a.e(f"    mov esi, dword ptr [{ar.di}]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+4]")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_untrail_to")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov dword ptr [__prolog_heap_top], esi")
        a.e("    mov dword ptr [__prolog_choice_top], ebx")
        a.l("__rt_choice_restore_slot_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Drop the top choicepoint without undoing bindings/heap. Used by
        # commit-like side effects such as successful retract/1.
        a.l("__rt_choice_commit_pop")
        a.e("    mov eax, dword ptr [__prolog_choice_top]")
        a.e("    test eax, eax")
        a.e("    je __rt_choice_commit_done")
        a.e("    dec eax")
        a.e("    mov dword ptr [__prolog_choice_top], eax")
        a.l("__rt_choice_commit_done")
        a.e("    ret")
        a.e()

        # Structural unification ----------------------------------------
        self._emit_unify(a)
        self._emit_equal(a)
        self._emit_struct_arg(a)
        self._emit_goal_chain_helpers(a)
        self._emit_arithmetic(a)

    def _emit_unify(self, a: _A) -> None:
        ar = self.arch
        # unify(a,b) stack args, atomic on failure via trail mark.
        #
        # IMPORTANT: __rt_node_ptr uses ECX/RCX as a scratch register.  The
        # right-hand term handle must therefore NOT live in ECX across a
        # __rt_node_ptr call.  Keep it in EBX instead.  The old implementation
        # lost the right handle here, which made VAR <-> value unification
        # fail (e.g. X is 1+2) and also corrupted LIST/STRUCT recursion.
        a.l("__rt_unify")
        a.e(f"    push {ar.bp}")
        a.e(f"    mov {ar.bp}, {ar.sp}")
        a.e(f"    sub {ar.sp}, {ar.ptr}")
        a.e("    mov eax, dword ptr [__prolog_trail_top]")
        a.e(f"    mov dword ptr [{ar.bp}-{ar.ptr}], eax")
        a.e(f"    push {ar.bx}")
        a.e(f"    push {ar.si}")
        a.e(f"    push {ar.di}")

        # ESI = dereferenced left handle, EBX = dereferenced right handle.
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    mov esi, eax")
        a.e(f"    mov eax, {ar.arg(1)}")
        a.e("    call __rt_deref")
        a.e("    mov ebx, eax")
        a.e("    cmp esi, ebx")
        a.e("    je __rt_unify_success")

        # Left variable?
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov edx, dword ptr [{ar.di}]")
        a.e(f"    cmp edx, {NODE_VAR}")
        a.e("    jne __rt_unify_check_right_var")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_bind_var")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_unify_fail")
        a.e("    jmp __rt_unify_success")

        # Right variable?
        a.l("__rt_unify_check_right_var")
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_VAR}")
        a.e("    jne __rt_unify_nonvar")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_bind_var")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_unify_fail")
        a.e("    jmp __rt_unify_success")

        # Both non-variable: compare tags.  EBX remains the right handle.
        a.l("__rt_unify_nonvar")
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov edx, dword ptr [{ar.di}]")
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp edx, dword ptr [{ar.di}]")
        a.e("    jne __rt_unify_fail")

        for tag in (NODE_ATOM, NODE_INT, NODE_STRING):
            a.e(f"    cmp edx, {tag}")
            a.e("    je __rt_unify_scalar")
        a.e(f"    cmp edx, {NODE_FLOAT}")
        a.e("    je __rt_unify_float")
        a.e(f"    cmp edx, {NODE_NIL}")
        a.e("    je __rt_unify_success")
        a.e(f"    cmp edx, {NODE_LIST}")
        a.e("    je __rt_unify_list")
        a.e(f"    cmp edx, {NODE_STRUCT}")
        a.e("    je __rt_unify_struct")
        a.e("    jmp __rt_unify_fail")

        # Scalar: DI still points at right node.  EDX can now hold its value;
        # __rt_node_ptr does not clobber EDX.
        a.l("__rt_unify_scalar")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]")
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}+4], edx")
        a.e("    jne __rt_unify_fail")
        a.e("    jmp __rt_unify_success")

        a.l("__rt_unify_float")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    pop {ar.dx}")
        a.e(f"    pop {ar.cx}")
        a.e(f"    cmp dword ptr [{ar.di}+4], edx")
        a.e("    jne __rt_unify_fail")
        a.e(f"    cmp dword ptr [{ar.di}+8], ecx")
        a.e("    jne __rt_unify_fail")
        a.e("    jmp __rt_unify_success")

        # Lists: preserve the right handle in EBX; ECX is scratch for
        # __rt_node_ptr and therefore only receives right-next after the call.
        a.l("__rt_unify_list")
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov eax, dword ptr [{ar.di}+8]")   # left head
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")  # left tail
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov eax, dword ptr [{ar.di}+8]")   # right head
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")  # right tail
        a.e(f"    pop {ar.si}")                       # left head
        a.e(f"    {ar.push_reg32('edx')}")            # preserve right tail
        a.e(f"    {ar.push_reg32('eax')}")            # arg1 right head
        a.e(f"    {ar.push_reg32('esi')}")            # arg0 left head
        a.e("    call __rt_unify")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_unify_fail_pop_tails")
        a.e(f"    pop {ar.dx}")                       # right tail
        a.e(f"    pop {ar.si}")                       # left tail
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_unify")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_unify_fail")
        a.e("    jmp __rt_unify_success")
        a.l("__rt_unify_fail_pop_tails")
        a.e(f"    pop {ar.dx}")
        a.e(f"    pop {ar.si}")
        a.e("    jmp __rt_unify_fail")

        # Structures: compare functor/arity, then recursively unify each pair
        # of arguments.  The right argument-link must be preserved around
        # __rt_node_ptr because ECX is its scratch register.
        a.l("__rt_unify_struct")
        a.e(f"    {ar.push_reg32('ebx')}")             # right struct handle
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov ebx, dword ptr [{ar.di}+4]")    # left functor
        a.e(f"    mov esi, dword ptr [{ar.di}+8]")    # arity
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")   # left arg link
        a.e(f"    pop {ar.cx}")                        # right struct handle
        a.e("    mov eax, ecx")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp ebx, dword ptr [{ar.di}+4]")
        a.e("    jne __rt_unify_fail")
        a.e(f"    cmp esi, dword ptr [{ar.di}+8]")
        a.e("    jne __rt_unify_fail")
        a.e(f"    mov ecx, dword ptr [{ar.di}+12]")   # right arg link
        a.e("    mov ebx, esi")                         # remaining count
        a.l("__rt_unify_struct_loop")
        a.e("    test ebx, ebx")
        a.e("    je __rt_unify_success")
        a.e(f"    {ar.push_reg32('ecx')}")             # preserve right link
        a.e("    mov eax, edx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov esi, dword ptr [{ar.di}+8]")    # left term
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")   # left next
        a.e(f"    pop {ar.cx}")                        # restore right link
        a.e(f"    {ar.push_reg32('edx')}")             # preserve left next
        a.e("    mov eax, ecx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov eax, dword ptr [{ar.di}+8]")    # right term
        a.e(f"    mov ecx, dword ptr [{ar.di}+12]")   # right next
        a.e(f"    {ar.push_reg32('ecx')}")             # preserve right next
        a.e(f"    {ar.push_reg32('eax')}")             # arg1 right term
        a.e(f"    {ar.push_reg32('esi')}")             # arg0 left term
        a.e("    call __rt_unify")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_unify_struct_fail_stack")
        a.e(f"    pop {ar.cx}")                        # right next
        a.e(f"    pop {ar.dx}")                        # left next
        a.e("    dec ebx")
        a.e("    jmp __rt_unify_struct_loop")
        a.l("__rt_unify_struct_fail_stack")
        a.e(f"    pop {ar.cx}")
        a.e(f"    pop {ar.dx}")
        a.e("    jmp __rt_unify_fail")

        a.l("__rt_unify_success")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_unify_done")
        a.l("__rt_unify_fail")
        a.e(f"    push dword ptr [{ar.bp}-{ar.ptr}]")
        a.e("    call __rt_untrail_to")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    xor eax, eax")
        a.l("__rt_unify_done")
        a.e(f"    pop {ar.di}")
        a.e(f"    pop {ar.si}")
        a.e(f"    pop {ar.bx}")
        a.e(f"    mov {ar.sp}, {ar.bp}")
        a.e(f"    pop {ar.bp}")
        a.e("    ret")
        a.e()

    def _emit_equal(self, a: _A) -> None:
        # ISO ==/2: exact term identity after dereference, without creating
        # bindings. Two distinct unbound variables are therefore NOT equal.
        ar = self.arch
        a.l("__rt_equal_terms")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    mov ebx, eax")
        a.e(f"    mov eax, {ar.arg(1)}")
        a.e("    call __rt_deref")
        a.e("    mov esi, eax")
        a.e("    cmp ebx, esi")
        a.e("    je __rt_equal_yes")
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov edx, dword ptr [{ar.di}]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+4]")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    pop {ar.dx}")
        a.e(f"    pop {ar.cx}")
        a.e(f"    cmp edx, dword ptr [{ar.di}]")
        a.e("    jne __rt_equal_no")
        # Different variables are not identical.
        a.e(f"    cmp edx, {NODE_VAR}")
        a.e("    je __rt_equal_no")
        for tag in (NODE_ATOM, NODE_INT, NODE_STRING):
            a.e(f"    cmp edx, {tag}")
            a.e("    je __rt_equal_scalar")
        a.e(f"    cmp edx, {NODE_FLOAT}")
        a.e("    je __rt_equal_float")
        a.e(f"    cmp edx, {NODE_NIL}")
        a.e("    je __rt_equal_yes")
        a.e(f"    cmp edx, {NODE_LIST}")
        a.e("    je __rt_equal_list")
        a.e(f"    cmp edx, {NODE_STRUCT}")
        a.e("    je __rt_equal_struct")
        a.e("    jmp __rt_equal_no")
        a.l("__rt_equal_scalar")
        a.e(f"    cmp ecx, dword ptr [{ar.di}+4]")
        a.e("    je __rt_equal_yes")
        a.e("    jmp __rt_equal_no")
        a.l("__rt_equal_float")
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    pop {ar.dx}")
        a.e(f"    pop {ar.cx}")
        a.e(f"    cmp dword ptr [{ar.di}+4], edx")
        a.e("    jne __rt_equal_no")
        a.e(f"    cmp dword ptr [{ar.di}+8], ecx")
        a.e("    je __rt_equal_yes")
        a.e("    jmp __rt_equal_no")
        a.l("__rt_equal_list")
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        # stack: left_tail,left_head,right_tail,right_head
        a.e(f"    pop {ar.cx}")
        a.e(f"    pop {ar.dx}")
        a.e(f"    pop {ar.ax}")
        a.e(f"    pop {ar.si}")
        # preserve tails, compare heads
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_equal_terms")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    pop {ar.dx}")
        a.e(f"    pop {ar.si}")
        a.e("    test eax, eax")
        a.e("    je __rt_equal_no")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_equal_terms")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    jmp __rt_equal_done")
        a.l("__rt_equal_struct")
        # functor/arity then each argument link.
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov ebx, dword ptr [{ar.di}+4]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp ebx, dword ptr [{ar.di}+4]")
        a.e("    jne __rt_equal_struct_fail_pop")
        a.e(f"    pop {ar.cx}")
        a.e(f"    cmp ecx, dword ptr [{ar.di}+8]")
        a.e("    jne __rt_equal_struct_fail_one")
        a.e(f"    mov esi, dword ptr [{ar.di}+12]")
        a.e(f"    pop {ar.dx}")
        a.l("__rt_equal_struct_loop")
        a.e("    test ecx, ecx")
        a.e("    je __rt_equal_yes")
        a.e("    mov eax, edx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov ebx, dword ptr [{ar.di}+8]")
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov eax, dword ptr [{ar.di}+8]")
        a.e(f"    mov esi, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_equal_terms")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    pop {ar.si}")
        a.e(f"    pop {ar.cx}")
        a.e(f"    pop {ar.dx}")
        a.e("    test eax, eax")
        a.e("    je __rt_equal_no")
        a.e("    dec ecx")
        a.e("    jmp __rt_equal_struct_loop")
        a.l("__rt_equal_struct_fail_pop")
        a.e(f"    pop {ar.cx}")
        a.l("__rt_equal_struct_fail_one")
        a.e(f"    pop {ar.dx}")
        a.e("    jmp __rt_equal_no")
        a.l("__rt_equal_yes")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_equal_done")
        a.l("__rt_equal_no")
        a.e("    xor eax, eax")
        a.l("__rt_equal_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    def _emit_struct_arg(self, a: _A) -> None:
        ar = self.arch
        # struct_arg(term, zero-based index) -> EAX term index or INVALID
        a.l("__rt_struct_arg")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e("    jne __rt_struct_arg_fail")
        a.e(f"    mov esi, dword ptr [{ar.di}+12]")
        a.e(f"    mov ebx, {ar.arg(1)}")
        a.l("__rt_struct_arg_loop")
        a.e(f"    cmp esi, {INVALID}")
        a.e("    je __rt_struct_arg_fail")
        a.e("    mov eax, esi")
        a.e("    call __rt_node_ptr")
        a.e("    test ebx, ebx")
        a.e("    je __rt_struct_arg_found")
        a.e(f"    mov esi, dword ptr [{ar.di}+12]")
        a.e("    dec ebx")
        a.e("    jmp __rt_struct_arg_loop")
        a.l("__rt_struct_arg_found")
        a.e(f"    mov eax, dword ptr [{ar.di}+8]")
        a.e("    jmp __rt_struct_arg_done")
        a.l("__rt_struct_arg_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_struct_arg_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    def _emit_goal_chain_helpers(self, a: _A) -> None:
        ar = self.arch
        # goal_expr_to_chain(expr, rest, barrier) expands conjunctions while
        # keeping disjunctions as goals handled by ;/2.  Every generated link
        # carries its lexical cut barrier in node+4.
        a.l("__rt_goal_expr_to_chain")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        # The lexical barrier remains available in the function argument.
        # Do not cache it in volatile EDX across recursive calls.
        a.e("    mov eax, ebx")
        a.e("    call __rt_deref")
        a.e("    mov ebx, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e("    jne __rt_goal_expr_single")
        a.e(f"    cmp dword ptr [{ar.di}+4], {self.atom_id(',')}")
        a.e("    jne __rt_goal_expr_single")
        a.e(f"    cmp dword ptr [{ar.di}+8], 2")
        a.e("    jne __rt_goal_expr_single")
        # right branch first -> tail chain
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    push {ar.arg(2)}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_goal_expr_to_chain")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    mov esi, eax")
        # left branch
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    push {ar.arg(2)}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_goal_expr_to_chain")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    jmp __rt_goal_expr_done")
        a.l("__rt_goal_expr_single")
        a.e(f"    push {ar.arg(2)}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_make_goal_link")
        a.e(f"    {ar.cleanup(3)}")
        a.l("__rt_goal_expr_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # make_binary_term(functor,left,right) / make_unary_term(functor,arg)
        a.l("__rt_make_binary_term")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        a.e(f"    mov ecx, {ar.arg(2)}")
        a.e(f"    push {INVALID}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_make_link")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ecx, eax")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_make_link")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ecx, eax")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    push 2")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_make_struct")
        a.e(f"    {ar.cleanup(3)}")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()
        a.l("__rt_make_unary_term")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        a.e(f"    push {INVALID}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_make_link")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_make_struct")
        a.e(f"    {ar.cleanup(3)}")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

    def _emit_arithmetic(self, a: _A) -> None:
        ar = self.arch

        # Load a numeric term onto the x87 stack. EAX=1 on success, 0 on fail.
        a.l("__rt_load_number")
        self._prologue(a, save=(ar.bx, ar.di))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    mov ebx, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_INT}")
        a.e("    je __rt_load_number_int")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_FLOAT}")
        a.e("    je __rt_load_number_float")
        a.e("    xor eax, eax")
        a.e("    jmp __rt_load_number_done")
        a.l("__rt_load_number_int")
        a.e(f"    fild dword ptr [{ar.di}+4]")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_load_number_done")
        a.l("__rt_load_number_float")
        a.e(f"    fld qword ptr [{ar.di}+4]")
        a.e("    mov eax, 1")
        a.l("__rt_load_number_done")
        self._epilogue(a, save=(ar.bx, ar.di))
        a.e()

        # numeric_zero(term) -> EAX=1 if numeric zero, EDX=1 on numeric input.
        a.l("__rt_numeric_zero")
        self._prologue(a, save=(ar.di,))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_INT}")
        a.e("    je __rt_numeric_zero_int")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_FLOAT}")
        a.e("    je __rt_numeric_zero_float")
        a.e("    xor eax, eax")
        a.e("    xor edx, edx")
        a.e("    jmp __rt_numeric_zero_done")
        a.l("__rt_numeric_zero_int")
        a.e("    xor eax, eax")
        a.e(f"    cmp dword ptr [{ar.di}+4], 0")
        a.e("    sete al")
        a.e("    mov edx, 1")
        a.e("    jmp __rt_numeric_zero_done")
        a.l("__rt_numeric_zero_float")
        a.e(f"    mov eax, dword ptr [{ar.di}+4]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e("    and ecx, 2147483647")
        a.e("    or eax, ecx")
        a.e("    sete al")
        a.e("    and eax, 1")
        a.e("    mov edx, 1")
        a.l("__rt_numeric_zero_done")
        self._epilogue(a, save=(ar.di,))
        a.e()

        # numeric_compare(left,right) -> EAX=-1/0/1, EDX=1; NaN/non-number fails.
        a.l("__rt_numeric_compare")
        self._prologue(a)
        a.e(f"    push {ar.arg(1)}")
        a.e("    call __rt_load_number")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    je __rt_numeric_compare_fail")
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_load_number")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    jne __rt_numeric_compare_have")
        a.e("    fstp st0")
        a.e("    jmp __rt_numeric_compare_fail")
        a.l("__rt_numeric_compare_have")
        # ST0=left, ST1=right. FUCOMIP pops left, then discard right.
        a.e("    fucomip st0, st1")
        a.e("    fstp st0")
        a.e("    jp __rt_numeric_compare_fail")
        a.e("    je __rt_numeric_compare_equal")
        a.e("    jb __rt_numeric_compare_less")
        a.e("    mov eax, 1")
        a.e("    mov edx, 1")
        a.e("    jmp __rt_numeric_compare_done")
        a.l("__rt_numeric_compare_less")
        a.e("    mov eax, -1")
        a.e("    mov edx, 1")
        a.e("    jmp __rt_numeric_compare_done")
        a.l("__rt_numeric_compare_equal")
        a.e("    xor eax, eax")
        a.e("    mov edx, 1")
        a.e("    jmp __rt_numeric_compare_done")
        a.l("__rt_numeric_compare_fail")
        a.e("    xor eax, eax")
        a.e("    xor edx, edx")
        a.l("__rt_numeric_compare_done")
        self._epilogue(a)
        a.e()

        # eval_arith(term) -> EAX numeric term handle, EDX=1 on success.
        a.l("__rt_eval_arith")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    mov ebx, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_INT}")
        a.e("    je __rt_eval_numeric_leaf")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_FLOAT}")
        a.e("    je __rt_eval_numeric_leaf")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e("    jne __rt_eval_fail")
        a.e(f"    mov esi, dword ptr [{ar.di}+4]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")

        # Arithmetic float/1 is a function in expression context, not the
        # float/1 type-test predicate dispatched by __rt_builtin_dispatch.
        a.e(f"    cmp esi, {self.atom_id('float')}")
        a.e("    jne __rt_eval_float_next")
        a.e("    cmp ecx, 1")
        a.e("    je __rt_eval_float")
        a.l("__rt_eval_float_next")

        for op,label in (("+","__rt_eval_uplus"),("-","__rt_eval_uminus")):
            a.e(f"    cmp esi, {self.atom_id(op)}")
            a.e(f"    jne {label}_next")
            a.e("    cmp ecx, 1")
            a.e(f"    je {label}")
            a.l(f"{label}_next")
        for op,label in (("+","__rt_eval_add"),("-","__rt_eval_sub"),("*","__rt_eval_mul"),("/","__rt_eval_div"),("mod","__rt_eval_mod")):
            a.e(f"    cmp esi, {self.atom_id(op)}")
            a.e(f"    jne {label}_next")
            a.e("    cmp ecx, 2")
            a.e(f"    je {label}")
            a.l(f"{label}_next")
        a.e("    jmp __rt_eval_fail")

        a.l("__rt_eval_numeric_leaf")
        a.e("    mov eax, ebx")
        a.e("    mov edx, 1")
        a.e("    jmp __rt_eval_done")

        def unary(label: str, negate: bool) -> None:
            a.l(label)
            a.e("    push 0")
            a.e(f"    {ar.push_reg32('ebx')}")
            a.e("    call __rt_struct_arg")
            a.e(f"    {ar.cleanup(2)}")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    call __rt_eval_arith")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    test edx, edx")
            a.e("    je __rt_eval_fail")
            a.e("    mov ebx, eax")
            if not negate:
                a.e("    mov eax, ebx")
                a.e("    mov edx, 1")
                a.e("    jmp __rt_eval_done")
                return
            a.e("    mov eax, ebx")
            a.e("    call __rt_node_ptr")
            a.e(f"    cmp dword ptr [{ar.di}], {NODE_INT}")
            a.e(f"    jne {label}_float")
            a.e(f"    mov eax, dword ptr [{ar.di}+4]")
            a.e("    neg eax")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    call __rt_make_int")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    mov edx, 1")
            a.e("    jmp __rt_eval_done")
            a.l(f"{label}_float")
            a.e(f"    {ar.push_reg32('ebx')}")
            a.e("    call __rt_load_number")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    test eax, eax")
            a.e("    je __rt_eval_fail")
            a.e("    fchs")
            a.e("    call __rt_make_float_from_st0")
            a.e("    mov edx, 1")
            a.e("    jmp __rt_eval_done")

        # Arithmetic float(Expression): evaluate Expression recursively and
        # always construct a NODE_FLOAT result.  __rt_load_number accepts both
        # NODE_INT and NODE_FLOAT and leaves the numeric value in ST0.
        a.l("__rt_eval_float")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_eval_arith")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_eval_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_load_number")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    je __rt_eval_fail")
        a.e("    call __rt_make_float_from_st0")
        a.e("    mov edx, 1")
        a.e("    jmp __rt_eval_done")

        unary("__rt_eval_uplus", False)
        unary("__rt_eval_uminus", True)

        def binary(label: str, operation: str) -> None:
            a.l(label)
            # Evaluate left and right first; both return numeric term handles.
            a.e("    push 0")
            a.e(f"    {ar.push_reg32('ebx')}")
            a.e("    call __rt_struct_arg")
            a.e(f"    {ar.cleanup(2)}")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    call __rt_eval_arith")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    test edx, edx")
            a.e("    je __rt_eval_fail")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    push 1")
            a.e(f"    {ar.push_reg32('ebx')}")
            a.e("    call __rt_struct_arg")
            a.e(f"    {ar.cleanup(2)}")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    call __rt_eval_arith")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    test edx, edx")
            a.e("    je __rt_eval_fail_pop")
            a.e("    mov esi, eax")       # right numeric handle
            a.e(f"    pop {ar.bx}")       # left numeric handle

            if operation == "mod":
                # MOD remains integer-only.
                a.e("    mov eax, ebx")
                a.e("    call __rt_node_ptr")
                a.e(f"    cmp dword ptr [{ar.di}], {NODE_INT}")
                a.e("    jne __rt_eval_fail")
                a.e(f"    mov ebx, dword ptr [{ar.di}+4]")
                a.e("    mov eax, esi")
                a.e("    call __rt_node_ptr")
                a.e(f"    cmp dword ptr [{ar.di}], {NODE_INT}")
                a.e("    jne __rt_eval_fail")
                a.e(f"    mov ecx, dword ptr [{ar.di}+4]")
                a.e("    test ecx, ecx")
                a.e("    je __rt_eval_fail")
                a.e("    mov eax, ebx")
                a.e("    cdq")
                a.e("    idiv ecx")
                a.e("    mov eax, edx")
                a.e(f"    {ar.push_reg32('eax')}")
                a.e("    call __rt_make_int")
                a.e(f"    {ar.cleanup(1)}")
                a.e("    mov edx, 1")
                a.e("    jmp __rt_eval_done")
                return

            if operation != "div":
                # Preserve integer arithmetic when both operands are integers.
                a.e("    mov eax, ebx")
                a.e("    call __rt_node_ptr")
                a.e(f"    cmp dword ptr [{ar.di}], {NODE_INT}")
                a.e(f"    jne {label}_float")
                a.e("    mov eax, esi")
                a.e("    call __rt_node_ptr")
                a.e(f"    cmp dword ptr [{ar.di}], {NODE_INT}")
                a.e(f"    jne {label}_float")
                a.e("    mov eax, ebx")
                a.e("    call __rt_node_ptr")
                a.e(f"    mov ebx, dword ptr [{ar.di}+4]")
                a.e("    mov eax, esi")
                a.e("    call __rt_node_ptr")
                a.e(f"    mov ecx, dword ptr [{ar.di}+4]")
                a.e("    mov eax, ebx")
                if operation == "add": a.e("    add eax, ecx")
                elif operation == "sub": a.e("    sub eax, ecx")
                elif operation == "mul": a.e("    imul eax, ecx")
                a.e(f"    {ar.push_reg32('eax')}")
                a.e("    call __rt_make_int")
                a.e(f"    {ar.cleanup(1)}")
                a.e("    mov edx, 1")
                a.e("    jmp __rt_eval_done")
                a.l(f"{label}_float")
            else:
                # / always produces a floating-point result.
                a.e(f"    {ar.push_reg32('esi')}")
                a.e("    call __rt_numeric_zero")
                a.e(f"    {ar.cleanup(1)}")
                a.e("    test edx, edx")
                a.e("    je __rt_eval_fail")
                a.e("    test eax, eax")
                a.e("    jne __rt_eval_fail")

            # x87 binary order is significant for FSUBP/FDIVP.
            # Load LEFT first and RIGHT second so that immediately before
            # the pop-operation ST0=right and ST1=left.  The no-operand
            # encodings emitted by d64_dism are FSUBP ST1,ST0 /
            # FDIVP ST1,ST0, i.e. ST1 := ST1 op ST0 followed by pop.
            # Loading right first would therefore compute right-left and
            # right/left (the old 1/2 -> 2 bug).
            a.e(f"    {ar.push_reg32('ebx')}")
            a.e("    call __rt_load_number")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    test eax, eax")
            a.e("    je __rt_eval_fail")
            a.e(f"    {ar.push_reg32('esi')}")
            a.e("    call __rt_load_number")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    test eax, eax")
            a.e(f"    jne {label}_fpu")
            a.e("    fstp st0")
            a.e("    jmp __rt_eval_fail")
            a.l(f"{label}_fpu")
            if operation == "add": a.e("    faddp")
            elif operation == "sub": a.e("    fsubp")
            elif operation == "mul": a.e("    fmulp")
            elif operation == "div": a.e("    fdivp")
            a.e("    call __rt_make_float_from_st0")
            a.e("    mov edx, 1")
            a.e("    jmp __rt_eval_done")

        binary("__rt_eval_add", "add")
        binary("__rt_eval_sub", "sub")
        binary("__rt_eval_mul", "mul")
        binary("__rt_eval_div", "div")
        binary("__rt_eval_mod", "mod")

        a.l("__rt_eval_fail_pop")
        a.e(f"    pop {ar.bx}")
        a.l("__rt_eval_fail")
        a.e("    xor eax, eax")
        a.e("    xor edx, edx")
        a.l("__rt_eval_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    # ------------------------------------------------------------------
    # Persistent dynamic fact database (assert/retract)
    # ------------------------------------------------------------------
    def _emit_dynamic_db(self, a: _A) -> None:
        ar = self.arch
        # Copy a ground transient term into persistent dynamic heap.
        a.l("__rt_dyn_copy_ground")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    mov ebx, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov esi, dword ptr [{ar.di}]")
        a.e(f"    cmp esi, {NODE_VAR}")
        a.e("    je __rt_dyn_copy_var")
        # scalar
        for tag in (NODE_ATOM, NODE_INT, NODE_STRING, NODE_NIL):
            a.e(f"    cmp esi, {tag}")
            a.e("    je __rt_dyn_copy_scalar")
        a.e(f"    cmp esi, {NODE_FLOAT}")
        a.e("    je __rt_dyn_copy_float")
        a.e(f"    cmp esi, {NODE_LIST}")
        a.e("    je __rt_dyn_copy_list")
        a.e(f"    cmp esi, {NODE_STRUCT}")
        a.e("    je __rt_dyn_copy_struct")
        a.e("    jmp __rt_dyn_copy_fail")
        a.l("__rt_dyn_copy_var")
        # Preserve variable identity within one asserted fact.
        a.e("    xor ecx, ecx")
        a.l("__rt_dyn_copy_var_scan")
        a.e("    cmp ecx, dword ptr [__prolog_dyn_copy_var_count]")
        a.e("    jae __rt_dyn_copy_var_new")
        self._arena_to(a, ar.di, DYN_COPY_SRC_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.cx}*4], ebx")
        a.e("    jne __rt_dyn_copy_var_scan_next")
        self._arena_to(a, ar.di, DYN_COPY_DST_OFF)
        a.e(f"    mov eax, dword ptr [{ar.di}+{ar.cx}*4]")
        a.e("    jmp __rt_dyn_copy_done")
        a.l("__rt_dyn_copy_var_scan_next")
        a.e("    inc ecx")
        a.e("    jmp __rt_dyn_copy_var_scan")
        a.l("__rt_dyn_copy_var_new")
        a.e(f"    cmp ecx, {BUILD_VAR_MAX}")
        a.e("    jae __rt_dyn_copy_fail")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_new_dyn_node")
        a.e(f"    pop {ar.cx}")
        a.e("    mov edx, eax")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_VAR}")
        a.e(f"    mov dword ptr [{ar.di}+4], edx")
        self._arena_to(a, ar.di, DYN_COPY_SRC_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], ebx")
        self._arena_to(a, ar.di, DYN_COPY_DST_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], edx")
        a.e("    inc dword ptr [__prolog_dyn_copy_var_count]")
        a.e("    mov eax, edx")
        a.e("    jmp __rt_dyn_copy_done")
        a.l("__rt_dyn_copy_scalar")
        a.e(f"    mov ebx, dword ptr [{ar.di}+4]")
        a.e("    call __rt_new_dyn_node")
        a.e(f"    mov dword ptr [{ar.di}], esi")
        a.e(f"    mov dword ptr [{ar.di}+4], ebx")
        a.e("    jmp __rt_dyn_copy_done")
        a.l("__rt_dyn_copy_float")
        a.e(f"    mov ebx, dword ptr [{ar.di}+4]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_new_dyn_node")
        a.e(f"    pop {ar.cx}")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_FLOAT}")
        a.e(f"    mov dword ptr [{ar.di}+4], ebx")
        a.e(f"    mov dword ptr [{ar.di}+8], ecx")
        a.e("    jmp __rt_dyn_copy_done")
        a.l("__rt_dyn_copy_list")
        # capture head/tail from transient
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov esi, dword ptr [{ar.di}+8]")
        a.e(f"    mov ebx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_dyn_copy_ground")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_dyn_copy_fail")
        a.e(f"    {ar.push_reg32('eax')}")  # dyn head
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_dyn_copy_ground")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_dyn_copy_list_fail_stack")
        a.e("    mov ebx, eax") # dyn tail
        a.e(f"    pop {ar.si}") # dyn head
        a.e("    call __rt_new_dyn_node")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_LIST}")
        a.e(f"    mov dword ptr [{ar.di}+8], esi")
        a.e(f"    mov dword ptr [{ar.di}+12], ebx")
        a.e("    jmp __rt_dyn_copy_done")
        a.l("__rt_dyn_copy_list_fail_stack")
        a.e(f"    pop {ar.si}")
        a.e("    jmp __rt_dyn_copy_fail")
        a.l("__rt_dyn_copy_struct")
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov ebx, dword ptr [{ar.di}+4]") # functor
        a.e(f"    mov esi, dword ptr [{ar.di}+8]") # arity
        a.e(f"    mov ecx, dword ptr [{ar.di}+12]") # first transient arg link
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_dyn_copy_links")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_dyn_copy_fail")
        a.e("    mov ecx, eax")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_new_dyn_node")
        a.e(f"    pop {ar.cx}")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e(f"    mov dword ptr [{ar.di}+4], ebx")
        a.e(f"    mov dword ptr [{ar.di}+8], esi")
        a.e(f"    mov dword ptr [{ar.di}+12], ecx")
        a.e("    jmp __rt_dyn_copy_done")
        a.l("__rt_dyn_copy_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_dyn_copy_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Copy transient argument links to dynamic links, preserving order.
        # dyn_copy_links(first_transient_link,count) -> first_dynamic_link.
        a.l("__rt_dyn_copy_links")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        a.e("    test esi, esi")
        a.e("    jne __rt_dyn_copy_links_some")
        a.e(f"    mov eax, {INVALID}")
        a.e("    jmp __rt_dyn_copy_links_done")
        a.l("__rt_dyn_copy_links_some")
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov eax, dword ptr [{ar.di}+8]")
        a.e(f"    mov ebx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    dec esi")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_dyn_copy_links")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ecx, eax")
        a.e(f"    pop {ar.ax}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_dyn_copy_ground")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    pop {ar.cx}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_dyn_copy_links_fail")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_new_dyn_link")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    jmp __rt_dyn_copy_links_done")
        a.l("__rt_dyn_copy_links_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_dyn_copy_links_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # dynamic link constructor (term,next)
        a.l("__rt_new_dyn_link")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        a.e("    call __rt_new_dyn_node")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_LINK}")
        a.e(f"    mov dword ptr [{ar.di}+8], ebx")
        a.e(f"    mov dword ptr [{ar.di}+12], esi")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # clone dynamic ground term to transient heap
        self._emit_dyn_clone(a)

        # assert/1 and assertz/1 append; asserta/1 inserts at the beginning.
        # A stored root may be either Head or (Head :- Body).  The DB metadata
        # always describes Head, while +12 retains the complete persistent
        # clause term so retract/1 can match rules as well as facts.
        a.l("__rt_assert")
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_assertz")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    ret")
        a.e()
        a.l("__rt_assertz")
        self._prologue(a)
        a.e("    push 0")
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_assert_common")
        a.e(f"    {ar.cleanup(2)}")
        self._epilogue(a)
        a.e()
        a.l("__rt_asserta")
        self._prologue(a)
        a.e("    push 1")
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_assert_common")
        a.e(f"    {ar.cleanup(2)}")
        self._epilogue(a)
        a.e()
        a.l("__rt_assert_common")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")  # complete clause root
        a.e(f"    mov esi, {ar.arg(1)}")  # 0=z, 1=a
        # Normal assert/1 under database_select/1 must respect read-only DBs.
        # database_open sets __prolog_db_loading while it imports source facts.
        a.e("    mov eax, dword ptr [__prolog_current_db]")
        a.e("    test eax, eax")
        a.e("    je __rt_assert_modify_ok")
        a.e("    cmp dword ptr [__prolog_db_loading], 0")
        a.e("    jne __rt_assert_modify_ok")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_db_can_modify_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    je __rt_assert_common_fail")
        a.l("__rt_assert_modify_ok")
        # Reclaim inactive DB slots and compact persistent heap before pressure.
        a.e(f"    cmp dword ptr [__prolog_dyn_count], {DYN_DB_COUNT_MAX}")
        a.e("    jb __rt_assert_count_ok")
        a.e("    call __rt_dyn_db_compact")
        a.l("__rt_assert_count_ok")
        a.e(f"    cmp dword ptr [__prolog_dyn_count], {DYN_DB_COUNT_MAX}")
        a.e("    jae __rt_assert_common_fail")
        a.e(f"    cmp dword ptr [__prolog_dyn_heap_top], {max(1,(DYN_NODE_COUNT*3)//4)}")
        a.e("    jb __rt_assert_heap_ok")
        a.e("    call __rt_gc_dynamic")
        a.l("__rt_assert_heap_ok")
        # root/head inspection
        a.e("    mov eax, ebx")
        a.e("    call __rt_deref")
        a.e("    mov ebx, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e("    jne __rt_assert_head_ready_root")
        a.e(f"    cmp dword ptr [{ar.di}+4], {self.atom_id(':-')}")
        a.e("    jne __rt_assert_head_ready_root")
        a.e(f"    cmp dword ptr [{ar.di}+8], 2")
        a.e("    jne __rt_assert_head_ready_root")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ecx, eax")
        a.e("    jmp __rt_assert_head_ready")
        a.l("__rt_assert_head_ready_root")
        a.e("    mov ecx, ebx")
        a.l("__rt_assert_head_ready")
        # derive head functor / arity
        a.e("    mov eax, ecx")
        a.e("    call __rt_deref")
        a.e("    mov ecx, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov edx, dword ptr [{ar.di}]")
        a.e(f"    cmp edx, {NODE_ATOM}")
        a.e("    je __rt_assert_common_atom")
        a.e(f"    cmp edx, {NODE_STRUCT}")
        a.e("    jne __rt_assert_common_fail")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]") # functor
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]") # arity
        a.e("    jmp __rt_assert_common_copy")
        a.l("__rt_assert_common_atom")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]")
        a.e("    xor ecx, ecx")
        a.l("__rt_assert_common_copy")
        # Preserve functor, arity and mode while persistent copy runs.
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    mov dword ptr [__prolog_dyn_copy_var_count], 0")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_dyn_copy_ground")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov ebx, eax")
        a.e(f"    pop {ar.dx}")
        a.e(f"    pop {ar.cx}")
        a.e(f"    pop {ar.si}")
        a.e(f"    cmp ebx, {INVALID}")
        a.e("    je __rt_assert_common_fail")
        # Keep metadata alive across the asserta record-shift loop.  That loop
        # uses ECX/EDX as scratch registers while copying existing entries.
        a.e(f"    {ar.push_reg32('ecx')}")  # arity
        a.e(f"    {ar.push_reg32('edx')}")  # functor
        # assertz index = count. asserta shifts records right then index=0.
        a.e("    mov eax, dword ptr [__prolog_dyn_count]")
        a.e("    test esi, esi")
        a.e("    je __rt_assert_store")
        a.e("    mov esi, eax")
        a.l("__rt_asserta_shift_loop")
        a.e("    test esi, esi")
        a.e("    je __rt_asserta_shift_done")
        # src=(esi-1)*16, dst=esi*16
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, esi")
        a.e("    dec eax")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    mov eax, dword ptr [{ar.di}]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+4]")
        a.e(f"    mov edx, dword ptr [{ar.di}+8]")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    mov ebx, dword ptr [{ar.di}+12]")
        a.e(f"    add {ar.di}, 16")
        a.e(f"    mov dword ptr [{ar.di}], eax")
        a.e(f"    mov dword ptr [{ar.di}+4], ecx")
        a.e(f"    mov dword ptr [{ar.di}+8], edx")
        a.e(f"    mov dword ptr [{ar.di}+12], ebx")
        a.e(f"    pop {ar.bx}")
        # Keep the parallel Database-ID owner table in the same order.
        self._arena_to(a, ar.di, DYN_DB_OWNER_OFF)
        a.e("    mov eax, esi")
        a.e("    dec eax")
        a.e(f"    mov ecx, dword ptr [{ar.di}+{ar.ax}*4]")
        a.e(f"    mov dword ptr [{ar.di}+{ar.si}*4], ecx")
        a.e("    dec esi")
        a.e("    jmp __rt_asserta_shift_loop")
        a.l("__rt_asserta_shift_done")
        a.e("    xor eax, eax")
        a.l("__rt_assert_store")
        a.e(f"    pop {ar.dx}")   # restore functor
        a.e(f"    pop {ar.cx}")   # restore arity
        a.e(f"    {ar.push_reg32('eax')}")  # preserve DB slot index
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    mov dword ptr [{ar.di}], 1")
        a.e(f"    mov dword ptr [{ar.di}+4], edx")
        a.e(f"    mov dword ptr [{ar.di}+8], ecx")
        a.e(f"    mov dword ptr [{ar.di}+12], ebx")
        a.e(f"    pop {ar.ax}")
        self._arena_to(a, ar.di, DYN_DB_OWNER_OFF)
        a.e("    mov edx, dword ptr [__prolog_current_db]")
        a.e(f"    mov dword ptr [{ar.di}+{ar.ax}*4], edx")
        a.e("    inc dword ptr [__prolog_dyn_count]")
        a.e("    test edx, edx")
        a.e("    je __rt_assert_store_no_dirty")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_db_mark_modified_id")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_assert_store_no_dirty")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_assert_common_done")
        a.l("__rt_assert_common_fail")
        a.e("    xor eax, eax")
        a.l("__rt_assert_common_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # retract(pattern): first matching dynamic fact, runtime unification.
        a.l("__rt_retract")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e("    mov eax, dword ptr [__prolog_current_db]")
        a.e("    test eax, eax")
        a.e("    je __rt_retract_modify_ok")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_db_can_modify_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    je __rt_retract_fail")
        a.l("__rt_retract_modify_ok")
        a.e("    xor esi, esi")
        a.l("__rt_retract_loop")
        a.e("    cmp esi, dword ptr [__prolog_dyn_count]")
        a.e("    jae __rt_retract_fail")
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, esi")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    cmp dword ptr [{ar.di}], 0")
        a.e("    je __rt_retract_next")
        # Destructive retract/1 is always scoped to the current owner.
        # current_db=0 means the ordinary process-local dynamic database;
        # loaded external knowledge is changed only after database_select/1,
        # with_database/2 or database_retract/2.
        a.e("    mov edx, dword ptr [__prolog_current_db]")
        self._arena_to(a, ar.di, DYN_DB_OWNER_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.si}*4], edx")
        a.e("    jne __rt_retract_next")
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, esi")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    mov eax, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_choice_push")
        a.e(f"    pop {ar.ax}")
        a.e("    mov dword ptr [__prolog_dyn_clone_var_count], 0")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_dyn_clone")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_unify")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_retract_restore_next")
        # mark inactive before restoring transient bindings
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, esi")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    mov dword ptr [{ar.di}], 0")
        self._arena_to(a, ar.di, DYN_DB_OWNER_OFF)
        a.e(f"    mov edx, dword ptr [{ar.di}+{ar.si}*4]")
        a.e("    test edx, edx")
        a.e("    je __rt_retract_no_dirty")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_db_mark_modified_id")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_retract_no_dirty")
        a.e("    call __rt_choice_commit_pop")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_retract_done")
        a.l("__rt_retract_restore_next")
        a.e("    call __rt_choice_restore_pop")
        a.l("__rt_retract_next")
        a.e("    inc esi")
        a.e("    jmp __rt_retract_loop")
        a.l("__rt_retract_fail")
        a.e("    xor eax, eax")
        a.l("__rt_retract_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # DB compaction removes inactive retract slots while preserving order.
        a.l("__rt_dyn_db_compact")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e("    xor esi, esi")  # read index
        a.e("    xor ebx, ebx")  # write index
        a.l("__rt_dyn_compact_loop")
        a.e("    cmp esi, dword ptr [__prolog_dyn_count]")
        a.e("    jae __rt_dyn_compact_done")
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, esi")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    cmp dword ptr [{ar.di}], 0")
        a.e("    je __rt_dyn_compact_next")
        a.e("    cmp esi, ebx")
        a.e("    je __rt_dyn_compact_kept")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    mov eax, dword ptr [{ar.di}+4]")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    mov eax, dword ptr [{ar.di}+8]")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    mov eax, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('eax')}")
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, ebx")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    pop {ar.ax}")
        a.e(f"    pop {ar.dx}")
        a.e(f"    pop {ar.cx}")
        a.e(f"    pop {ar.si}")
        a.e(f"    mov dword ptr [{ar.di}], 1")
        a.e(f"    mov dword ptr [{ar.di}+4], ecx")
        a.e(f"    mov dword ptr [{ar.di}+8], edx")
        a.e(f"    mov dword ptr [{ar.di}+12], eax")
        # Move the parallel Database-ID owner alongside the compacted record.
        self._arena_to(a, ar.di, DYN_DB_OWNER_OFF)
        a.e(f"    mov eax, dword ptr [{ar.di}+{ar.si}*4]")
        a.e(f"    mov dword ptr [{ar.di}+{ar.bx}*4], eax")
        a.l("__rt_dyn_compact_kept")
        a.e("    inc ebx")
        a.l("__rt_dyn_compact_next")
        a.e("    inc esi")
        a.e("    jmp __rt_dyn_compact_loop")
        a.l("__rt_dyn_compact_done")
        a.e("    mov dword ptr [__prolog_dyn_count], ebx")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Copying GC for the persistent dynamic heap.  Active clauses are first
        # cloned into the transient heap, the semispace pointers are flipped,
        # then the clones are copied into the new persistent semispace.
        a.l("__rt_gc_dynamic")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e("    call __rt_dyn_db_compact")
        a.e("    mov eax, dword ptr [__prolog_heap_top]")
        a.e("    mov dword ptr [__prolog_gc_heap_mark], eax")
        a.e("    xor esi, esi")
        a.l("__rt_gc_clone_loop")
        a.e("    cmp esi, dword ptr [__prolog_dyn_count]")
        a.e("    jae __rt_gc_flip")
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, esi")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    mov eax, dword ptr [{ar.di}+12]")
        a.e("    mov dword ptr [__prolog_dyn_clone_var_count], 0")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_dyn_clone")
        a.e(f"    {ar.cleanup(1)}")
        self._arena_to(a, ar.di, GC_ROOT_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.si}*4], eax")
        a.e("    inc esi")
        a.e("    jmp __rt_gc_clone_loop")
        a.l("__rt_gc_flip")
        # swap active/alternate base pointers
        a.e(f"    mov {ar.ax}, {ar.mem_ptr('__prolog_dyn_base')}")
        a.e(f"    mov {ar.di}, {ar.mem_ptr('__prolog_dyn_alt_base')}")
        a.e(f"    mov {ar.mem_ptr('__prolog_dyn_base')}, {ar.di}")
        a.e(f"    mov {ar.mem_ptr('__prolog_dyn_alt_base')}, {ar.ax}")
        a.e("    mov dword ptr [__prolog_dyn_heap_top], 0")
        a.e("    xor esi, esi")
        a.l("__rt_gc_copy_loop")
        a.e("    cmp esi, dword ptr [__prolog_dyn_count]")
        a.e("    jae __rt_gc_done")
        self._arena_to(a, ar.di, GC_ROOT_OFF)
        a.e(f"    mov eax, dword ptr [{ar.di}+{ar.si}*4]")
        a.e("    mov dword ptr [__prolog_dyn_copy_var_count], 0")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_dyn_copy_ground")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov ebx, eax")
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, esi")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    mov dword ptr [{ar.di}+12], ebx")
        a.e("    inc esi")
        a.e("    jmp __rt_gc_copy_loop")
        a.l("__rt_gc_done")
        a.e("    mov eax, dword ptr [__prolog_gc_heap_mark]")
        a.e("    mov dword ptr [__prolog_heap_top], eax")
        a.e("    mov eax, 1")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    def _emit_dyn_clone(self, a: _A) -> None:
        ar = self.arch
        a.l("__rt_dyn_clone")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_dyn_clone_fail")
        a.e(f"    cmp eax, {DYN_NODE_COUNT}")
        a.e("    jae __rt_dyn_clone_fail")
        a.e("    mov ebx, eax")
        a.e("    call __rt_dyn_ptr")
        a.e(f"    mov esi, dword ptr [{ar.di}]")
        a.e(f"    cmp esi, {NODE_VAR}")
        a.e("    je __rt_dyn_clone_var")
        for tag in (NODE_ATOM, NODE_INT, NODE_STRING, NODE_NIL):
            a.e(f"    cmp esi, {tag}")
            a.e("    je __rt_dyn_clone_scalar")
        a.e(f"    cmp esi, {NODE_FLOAT}")
        a.e("    je __rt_dyn_clone_float")
        a.e(f"    cmp esi, {NODE_LIST}")
        a.e("    je __rt_dyn_clone_list")
        a.e(f"    cmp esi, {NODE_STRUCT}")
        a.e("    je __rt_dyn_clone_struct")
        a.e(f"    mov eax, {INVALID}")
        a.e("    jmp __rt_dyn_clone_done")
        a.l("__rt_dyn_clone_var")
        # Freshen dynamic variables for every database attempt.
        a.e("    xor ecx, ecx")
        a.l("__rt_dyn_clone_var_scan")
        a.e("    cmp ecx, dword ptr [__prolog_dyn_clone_var_count]")
        a.e("    jae __rt_dyn_clone_var_new")
        self._arena_to(a, ar.di, DYN_CLONE_SRC_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.cx}*4], ebx")
        a.e("    jne __rt_dyn_clone_var_scan_next")
        self._arena_to(a, ar.di, DYN_CLONE_DST_OFF)
        a.e(f"    mov eax, dword ptr [{ar.di}+{ar.cx}*4]")
        a.e("    jmp __rt_dyn_clone_done")
        a.l("__rt_dyn_clone_var_scan_next")
        a.e("    inc ecx")
        a.e("    jmp __rt_dyn_clone_var_scan")
        a.l("__rt_dyn_clone_var_new")
        a.e(f"    cmp ecx, {BUILD_VAR_MAX}")
        a.e("    jae __rt_dyn_clone_fail")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_new_node")
        a.e(f"    pop {ar.cx}")
        a.e("    mov edx, eax")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_VAR}")
        a.e(f"    mov dword ptr [{ar.di}+4], edx")
        self._arena_to(a, ar.di, DYN_CLONE_SRC_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], ebx")
        self._arena_to(a, ar.di, DYN_CLONE_DST_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], edx")
        a.e("    inc dword ptr [__prolog_dyn_clone_var_count]")
        a.e("    mov eax, edx")
        a.e("    jmp __rt_dyn_clone_done")
        a.l("__rt_dyn_clone_scalar")
        a.e(f"    mov ebx, dword ptr [{ar.di}+4]")
        a.e("    call __rt_new_node")
        a.e(f"    mov dword ptr [{ar.di}], esi")
        a.e(f"    mov dword ptr [{ar.di}+4], ebx")
        a.e("    jmp __rt_dyn_clone_done")
        a.l("__rt_dyn_clone_float")
        a.e(f"    mov ebx, dword ptr [{ar.di}+4]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_new_node")
        a.e(f"    pop {ar.cx}")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_FLOAT}")
        a.e(f"    mov dword ptr [{ar.di}+4], ebx")
        a.e(f"    mov dword ptr [{ar.di}+8], ecx")
        a.e("    jmp __rt_dyn_clone_done")
        a.l("__rt_dyn_clone_list")
        a.e("    mov eax, ebx")
        a.e("    call __rt_dyn_ptr")
        a.e(f"    mov esi, dword ptr [{ar.di}+8]")
        a.e(f"    mov ebx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_dyn_clone")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_dyn_clone")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov ebx, eax")
        a.e(f"    pop {ar.si}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_make_list")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    jmp __rt_dyn_clone_done")
        a.l("__rt_dyn_clone_struct")
        a.e("    mov eax, ebx")
        a.e("    call __rt_dyn_ptr")
        a.e(f"    mov ebx, dword ptr [{ar.di}+4]")
        a.e(f"    mov esi, dword ptr [{ar.di}+8]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_dyn_clone_links")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ecx, eax")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_make_struct")
        a.e(f"    {ar.cleanup(3)}")
        # Successful STRUCT clones must return the newly-created transient
        # handle. Without this jump execution fell through to FAIL and all
        # asserted compound facts/rules became invisible to lookup/retract.
        a.e("    jmp __rt_dyn_clone_done")
        a.l("__rt_dyn_clone_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_dyn_clone_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # dyn_clone_links(first_dyn_link,count) -> transient first link
        a.l("__rt_dyn_clone_links")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        a.e("    test esi, esi")
        a.e("    jne __rt_dyn_clone_links_some")
        a.e(f"    mov eax, {INVALID}")
        a.e("    jmp __rt_dyn_clone_links_done")
        a.l("__rt_dyn_clone_links_some")
        a.e("    mov eax, ebx")
        a.e("    call __rt_dyn_ptr")
        a.e(f"    mov eax, dword ptr [{ar.di}+8]")
        a.e(f"    mov ebx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    dec esi")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_dyn_clone_links")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ecx, eax")
        a.e(f"    pop {ar.ax}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_dyn_clone")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    pop {ar.cx}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_make_link")
        a.e(f"    {ar.cleanup(2)}")
        a.l("__rt_dyn_clone_links_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    # ------------------------------------------------------------------
    # External knowledge databases
    # ------------------------------------------------------------------
    def _emit_database_runtime(self, a: _A) -> None:
        ar = self.arch

        def ptr_arg(index: int) -> str:
            return ar.arg(index, "qword") if ar.is64 else ar.arg(index)

        # term_int(term) -> EAX value, EDX=1 on success.
        a.l("__rt_term_int")
        self._prologue(a, save=(ar.di,))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_INT}")
        a.e("    jne __rt_term_int_fail")
        a.e(f"    mov eax, dword ptr [{ar.di}+4]")
        a.e("    mov edx, 1")
        a.e("    jmp __rt_term_int_done")
        a.l("__rt_term_int_fail")
        a.e("    xor eax, eax")
        a.e("    xor edx, edx")
        a.l("__rt_term_int_done")
        self._epilogue(a, save=(ar.di,))
        a.e()

        # term_atom_id(term) -> EAX atom-id, EDX=1 on success.
        a.l("__rt_term_atom_id")
        self._prologue(a, save=(ar.di,))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_ATOM}")
        a.e("    jne __rt_term_atom_id_fail")
        a.e(f"    mov eax, dword ptr [{ar.di}+4]")
        a.e("    mov edx, 1")
        a.e("    jmp __rt_term_atom_id_done")
        a.l("__rt_term_atom_id_fail")
        a.e("    xor eax, eax")
        a.e("    xor edx, edx")
        a.l("__rt_term_atom_id_done")
        self._epilogue(a, save=(ar.di,))
        a.e()

        # term_cstr(term) -> pointer in AX, EDX=1 for atom/string.
        a.l("__rt_term_cstr")
        self._prologue(a, save=(ar.di,))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_ATOM}")
        a.e("    je __rt_term_cstr_have_id")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRING}")
        a.e("    jne __rt_term_cstr_fail")
        a.l("__rt_term_cstr_have_id")
        a.e(f"    push dword ptr [{ar.di}+4]")
        a.e("    call __rt_atom_ptr")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    test {ar.ax}, {ar.ax}")
        a.e("    je __rt_term_cstr_fail")
        a.e("    mov edx, 1")
        a.e("    jmp __rt_term_cstr_done")
        a.l("__rt_term_cstr_fail")
        a.e(f"    xor {ar.ax}, {ar.ax}")
        a.e("    xor edx, edx")
        a.l("__rt_term_cstr_done")
        self._epilogue(a, save=(ar.di,))
        a.e()

        # cstr_copy_limit(src,dst,max_bytes) -> 1 if fully copied, 0 if truncated.
        a.l("__rt_cstr_copy_limit")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        if ar.is64:
            a.e(f"    mov rsi, {ptr_arg(0)}")
            a.e(f"    mov rdi, {ptr_arg(1)}")
        else:
            a.e(f"    mov esi, {ptr_arg(0)}")
            a.e(f"    mov edi, {ptr_arg(1)}")
        a.e(f"    mov ebx, {ar.arg(2)}")
        a.e("    test ebx, ebx")
        a.e("    je __rt_cstr_copy_fail")
        a.e("    xor ecx, ecx")
        a.l("__rt_cstr_copy_loop")
        a.e("    mov eax, ebx")
        a.e("    dec eax")
        a.e("    cmp ecx, eax")
        a.e("    jae __rt_cstr_copy_last")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e(f"    mov byte ptr [{ar.di}+{ar.cx}], al")
        a.e("    test eax, eax")
        a.e("    je __rt_cstr_copy_ok")
        a.e("    inc ecx")
        a.e("    jmp __rt_cstr_copy_loop")
        a.l("__rt_cstr_copy_last")
        a.e("    xor eax, eax")
        a.e(f"    mov byte ptr [{ar.di}+{ar.cx}], al")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e("    test eax, eax")
        a.e("    je __rt_cstr_copy_ok")
        a.l("__rt_cstr_copy_fail")
        a.e("    xor eax, eax")
        a.e("    jmp __rt_cstr_copy_done")
        a.l("__rt_cstr_copy_ok")
        a.e("    mov eax, 1")
        a.l("__rt_cstr_copy_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Stage 58: append one zero-terminated string to the temporary
        # knowledge-value materialization buffer.  Returns EAX=new length and
        # EDX=1 on success.
        a.l("__rt_knowledge_concat_append")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        if ar.is64:
            a.e(f"    mov rsi, {ptr_arg(0)}")
        else:
            a.e(f"    mov esi, {ptr_arg(0)}")
        a.e(f"    mov ebx, {ar.arg(1)}")
        a.e(f"    cmp ebx, {KNOWLEDGE_CONCAT_SIZE-1}")
        a.e("    jae __rt_knowledge_concat_append_fail")
        self._arena_to(a, ar.di, KNOWLEDGE_CONCAT_OFF)
        a.e(f"    add {ar.di}, {ar.bx}")
        a.e("    xor ecx, ecx")
        a.l("__rt_knowledge_concat_append_loop")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e("    test eax, eax")
        a.e("    je __rt_knowledge_concat_append_ok")
        a.e(f"    cmp ebx, {KNOWLEDGE_CONCAT_SIZE-1}")
        a.e("    jae __rt_knowledge_concat_append_fail")
        a.e(f"    mov byte ptr [{ar.di}], al")
        a.e(f"    inc {ar.di}")
        a.e("    inc ebx")
        a.e("    inc ecx")
        a.e("    jmp __rt_knowledge_concat_append_loop")
        a.l("__rt_knowledge_concat_append_ok")
        a.e("    xor eax, eax")
        a.e(f"    mov byte ptr [{ar.di}], al")
        a.e("    mov eax, ebx")
        a.e("    mov edx, 1")
        a.e("    jmp __rt_knowledge_concat_append_done")
        a.l("__rt_knowledge_concat_append_fail")
        a.e("    xor eax, eax")
        a.e("    xor edx, edx")
        a.l("__rt_knowledge_concat_append_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Stage 58: find the most recently loaded dynamic named knowledge
        # value and return its string pointer.  Reverse scanning makes values
        # from the database currently being loaded win over older databases.
        a.l("__rt_db_lookup_knowledge_string")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")  # name atom id
        a.e("    mov esi, dword ptr [__prolog_dyn_count]")
        a.l("__rt_db_lookup_knowledge_string_loop")
        a.e("    test esi, esi")
        a.e("    je __rt_db_lookup_knowledge_string_fail")
        a.e("    dec esi")
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, esi")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    cmp dword ptr [{ar.di}], 0")
        a.e("    je __rt_db_lookup_knowledge_string_loop")
        a.e(f"    cmp dword ptr [{ar.di}+4], {self.atom_id('d64_knowledge_value')}")
        a.e("    jne __rt_db_lookup_knowledge_string_loop")
        a.e(f"    cmp dword ptr [{ar.di}+8], 2")
        a.e("    jne __rt_db_lookup_knowledge_string_loop")
        a.e(f"    mov eax, dword ptr [{ar.di}+12]")
        a.e("    call __rt_dyn_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e("    jne __rt_db_lookup_knowledge_string_loop")
        a.e(f"    mov eax, dword ptr [{ar.di}+12]")
        a.e("    call __rt_dyn_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_LINK}")
        a.e("    jne __rt_db_lookup_knowledge_string_loop")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e(f"    mov edx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    mov eax, ecx")
        a.e("    call __rt_dyn_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_ATOM}")
        a.e("    jne __rt_db_lookup_knowledge_string_pop_next")
        a.e(f"    cmp dword ptr [{ar.di}+4], ebx")
        a.e("    jne __rt_db_lookup_knowledge_string_pop_next")
        a.e(f"    pop {ar.ax}")
        a.e("    call __rt_dyn_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_LINK}")
        a.e("    jne __rt_db_lookup_knowledge_string_loop")
        a.e(f"    mov eax, dword ptr [{ar.di}+8]")
        a.e("    call __rt_dyn_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRING}")
        a.e("    jne __rt_db_lookup_knowledge_string_loop")
        a.e(f"    push dword ptr [{ar.di}+4]")
        a.e("    call __rt_atom_ptr")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    test {ar.ax}, {ar.ax}")
        a.e("    je __rt_db_lookup_knowledge_string_loop")
        a.e("    mov edx, 1")
        a.e("    jmp __rt_db_lookup_knowledge_string_done")
        a.l("__rt_db_lookup_knowledge_string_pop_next")
        a.e(f"    pop {ar.ax}")
        a.e("    jmp __rt_db_lookup_knowledge_string_loop")
        a.l("__rt_db_lookup_knowledge_string_fail")
        a.e(f"    xor {ar.ax}, {ar.ax}")
        a.e("    xor edx, edx")
        a.l("__rt_db_lookup_knowledge_string_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # db_filename_ptr(slot) -> pointer in AX.
        a.l("__rt_db_filename_ptr")
        self._prologue(a, save=(ar.bx, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e("    mov eax, ebx")
        a.e("    shl eax, 8")          # slot * 256
        a.e("    mov ecx, ebx")
        a.e("    shl ecx, 2")          # slot * 4
        a.e("    add eax, ecx")        # slot * 260
        self._arena_to(a, ar.di, DB_FILENAMES_OFF)
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    mov {ar.ax}, {ar.di}")
        self._epilogue(a, save=(ar.bx, ar.di))
        a.e()

        # Find a live database slot by stable Database-ID.
        a.l("__rt_db_find_slot")
        self._prologue(a, save=(ar.bx, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e("    xor ecx, ecx")
        a.l("__rt_db_find_slot_loop")
        a.e(f"    cmp ecx, {DATABASE_MAX}")
        a.e("    jae __rt_db_find_slot_fail")
        self._arena_to(a, ar.di, DB_ACTIVE_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.cx}*4], 0")
        a.e("    je __rt_db_find_slot_next")
        self._arena_to(a, ar.di, DB_IDS_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.cx}*4], ebx")
        a.e("    je __rt_db_find_slot_found")
        a.l("__rt_db_find_slot_next")
        a.e("    inc ecx")
        a.e("    jmp __rt_db_find_slot_loop")
        a.l("__rt_db_find_slot_found")
        a.e("    mov eax, ecx")
        a.e("    jmp __rt_db_find_slot_done")
        a.l("__rt_db_find_slot_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_db_find_slot_done")
        self._epilogue(a, save=(ar.bx, ar.di))
        a.e()

        a.l("__rt_db_find_free_slot")
        self._prologue(a, save=(ar.di,))
        a.e("    xor ecx, ecx")
        a.l("__rt_db_find_free_loop")
        a.e(f"    cmp ecx, {DATABASE_MAX}")
        a.e("    jae __rt_db_find_free_fail")
        self._arena_to(a, ar.di, DB_ACTIVE_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.cx}*4], 0")
        a.e("    je __rt_db_find_free_found")
        a.e("    inc ecx")
        a.e("    jmp __rt_db_find_free_loop")
        a.l("__rt_db_find_free_found")
        a.e("    mov eax, ecx")
        a.e("    jmp __rt_db_find_free_done")
        a.l("__rt_db_find_free_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_db_find_free_done")
        self._epilogue(a, save=(ar.di,))
        a.e()

        # Is the database writable and not SYSTEM?
        a.l("__rt_db_can_modify_id")
        self._prologue(a, save=(ar.bx, ar.di))
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_db_can_modify_no")
        a.e("    mov ebx, eax")
        self._arena_to(a, ar.di, DB_MODES_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.bx}*4], {DATABASE_MODE_READ_WRITE}")
        a.e("    jne __rt_db_can_modify_no")
        self._arena_to(a, ar.di, DB_KINDS_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.bx}*4], {DATABASE_KIND_SYSTEM}")
        a.e("    je __rt_db_can_modify_no")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_db_can_modify_done")
        a.l("__rt_db_can_modify_no")
        a.e("    xor eax, eax")
        a.l("__rt_db_can_modify_done")
        self._epilogue(a, save=(ar.bx, ar.di))
        a.e()

        a.l("__rt_db_mark_modified_id")
        self._prologue(a, save=(ar.bx, ar.di))
        a.e("    cmp dword ptr [__prolog_db_loading], 0")
        a.e("    jne __rt_db_mark_modified_done")
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_db_mark_modified_done")
        a.e("    mov ebx, eax")
        self._arena_to(a, ar.di, DB_MODIFIED_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.bx}*4], 1")
        a.l("__rt_db_mark_modified_done")
        a.e("    mov eax, 1")
        self._epilogue(a, save=(ar.bx, ar.di))
        a.e()

        # Convert read_only/read_write and knowledge/record/system atoms.
        a.l("__rt_db_mode_from_term")
        self._prologue(a)
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_term_atom_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_db_mode_fail")
        a.e(f"    cmp eax, {self.atom_id('read_only')}")
        a.e("    je __rt_db_mode_ro")
        a.e(f"    cmp eax, {self.atom_id('read_write')}")
        a.e("    je __rt_db_mode_rw")
        a.e("    jmp __rt_db_mode_fail")
        a.l("__rt_db_mode_ro")
        a.e(f"    mov eax, {DATABASE_MODE_READ_ONLY}")
        a.e("    jmp __rt_db_mode_done")
        a.l("__rt_db_mode_rw")
        a.e(f"    mov eax, {DATABASE_MODE_READ_WRITE}")
        a.e("    jmp __rt_db_mode_done")
        a.l("__rt_db_mode_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_db_mode_done")
        self._epilogue(a)
        a.e()

        a.l("__rt_db_kind_from_term")
        self._prologue(a)
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_term_atom_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_db_kind_fail")
        for name, value, label in (
            ("knowledge", DATABASE_KIND_KNOWLEDGE, "knowledge"),
            ("record", DATABASE_KIND_RECORD, "record"),
            ("system", DATABASE_KIND_SYSTEM, "system"),
        ):
            a.e(f"    cmp eax, {self.atom_id(name)}")
            a.e(f"    je __rt_db_kind_{label}")
        a.e("    jmp __rt_db_kind_fail")
        for _name, value, label in (
            ("knowledge", DATABASE_KIND_KNOWLEDGE, "knowledge"),
            ("record", DATABASE_KIND_RECORD, "record"),
            ("system", DATABASE_KIND_SYSTEM, "system"),
        ):
            a.l(f"__rt_db_kind_{label}")
            a.e(f"    mov eax, {value}")
            a.e("    jmp __rt_db_kind_done")
        a.l("__rt_db_kind_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_db_kind_done")
        self._epilogue(a)
        a.e()

        # Make <filename>.tmp in a fixed private buffer.
        a.l("__rt_db_make_temp_path")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_db_filename_ptr")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    mov {ar.si}, {ar.ax}")
        self._arena_to(a, ar.di, DB_TEMP_PATH_OFF)
        a.e("    xor ebx, ebx")
        a.l("__rt_db_temp_copy")
        a.e(f"    cmp ebx, {DATABASE_FILENAME_SIZE-5}")
        a.e("    jae __rt_db_temp_fail")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.bx}]")
        a.e("    test eax, eax")
        a.e("    je __rt_db_temp_suffix")
        a.e(f"    mov byte ptr [{ar.di}+{ar.bx}], al")
        a.e("    inc ebx")
        a.e("    jmp __rt_db_temp_copy")
        a.l("__rt_db_temp_suffix")
        for byte in (46, 116, 109, 112, 0):  # .tmp\0
            a.e(f"    mov byte ptr [{ar.di}+{ar.bx}], {byte}")
            if byte:
                a.e("    inc ebx")
        a.e(f"    mov {ar.ax}, {ar.di}")
        a.e("    jmp __rt_db_temp_done")
        a.l("__rt_db_temp_fail")
        a.e(f"    xor {ar.ax}, {ar.ax}")
        a.l("__rt_db_temp_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Canonical variables are emitted as _V0, _V1, ... while saving.
        a.l("__rt_emit_saved_var")
        self._prologue(a, save=(ar.bx, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e("    xor ecx, ecx")
        a.l("__rt_emit_saved_var_scan")
        a.e("    cmp ecx, dword ptr [__prolog_save_var_count]")
        a.e("    jae __rt_emit_saved_var_new")
        self._arena_to(a, ar.di, DB_SAVE_VAR_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.cx}*4], ebx")
        a.e("    je __rt_emit_saved_var_have")
        a.e("    inc ecx")
        a.e("    jmp __rt_emit_saved_var_scan")
        a.l("__rt_emit_saved_var_new")
        a.e(f"    cmp ecx, {BUILD_VAR_MAX}")
        a.e("    jae __rt_emit_saved_var_have")
        self._arena_to(a, ar.di, DB_SAVE_VAR_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], ebx")
        a.e("    inc dword ptr [__prolog_save_var_count]")
        a.l("__rt_emit_saved_var_have")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    push __prolog_fmt_saved_var")
        a.e("    push __prolog_format_buffer")
        a.e("    call wsprintfA")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    push __prolog_format_buffer")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov eax, 1")
        self._epilogue(a, save=(ar.bx, ar.di))
        a.e()

        # Source renderer for operator expressions used in rule bodies.
        a.l("__rt_emit_source_expr")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    mov esi, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e("    jne __rt_emit_source_expr_generic")
        a.e(f"    cmp dword ptr [{ar.di}+8], 2")
        a.e("    jne __rt_emit_source_expr_generic")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]")
        operator_labels = [
            (",", "__prolog_text_op_comma"),
            (";", "__prolog_text_op_semi"),
            ("=", "__prolog_text_op_eq"),
            ("\\=", "__prolog_text_op_ne"),
            ("==", "__prolog_text_op_strict_eq"),
            ("is", "__prolog_text_op_is"),
            ("<", "__prolog_text_op_lt"),
            ("=<", "__prolog_text_op_le"),
            (">", "__prolog_text_op_gt"),
            (">=", "__prolog_text_op_ge"),
            ("+", "__prolog_text_op_plus"),
            ("-", "__prolog_text_op_minus"),
            ("*", "__prolog_text_op_mul"),
            ("/", "__prolog_text_op_div"),
            ("mod", "__prolog_text_op_mod"),
        ]
        for i, (name, text_label) in enumerate(operator_labels):
            a.e(f"    cmp edx, {self.atom_id(name)}")
            a.e(f"    je __rt_emit_source_expr_op_{i}")
        a.e("    jmp __rt_emit_source_expr_generic")
        for i, (_name, text_label) in enumerate(operator_labels):
            a.l(f"__rt_emit_source_expr_op_{i}")
            a.e(f"    mov {ar.bx}, {text_label}")
            a.e("    jmp __rt_emit_source_expr_binary")
        a.l("__rt_emit_source_expr_binary")
        a.e("    push __prolog_text_lparen")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_emit_source_expr")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    {'push rbx' if ar.is64 else 'push ebx'}")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_emit_source_expr")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push __prolog_text_rparen")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_source_expr_done")
        a.l("__rt_emit_source_expr_generic")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_emit_term")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_emit_source_expr_done")
        a.e("    mov eax, 1")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        a.l("__rt_emit_clause_source")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    mov esi, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e("    jne __rt_emit_clause_fact")
        # Preserve the friendly Stage-56 syntax when a loaded database is
        # saved again: d64_knowledge_value(apfel,V) -> _apfel = V
        a.e(f"    cmp dword ptr [{ar.di}+4], {self.atom_id('d64_knowledge_value')}")
        a.e("    jne __rt_emit_clause_check_rule")
        a.e(f"    cmp dword ptr [{ar.di}+8], 2")
        a.e("    je __rt_emit_clause_knowledge")
        a.l("__rt_emit_clause_check_rule")
        a.e(f"    cmp dword ptr [{ar.di}+4], {self.atom_id(':-')}")
        a.e("    jne __rt_emit_clause_fact")
        a.e(f"    cmp dword ptr [{ar.di}+8], 2")
        a.e("    jne __rt_emit_clause_fact")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_emit_term")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push __prolog_text_rule_sep")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_emit_source_expr")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_clause_done")
        a.l("__rt_emit_clause_knowledge")
        a.e("    push __prolog_text_underscore")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_emit_term")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push __prolog_text_knowledge_sep")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_emit_source_expr")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_clause_done")
        a.l("__rt_emit_clause_fact")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_emit_term")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_emit_clause_done")
        a.e("    mov eax, 1")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Load and parse all clauses from one database file.
        a.l("__rt_db_load_slot")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")  # slot
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_filename_ptr")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    mov {ar.si}, {ar.ax}")
        # CreateFileA(filename, GENERIC_READ, FILE_SHARE_READ, 0, OPEN_EXISTING, NORMAL, 0)
        a.e("    push 0")
        a.e("    push 128")
        a.e("    push 3")
        a.e("    push 0")
        a.e("    push 1")
        a.e("    push -2147483648")
        a.e(f"    {'push rsi' if ar.is64 else 'push esi'}")
        a.e("    call CreateFileA")
        a.e("    cmp eax, -1")
        a.e("    jne __rt_db_load_have_file")
        # Missing read-write RECORD/KNOWLEDGE file starts empty; read-only fails.
        self._arena_to(a, ar.di, DB_MODES_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.bx}*4], {DATABASE_MODE_READ_WRITE}")
        a.e("    jne __rt_db_load_fail")
        a.e("    push 0")
        a.e("    push 128")
        a.e("    push 2")
        a.e("    push 0")
        a.e("    push 0")
        a.e("    push 1073741824")
        a.e(f"    {'push rsi' if ar.is64 else 'push esi'}")
        a.e("    call CreateFileA")
        a.e("    cmp eax, -1")
        a.e("    je __rt_db_load_fail")
        if ar.is64:
            a.e("    push rax")
        else:
            a.e("    push eax")
        a.e("    call CloseHandle")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_db_load_done")
        a.l("__rt_db_load_have_file")
        a.e(f"    mov {ar.mem_ptr('__prolog_db_file_handle')}, {ar.ax}")
        self._arena_to(a, ar.di, FILE_BUFFER_OFF)
        a.e("    mov dword ptr [__prolog_db_file_read], 0")
        a.e("    push 0")
        a.e("    push __prolog_db_file_read")
        a.e(f"    push {FILE_BUFFER_SIZE-1}")
        a.e(f"    {'push rdi' if ar.is64 else 'push edi'}")
        a.e(f"    push {ar.mem_ptr('__prolog_db_file_handle')}")
        a.e("    call ReadFile")
        a.e("    test eax, eax")
        a.e("    je __rt_db_load_close_fail")
        a.e(f"    push {ar.mem_ptr('__prolog_db_file_handle')}")
        a.e("    call CloseHandle")
        a.e(f"    mov {ar.mem_ptr('__prolog_db_file_handle')}, 0")
        a.e("    mov ecx, dword ptr [__prolog_db_file_read]")
        a.e(f"    cmp ecx, {FILE_BUFFER_SIZE-1}")
        a.e("    jae __rt_db_load_fail")
        self._arena_to(a, ar.di, FILE_BUFFER_OFF)
        a.e("    xor eax, eax")
        a.e(f"    mov byte ptr [{ar.di}+{ar.cx}], al")
        a.e("    mov dword ptr [__prolog_db_file_pos], 0")
        a.e("    mov dword ptr [__prolog_parser_db_mode], 1")
        a.l("__rt_db_load_clause_loop")
        # Copy a parse window from FILE_BUFFER+file_pos to INPUT.
        self._arena_to(a, ar.si, FILE_BUFFER_OFF)
        a.e("    mov eax, dword ptr [__prolog_db_file_pos]")
        a.e(f"    add {ar.si}, {ar.ax}")
        self._arena_to(a, ar.di, INPUT_OFF)
        a.e("    xor ecx, ecx")
        a.l("__rt_db_load_window_copy")
        a.e(f"    cmp ecx, {INPUT_SIZE-1}")
        a.e("    jae __rt_db_load_window_full")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e(f"    mov byte ptr [{ar.di}+{ar.cx}], al")
        a.e("    test eax, eax")
        a.e("    je __rt_db_load_window_ready")
        a.e("    inc ecx")
        a.e("    jmp __rt_db_load_window_copy")
        a.l("__rt_db_load_window_full")
        a.e("    xor eax, eax")
        a.e(f"    mov byte ptr [{ar.di}+{ar.cx}], al")
        a.l("__rt_db_load_window_ready")
        a.e("    mov dword ptr [__prolog_parse_pos], 0")
        a.e("    call __rt_parse_skip_ws")
        a.e("    test eax, eax")
        a.e("    je __rt_db_load_success")
        a.e("    mov eax, dword ptr [__prolog_heap_top]")
        a.e("    mov dword ptr [__prolog_db_heap_mark], eax")
        a.e("    mov dword ptr [__prolog_db_parser_var_count], 0")
        a.e("    mov dword ptr [__prolog_db_parser_name_top], 0")
        # Stage 56: external files may start a clause with _name = Term.
        # The helper resets parse_pos when this is not such an assignment.
        a.e("    call __rt_parse_knowledge_assignment")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    jne __rt_db_load_clause_parsed")
        a.e("    call __rt_parse_rule_expr")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_db_load_parse_fail")
        a.l("__rt_db_load_clause_parsed")
        a.e("    mov ebx, eax")  # clause term
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 46")  # .
        a.e("    jne __rt_db_load_parse_fail")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_skip_ws")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_assertz")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov edx, eax")
        a.e("    mov eax, dword ptr [__prolog_db_heap_mark]")
        a.e("    mov dword ptr [__prolog_heap_top], eax")
        a.e("    test edx, edx")
        a.e("    je __rt_db_load_fail")
        a.e("    mov eax, dword ptr [__prolog_parse_pos]")
        a.e("    test eax, eax")
        a.e("    je __rt_db_load_fail")
        a.e("    add dword ptr [__prolog_db_file_pos], eax")
        a.e("    jmp __rt_db_load_clause_loop")
        a.l("__rt_db_load_parse_fail")
        a.e("    mov eax, dword ptr [__prolog_db_heap_mark]")
        a.e("    mov dword ptr [__prolog_heap_top], eax")
        a.e("    jmp __rt_db_load_fail")
        a.l("__rt_db_load_close_fail")
        a.e(f"    push {ar.mem_ptr('__prolog_db_file_handle')}")
        a.e("    call CloseHandle")
        a.e(f"    mov {ar.mem_ptr('__prolog_db_file_handle')}, 0")
        a.e("    jmp __rt_db_load_fail")
        a.l("__rt_db_load_success")
        a.e("    mov dword ptr [__prolog_parser_db_mode], 0")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_db_load_done")
        a.l("__rt_db_load_fail")
        a.e("    mov dword ptr [__prolog_parser_db_mode], 0")
        a.e("    xor eax, eax")
        a.l("__rt_db_load_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Create a database record and load its clauses. Returns stable DB-ID.
        a.l("__rt_database_open")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(1)}")  # mode enum
        a.e(f"    mov esi, {ar.arg(2)}")  # kind enum
        # SYSTEM databases are deliberately immutable and therefore must be
        # opened read_only. Reject a contradictory read_write SYSTEM request.
        a.e(f"    cmp esi, {DATABASE_KIND_SYSTEM}")
        a.e("    jne __rt_database_open_mode_ok")
        a.e(f"    cmp ebx, {DATABASE_MODE_READ_ONLY}")
        a.e("    jne __rt_database_open_fail")
        a.l("__rt_database_open_mode_ok")
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_term_cstr")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_database_open_fail")
        if ar.is64:
            a.e("    push rax")  # filename ptr
        else:
            a.e("    push eax")
        a.e("    call __rt_db_find_free_slot")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_database_open_fail_pop")
        a.e("    mov ecx, eax")  # slot
        # filename
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_db_filename_ptr")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    mov {ar.di}, {ar.ax}")
        a.e(f"    pop {ar.ax}")  # filename ptr
        a.e(f"    push {DATABASE_FILENAME_SIZE}")
        if ar.is64:
            a.e("    push rdi")
            a.e("    push rax")
        else:
            a.e("    push edi")
            a.e("    push eax")
        a.e("    call __rt_cstr_copy_limit")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    test eax, eax")
        a.e("    je __rt_database_open_fail")
        # Allocate monotonically increasing ID, never 0.
        a.e("    mov eax, dword ptr [__prolog_db_next_id]")
        a.e("    test eax, eax")
        a.e("    jne __rt_database_open_id_ok")
        a.e("    mov eax, 1")
        a.l("__rt_database_open_id_ok")
        a.e("    mov edx, eax")
        a.e("    inc eax")
        a.e("    mov dword ptr [__prolog_db_next_id], eax")
        # We lost slot in ECX across cstr call? cstr preserves caller ECX? no.
        # Recover free slot by scanning again; still free until active is set.
        a.e("    call __rt_db_find_free_slot")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_database_open_fail")
        a.e("    mov ecx, eax")
        self._arena_to(a, ar.di, DB_ACTIVE_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], 1")
        self._arena_to(a, ar.di, DB_IDS_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], edx")
        self._arena_to(a, ar.di, DB_MODES_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], ebx")
        self._arena_to(a, ar.di, DB_KINDS_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], esi")
        self._arena_to(a, ar.di, DB_MODIFIED_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], 0")
        # Save caller's selected DB and import clauses under the new owner ID.
        a.e(f"    {ar.push_reg32('edx')}")  # keep new stable DB-ID across file parser
        a.e("    mov eax, dword ptr [__prolog_current_db]")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    mov dword ptr [__prolog_current_db], edx")
        a.e("    mov dword ptr [__prolog_db_loading], 1")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_db_load_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov esi, eax")  # load result
        a.e("    mov dword ptr [__prolog_db_loading], 0")
        a.e(f"    pop {ar.cx}")  # previous current DB
        a.e(f"    pop {ar.dx}")  # new DB-ID
        a.e("    mov dword ptr [__prolog_current_db], ecx")
        a.e("    test esi, esi")
        a.e("    je __rt_database_open_cleanup")
        # Find slot again from ID and clear dirty flag after import.
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_database_open_fail")
        a.e("    mov ecx, eax")
        self._arena_to(a, ar.di, DB_MODIFIED_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], 0")
        a.e("    mov eax, edx")
        a.e("    jmp __rt_database_open_done")
        a.l("__rt_database_open_cleanup")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_db_unload_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    xor eax, eax")
        a.e("    jmp __rt_database_open_done")
        a.l("__rt_database_open_fail_pop")
        if ar.is64:
            a.e("    pop rax")
        else:
            a.e("    pop eax")
        a.l("__rt_database_open_fail")
        a.e("    xor eax, eax")
        a.l("__rt_database_open_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Remove every dynamic clause owned by one database, then compact/GC.
        a.l("__rt_db_unload_id")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e("    xor esi, esi")
        a.l("__rt_db_unload_clause_loop")
        a.e("    cmp esi, dword ptr [__prolog_dyn_count]")
        a.e("    jae __rt_db_unload_clause_done")
        self._arena_to(a, ar.di, DYN_DB_OWNER_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.si}*4], ebx")
        a.e("    jne __rt_db_unload_clause_next")
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, esi")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    mov dword ptr [{ar.di}], 0")
        a.l("__rt_db_unload_clause_next")
        a.e("    inc esi")
        a.e("    jmp __rt_db_unload_clause_loop")
        a.l("__rt_db_unload_clause_done")
        a.e("    call __rt_dyn_db_compact")
        a.e("    call __rt_gc_dynamic")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_db_unload_after_slot")
        a.e("    mov ecx, eax")
        for array_off in (DB_ACTIVE_OFF, DB_IDS_OFF, DB_MODES_OFF, DB_KINDS_OFF, DB_MODIFIED_OFF):
            self._arena_to(a, ar.di, array_off)
            a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], 0")
        a.l("__rt_db_unload_after_slot")
        a.e("    cmp dword ptr [__prolog_current_db], ebx")
        a.e("    jne __rt_db_unload_current_ok")
        a.e("    mov dword ptr [__prolog_current_db], 0")
        a.l("__rt_db_unload_current_ok")
        a.e("    mov eax, 1")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Save exactly the clauses owned by DB-ID through the normal term
        # renderer redirected to a temporary file.
        a.l("__rt_database_save_id")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_can_modify_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    je __rt_database_save_fail")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_database_save_fail")
        a.e("    mov esi, eax")  # slot
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_db_make_temp_path")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    test {ar.ax}, {ar.ax}")
        a.e("    je __rt_database_save_fail")
        a.e(f"    mov {ar.di}, {ar.ax}")  # temp ptr
        # Create temp file.
        a.e("    push 0")
        a.e("    push 128")
        a.e("    push 2")
        a.e("    push 0")
        a.e("    push 0")
        a.e("    push 1073741824")
        a.e(f"    {'push rdi' if ar.is64 else 'push edi'}")
        a.e("    call CreateFileA")
        a.e("    cmp eax, -1")
        a.e("    je __rt_database_save_fail")
        a.e(f"    mov {ar.mem_ptr('__prolog_emit_file_handle')}, {ar.ax}")
        a.e("    mov dword ptr [__prolog_emit_to_file], 1")
        a.e("    mov dword ptr [__prolog_emit_file_error], 0")
        a.e("    mov eax, dword ptr [__prolog_heap_top]")
        a.e("    mov dword ptr [__prolog_db_heap_mark], eax")
        a.e("    xor esi, esi")  # clause index
        a.l("__rt_database_save_loop")
        a.e("    cmp esi, dword ptr [__prolog_dyn_count]")
        a.e("    jae __rt_database_save_written")
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, esi")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    cmp dword ptr [{ar.di}], 0")
        a.e("    je __rt_database_save_next")
        self._arena_to(a, ar.di, DYN_DB_OWNER_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.si}*4], ebx")
        a.e("    jne __rt_database_save_next")
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, esi")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    mov eax, dword ptr [{ar.di}+12]")
        a.e("    mov dword ptr [__prolog_dyn_clone_var_count], 0")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_dyn_clone")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_database_save_io_fail")
        a.e("    mov dword ptr [__prolog_save_var_count], 0")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_emit_clause_source")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push __prolog_text_clause_end")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov eax, dword ptr [__prolog_db_heap_mark]")
        a.e("    mov dword ptr [__prolog_heap_top], eax")
        a.e("    cmp dword ptr [__prolog_emit_file_error], 0")
        a.e("    jne __rt_database_save_io_fail")
        a.l("__rt_database_save_next")
        a.e("    inc esi")
        a.e("    jmp __rt_database_save_loop")
        a.l("__rt_database_save_written")
        a.e(f"    push {ar.mem_ptr('__prolog_emit_file_handle')}")
        a.e("    call FlushFileBuffers")
        a.e("    test eax, eax")
        a.e("    je __rt_database_save_io_fail")
        a.e(f"    push {ar.mem_ptr('__prolog_emit_file_handle')}")
        a.e("    call CloseHandle")
        a.e(f"    mov {ar.mem_ptr('__prolog_emit_file_handle')}, 0")
        a.e("    mov dword ptr [__prolog_emit_to_file], 0")
        # MoveFileExA(temp, original, REPLACE_EXISTING|WRITE_THROUGH)
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_database_save_fail")
        a.e("    mov esi, eax")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_db_filename_ptr")
        a.e(f"    {ar.cleanup(1)}")
        if ar.is64:
            a.e("    push rax")  # original
        else:
            a.e("    push eax")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_db_make_temp_path")
        a.e(f"    {ar.cleanup(1)}")
        if ar.is64:
            a.e("    pop rdx")   # original
            a.e("    push 9")
            a.e("    push rdx")
            a.e("    push rax")  # temp
        else:
            a.e("    pop edx")
            a.e("    push 9")
            a.e("    push edx")
            a.e("    push eax")
        a.e("    call MoveFileExA")
        a.e("    test eax, eax")
        a.e("    je __rt_database_save_move_fail")
        self._arena_to(a, ar.di, DB_MODIFIED_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.si}*4], 0")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_database_save_done")
        a.l("__rt_database_save_io_fail")
        a.e("    mov eax, dword ptr [__prolog_db_heap_mark]")
        a.e("    mov dword ptr [__prolog_heap_top], eax")
        a.e("    mov dword ptr [__prolog_emit_to_file], 0")
        a.e(f"    cmp {ar.mem_ptr('__prolog_emit_file_handle')}, 0")
        a.e("    je __rt_database_save_delete_temp")
        a.e(f"    push {ar.mem_ptr('__prolog_emit_file_handle')}")
        a.e("    call CloseHandle")
        a.e(f"    mov {ar.mem_ptr('__prolog_emit_file_handle')}, 0")
        a.l("__rt_database_save_delete_temp")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_database_save_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_db_make_temp_path")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    test {ar.ax}, {ar.ax}")
        a.e("    je __rt_database_save_fail")
        if ar.is64:
            a.e("    push rax")
        else:
            a.e("    push eax")
        a.e("    call DeleteFileA")
        a.e("    jmp __rt_database_save_fail")
        a.l("__rt_database_save_move_fail")
        # Best-effort cleanup of the temp file.
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_db_make_temp_path")
        a.e(f"    {ar.cleanup(1)}")
        if ar.is64:
            a.e("    push rax")
        else:
            a.e("    push eax")
        a.e("    call DeleteFileA")
        a.l("__rt_database_save_fail")
        a.e("    xor eax, eax")
        a.l("__rt_database_save_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        a.l("__rt_database_close_id")
        self._prologue(a, save=(ar.bx, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_database_close_fail")
        a.e("    mov ecx, eax")
        self._arena_to(a, ar.di, DB_KINDS_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.cx}*4], {DATABASE_KIND_SYSTEM}")
        a.e("    je __rt_database_close_fail")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_unload_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_database_close_done")
        a.l("__rt_database_close_fail")
        a.e("    xor eax, eax")
        a.l("__rt_database_close_done")
        self._epilogue(a, save=(ar.bx, ar.di))
        a.e()

        # Save under a new file name.  On failure restore the old path.
        a.l("__rt_database_save_as")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")  # DB-ID
        a.e(f"    push {ar.arg(1)}")
        a.e("    call __rt_term_cstr")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_database_save_as_fail")
        a.e(f"    mov {ar.si}, {ar.ax}")  # new path
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_database_save_as_fail")
        a.e("    mov ecx, eax")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_db_filename_ptr")
        a.e(f"    {ar.cleanup(1)}")
        # old -> backup
        a.e(f"    push {DATABASE_FILENAME_SIZE}")
        self._arena_to(a, ar.di, DB_OLD_PATH_OFF)
        if ar.is64:
            a.e("    push rdi")
            a.e("    push rax")
        else:
            a.e("    push edi")
            a.e("    push eax")
        a.e("    call __rt_cstr_copy_limit")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    test eax, eax")
        a.e("    je __rt_database_save_as_fail")
        # __rt_cstr_copy_limit uses ECX as its copy counter. Recover the slot
        # from the stable Database-ID before addressing the filename again.
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_database_save_as_fail")
        a.e("    mov ecx, eax")
        # new -> slot
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_db_filename_ptr")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    mov {ar.di}, {ar.ax}")
        a.e(f"    push {DATABASE_FILENAME_SIZE}")
        if ar.is64:
            a.e("    push rdi")
            a.e("    push rsi")
        else:
            a.e("    push edi")
            a.e("    push esi")
        a.e("    call __rt_cstr_copy_limit")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    test eax, eax")
        a.e("    je __rt_database_save_as_restore")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_database_save_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    je __rt_database_save_as_restore")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_database_save_as_done")
        a.l("__rt_database_save_as_restore")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_database_save_as_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_db_filename_ptr")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    mov {ar.di}, {ar.ax}")
        a.e(f"    push {DATABASE_FILENAME_SIZE}")
        if ar.is64:
            a.e("    push rdi")
        else:
            a.e("    push edi")
        self._arena_to(a, ar.si, DB_OLD_PATH_OFF)
        if ar.is64:
            a.e("    push rsi")
        else:
            a.e("    push esi")
        a.e("    call __rt_cstr_copy_limit")
        a.e(f"    {ar.cleanup(3)}")
        a.l("__rt_database_save_as_fail")
        a.e("    xor eax, eax")
        a.l("__rt_database_save_as_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # Explicit database_assert* keeps the selected database unchanged.
        a.l("__rt_database_assert_scoped")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e(f"    mov ebx, {ar.arg(0)}")  # DB-ID
        a.e(f"    mov esi, {ar.arg(1)}")  # clause
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_can_modify_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    je __rt_database_assert_scoped_fail")
        a.e("    mov eax, dword ptr [__prolog_current_db]")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    mov dword ptr [__prolog_current_db], ebx")
        a.e(f"    cmp {ar.arg(2)}, 0")
        a.e("    jne __rt_database_assert_scoped_front")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_assertz")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_database_assert_scoped_restore")
        a.l("__rt_database_assert_scoped_front")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_asserta")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_database_assert_scoped_restore")
        a.e("    mov edx, eax")
        a.e(f"    pop {ar.ax}")
        a.e("    mov dword ptr [__prolog_current_db], eax")
        a.e("    mov eax, edx")
        a.e("    jmp __rt_database_assert_scoped_done")
        a.l("__rt_database_assert_scoped_fail")
        a.e("    xor eax, eax")
        a.l("__rt_database_assert_scoped_done")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        a.l("__rt_database_retract_scoped")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    mov esi, {ar.arg(1)}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_db_can_modify_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    je __rt_database_retract_scoped_fail")
        a.e("    mov eax, dword ptr [__prolog_current_db]")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    mov dword ptr [__prolog_current_db], ebx")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_retract")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov edx, eax")
        a.e(f"    pop {ar.ax}")
        a.e("    mov dword ptr [__prolog_current_db], eax")
        a.e("    mov eax, edx")
        a.e("    jmp __rt_database_retract_scoped_done")
        a.l("__rt_database_retract_scoped_fail")
        a.e("    xor eax, eax")
        a.l("__rt_database_retract_scoped_done")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

    # ------------------------------------------------------------------
    # Output / term rendering / atom lookup
    # ------------------------------------------------------------------
    def _emit_io(self, a: _A) -> None:
        ar = self.arch
        # strlen(ptr) -> eax length
        a.l("__rt_strlen")
        self._prologue(a, save=(ar.si,))
        if ar.is64:
            a.e(f"    mov rsi, {ar.arg(0, 'qword')}")
        else:
            a.e(f"    mov esi, {ar.arg(0)}")
        a.e("    xor eax, eax")
        a.l("__rt_strlen_loop")
        a.e(f"    movzx ecx, byte ptr [{ar.si}+{ar.ax}]")
        a.e("    test ecx, ecx")
        a.e("    je __rt_strlen_done")
        a.e("    inc eax")
        a.e("    jmp __rt_strlen_loop")
        a.l("__rt_strlen_done")
        self._epilogue(a, save=(ar.si,))
        a.e()

        # emit_text(cstr). Console writes immediately; GUI appends to buffer.
        # database_save/1 can temporarily redirect the same renderer to a file.
        a.l("__rt_emit_text")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        if ar.is64:
            a.e(f"    mov rsi, {ar.arg(0, 'qword')}")
        else:
            a.e(f"    mov esi, {ar.arg(0)}")

        a.e("    cmp dword ptr [__prolog_emit_to_file], 0")
        a.e("    je __rt_emit_text_normal")
        a.e(f"    {'push rsi' if ar.is64 else 'push esi'}")
        a.e("    call __rt_strlen")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov ebx, eax")
        a.e("    push 0")
        a.e("    push __prolog_written")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {'push rsi' if ar.is64 else 'push esi'}")
        a.e(f"    push {ar.mem_ptr('__prolog_emit_file_handle')}")
        a.e("    call WriteFile")
        a.e("    test eax, eax")
        a.e("    jne __rt_emit_text_done")
        a.e("    mov dword ptr [__prolog_emit_file_error], 1")
        a.e("    jmp __rt_emit_text_done")

        a.l("__rt_emit_text_normal")
        if self.is_gui:
            a.e("    mov ebx, dword ptr [__prolog_output_top]")
            self._arena_to(a, ar.di, OUTPUT_OFF)
            a.l("__rt_emit_text_gui_loop")
            a.e(f"    movzx eax, byte ptr [{ar.si}]")
            a.e("    test eax, eax")
            a.e("    je __rt_emit_text_gui_done")
            a.e(f"    cmp ebx, {OUTPUT_SIZE-1}")
            a.e("    jae __rt_emit_text_gui_done")
            a.e(f"    mov byte ptr [{ar.di}+{ar.bx}], al")
            a.e(f"    inc {ar.si}")
            a.e("    inc ebx")
            a.e("    jmp __rt_emit_text_gui_loop")
            a.l("__rt_emit_text_gui_done")
            a.e("    mov dword ptr [__prolog_output_top], ebx")
            a.e("    xor eax, eax")
            a.e(f"    mov byte ptr [{ar.di}+{ar.bx}], al")
        else:
            a.e(f"    {'push rsi' if ar.is64 else 'push esi'}")
            a.e("    call __rt_strlen")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    mov ebx, eax")
            a.e("    push 0")
            a.e("    push __prolog_written")
            a.e(f"    {ar.push_reg32('ebx')}")
            a.e(f"    {'push rsi' if ar.is64 else 'push esi'}")
            a.e(f"    push {ar.mem_ptr('__prolog_stdout')}")
            a.e("    call WriteFile")
        a.l("__rt_emit_text_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # atom_ptr(atom_id) -> pointer in AX
        a.l("__rt_atom_ptr")
        self._prologue(a, save=(ar.bx, ar.di))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    cmp ebx, {len(self.atom_ids)}")
        a.e("    ja __rt_atom_ptr_dynamic")
        a.e("    test ebx, ebx")
        a.e("    je __rt_atom_ptr_fail")
        a.e("    dec ebx")
        if ar.is64:
            a.e("    mov rdi, __prolog_static_atom_table")
            a.e("    mov rax, qword ptr [rdi+rbx*8]")
        else:
            a.e("    mov edi, __prolog_static_atom_table")
            a.e("    mov eax, dword ptr [edi+ebx*4]")
        a.e("    jmp __rt_atom_ptr_done")
        a.l("__rt_atom_ptr_dynamic")
        a.e(f"    sub ebx, {len(self.atom_ids)+1}")
        a.e("    cmp ebx, dword ptr [__prolog_dyn_atom_count]")
        a.e("    jae __rt_atom_ptr_fail")
        self._arena_to(a, ar.di, DYN_ATOM_TABLE_OFF)
        if ar.is64:
            a.e("    mov rax, qword ptr [rdi+rbx*8]")
        else:
            a.e("    mov eax, dword ptr [edi+ebx*4]")
        a.e("    jmp __rt_atom_ptr_done")
        a.l("__rt_atom_ptr_fail")
        a.e("    xor eax, eax")
        a.l("__rt_atom_ptr_done")
        self._epilogue(a, save=(ar.bx, ar.di))
        a.e()

        # emit atom/string by id
        a.l("__rt_emit_atom_id")
        self._prologue(a)
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_atom_ptr")
        a.e(f"    {ar.cleanup(1)}")
        if ar.is64:
            a.e("    push rax")
        else:
            a.e("    push eax")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        self._epilogue(a)
        a.e()

        # integer print via wsprintfA
        a.l("__rt_emit_int")
        self._prologue(a)
        a.e(f"    push {ar.arg(0)}")
        a.e("    push __prolog_fmt_int")
        a.e("    push __prolog_format_buffer")
        a.e("    call wsprintfA")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    push __prolog_format_buffer")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        self._epilogue(a)
        a.e()

        # float print through msvcrt _gcvt(double, digits, buffer).  It keeps
        # enough significant digits for useful PROLOG arithmetic while
        # trimming insignificant trailing zeroes.
        a.l("__rt_emit_float")
        self._prologue(a, save=(ar.di,))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    call __rt_node_ptr")
        if ar.is64:
            a.e(f"    movsd xmm0, qword ptr [{ar.di}+4]")
            a.e("    mov edx, 15")
            a.e("    mov r8, __prolog_format_buffer")
            # Current prologue saves one register, leaving RSP 8 mod 16.
            # Reserve 40 bytes = 32-byte shadow space + 8-byte alignment.
            a.e("    sub rsp, 40")
            a.e("    call __prolog_gcvt")
            a.e("    add rsp, 40")
            a.e("    push rax")
        else:
            a.e("    push __prolog_format_buffer")
            a.e("    push 15")
            a.e(f"    push dword ptr [{ar.di}+8]")
            a.e(f"    push dword ptr [{ar.di}+4]")
            a.e("    call __prolog_gcvt")
            a.e("    add esp, 16")
            a.e("    push eax")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        self._epilogue(a, save=(ar.di,))
        a.e()

        # recursive term printer
        self._emit_term_printer(a)
        self._emit_solution_printer(a)

    def _emit_term_printer(self, a: _A) -> None:
        ar = self.arch
        a.l("__rt_emit_term")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov eax, {ar.arg(0)}")
        a.e("    call __rt_deref")
        a.e("    mov ebx, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov esi, dword ptr [{ar.di}]")
        a.e(f"    cmp esi, {NODE_VAR}")
        a.e("    je __rt_emit_term_var")
        a.e(f"    cmp esi, {NODE_ATOM}")
        a.e("    je __rt_emit_term_atom")
        a.e(f"    cmp esi, {NODE_STRING}")
        a.e("    je __rt_emit_term_string")
        a.e(f"    cmp esi, {NODE_INT}")
        a.e("    je __rt_emit_term_int")
        a.e(f"    cmp esi, {NODE_FLOAT}")
        a.e("    je __rt_emit_term_float")
        a.e(f"    cmp esi, {NODE_NIL}")
        a.e("    je __rt_emit_term_nil")
        a.e(f"    cmp esi, {NODE_LIST}")
        a.e("    je __rt_emit_term_list")
        a.e(f"    cmp esi, {NODE_STRUCT}")
        a.e("    je __rt_emit_term_struct")
        a.e("    jmp __rt_emit_term_done")
        a.l("__rt_emit_term_var")
        a.e("    cmp dword ptr [__prolog_emit_to_file], 0")
        a.e("    je __rt_emit_term_var_plain")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_emit_saved_var")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_term_done")
        a.l("__rt_emit_term_var_plain")
        a.e("    push __prolog_text_underscore")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_term_done")
        a.l("__rt_emit_term_atom")
        a.e(f"    push dword ptr [{ar.di}+4]")
        a.e("    call __rt_emit_atom_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_term_done")
        a.l("__rt_emit_term_string")
        a.e("    push __prolog_text_quote")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    push dword ptr [{ar.di}+4]")
        a.e("    call __rt_emit_atom_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push __prolog_text_quote")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_term_done")
        a.l("__rt_emit_term_int")
        a.e(f"    push dword ptr [{ar.di}+4]")
        a.e("    call __rt_emit_int")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_term_done")
        a.l("__rt_emit_term_float")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_emit_float")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_term_done")
        a.l("__rt_emit_term_nil")
        a.e("    push __prolog_text_nil")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_term_done")
        a.l("__rt_emit_term_list")
        a.e("    push __prolog_text_lbrack")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov esi, ebx")
        a.e("    xor ebx, ebx") # first flag 0
        a.l("__rt_emit_term_list_loop")
        a.e("    mov eax, esi")
        a.e("    call __rt_deref")
        a.e("    mov esi, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_NIL}")
        a.e("    je __rt_emit_term_list_close")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_LIST}")
        a.e("    jne __rt_emit_term_list_tail")
        a.e("    test ebx, ebx")
        a.e("    je __rt_emit_term_list_no_comma")
        a.e("    push __prolog_text_comma_space")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_emit_term_list_no_comma")
        a.e(f"    mov eax, dword ptr [{ar.di}+8]")
        a.e(f"    mov esi, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_emit_term")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    pop {ar.si}")
        a.e("    mov ebx, 1")
        a.e("    jmp __rt_emit_term_list_loop")
        a.l("__rt_emit_term_list_tail")
        a.e("    push __prolog_text_bar")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_emit_term")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_emit_term_list_close")
        a.e("    push __prolog_text_rbrack")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_term_done")
        a.l("__rt_emit_term_struct")
        a.e(f"    mov esi, dword ptr [{ar.di}+4]") # functor
        a.e(f"    mov ebx, dword ptr [{ar.di}+8]") # arity
        a.e(f"    mov ecx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_emit_atom_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push __prolog_text_lparen")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    pop {ar.cx}")
        a.e("    xor esi, esi") # index
        a.l("__rt_emit_term_struct_loop")
        a.e("    cmp esi, ebx")
        a.e("    jae __rt_emit_term_struct_close")
        a.e("    test esi, esi")
        a.e("    je __rt_emit_term_struct_no_comma")
        # ECX is the next argument-link handle. __rt_emit_text/strlen is
        # caller-clobbering and uses ECX internally, so keep the link alive
        # across the separator write.  Without this, database_save/1 crashes
        # while serializing the second argument of a structure.
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    push __prolog_text_comma_space")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    pop {ar.cx}")
        a.l("__rt_emit_term_struct_no_comma")
        a.e("    mov eax, ecx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov eax, dword ptr [{ar.di}+8]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+12]")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_emit_term")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    pop {ar.cx}")
        a.e("    inc esi")
        a.e("    jmp __rt_emit_term_struct_loop")
        a.l("__rt_emit_term_struct_close")
        a.e("    push __prolog_text_rparen")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_emit_term_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    def _emit_solution_printer(self, a: _A) -> None:
        ar = self.arch
        a.l("__rt_emit_solution")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        # A solution always counts, even when verbose=true suppresses the
        # implicit Top-Level representation.  This keeps failure detection
        # and backtracking semantics independent of presentation.
        a.e("    inc dword ptr [__prolog_solution_count]")
        a.e("    cmp dword ptr [__prolog_verbose], 0")
        a.e("    jne __rt_emit_solution_after_auto_output")
        a.e("    mov ebx, dword ptr [__prolog_query_var_count]")
        a.e("    test ebx, ebx")
        a.e("    jne __rt_emit_solution_vars")
        a.e("    push __prolog_text_true_line")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_emit_solution_after_auto_output")
        a.l("__rt_emit_solution_vars")
        a.e("    xor esi, esi")
        a.l("__rt_emit_solution_loop")
        a.e("    cmp esi, ebx")
        a.e("    jae __rt_emit_solution_line_done")
        a.e("    test esi, esi")
        a.e("    je __rt_emit_solution_no_sep")
        a.e("    push __prolog_text_comma_space")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_emit_solution_no_sep")
        self._arena_to(a, ar.di, QUERY_NAME_OFF)
        if ar.is64:
            a.e("    mov rax, qword ptr [rdi+rsi*8]")
            a.e("    push rax")
        else:
            a.e("    mov eax, dword ptr [edi+esi*4]")
            a.e("    push eax")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    push __prolog_text_equals")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        self._arena_to(a, ar.di, QUERY_NODE_OFF)
        a.e(f"    mov eax, dword ptr [{ar.di}+{ar.si}*4]")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_emit_term")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    inc esi")
        a.e("    jmp __rt_emit_solution_loop")
        a.l("__rt_emit_solution_line_done")
        a.e("    push __prolog_text_dot_nl")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_emit_solution_after_auto_output")
        # Interactive console top-level: keep ';' backtracking available.
        # In verbose=true mode a deterministic solution should remain fully
        # silent, so skip the continuation prompt when no choice point exists.
        if not self.is_gui:
            a.e("    cmp dword ptr [__prolog_interactive_mode], 0")
            a.e("    je __rt_emit_solution_return")
            a.e("    cmp dword ptr [__prolog_verbose], 0")
            a.e("    je __rt_emit_solution_prompt_more")
            a.e("    cmp dword ptr [__prolog_choice_top], 0")
            a.e("    je __rt_emit_solution_verbose_stop")
            a.l("__rt_emit_solution_prompt_more")
            a.e("    push __prolog_text_more_prompt")
            a.e("    call __rt_emit_text")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    call __rt_read_line")
            a.e(f"    movzx ecx, byte ptr [{ar.ax}]")
            a.e("    cmp ecx, 59")  # ';'
            a.e("    je __rt_emit_solution_more")
            a.e("    mov dword ptr [__prolog_stop_search], 1")
            a.e("    jmp __rt_emit_solution_return")
            a.l("__rt_emit_solution_verbose_stop")
            a.e("    mov dword ptr [__prolog_stop_search], 1")
            a.e("    jmp __rt_emit_solution_return")
            a.l("__rt_emit_solution_more")
            a.e("    mov dword ptr [__prolog_requested_more], 1")
            a.l("__rt_emit_solution_return")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    # ------------------------------------------------------------------
    # Solver + builtins
    # ------------------------------------------------------------------
    def _emit_solver(self, a: _A) -> None:
        ar = self.arch
        # solve_goals(chain)
        a.l("__rt_solve_goals")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e("    cmp dword ptr [__prolog_stop_search], 0")
        a.e("    jne __rt_solve_done")
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e(f"    cmp ebx, {INVALID}")
        a.e("    jne __rt_solve_have_goal")
        a.e("    call __rt_emit_solution")
        a.e("    jmp __rt_solve_done")
        a.l("__rt_solve_have_goal")
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    mov eax, dword ptr [{ar.di}+4]")
        a.e("    mov dword ptr [__prolog_current_cut_barrier], eax")
        a.e(f"    mov esi, dword ptr [{ar.di}+8]")  # term
        a.e(f"    mov ebx, dword ptr [{ar.di}+12]") # rest
        a.e("    mov eax, esi")
        a.e("    call __rt_deref")
        a.e("    mov esi, eax")
        # Determine functor/arity into EDX/ECX.
        a.e("    call __rt_node_ptr")
        a.e(f"    mov ecx, dword ptr [{ar.di}]")
        a.e(f"    cmp ecx, {NODE_ATOM}")
        a.e("    je __rt_solve_atom_goal")
        a.e(f"    cmp ecx, {NODE_STRUCT}")
        a.e("    jne __rt_solve_done")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e("    jmp __rt_solve_dispatch")
        a.l("__rt_solve_atom_goal")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]")
        a.e("    xor ecx, ecx")
        a.l("__rt_solve_dispatch")
        self._emit_builtin_dispatch(a)
        # user predicate
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_try_user")
        a.e(f"    {ar.cleanup(2)}")
        a.l("__rt_solve_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        self._emit_user_dispatch(a)
        self._emit_dynamic_user_loop(a)
        self._emit_run_query(a)

    def _builtin_cmp(self, a: _A, name: str, arity: int, label: str) -> None:
        a.e(f"    cmp edx, {self.atom_id(name)}")
        a.e(f"    jne {label}_next")
        a.e(f"    cmp ecx, {arity}")
        a.e(f"    je {label}")
        a.l(f"{label}_next")

    def _emit_builtin_dispatch(self, a: _A) -> None:
        ar = self.arch
        # Branch labels followed by shared continuation helper.
        builtins = [
            ("true",0,"__rt_bi_true"),("fail",0,"__rt_bi_fail"),("!",0,"__rt_bi_cut"),
            ("nl",0,"__rt_bi_nl"),("repl",0,"__rt_bi_repl"),("halt",0,"__rt_bi_halt"),("quit",0,"__rt_bi_halt"),
            ("gc",0,"__rt_bi_gc"),("garbage_collect",0,"__rt_bi_gc"),
            ("verbose",1,"__rt_bi_verbose"),
            ("write",1,"__rt_bi_write"),("writeln",1,"__rt_bi_writeln"),
            ("var",1,"__rt_bi_var"),("nonvar",1,"__rt_bi_nonvar"),("atom",1,"__rt_bi_atom"),
            ("integer",1,"__rt_bi_integer"),("float",1,"__rt_bi_float"),("number",1,"__rt_bi_number"),("string",1,"__rt_bi_string"),
            ("assert",1,"__rt_bi_assertz"),("asserta",1,"__rt_bi_asserta"),("assertz",1,"__rt_bi_assertz"),
            ("retract",1,"__rt_bi_retract"),
            ("database_open",2,"__rt_bi_database_open2"),
            ("database_open",3,"__rt_bi_database_open3"),
            ("database_open",4,"__rt_bi_database_open4"),
            ("database_close",1,"__rt_bi_database_close"),
            ("database_save",1,"__rt_bi_database_save"),
            ("database_save_as",2,"__rt_bi_database_save_as"),
            ("database_select",1,"__rt_bi_database_select"),
            ("current_database",1,"__rt_bi_current_database"),
            ("database_modified",1,"__rt_bi_database_modified"),
            ("database_assert",2,"__rt_bi_database_assertz"),
            ("database_asserta",2,"__rt_bi_database_asserta"),
            ("database_assertz",2,"__rt_bi_database_assertz"),
            ("database_retract",2,"__rt_bi_database_retract"),
            ("with_database",2,"__rt_bi_with_database"),
            (",",2,"__rt_bi_conjunction"),(";",2,"__rt_bi_disjunction"),
            ("=",2,"__rt_bi_unify"),("\\=",2,"__rt_bi_notunify"),("==",2,"__rt_bi_equal"),("is",2,"__rt_bi_is"),
            ("<",2,"__rt_bi_lt"),("=<",2,"__rt_bi_le"),(">",2,"__rt_bi_gt"),(">=",2,"__rt_bi_ge"),
        ]
        for i,(name,arity,label) in enumerate(builtins):
            nxt=f"__rt_builtin_next_{i}"
            a.e(f"    cmp edx, {self.atom_id(name)}")
            a.e(f"    jne {nxt}")
            a.e(f"    cmp ecx, {arity}")
            a.e(f"    je {label}")
            a.l(nxt)
        a.e("    jmp __rt_builtin_fallthrough")

        def solve_rest():
            a.e(f"    {ar.push_reg32('ebx')}")
            a.e("    call __rt_solve_goals")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    jmp __rt_solve_done")

        a.l("__rt_bi_true")
        solve_rest()
        a.l("__rt_bi_fail")
        a.e("    jmp __rt_solve_done")
        a.l("__rt_bi_cut")
        # Lexical cut barrier comes from the current goal-link.  Pruning only
        # changes choice_top; the clause snapshot is restored explicitly by
        # the dispatcher after the continuation has been exhausted.
        a.e("    mov eax, dword ptr [__prolog_current_cut_barrier]")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_bi_cut_cont")
        a.e("    mov dword ptr [__prolog_choice_top], eax")
        a.e("    mov dword ptr [__prolog_cut_active_barrier], eax")
        a.l("__rt_bi_cut_cont")
        solve_rest()
        a.l("__rt_bi_nl")
        a.e("    push __prolog_text_newline")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        solve_rest()
        a.l("__rt_bi_gc")
        a.e("    call __rt_gc_dynamic")
        solve_rest()
        a.l("__rt_bi_verbose")
        # verbose(true/false): runtime switch.  true suppresses automatic
        # top-level solution printing; explicit write/writeln is unaffected.
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    call __rt_deref")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_ATOM}")
        a.e("    jne __rt_solve_done")
        a.e(f"    cmp dword ptr [{ar.di}+4], {self.atom_id('true')}")
        a.e("    jne __rt_bi_verbose_false_test")
        a.e("    mov dword ptr [__prolog_verbose], 1")
        solve_rest()
        a.l("__rt_bi_verbose_false_test")
        a.e(f"    cmp dword ptr [{ar.di}+4], {self.atom_id('false')}")
        a.e("    jne __rt_solve_done")
        a.e("    mov dword ptr [__prolog_verbose], 0")
        solve_rest()
        a.l("__rt_bi_halt")
        a.e("    push 0")
        a.e("    call ExitProcess")
        a.e("    jmp __rt_solve_done")
        a.l("__rt_bi_repl")
        if self.is_gui:
            a.e("    push __prolog_text_repl_gui")
            a.e("    call __rt_emit_text")
            a.e(f"    {ar.cleanup(1)}")
        else:
            a.e("    call __rt_repl")
        solve_rest()

        for label, newline in (("__rt_bi_write",False),("__rt_bi_writeln",True)):
            a.l(label)
            a.e("    push 0")
            a.e(f"    {ar.push_reg32('esi')}")
            a.e("    call __rt_struct_arg")
            a.e(f"    {ar.cleanup(2)}")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    call __rt_emit_term")
            a.e(f"    {ar.cleanup(1)}")
            if newline:
                a.e("    push __prolog_text_newline")
                a.e("    call __rt_emit_text")
                a.e(f"    {ar.cleanup(1)}")
            solve_rest()

        # Type tests are pure recognizers: they dereference the argument and
        # compare its existing runtime tag.  In particular string/1 never
        # binds an unbound variable and accepts only NODE_STRING (double-quoted
        # PROLOG strings), not NODE_ATOM (single-quoted atoms).
        for name, tag, invert in (
            ("var", NODE_VAR, False),("nonvar", NODE_VAR, True),("atom", NODE_ATOM, False),
            ("integer", NODE_INT, False),("float", NODE_FLOAT, False),("string", NODE_STRING, False),
        ):
            label=f"__rt_bi_{name}"
            a.l(label)
            a.e("    push 0")
            a.e(f"    {ar.push_reg32('esi')}")
            a.e("    call __rt_struct_arg")
            a.e(f"    {ar.cleanup(2)}")
            a.e("    call __rt_deref")
            a.e("    call __rt_node_ptr")
            a.e(f"    cmp dword ptr [{ar.di}], {tag}")
            if invert:
                a.e("    je __rt_solve_done")
            else:
                a.e("    jne __rt_solve_done")
            solve_rest()

        a.l("__rt_bi_number")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    call __rt_deref")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_INT}")
        a.e("    je __rt_bi_number_ok")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_FLOAT}")
        a.e("    jne __rt_solve_done")
        a.l("__rt_bi_number_ok")
        solve_rest()

        # assert/retract. assert/1 follows assertz/1 ordering.
        for label, runtime_fn in (("__rt_bi_assertz","__rt_assertz"),("__rt_bi_asserta","__rt_asserta")):
            a.l(label)
            a.e("    push 0")
            a.e(f"    {ar.push_reg32('esi')}")
            a.e("    call __rt_struct_arg")
            a.e(f"    {ar.cleanup(2)}")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e(f"    call {runtime_fn}")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    test eax, eax")
            a.e("    je __rt_solve_done")
            solve_rest()
        a.l("__rt_bi_retract")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_retract")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    je __rt_solve_done")
        solve_rest()

        # --------------------------------------------------------------
        # External knowledge database builtins
        # --------------------------------------------------------------
        def emit_db_open_finish(fail_label: str):
            a.e("    test eax, eax")
            a.e(f"    je {fail_label}")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    call __rt_make_int")
            a.e(f"    {ar.cleanup(1)}")
            a.e(f"    pop {ar.dx}")  # output DB term
            a.e(f"    {ar.push_reg32('eax')}")
            a.e(f"    {ar.push_reg32('edx')}")
            a.e("    call __rt_unify")
            a.e(f"    {ar.cleanup(2)}")
            a.e("    test eax, eax")
            a.e("    je __rt_solve_done")
            solve_rest()
            a.l(fail_label)
            a.e(f"    pop {ar.dx}")
            a.e("    jmp __rt_solve_done")

        # database_open(File, DB) -> read_write RECORD
        a.l("__rt_bi_database_open2")
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")  # output term
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    push {DATABASE_KIND_RECORD}")
        a.e(f"    push {DATABASE_MODE_READ_WRITE}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_database_open")
        a.e(f"    {ar.cleanup(3)}")
        emit_db_open_finish("__rt_bi_database_open2_fail")

        # database_open(File, Mode, DB)
        a.l("__rt_bi_database_open3")
        a.e("    push 2")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")  # output
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_db_mode_from_term")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_bi_database_open3_fail")
        a.e(f"    {ar.push_reg32('eax')}")  # mode
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    pop {ar.cx}")  # mode
        a.e(f"    push {DATABASE_KIND_RECORD}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_database_open")
        a.e(f"    {ar.cleanup(3)}")
        emit_db_open_finish("__rt_bi_database_open3_fail")

        # database_open(File, Mode, Kind, DB)
        a.l("__rt_bi_database_open4")
        a.e("    push 3")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")  # output
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_db_mode_from_term")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_bi_database_open4_fail")
        a.e(f"    {ar.push_reg32('eax')}")  # mode
        a.e("    push 2")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_db_kind_from_term")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_bi_database_open4_fail_mode")
        a.e(f"    {ar.push_reg32('eax')}")  # kind
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    pop {ar.dx}")  # kind
        a.e(f"    pop {ar.cx}")  # mode
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_database_open")
        a.e(f"    {ar.cleanup(3)}")
        emit_db_open_finish("__rt_bi_database_open4_fail")
        a.l("__rt_bi_database_open4_fail_mode")
        a.e(f"    pop {ar.cx}")  # discard mode
        a.e("    jmp __rt_bi_database_open4_fail")

        a.l("__rt_bi_database_close")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_term_int")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_solve_done")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_database_close_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    je __rt_solve_done")
        solve_rest()

        a.l("__rt_bi_database_save")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_term_int")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_solve_done")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_database_save_id")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test eax, eax")
        a.e("    je __rt_solve_done")
        solve_rest()

        a.l("__rt_bi_database_save_as")
        # DB
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_term_int")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_solve_done")
        a.e(f"    {ar.push_reg32('eax')}")  # dbid
        # file
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov edx, eax")
        a.e(f"    pop {ar.ax}")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_database_save_as")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_solve_done")
        solve_rest()

        a.l("__rt_bi_database_select")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_term_int")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_solve_done")
        a.e("    test eax, eax")
        a.e("    je __rt_bi_database_select_set")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_solve_done")
        # recover requested DB from goal
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_term_int")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_bi_database_select_set")
        a.e("    mov dword ptr [__prolog_current_db], eax")
        solve_rest()

        a.l("__rt_bi_current_database")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")  # output
        a.e("    push dword ptr [__prolog_current_db]")
        a.e("    call __rt_make_int")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    pop {ar.dx}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_unify")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_solve_done")
        solve_rest()

        a.l("__rt_bi_database_modified")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_term_int")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_solve_done")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_solve_done")
        self._arena_to(a, ar.di, DB_MODIFIED_OFF)
        a.e(f"    cmp dword ptr [{ar.di}+{ar.ax}*4], 0")
        a.e("    je __rt_solve_done")
        solve_rest()

        # database_assert*/2
        for label, front in (
            ("__rt_bi_database_assertz", 0),
            ("__rt_bi_database_asserta", 1),
        ):
            a.l(label)
            a.e("    push 0")
            a.e(f"    {ar.push_reg32('esi')}")
            a.e("    call __rt_struct_arg")
            a.e(f"    {ar.cleanup(2)}")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    call __rt_term_int")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    test edx, edx")
            a.e("    je __rt_solve_done")
            a.e(f"    {ar.push_reg32('eax')}")  # DB-ID
            a.e("    push 1")
            a.e(f"    {ar.push_reg32('esi')}")
            a.e("    call __rt_struct_arg")
            a.e(f"    {ar.cleanup(2)}")
            a.e("    mov edx, eax")
            a.e(f"    pop {ar.ax}")
            a.e(f"    push {front}")
            a.e(f"    {ar.push_reg32('edx')}")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    call __rt_database_assert_scoped")
            a.e(f"    {ar.cleanup(3)}")
            a.e("    test eax, eax")
            a.e("    je __rt_solve_done")
            solve_rest()

        a.l("__rt_bi_database_retract")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_term_int")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_solve_done")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov edx, eax")
        a.e(f"    pop {ar.ax}")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_database_retract_scoped")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_solve_done")
        solve_rest()

        # with_database(DB, Goal): scoped current DB across the complete
        # Goal+continuation search, including backtracking.
        a.l("__rt_bi_with_database")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_term_int")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_solve_done")
        a.e(f"    {ar.push_reg32('eax')}")  # requested DB
        a.e("    test eax, eax")
        a.e("    je __rt_bi_with_database_have_db")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_db_find_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_bi_with_database_fail_pop")
        a.l("__rt_bi_with_database_have_db")
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov edx, dword ptr [__prolog_current_cut_barrier]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_goal_expr_to_chain")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    mov edx, eax")  # scoped chain
        a.e(f"    pop {ar.cx}")  # requested DB
        a.e("    mov eax, dword ptr [__prolog_current_db]")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    mov dword ptr [__prolog_current_db], ecx")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_solve_goals")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    pop {ar.ax}")
        a.e("    mov dword ptr [__prolog_current_db], eax")
        a.e("    jmp __rt_solve_done")
        a.l("__rt_bi_with_database_fail_pop")
        a.e(f"    pop {ar.cx}")
        a.e("    jmp __rt_solve_done")

        # Conjunction/disjunction are runtime control constructs.  The helper
        # converts a conjunction expression to ordinary goal links while
        # preserving the current lexical cut barrier.
        a.l("__rt_bi_conjunction")
        a.e("    mov edx, dword ptr [__prolog_current_cut_barrier]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_goal_expr_to_chain")
        a.e(f"    {ar.cleanup(3)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_solve_goals")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_solve_done")

        a.l("__rt_bi_disjunction")
        # fetch left/right alternatives
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    {ar.push_reg32('eax')}")  # left
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ecx, eax") # right
        a.e(f"    pop {ar.ax}") # left
        a.e(f"    {ar.push_reg32('ecx')}") # keep right across left branch
        # branch mark
        a.e("    mov edx, dword ptr [__prolog_choice_top]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_choice_push")
        a.e("    mov edx, dword ptr [__prolog_current_cut_barrier]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_goal_expr_to_chain")
        a.e(f"    {ar.cleanup(3)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_solve_goals")
        a.e(f"    {ar.cleanup(1)}")
        # restore left branch snapshot
        a.e(f"    mov edx, dword ptr [{ar.sp}]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_choice_restore_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    pop {ar.dx}") # mark
        a.e(f"    pop {ar.cx}") # right
        a.e("    cmp dword ptr [__prolog_stop_search], 0")
        a.e("    jne __rt_solve_done")
        # A cut belonging to this surrounding clause prunes the second arm.
        a.e("    mov eax, dword ptr [__prolog_current_cut_barrier]")
        a.e("    cmp dword ptr [__prolog_cut_active_barrier], eax")
        a.e("    je __rt_solve_done")
        # right branch gets its own reversible snapshot
        a.e("    mov edx, dword ptr [__prolog_choice_top]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_choice_push")
        a.e("    mov edx, dword ptr [__prolog_current_cut_barrier]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_goal_expr_to_chain")
        a.e(f"    {ar.cleanup(3)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_solve_goals")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    mov edx, dword ptr [{ar.sp}]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_choice_restore_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    pop {ar.dx}")
        a.e("    jmp __rt_solve_done")

        # binary arg helper sequences
        def get2():
            a.e("    push 0")
            a.e(f"    {ar.push_reg32('esi')}")
            a.e("    call __rt_struct_arg")
            a.e(f"    {ar.cleanup(2)}")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    push 1")
            a.e(f"    {ar.push_reg32('esi')}")
            a.e("    call __rt_struct_arg")
            a.e(f"    {ar.cleanup(2)}")
            a.e("    mov ecx, eax")
            a.e(f"    pop {ar.ax}")

        a.l("__rt_bi_is")
        get2()
        # EAX=left term, ECX=right arithmetic expression. __rt_eval_arith
        # returns an INTEGER or FLOAT term handle directly.
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_eval_arith")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_bi_is_fail_pop")
        a.e("    mov ecx, eax")
        a.e(f"    pop {ar.ax}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_unify")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_solve_done")
        solve_rest()
        a.l("__rt_bi_is_fail_pop")
        a.e(f"    pop {ar.ax}")
        a.e("    jmp __rt_solve_done")

        a.l("__rt_bi_unify")
        get2()
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_unify")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_solve_done")
        solve_rest()

        a.l("__rt_bi_notunify")
        a.e("    call __rt_choice_push")
        get2()
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_unify")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ecx, eax")
        a.e("    call __rt_choice_restore_pop")
        a.e("    test ecx, ecx")
        a.e("    jne __rt_solve_done")
        solve_rest()

        a.l("__rt_bi_equal")
        get2()
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_equal_terms")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test eax, eax")
        a.e("    je __rt_solve_done")
        solve_rest()

        # Arithmetic comparisons evaluate both sides to numeric term handles
        # and compare INTEGER/FLOAT combinations through x87.
        for name,label,op in (("lt","__rt_bi_lt","jl"),("le","__rt_bi_le","jle"),("gt","__rt_bi_gt","jg"),("ge","__rt_bi_ge","jge")):
            a.l(label)
            get2()
            a.e(f"    {ar.push_reg32('ecx')}")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    call __rt_eval_arith")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    test edx, edx")
            a.e("    je __rt_cmp_fail_pop")
            # EBX is the continuation goal-chain owned by __rt_solve_goals.
            # Never reuse it as arithmetic scratch: solve_rest() must receive
            # the original continuation, not the evaluated numeric term.
            # ESI no longer needs the current comparison goal after get2(),
            # and __rt_eval_arith preserves ESI, so keep the left numeric term
            # there instead.
            a.e("    mov esi, eax")
            a.e(f"    pop {ar.ax}")
            a.e(f"    {ar.push_reg32('eax')}")
            a.e("    call __rt_eval_arith")
            a.e(f"    {ar.cleanup(1)}")
            a.e("    test edx, edx")
            a.e("    je __rt_solve_done")
            a.e("    mov ecx, eax")
            a.e(f"    {ar.push_reg32('ecx')}")  # right
            a.e(f"    {ar.push_reg32('esi')}")  # left; EBX remains rest chain
            a.e("    call __rt_numeric_compare")
            a.e(f"    {ar.cleanup(2)}")
            a.e("    test edx, edx")
            a.e("    je __rt_solve_done")
            ok=f"{label}_ok"
            a.e("    cmp eax, 0")
            a.e(f"    {op} {ok}")
            a.e("    jmp __rt_solve_done")
            a.l(ok)
            solve_rest()
        a.l("__rt_cmp_fail_pop")
        a.e(f"    pop {ar.ax}")
        a.e("    jmp __rt_solve_done")

        a.l("__rt_builtin_fallthrough")

    def _emit_user_dispatch(self, a: _A) -> None:
        ar = self.arch
        a.l("__rt_try_user")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov esi, {ar.arg(0)}") # goal term
        a.e(f"    mov ebx, {ar.arg(1)}") # rest chain
        # extract goal functor/arity -> edx/ecx
        a.e("    mov eax, esi")
        a.e("    call __rt_deref")
        a.e("    mov esi, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_ATOM}")
        a.e("    je __rt_try_user_atom")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e("    jne __rt_try_user_dynamic")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e("    jmp __rt_try_user_dispatch")
        a.l("__rt_try_user_atom")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]")
        a.e("    xor ecx, ecx")
        a.l("__rt_try_user_dispatch")
        group_index=0
        for (name,arity), entries in sorted(self.pred_groups.items(), key=lambda x:(x[0][0],x[0][1])):
            if name in set(BUILTIN_NAMES):
                continue
            nxt=f"__rt_try_pred_next_{group_index}"; group_index+=1
            a.e(f"    cmp edx, {self.atom_id(name)}")
            a.e(f"    jne {nxt}")
            a.e(f"    cmp ecx, {arity}")
            a.e(f"    jne {nxt}")
            for clause_idx,_clause in entries:
                # Exact clause-choice slot is retained on the CPU stack. ! may
                # lower choice_top, but restore_slot can still restore this
                # snapshot without accidentally touching an outer choicepoint.
                a.e("    mov eax, dword ptr [__prolog_choice_top]")
                a.e("    mov dword ptr [__prolog_build_barrier], eax")
                a.e(f"    {ar.push_reg32('eax')}")
                a.e("    call __rt_choice_push")
                a.e("    mov edx, ebx")
                a.e(f"    call __prolog_clause_{clause_idx}_build")
                # eax=head, ecx=new chain
                a.e(f"    {ar.push_reg32('ecx')}")
                a.e(f"    {ar.push_reg32('eax')}")
                a.e(f"    {ar.push_reg32('esi')}")
                a.e("    call __rt_unify")
                a.e(f"    {ar.cleanup(2)}")
                a.e(f"    pop {ar.cx}")
                fail=f"__rt_clause_{clause_idx}_after"
                cont=f"__rt_clause_{clause_idx}_continue"
                a.e("    test eax, eax")
                a.e(f"    je {fail}")
                a.e(f"    {ar.push_reg32('ecx')}")
                a.e("    call __rt_solve_goals")
                a.e(f"    {ar.cleanup(1)}")
                a.l(fail)
                # duplicate mark from stack for restore_slot, then consume it
                a.e(f"    mov ecx, dword ptr [{ar.sp}]")
                a.e(f"    {ar.push_reg32('ecx')}")
                a.e("    call __rt_choice_restore_slot")
                a.e(f"    {ar.cleanup(1)}")
                a.e(f"    pop {ar.cx}")
                a.e("    cmp dword ptr [__prolog_cut_active_barrier], ecx")
                a.e(f"    jne {cont}")
                a.e(f"    mov dword ptr [__prolog_cut_active_barrier], {INVALID}")
                a.e("    jmp __rt_try_user_return")
                a.l(cont)
                a.e("    cmp dword ptr [__prolog_stop_search], 0")
                a.e("    jne __rt_try_user_return")
            a.e("    jmp __rt_try_user_dynamic")
            a.l(nxt)
        a.l("__rt_try_user_dynamic")
        # Dynamic facts/rules are attempted after static clauses.
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_try_dynamic")
        a.e(f"    {ar.cleanup(2)}")
        a.l("__rt_try_user_return")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    def _emit_dynamic_user_loop(self, a: _A) -> None:
        ar = self.arch
        a.l("__rt_try_dynamic")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e(f"    mov esi, {ar.arg(0)}") # goal
        a.e(f"    mov ebx, {ar.arg(1)}") # rest
        # functor/arity goal into edx/ecx
        a.e("    mov eax, esi")
        a.e("    call __rt_deref")
        a.e("    mov esi, eax")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_ATOM}")
        a.e("    je __rt_try_dynamic_atom")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e("    jne __rt_try_dynamic_return")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]")
        a.e(f"    mov ecx, dword ptr [{ar.di}+8]")
        a.e("    jmp __rt_try_dynamic_scan")
        a.l("__rt_try_dynamic_atom")
        a.e(f"    mov edx, dword ptr [{ar.di}+4]")
        a.e("    xor ecx, ecx")
        a.l("__rt_try_dynamic_scan")
        # stack retains arity then functor across scan
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    xor ecx, ecx") # db index
        a.l("__rt_try_dynamic_loop")
        a.e("    cmp dword ptr [__prolog_stop_search], 0")
        a.e("    jne __rt_try_dynamic_done_pop")
        a.e("    cmp ecx, dword ptr [__prolog_dyn_count]")
        a.e("    jae __rt_try_dynamic_done_pop")
        self._arena_to(a, ar.di, DYN_DB_OFF)
        a.e("    mov eax, ecx")
        a.e("    shl eax, 4")
        a.e(f"    add {ar.di}, {ar.ax}")
        a.e(f"    cmp dword ptr [{ar.di}], 0")
        a.e("    je __rt_try_dynamic_next")
        a.e(f"    mov eax, dword ptr [{ar.sp}]")       # saved functor
        a.e(f"    cmp dword ptr [{ar.di}+4], eax")
        a.e("    jne __rt_try_dynamic_next")
        a.e(f"    mov eax, dword ptr [{ar.sp}+{ar.ptr}]") # saved arity
        a.e(f"    cmp dword ptr [{ar.di}+8], eax")
        a.e("    jne __rt_try_dynamic_next")
        a.e(f"    mov eax, dword ptr [{ar.di}+12]")
        # Stage 51: __rt_choice_push returns its choice-slot in EAX.  Preserve
        # the persistent clause root in DI, which choice_push itself preserves.
        a.e(f"    mov {ar.di}, {ar.ax}")
        # preserve scan index and exact choice mark
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    mov edx, dword ptr [__prolog_choice_top]")
        a.e("    mov dword ptr [__prolog_build_barrier], edx")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_choice_push")
        a.e("    mov dword ptr [__prolog_dyn_clone_var_count], 0")
        a.e(f"    {'push rdi' if ar.is64 else 'push edi'}")
        a.e("    call __rt_dyn_clone")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_try_dynamic_after_solve")
        a.e("    mov edx, eax")  # cloned complete clause
        # Decode dynamic rule (Head :- Body), otherwise fact Head.
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_STRUCT}")
        a.e("    jne __rt_try_dynamic_fact")
        a.e(f"    cmp dword ptr [{ar.di}+4], {self.atom_id(':-')}")
        a.e("    jne __rt_try_dynamic_fact")
        a.e(f"    cmp dword ptr [{ar.di}+8], 2")
        a.e("    jne __rt_try_dynamic_fact")
        a.e("    push 1")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ecx, eax")  # body expression
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    push 0")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_struct_arg")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov edx, eax")  # head
        a.e(f"    pop {ar.cx}") # body
        a.e("    jmp __rt_try_dynamic_unify")
        a.l("__rt_try_dynamic_fact")
        a.e(f"    mov ecx, {INVALID}")
        a.l("__rt_try_dynamic_unify")
        # preserve body while unifying goal with head
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_unify")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    pop {ar.cx}")
        a.e("    test eax, eax")
        a.e("    je __rt_try_dynamic_after_solve")
        a.e(f"    cmp ecx, {INVALID}")
        a.e("    je __rt_try_dynamic_solve_rest")
        # Convert rule body expression to goal chain using this clause barrier.
        a.e(f"    mov edx, dword ptr [{ar.sp}]") # mark is top
        a.e(f"    {ar.push_reg32('edx')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_goal_expr_to_chain")
        a.e(f"    {ar.cleanup(3)}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_solve_goals")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_try_dynamic_after_solve")
        a.l("__rt_try_dynamic_solve_rest")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_solve_goals")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_try_dynamic_after_solve")
        # restore exact choice slot; then recover mark and scan index
        a.e(f"    mov edx, dword ptr [{ar.sp}]")
        a.e(f"    {ar.push_reg32('edx')}")
        a.e("    call __rt_choice_restore_slot")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    pop {ar.dx}")
        a.e(f"    pop {ar.cx}")
        a.e("    cmp dword ptr [__prolog_cut_active_barrier], edx")
        a.e("    jne __rt_try_dynamic_next")
        a.e(f"    mov dword ptr [__prolog_cut_active_barrier], {INVALID}")
        a.e("    jmp __rt_try_dynamic_done_pop")
        a.l("__rt_try_dynamic_next")
        a.e("    inc ecx")
        a.e("    jmp __rt_try_dynamic_loop")
        a.l("__rt_try_dynamic_done_pop")
        a.e(f"    pop {ar.dx}")
        a.e(f"    pop {ar.cx}")
        a.l("__rt_try_dynamic_return")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    def _emit_run_query(self, a: _A) -> None:
        ar = self.arch
        a.l("__rt_run_query")
        self._prologue(a)
        a.e("    mov dword ptr [__prolog_solution_count], 0")
        a.e("    mov dword ptr [__prolog_stop_search], 0")
        a.e("    mov dword ptr [__prolog_requested_more], 0")
        a.e(f"    push {ar.arg(0)}")
        a.e("    call __rt_solve_goals")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    cmp dword ptr [__prolog_solution_count], 0")
        a.e("    je __rt_run_query_false")
        # If the user explicitly requested another answer with ';' and the
        # search exhausted without being stopped by ENTER, report failure just
        # like an interactive Prolog top-level does after the last solution.
        a.e("    cmp dword ptr [__prolog_interactive_mode], 0")
        a.e("    je __rt_run_query_done")
        a.e("    cmp dword ptr [__prolog_requested_more], 0")
        a.e("    je __rt_run_query_done")
        a.e("    cmp dword ptr [__prolog_stop_search], 0")
        a.e("    jne __rt_run_query_done")
        a.l("__rt_run_query_false")
        a.e("    push __prolog_text_false_line")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.l("__rt_run_query_done")
        self._epilogue(a)
        a.e()

    # ------------------------------------------------------------------
    # Console input + interactive query parser
    # ------------------------------------------------------------------
    def _emit_repl(self, a: _A) -> None:
        if self.is_gui:
            return
        ar = self.arch
        # read line -> pointer in AX, trim CR/LF
        a.l("__rt_read_line")
        self._prologue(a, save=(ar.si, ar.di))
        self._arena_to(a, ar.si, INPUT_OFF)
        a.e("    mov dword ptr [__prolog_read_count], 0")
        a.e("    push 0")
        a.e("    push __prolog_read_count")
        a.e(f"    push {INPUT_SIZE-1}")
        a.e(f"    push {ar.si}")
        a.e(f"    push {ar.mem_ptr('__prolog_stdin')}")
        a.e("    call ReadFile")
        a.e("    mov edx, dword ptr [__prolog_read_count]")
        a.l("__rt_read_trim")
        a.e("    test edx, edx")
        a.e("    je __rt_read_terminate")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.dx}-1]")
        a.e("    cmp eax, 10")
        a.e("    je __rt_read_trim_one")
        a.e("    cmp eax, 13")
        a.e("    jne __rt_read_terminate")
        a.l("__rt_read_trim_one")
        a.e("    dec edx")
        a.e("    jmp __rt_read_trim")
        a.l("__rt_read_terminate")
        a.e("    xor eax, eax")
        a.e(f"    mov byte ptr [{ar.si}+{ar.dx}], al")
        a.e(f"    mov {ar.ax}, {ar.si}")
        self._epilogue(a, save=(ar.si, ar.di))
        a.e()

        a.l("__rt_repl")
        self._prologue(a)
        a.l("__rt_repl_loop")
        a.e("    push __prolog_text_prompt")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    call __rt_read_line")
        # Empty line -> continue
        a.e(f"    movzx ecx, byte ptr [{ar.ax}]")
        a.e("    test ecx, ecx")
        a.e("    je __rt_repl_loop")
        # reset transient query state
        a.e("    mov dword ptr [__prolog_heap_top], 0")
        a.e("    mov dword ptr [__prolog_trail_top], 0")
        a.e("    mov dword ptr [__prolog_choice_top], 0")
        a.e("    mov dword ptr [__prolog_query_var_count], 0")
        a.e("    mov dword ptr [__prolog_qname_top], 0")
        a.e("    mov dword ptr [__prolog_parse_pos], 0")
        a.e("    call __rt_parse_query")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    jne __rt_repl_run")
        a.e("    push __prolog_text_parse_error")
        a.e("    call __rt_emit_text")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_repl_loop")
        a.l("__rt_repl_run")
        a.e("    mov dword ptr [__prolog_interactive_mode], 1")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_run_query")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    mov dword ptr [__prolog_interactive_mode], 0")
        a.e("    mov dword ptr [__prolog_stop_search], 0")
        a.e("    jmp __rt_repl_loop")
        self._epilogue(a)
        a.e()

    def _emit_parser(self, a: _A) -> None:
        ar = self.arch
        # skip whitespace; returns next char in eax
        a.l("__rt_parse_skip_ws")
        self._prologue(a, save=(ar.si,))
        self._arena_to(a, ar.si, INPUT_OFF)
        a.l("__rt_parse_skip_ws_loop")
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        for code in (32,9,13,10):
            a.e(f"    cmp eax, {code}")
            a.e("    je __rt_parse_skip_ws_one")
        # File-backed databases may contain normal PROLOG comments.
        a.e("    cmp eax, 37")  # %
        a.e("    je __rt_parse_skip_ws_line_comment")
        a.e("    cmp eax, 47")  # /
        a.e("    jne __rt_parse_skip_ws_done")
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}+1]")
        a.e("    cmp eax, 42")  # *
        a.e("    jne __rt_parse_skip_ws_done")
        a.e("    add dword ptr [__prolog_parse_pos], 2")
        a.l("__rt_parse_skip_ws_block_comment")
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e("    test eax, eax")
        a.e("    je __rt_parse_skip_ws_done")
        a.e("    cmp eax, 42")
        a.e("    jne __rt_parse_skip_ws_block_next")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}+1]")
        a.e("    cmp eax, 47")
        a.e("    jne __rt_parse_skip_ws_block_next")
        a.e("    add dword ptr [__prolog_parse_pos], 2")
        a.e("    jmp __rt_parse_skip_ws_loop")
        a.l("__rt_parse_skip_ws_block_next")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    jmp __rt_parse_skip_ws_block_comment")
        a.l("__rt_parse_skip_ws_line_comment")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e("    test eax, eax")
        a.e("    je __rt_parse_skip_ws_done")
        a.e("    cmp eax, 10")
        a.e("    je __rt_parse_skip_ws_loop")
        a.e("    cmp eax, 13")
        a.e("    je __rt_parse_skip_ws_loop")
        a.e("    jmp __rt_parse_skip_ws_line_comment")
        a.l("__rt_parse_skip_ws_one")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    jmp __rt_parse_skip_ws_loop")
        a.l("__rt_parse_skip_ws_done")
        self._epilogue(a, save=(ar.si,))
        a.e()

        # consume exact current char in AL expected immediate arg; returns 1/0
        a.l("__rt_parse_consume")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e(f"    mov ebx, {ar.arg(0)}")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, ebx")
        a.e("    jne __rt_parse_consume_fail")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_parse_consume_done")
        a.l("__rt_parse_consume_fail")
        a.e("    xor eax, eax")
        a.l("__rt_parse_consume_done")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # identifier/token reader. input type mode ignored; returns token ptr in AX, len ECX.
        a.l("__rt_parse_token")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        self._arena_to(a, ar.si, INPUT_OFF)
        self._arena_to(a, ar.di, TOKEN_OFF)
        a.e("    mov ebx, dword ptr [__prolog_parse_pos]")
        a.e("    xor ecx, ecx")
        a.l("__rt_parse_token_loop")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.bx}]")
        # alnum or underscore
        a.e("    cmp eax, 48")
        a.e("    jb __rt_parse_token_check_alpha")
        a.e("    cmp eax, 57")
        a.e("    jbe __rt_parse_token_store")
        a.l("__rt_parse_token_check_alpha")
        a.e("    cmp eax, 65")
        a.e("    jb __rt_parse_token_check_lower")
        a.e("    cmp eax, 90")
        a.e("    jbe __rt_parse_token_store")
        a.l("__rt_parse_token_check_lower")
        a.e("    cmp eax, 97")
        a.e("    jb __rt_parse_token_check_us")
        a.e("    cmp eax, 122")
        a.e("    jbe __rt_parse_token_store")
        a.l("__rt_parse_token_check_us")
        a.e("    cmp eax, 95")
        a.e("    je __rt_parse_token_store")
        # Stage 58: German umlauts may arrive as Latin-1 bytes or UTF-8.
        # Normalize the common UTF-8 C3 xx sequences to the same Latin-1 byte
        # representation used by the static atom table.
        a.e("    cmp eax, 128")
        a.e("    jb __rt_parse_token_done")
        a.e("    cmp eax, 195")
        a.e("    jne __rt_parse_token_store")
        a.e(f"    movzx edx, byte ptr [{ar.si}+{ar.bx}+1]")
        for utf8_tail, latin1 in ((164,228),(182,246),(188,252),(132,196),(150,214),(156,220),(159,223)):
            a.e(f"    cmp edx, {utf8_tail}")
            a.e(f"    je __rt_parse_token_utf8_{latin1}")
        a.e("    jmp __rt_parse_token_store")
        for utf8_tail, latin1 in ((164,228),(182,246),(188,252),(132,196),(150,214),(156,220),(159,223)):
            a.l(f"__rt_parse_token_utf8_{latin1}")
            a.e(f"    mov eax, {latin1}")
            a.e("    inc ebx")  # store path consumes the second byte too
            a.e("    jmp __rt_parse_token_store")
        a.l("__rt_parse_token_store")
        a.e(f"    cmp ecx, {TOKEN_SIZE-1}")
        a.e("    jae __rt_parse_token_done")
        a.e(f"    mov byte ptr [{ar.di}+{ar.cx}], al")
        a.e("    inc ecx")
        a.e("    inc ebx")
        a.e("    jmp __rt_parse_token_loop")
        a.l("__rt_parse_token_done")
        a.e("    xor eax, eax")
        a.e(f"    mov byte ptr [{ar.di}+{ar.cx}], al")
        a.e("    mov dword ptr [__prolog_parse_pos], ebx")
        a.e(f"    mov {ar.ax}, {ar.di}")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # token equals c-string helper (ptr,len,cstr) -> 1/0
        a.l("__rt_token_eq")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        if ar.is64:
            a.e(f"    mov rsi, {ar.arg(0,'qword')}")
            a.e(f"    mov rdi, {ar.arg(2,'qword')}")
        else:
            a.e(f"    mov esi, {ar.arg(0)}")
            a.e(f"    mov edi, {ar.arg(2)}")
        a.e(f"    mov ebx, {ar.arg(1)}")
        a.e("    xor ecx, ecx")
        a.l("__rt_token_eq_loop")
        a.e("    cmp ecx, ebx")
        a.e("    jae __rt_token_eq_endcheck")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e(f"    movzx edx, byte ptr [{ar.di}+{ar.cx}]")
        a.e("    cmp eax, edx")
        a.e("    jne __rt_token_eq_fail")
        a.e("    inc ecx")
        a.e("    jmp __rt_token_eq_loop")
        a.l("__rt_token_eq_endcheck")
        a.e(f"    movzx eax, byte ptr [{ar.di}+{ar.cx}]")
        a.e("    test eax, eax")
        a.e("    jne __rt_token_eq_fail")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_token_eq_done")
        a.l("__rt_token_eq_fail")
        a.e("    xor eax, eax")
        a.l("__rt_token_eq_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # intern atom token(ptr,len) -> id
        self._emit_atom_intern(a)
        self._emit_query_var_parser(a)
        self._emit_db_parser_var(a)
        self._emit_parse_term(a)
        self._emit_parse_goal(a)
        self._emit_parse_goal_list(a)
        self._emit_parse_knowledge_assignment(a)

        # parse_query: optional ?- then goal list, handles halt./quit. by ExitProcess.
        a.l("__rt_parse_query")
        self._prologue(a, save=(ar.si,))
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 63") # ?
        a.e("    jne __rt_parse_query_goals")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        self._call1_imm(a, "__rt_parse_consume", 45) # -
        a.e("    test eax, eax")
        a.e("    je __rt_parse_query_fail")
        a.l("__rt_parse_query_goals")
        a.e("    call __rt_parse_goal_list")
        a.e("    jmp __rt_parse_query_done")
        a.l("__rt_parse_query_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_query_done")
        self._epilogue(a, save=(ar.si,))
        a.e()

    def _emit_parse_knowledge_assignment(self, a: _A) -> None:
        """Parse dBase2Many named knowledge assignments in external DBs.

        Stage 58 adds Unicode-aware German identifiers and load-time string
        materialization for expressions such as ``_b = _a + "text"``.  The
        dynamic database still stores an ordinary ground
        ``d64_knowledge_value(Name, Value)`` fact, so Database-ID ownership,
        save/close and GC continue to use the existing code paths.
        """
        ar = self.arch

        # current parse_pos starts at '_' -> EAX=1 for _lower / _ä/_ö/_ü/_ß.
        a.l("__rt_is_knowledge_start")
        self._prologue(a, save=(ar.si,))
        self._arena_to(a, ar.si, INPUT_OFF)
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e("    cmp eax, 95")
        a.e("    jne __rt_is_knowledge_start_no")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}+1]")
        a.e("    cmp eax, 97")
        a.e("    jb __rt_is_knowledge_start_latin1")
        a.e("    cmp eax, 122")
        a.e("    jbe __rt_is_knowledge_start_yes")
        a.l("__rt_is_knowledge_start_latin1")
        for value in (223, 228, 246, 252):  # ß ä ö ü in Latin-1
            a.e(f"    cmp eax, {value}")
            a.e("    je __rt_is_knowledge_start_yes")
        a.e("    cmp eax, 195")  # UTF-8 C3
        a.e("    jne __rt_is_knowledge_start_no")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}+2]")
        for value in (159, 164, 182, 188):  # ß ä ö ü UTF-8 tails
            a.e(f"    cmp eax, {value}")
            a.e("    je __rt_is_knowledge_start_yes")
        a.e("    jmp __rt_is_knowledge_start_no")
        a.l("__rt_is_knowledge_start_yes")
        a.e("    mov eax, 1")
        a.e("    jmp __rt_is_knowledge_start_done")
        a.l("__rt_is_knowledge_start_no")
        a.e("    xor eax, eax")
        a.l("__rt_is_knowledge_start_done")
        self._epilogue(a, save=(ar.si,))
        a.e()

        # Parse a string expression made from string literals and/or previously
        # loaded named string values, joined with '+'.  Result is a transient
        # NODE_STRING handle. On failure parse_pos is restored.
        a.l("__rt_parse_knowledge_string_expr")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e("    mov esi, dword ptr [__prolog_parse_pos]")
        a.e("    xor ebx, ebx")  # concatenated byte length
        self._arena_to(a, ar.di, KNOWLEDGE_CONCAT_OFF)
        a.e("    xor eax, eax")
        a.e(f"    mov byte ptr [{ar.di}], al")
        a.l("__rt_parse_knowledge_string_operand")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 34")
        a.e("    je __rt_parse_knowledge_string_literal")
        a.e("    cmp eax, 95")
        a.e("    jne __rt_parse_knowledge_string_fail")
        a.e("    call __rt_is_knowledge_start")
        a.e("    test eax, eax")
        a.e("    je __rt_parse_knowledge_string_fail")
        # Parse and normalize _name token, then intern the name without '_'.
        a.e("    call __rt_parse_token")
        a.e("    cmp ecx, 2")
        a.e("    jb __rt_parse_knowledge_string_fail")
        a.e("    dec ecx")
        if ar.is64:
            a.e("    inc rax")
            a.e("    push rcx")
            a.e("    push rax")
        else:
            a.e("    inc eax")
            a.e("    push ecx")
            a.e("    push eax")
        a.e("    call __rt_intern_atom")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    push eax")
        a.e("    call __rt_db_lookup_knowledge_string")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_parse_knowledge_string_fail")
        a.e("    jmp __rt_parse_knowledge_string_append")

        a.l("__rt_parse_knowledge_string_literal")
        a.e("    call __rt_parse_term")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_knowledge_string_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_term_cstr")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    test edx, edx")
        a.e("    je __rt_parse_knowledge_string_fail")

        a.l("__rt_parse_knowledge_string_append")
        a.e(f"    {ar.push_reg32('ebx')}")
        if ar.is64:
            a.e("    push rax")
        else:
            a.e("    push eax")
        a.e("    call __rt_knowledge_concat_append")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    test edx, edx")
        a.e("    je __rt_parse_knowledge_string_fail")
        a.e("    mov ebx, eax")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 43")  # '+'
        a.e("    jne __rt_parse_knowledge_string_finish")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    jmp __rt_parse_knowledge_string_operand")

        a.l("__rt_parse_knowledge_string_finish")
        self._arena_to(a, ar.di, KNOWLEDGE_CONCAT_OFF)
        if ar.is64:
            a.e("    push rbx")
            a.e("    push rdi")
        else:
            a.e("    push ebx")
            a.e("    push edi")
        a.e("    call __rt_intern_atom")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    push eax")
        a.e("    call __rt_make_string")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_parse_knowledge_string_done")
        a.l("__rt_parse_knowledge_string_fail")
        a.e("    mov dword ptr [__prolog_parse_pos], esi")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_knowledge_string_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        a.l("__rt_parse_knowledge_assignment")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e("    mov ebx, dword ptr [__prolog_parse_pos]")  # restore point
        a.e("    call __rt_parse_skip_ws")
        a.e("    call __rt_is_knowledge_start")
        a.e("    test eax, eax")
        a.e("    je __rt_parse_knowledge_fail")
        a.e("    call __rt_parse_token")
        # AX points at normalized TOKEN and ECX is token length. Intern without '_'.
        a.e("    cmp ecx, 2")
        a.e("    jb __rt_parse_knowledge_fail")
        a.e("    dec ecx")
        if ar.is64:
            a.e("    inc rax")
            a.e("    push rcx")
            a.e("    push rax")
        else:
            a.e("    inc eax")
            a.e("    push ecx")
            a.e("    push eax")
        a.e("    call __rt_intern_atom")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov edi, eax")  # name atom id
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 61")  # '='
        a.e("    jne __rt_parse_knowledge_fail")
        # Exclude == and =< from assignment syntax.
        self._arena_to(a, ar.si, INPUT_OFF)
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}+1]")
        a.e("    cmp eax, 61")
        a.e("    je __rt_parse_knowledge_fail")
        a.e("    cmp eax, 60")
        a.e("    je __rt_parse_knowledge_fail")
        a.e("    inc dword ptr [__prolog_parse_pos]")

        # A string literal or named string reference uses the Stage-58
        # materializer. Other RHS terms keep the Stage-56 generic parser.
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 34")
        a.e("    je __rt_parse_knowledge_string_required")
        a.e("    cmp eax, 95")
        a.e("    jne __rt_parse_knowledge_generic_rhs")
        a.e("    call __rt_is_knowledge_start")
        a.e("    test eax, eax")
        a.e("    je __rt_parse_knowledge_generic_rhs")
        a.l("__rt_parse_knowledge_string_required")
        a.e("    call __rt_parse_knowledge_string_expr")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_knowledge_fail")
        a.e("    mov esi, eax")
        a.e("    jmp __rt_parse_knowledge_build")

        a.l("__rt_parse_knowledge_generic_rhs")
        a.e(f"    {ar.push_reg32('edi')}")  # preserve name atom id
        a.e("    call __rt_parse_disjunction")
        a.e(f"    pop {ar.di}")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_knowledge_fail")
        a.e("    mov esi, eax")  # RHS handle

        a.l("__rt_parse_knowledge_build")
        # Build the name atom node then d64_knowledge_value(Name,RHS).
        a.e("    push edi")
        a.e("    call __rt_make_atom")
        a.e(f"    {ar.cleanup(1)}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    push {self.atom_id('d64_knowledge_value')}")
        a.e("    call __rt_make_binary_term")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    jmp __rt_parse_knowledge_done")
        a.l("__rt_parse_knowledge_fail")
        a.e("    mov dword ptr [__prolog_parse_pos], ebx")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_knowledge_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    def _emit_atom_intern(self, a: _A) -> None:
        ar = self.arch
        a.l("__rt_intern_atom")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        if ar.is64:
            a.e(f"    mov rsi, {ar.arg(0,'qword')}")
        else:
            a.e(f"    mov esi, {ar.arg(0)}")
        a.e(f"    mov ebx, {ar.arg(1)}")
        # static scan
        a.e("    xor ecx, ecx")
        a.l("__rt_intern_static_loop")
        a.e(f"    cmp ecx, {len(self.atom_ids)}")
        a.e("    jae __rt_intern_dynamic_scan")
        a.e(f"    {ar.push_reg32('ecx')}")  # preserve scan index below call arguments
        if ar.is64:
            a.e("    mov rdi, __prolog_static_atom_table")
            a.e("    mov rax, qword ptr [rdi+rcx*8]")
            a.e("    push rax")
        else:
            a.e("    mov edi, __prolog_static_atom_table")
            a.e("    mov eax, dword ptr [edi+ecx*4]")
            a.e("    push eax")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {'push rsi' if ar.is64 else 'push esi'}")
        a.e("    call __rt_token_eq")
        a.e(f"    {ar.cleanup(3)}")
        a.e(f"    pop {ar.cx}")
        a.e("    test eax, eax")
        a.e("    jne __rt_intern_static_found")
        a.e("    inc ecx")
        a.e("    jmp __rt_intern_static_loop")
        a.l("__rt_intern_static_found")
        a.e("    lea eax, [ecx+1]")
        a.e("    jmp __rt_intern_done")
        # dynamic scan
        a.l("__rt_intern_dynamic_scan")
        a.e("    xor ecx, ecx")
        a.l("__rt_intern_dynamic_loop")
        a.e("    cmp ecx, dword ptr [__prolog_dyn_atom_count]")
        a.e("    jae __rt_intern_create")
        a.e(f"    {ar.push_reg32('ecx')}")  # preserve dynamic scan index
        self._arena_to(a, ar.di, DYN_ATOM_TABLE_OFF)
        if ar.is64:
            a.e("    mov rax, qword ptr [rdi+rcx*8]")
            a.e("    push rax")
        else:
            a.e("    mov eax, dword ptr [edi+ecx*4]")
            a.e("    push eax")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {'push rsi' if ar.is64 else 'push esi'}")
        a.e("    call __rt_token_eq")
        a.e(f"    {ar.cleanup(3)}")
        a.e(f"    pop {ar.cx}")
        a.e("    test eax, eax")
        a.e("    jne __rt_intern_dynamic_found")
        a.e("    inc ecx")
        a.e("    jmp __rt_intern_dynamic_loop")
        a.l("__rt_intern_dynamic_found")
        a.e(f"    add ecx, {len(self.atom_ids)+1}")
        a.e("    mov eax, ecx")
        a.e("    jmp __rt_intern_done")
        a.l("__rt_intern_create")
        a.e(f"    cmp ecx, {DYN_ATOM_COUNT_MAX}")
        a.e("    jae __rt_intern_fail")
        # destination = atom pool + atom_pool_top
        self._arena_to(a, ar.di, ATOM_POOL_OFF)
        a.e("    mov edx, dword ptr [__prolog_atom_pool_top]")
        a.e("    mov eax, edx")
        a.e("    add eax, ebx")
        a.e("    inc eax")
        a.e(f"    cmp eax, {ATOM_POOL_SIZE}")
        a.e("    jae __rt_intern_fail")
        a.e(f"    add {ar.di}, {ar.dx}")
        # save destination ptr
        if ar.is64:
            a.e("    push rdi")
        else:
            a.e("    push edi")
        a.e("    xor eax, eax")
        a.l("__rt_intern_copy_loop")
        a.e("    cmp eax, ebx")
        a.e("    jae __rt_intern_copy_done")
        a.e(f"    movzx edx, byte ptr [{ar.si}+{ar.ax}]")
        a.e(f"    mov byte ptr [{ar.di}+{ar.ax}], dl")
        a.e("    inc eax")
        a.e("    jmp __rt_intern_copy_loop")
        a.l("__rt_intern_copy_done")
        a.e("    xor edx, edx")
        a.e(f"    mov byte ptr [{ar.di}+{ar.ax}], dl")
        a.e("    inc eax")
        a.e("    add dword ptr [__prolog_atom_pool_top], eax")
        # store destination in dynamic table at current count
        a.e(f"    pop {ar.si}")
        a.e("    mov ecx, dword ptr [__prolog_dyn_atom_count]")
        self._arena_to(a, ar.di, DYN_ATOM_TABLE_OFF)
        if ar.is64:
            a.e("    mov qword ptr [rdi+rcx*8], rsi")
        else:
            a.e("    mov dword ptr [edi+ecx*4], esi")
        a.e("    inc dword ptr [__prolog_dyn_atom_count]")
        a.e(f"    add ecx, {len(self.atom_ids)+1}")
        a.e("    mov eax, ecx")
        a.e("    jmp __rt_intern_done")
        a.l("__rt_intern_fail")
        a.e("    xor eax, eax")
        a.l("__rt_intern_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    def _emit_query_var_parser(self, a: _A) -> None:
        ar = self.arch
        # query_var(token_ptr,len) -> node index; copies name to qname pool.
        a.l("__rt_query_var")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        if ar.is64:
            a.e(f"    mov rsi, {ar.arg(0,'qword')}")
        else:
            a.e(f"    mov esi, {ar.arg(0)}")
        a.e(f"    mov ebx, {ar.arg(1)}")
        a.e("    xor edx, edx")
        a.l("__rt_query_var_scan")
        # __rt_token_eq uses ECX as its character index. Compare against the
        # live table count in memory so a failed name comparison cannot corrupt
        # the variable-table scan bound.
        a.e("    cmp edx, dword ptr [__prolog_query_var_count]")
        a.e("    jae __rt_query_var_new")
        a.e(f"    {ar.push_reg32('edx')}")  # preserve variable-table index
        self._arena_to(a, ar.di, QUERY_NAME_OFF)
        if ar.is64:
            a.e("    mov rax, qword ptr [rdi+rdx*8]")
            a.e("    push rax")
        else:
            a.e("    mov eax, dword ptr [edi+edx*4]")
            a.e("    push eax")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {'push rsi' if ar.is64 else 'push esi'}")
        a.e("    call __rt_token_eq")
        a.e(f"    {ar.cleanup(3)}")
        a.e(f"    pop {ar.dx}")
        a.e("    test eax, eax")
        a.e("    jne __rt_query_var_found")
        a.e("    inc edx")
        a.e("    jmp __rt_query_var_scan")
        a.l("__rt_query_var_found")
        self._arena_to(a, ar.di, QUERY_NODE_OFF)
        a.e(f"    mov eax, dword ptr [{ar.di}+{ar.dx}*4]")
        a.e("    jmp __rt_query_var_done")
        a.l("__rt_query_var_new")
        a.e("    mov ecx, dword ptr [__prolog_query_var_count]")
        a.e(f"    cmp ecx, {QUERY_VAR_MAX}")
        a.e("    jae __rt_query_var_fail")
        # allocate unbound var directly; preserve query variable index.
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_new_node")
        a.e(f"    pop {ar.cx}")
        a.e("    mov edx, eax")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_VAR}")
        a.e(f"    mov dword ptr [{ar.di}+4], edx")
        self._arena_to(a, ar.di, QUERY_NODE_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], edx")
        # copy name into qname pool
        self._arena_to(a, ar.di, QNAME_OFF)
        a.e("    mov eax, dword ptr [__prolog_qname_top]")
        a.e(f"    add {ar.di}, {ar.ax}")
        if ar.is64:
            a.e("    push rdi")
        else:
            a.e("    push edi")
        a.e("    xor eax, eax")
        a.l("__rt_query_var_copy")
        a.e("    cmp eax, ebx")
        a.e("    jae __rt_query_var_copy_done")
        a.e(f"    movzx edx, byte ptr [{ar.si}+{ar.ax}]")
        a.e(f"    mov byte ptr [{ar.di}+{ar.ax}], dl")
        a.e("    inc eax")
        a.e("    jmp __rt_query_var_copy")
        a.l("__rt_query_var_copy_done")
        a.e("    xor edx, edx")
        a.e(f"    mov byte ptr [{ar.di}+{ar.ax}], dl")
        a.e("    inc eax")
        a.e("    add dword ptr [__prolog_qname_top], eax")
        a.e(f"    pop {ar.si}")
        self._arena_to(a, ar.di, QUERY_NAME_OFF)
        if ar.is64:
            a.e("    mov qword ptr [rdi+rcx*8], rsi")
        else:
            a.e("    mov dword ptr [edi+ecx*4], esi")
        a.e("    inc dword ptr [__prolog_query_var_count]")
        self._arena_to(a, ar.di, QUERY_NODE_OFF)
        a.e(f"    mov eax, dword ptr [{ar.di}+{ar.cx}*4]")
        a.e("    jmp __rt_query_var_done")
        a.l("__rt_query_var_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_query_var_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    def _emit_db_parser_var(self, a: _A) -> None:
        ar = self.arch
        # Separate variable table for clauses loaded from external databases.
        # This avoids clobbering the active REPL/query variable table while
        # database_open/.. parses facts and rules during a running query.
        a.l("__rt_db_parser_var")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        if ar.is64:
            a.e(f"    mov rsi, {ar.arg(0,'qword')}")
        else:
            a.e(f"    mov esi, {ar.arg(0)}")
        a.e(f"    mov ebx, {ar.arg(1)}")
        a.e("    xor edx, edx")
        a.l("__rt_db_parser_var_scan")
        # The token comparator clobbers ECX. Reload/compare the authoritative
        # count from memory on every scan iteration so repeated variables in
        # externally loaded rules retain identity.
        a.e("    cmp edx, dword ptr [__prolog_db_parser_var_count]")
        a.e("    jae __rt_db_parser_var_new")
        a.e(f"    {ar.push_reg32('edx')}")
        self._arena_to(a, ar.di, PARSER_VAR_NAME_OFF)
        if ar.is64:
            a.e("    mov rax, qword ptr [rdi+rdx*8]")
            a.e("    push rax")
        else:
            a.e("    mov eax, dword ptr [edi+edx*4]")
            a.e("    push eax")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {'push rsi' if ar.is64 else 'push esi'}")
        a.e("    call __rt_token_eq")
        a.e(f"    {ar.cleanup(3)}")
        a.e(f"    pop {ar.dx}")
        a.e("    test eax, eax")
        a.e("    jne __rt_db_parser_var_found")
        a.e("    inc edx")
        a.e("    jmp __rt_db_parser_var_scan")
        a.l("__rt_db_parser_var_found")
        self._arena_to(a, ar.di, PARSER_VAR_NODE_OFF)
        a.e(f"    mov eax, dword ptr [{ar.di}+{ar.dx}*4]")
        a.e("    jmp __rt_db_parser_var_done")
        a.l("__rt_db_parser_var_new")
        a.e("    mov ecx, dword ptr [__prolog_db_parser_var_count]")
        a.e(f"    cmp ecx, {QUERY_VAR_MAX}")
        a.e("    jae __rt_db_parser_var_fail")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e("    call __rt_new_node")
        a.e(f"    pop {ar.cx}")
        a.e("    mov edx, eax")
        a.e(f"    mov dword ptr [{ar.di}], {NODE_VAR}")
        a.e(f"    mov dword ptr [{ar.di}+4], edx")
        self._arena_to(a, ar.di, PARSER_VAR_NODE_OFF)
        a.e(f"    mov dword ptr [{ar.di}+{ar.cx}*4], edx")
        # Copy the name to the database parser's private name pool.
        self._arena_to(a, ar.di, DB_PARSER_NAME_POOL_OFF)
        a.e("    mov eax, dword ptr [__prolog_db_parser_name_top]")
        a.e("    mov edx, eax")
        a.e("    add eax, ebx")
        a.e("    inc eax")
        a.e(f"    cmp eax, {DB_PARSER_NAME_POOL_SIZE}")
        a.e("    jae __rt_db_parser_var_fail")
        a.e(f"    add {ar.di}, {ar.dx}")
        if ar.is64:
            a.e("    push rdi")
        else:
            a.e("    push edi")
        a.e("    xor eax, eax")
        a.l("__rt_db_parser_var_copy")
        a.e("    cmp eax, ebx")
        a.e("    jae __rt_db_parser_var_copy_done")
        a.e(f"    movzx edx, byte ptr [{ar.si}+{ar.ax}]")
        a.e(f"    mov byte ptr [{ar.di}+{ar.ax}], dl")
        a.e("    inc eax")
        a.e("    jmp __rt_db_parser_var_copy")
        a.l("__rt_db_parser_var_copy_done")
        a.e("    xor edx, edx")
        a.e(f"    mov byte ptr [{ar.di}+{ar.ax}], dl")
        a.e("    inc eax")
        a.e("    add dword ptr [__prolog_db_parser_name_top], eax")
        a.e(f"    pop {ar.si}")
        self._arena_to(a, ar.di, PARSER_VAR_NAME_OFF)
        if ar.is64:
            a.e("    mov qword ptr [rdi+rcx*8], rsi")
        else:
            a.e("    mov dword ptr [edi+ecx*4], esi")
        a.e("    inc dword ptr [__prolog_db_parser_var_count]")
        self._arena_to(a, ar.di, PARSER_VAR_NODE_OFF)
        a.e(f"    mov eax, dword ptr [{ar.di}+{ar.cx}*4]")
        a.e("    jmp __rt_db_parser_var_done")
        a.l("__rt_db_parser_var_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_db_parser_var_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

    def _emit_parse_term(self, a: _A) -> None:
        ar = self.arch
        # parse_term -> EAX node or INVALID
        a.l("__rt_parse_term")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e("    call __rt_parse_skip_ws")
        # parenthesized expression / list / cut atom
        a.e("    cmp eax, 40")
        a.e("    je __rt_parse_term_paren")
        a.e("    cmp eax, 91")
        a.e("    je __rt_parse_term_list")
        a.e("    cmp eax, 33")
        a.e("    je __rt_parse_term_cut")
        # string/quoted atom
        a.e("    cmp eax, 34")
        a.e("    je __rt_parse_term_string")
        a.e("    cmp eax, 39")
        a.e("    je __rt_parse_term_quoted")
        # integer sign/digit
        a.e("    cmp eax, 45")
        a.e("    je __rt_parse_term_number")
        a.e("    cmp eax, 48")
        a.e("    jb __rt_parse_term_identifier")
        a.e("    cmp eax, 57")
        a.e("    jbe __rt_parse_term_number")
        # variable/atom identifier
        a.l("__rt_parse_term_identifier")
        a.e("    cmp eax, 65")
        a.e("    jb __rt_parse_term_fail")
        a.e("    cmp eax, 90")
        a.e("    jbe __rt_parse_term_variable")
        a.e("    cmp eax, 95")
        a.e("    je __rt_parse_term_variable")
        a.e("    cmp eax, 97")
        a.e("    jb __rt_parse_term_fail")
        a.e("    cmp eax, 122")
        a.e("    jbe __rt_parse_term_atom")
        a.e("    cmp eax, 128")
        a.e("    jae __rt_parse_term_atom")
        a.e("    jmp __rt_parse_term_fail")

        a.l("__rt_parse_term_paren")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_rule_expr")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_term_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        self._call1_imm(a, "__rt_parse_consume", 41)
        a.e(f"    pop {ar.cx}")
        a.e("    test eax, eax")
        a.e("    je __rt_parse_term_fail")
        a.e("    mov eax, ecx")
        a.e("    jmp __rt_parse_term_done")

        a.l("__rt_parse_term_cut")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    push {self.atom_id('!')}")
        a.e("    call __rt_make_atom")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_parse_term_done")

        a.l("__rt_parse_term_variable")
        a.e("    call __rt_parse_token")
        # AX ptr, ECX len
        if ar.is64:
            a.e("    push rcx")
            a.e("    push rax")
        else:
            a.e("    push ecx")
            a.e("    push eax")
        a.e("    cmp dword ptr [__prolog_parser_db_mode], 0")
        a.e("    jne __rt_parse_term_variable_db")
        a.e("    call __rt_query_var")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    jmp __rt_parse_term_done")
        a.l("__rt_parse_term_variable_db")
        a.e("    call __rt_db_parser_var")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    jmp __rt_parse_term_done")

        a.l("__rt_parse_term_atom")
        a.e("    call __rt_parse_token")
        if ar.is64:
            a.e("    push rcx")
            a.e("    push rax")
        else:
            a.e("    push ecx")
            a.e("    push eax")
        a.e("    call __rt_intern_atom")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ebx, eax")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 40")
        a.e("    jne __rt_parse_term_atom_simple")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_args")
        # eax first link, ecx arity
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_make_struct")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    jmp __rt_parse_term_done")
        a.l("__rt_parse_term_atom_simple")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_make_atom")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_parse_term_done")

        # Parse integer or floating literal.  strtod is used only after the
        # native scanner has established the token boundary; this keeps the
        # REPL's strict trailing-token checks intact while providing full
        # IEEE-754 decimal conversion (including scientific notation).
        a.l("__rt_parse_term_number")
        self._arena_to(a, ar.si, INPUT_OFF)
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    {ar.push_reg32('ecx')}")  # original token start
        a.e("    xor ebx, ebx")
        a.e("    xor edx, edx") # sign flag for integer path
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e("    cmp eax, 45")
        a.e("    jne __rt_parse_number_loop")
        a.e("    mov edx, 1")
        a.e("    inc ecx")
        a.l("__rt_parse_number_loop")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e("    cmp eax, 48")
        a.e("    jb __rt_parse_number_integer_end")
        a.e("    cmp eax, 57")
        a.e("    ja __rt_parse_number_integer_end")
        a.e("    mov edi, ebx")
        a.e("    shl ebx, 3")
        a.e("    shl edi, 1")
        a.e("    add ebx, edi")
        a.e("    sub eax, 48")
        a.e("    add ebx, eax")
        a.e("    inc ecx")
        a.e("    jmp __rt_parse_number_loop")
        a.l("__rt_parse_number_integer_end")
        a.e("    xor edi, edi") # float flag

        # Fraction: decimal point is part of a number only if followed by digit.
        a.e("    cmp eax, 46")
        a.e("    jne __rt_parse_number_exp_check")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}+1]")
        a.e("    cmp eax, 48")
        a.e("    jb __rt_parse_number_exp_check")
        a.e("    cmp eax, 57")
        a.e("    ja __rt_parse_number_exp_check")
        a.e("    mov edi, 1")
        a.e("    inc ecx")
        a.l("__rt_parse_number_frac_loop")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e("    cmp eax, 48")
        a.e("    jb __rt_parse_number_exp_check")
        a.e("    cmp eax, 57")
        a.e("    ja __rt_parse_number_exp_check")
        a.e("    inc ecx")
        a.e("    jmp __rt_parse_number_frac_loop")

        # Optional exponent. It is consumed only when at least one digit exists.
        a.l("__rt_parse_number_exp_check")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e("    cmp eax, 101")
        a.e("    je __rt_parse_number_exp_candidate")
        a.e("    cmp eax, 69")
        a.e("    jne __rt_parse_number_finish")
        a.l("__rt_parse_number_exp_candidate")
        a.e("    mov eax, ecx")
        a.e("    inc eax")
        a.e(f"    movzx ebx, byte ptr [{ar.si}+{ar.ax}]")
        a.e("    cmp ebx, 43")
        a.e("    je __rt_parse_number_exp_sign")
        a.e("    cmp ebx, 45")
        a.e("    jne __rt_parse_number_exp_digit_check")
        a.l("__rt_parse_number_exp_sign")
        a.e("    inc eax")
        a.e(f"    movzx ebx, byte ptr [{ar.si}+{ar.ax}]")
        a.l("__rt_parse_number_exp_digit_check")
        a.e("    cmp ebx, 48")
        a.e("    jb __rt_parse_number_finish")
        a.e("    cmp ebx, 57")
        a.e("    ja __rt_parse_number_finish")
        a.e("    mov edi, 1")
        a.e("    mov ecx, eax")
        a.l("__rt_parse_number_exp_loop")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}]")
        a.e("    cmp eax, 48")
        a.e("    jb __rt_parse_number_finish")
        a.e("    cmp eax, 57")
        a.e("    ja __rt_parse_number_finish")
        a.e("    inc ecx")
        a.e("    jmp __rt_parse_number_exp_loop")

        a.l("__rt_parse_number_finish")
        a.e("    mov dword ptr [__prolog_parse_pos], ecx")
        a.e("    test edi, edi")
        a.e("    jne __rt_parse_number_float")
        a.e(f"    pop {ar.ax}") # discard original start
        a.e("    test edx, edx")
        a.e("    je __rt_parse_number_emit_int")
        a.e("    neg ebx")
        a.l("__rt_parse_number_emit_int")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_make_int")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_parse_term_done")

        a.l("__rt_parse_number_float")
        a.e(f"    pop {ar.ax}") # start offset
        # SI is still INPUT base; advance to token start for strtod.
        a.e(f"    add {ar.si}, {ar.ax}")
        if ar.is64:
            a.e("    mov rcx, rsi")
            a.e("    xor edx, edx")
            # parse_term saves RBX/RSI/RDI, also leaving RSP 8 mod 16.
            a.e("    sub rsp, 40")
            a.e("    call __prolog_strtod")
            a.e("    add rsp, 40")
            a.e("    call __rt_make_float_from_xmm0")
        else:
            a.e("    push 0")
            a.e("    push esi")
            a.e("    call __prolog_strtod")
            a.e("    add esp, 8")
            a.e("    call __rt_make_float_from_st0")
        a.e("    jmp __rt_parse_term_done")

        # quoted/string token parser shared, quote char in EBX, tag path.
        a.l("__rt_parse_term_string")
        a.e("    mov ebx, 34")
        a.e("    mov edx, 1") # string flag
        a.e("    jmp __rt_parse_quoted_common")
        a.l("__rt_parse_term_quoted")
        a.e("    mov ebx, 39")
        a.e("    xor edx, edx")
        a.l("__rt_parse_quoted_common")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    {ar.push_reg32('edx')}")  # preserve string/atom flag
        self._arena_to(a, ar.si, INPUT_OFF)
        self._arena_to(a, ar.di, TOKEN_OFF)
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e("    xor eax, eax") # length
        a.l("__rt_parse_quoted_loop")
        a.e(f"    movzx edx, byte ptr [{ar.si}+{ar.cx}]")
        a.e("    test edx, edx")
        a.e("    je __rt_parse_quoted_unclosed")
        a.e("    cmp edx, ebx")
        a.e("    je __rt_parse_quoted_done")
        a.e(f"    mov byte ptr [{ar.di}+{ar.ax}], dl")
        a.e("    inc eax")
        a.e("    inc ecx")
        a.e("    jmp __rt_parse_quoted_loop")
        a.l("__rt_parse_quoted_unclosed")
        a.e(f"    pop {ar.dx}")
        a.e("    jmp __rt_parse_term_fail")
        a.l("__rt_parse_quoted_done")
        a.e("    inc ecx")
        a.e("    mov dword ptr [__prolog_parse_pos], ecx")
        a.e("    xor ecx, ecx")
        a.e(f"    mov byte ptr [{ar.di}+{ar.ax}], cl")
        # intern token: AX currently length; restore string/atom flag from stack.
        a.e("    mov ecx, eax")
        a.e(f"    pop {ar.dx}")
        a.e(f"    {ar.push_reg32('edx')}")
        if ar.is64:
            a.e("    push rcx")
            a.e("    push rdi")
        else:
            a.e("    push ecx")
            a.e("    push edi")
        a.e("    call __rt_intern_atom")
        a.e(f"    {ar.cleanup(2)}")
        a.e(f"    pop {ar.dx}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    test edx, edx")
        a.e("    je __rt_parse_quoted_make_atom")
        a.e("    call __rt_make_string")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_parse_term_done")
        a.l("__rt_parse_quoted_make_atom")
        a.e("    call __rt_make_atom")
        a.e(f"    {ar.cleanup(1)}")
        a.e("    jmp __rt_parse_term_done")

        # list parser
        a.l("__rt_parse_term_list")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 93")
        a.e("    jne __rt_parse_list_nonempty")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_make_nil")
        a.e("    jmp __rt_parse_term_done")
        a.l("__rt_parse_list_nonempty")
        a.e("    call __rt_parse_list_elements")
        a.e("    jmp __rt_parse_term_done")

        a.l("__rt_parse_term_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_term_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # parse_args after '(' -> EAX first arg-link, ECX arity; consumes ')'
        a.l("__rt_parse_args")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 41")
        a.e("    jne __rt_parse_args_some")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    mov eax, {INVALID}")
        a.e("    xor ecx, ecx")
        a.e("    jmp __rt_parse_args_done")
        a.l("__rt_parse_args_some")
        a.e("    call __rt_parse_relation")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_args_fail")
        a.e("    mov ebx, eax")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 44")
        a.e("    jne __rt_parse_args_last")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_args")
        a.e("    mov esi, ecx")
        a.e("    mov ecx, eax")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_make_link")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ecx, esi")
        a.e("    inc ecx")
        a.e("    jmp __rt_parse_args_done")
        a.l("__rt_parse_args_last")
        a.e("    cmp eax, 41")
        a.e("    jne __rt_parse_args_fail")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    push {INVALID}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_make_link")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    mov ecx, 1")
        a.e("    jmp __rt_parse_args_done")
        a.l("__rt_parse_args_fail")
        a.e(f"    mov eax, {INVALID}")
        a.e("    xor ecx, ecx")
        a.l("__rt_parse_args_done")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # parse list elements recursively; current pointer at first item, consumes ']'
        a.l("__rt_parse_list_elements")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e("    call __rt_parse_relation")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_list_fail")
        a.e("    mov ebx, eax")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 44")
        a.e("    je __rt_parse_list_more")
        a.e("    cmp eax, 124")
        a.e("    je __rt_parse_list_tail")
        a.e("    cmp eax, 93")
        a.e("    jne __rt_parse_list_fail")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_make_nil")
        a.e("    mov ecx, eax")
        a.e("    jmp __rt_parse_list_cons")
        a.l("__rt_parse_list_more")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_list_elements")
        a.e("    mov ecx, eax")
        a.e("    jmp __rt_parse_list_cons")
        a.l("__rt_parse_list_tail")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_relation")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_list_fail")
        a.e("    mov ecx, eax")
        a.e(f"    {ar.push_reg32('ecx')}")
        self._call1_imm(a, "__rt_parse_consume", 93)
        a.e(f"    pop {ar.cx}")
        a.e("    test eax, eax")
        a.e("    je __rt_parse_list_fail")
        a.l("__rt_parse_list_cons")
        a.e(f"    {ar.push_reg32('ecx')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e("    call __rt_make_list")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    jmp __rt_parse_list_done")
        a.l("__rt_parse_list_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_list_done")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

    def _emit_parse_goal(self, a: _A) -> None:
        ar = self.arch

        # unary primary.  A '-' followed by a digit remains a signed integer
        # literal handled by parse_term; otherwise +/- become unary functors.
        a.l("__rt_parse_unary")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 43")
        a.e("    je __rt_parse_unary_plus")
        a.e("    cmp eax, 45")
        a.e("    jne __rt_parse_unary_primary")
        # if next byte is digit, let primary parse the signed literal
        self._arena_to(a, ar.si, INPUT_OFF)
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    movzx edx, byte ptr [{ar.si}+{ar.cx}+1]")
        a.e("    cmp edx, 48")
        a.e("    jb __rt_parse_unary_minus")
        a.e("    cmp edx, 57")
        a.e("    jbe __rt_parse_unary_primary")
        a.l("__rt_parse_unary_minus")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_unary")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_unary_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    push {self.atom_id('-')}")
        a.e("    call __rt_make_unary_term")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    jmp __rt_parse_unary_done")
        a.l("__rt_parse_unary_plus")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_unary")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_unary_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    push {self.atom_id('+')}")
        a.e("    call __rt_make_unary_term")
        a.e(f"    {ar.cleanup(2)}")
        a.e("    jmp __rt_parse_unary_done")
        a.l("__rt_parse_unary_primary")
        a.e("    call __rt_parse_term")
        a.e("    jmp __rt_parse_unary_done")
        a.l("__rt_parse_unary_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_unary_done")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # Numeric fraction operand.  d64 PROLOG intentionally treats a
        # literal NUMBER '/' NUMBER pair as one multiplicative operand.
        # Therefore ``1/2 / 1/2`` is parsed as ``(1/2) / (1/2)``.  General
        # symbolic division remains handled by __rt_parse_mul.
        a.l("__rt_parse_fraction")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e("    call __rt_parse_unary")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_fraction_fail")
        a.e("    mov ebx, eax")
        # Only a literal numeric node can begin the special fraction form.
        a.e("    mov eax, ebx")
        a.e("    call __rt_node_ptr")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_INT}")
        a.e("    je __rt_parse_fraction_numeric")
        a.e(f"    cmp dword ptr [{ar.di}], {NODE_FLOAT}")
        a.e("    jne __rt_parse_fraction_done")
        a.l("__rt_parse_fraction_numeric")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 47")
        a.e("    jne __rt_parse_fraction_done")
        # Save the slash position so a non-literal RHS can be left for the
        # ordinary multiplicative parser without consuming input.
        a.e("    mov esi, dword ptr [__prolog_parse_pos]")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 48")
        a.e("    jb __rt_parse_fraction_sign_check")
        a.e("    cmp eax, 57")
        a.e("    jbe __rt_parse_fraction_rhs")
        a.l("__rt_parse_fraction_sign_check")
        # A negative numeric literal is accepted as denominator too.
        a.e("    cmp eax, 45")
        a.e("    jne __rt_parse_fraction_restore")
        self._arena_to(a, ar.di, INPUT_OFF)
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    movzx eax, byte ptr [{ar.di}+{ar.cx}+1]")
        a.e("    cmp eax, 48")
        a.e("    jb __rt_parse_fraction_restore")
        a.e("    cmp eax, 57")
        a.e("    ja __rt_parse_fraction_restore")
        a.l("__rt_parse_fraction_rhs")
        a.e("    call __rt_parse_unary")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_fraction_restore")
        a.e("    mov edi, eax")
        a.e(f"    {ar.push_reg32('edi')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    push {self.atom_id('/')}")
        a.e("    call __rt_make_binary_term")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    jmp __rt_parse_fraction_exit")
        a.l("__rt_parse_fraction_restore")
        a.e("    mov dword ptr [__prolog_parse_pos], esi")
        a.l("__rt_parse_fraction_done")
        a.e("    mov eax, ebx")
        a.e("    jmp __rt_parse_fraction_exit")
        a.l("__rt_parse_fraction_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_fraction_exit")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # multiplication/division/mod precedence
        a.l("__rt_parse_mul")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e("    call __rt_parse_fraction")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_mul_fail")
        a.e("    mov ebx, eax")
        a.l("__rt_parse_mul_loop")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 42")
        a.e("    je __rt_parse_mul_star")
        a.e("    cmp eax, 47")
        a.e("    je __rt_parse_mul_slash")
        a.e("    cmp eax, 109") # m
        a.e("    jne __rt_parse_mul_done")
        # 'mod' lookahead
        self._arena_to(a, ar.si, INPUT_OFF)
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}+1]")
        a.e("    cmp eax, 111")
        a.e("    jne __rt_parse_mul_done")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}+2]")
        a.e("    cmp eax, 100")
        a.e("    jne __rt_parse_mul_done")
        a.e("    add dword ptr [__prolog_parse_pos], 3")
        a.e(f"    mov esi, {self.atom_id('mod')}")
        a.e("    jmp __rt_parse_mul_rhs")
        a.l("__rt_parse_mul_star")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    mov esi, {self.atom_id('*')}")
        a.e("    jmp __rt_parse_mul_rhs")
        a.l("__rt_parse_mul_slash")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    mov esi, {self.atom_id('/')}")
        a.l("__rt_parse_mul_rhs")
        a.e("    call __rt_parse_fraction")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_mul_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_make_binary_term")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    mov ebx, eax")
        a.e("    jmp __rt_parse_mul_loop")
        a.l("__rt_parse_mul_done")
        a.e("    mov eax, ebx")
        a.e("    jmp __rt_parse_mul_exit")
        a.l("__rt_parse_mul_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_mul_exit")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # addition/subtraction precedence
        a.l("__rt_parse_add")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e("    call __rt_parse_mul")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_add_fail")
        a.e("    mov ebx, eax")
        a.l("__rt_parse_add_loop")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 43")
        a.e("    je __rt_parse_add_plus")
        a.e("    cmp eax, 45")
        a.e("    je __rt_parse_add_minus")
        a.e("    jmp __rt_parse_add_done")
        a.l("__rt_parse_add_plus")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    mov esi, {self.atom_id('+')}")
        a.e("    jmp __rt_parse_add_rhs")
        a.l("__rt_parse_add_minus")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    mov esi, {self.atom_id('-')}")
        a.l("__rt_parse_add_rhs")
        a.e("    call __rt_parse_mul")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_add_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_make_binary_term")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    mov ebx, eax")
        a.e("    jmp __rt_parse_add_loop")
        a.l("__rt_parse_add_done")
        a.e("    mov eax, ebx")
        a.e("    jmp __rt_parse_add_exit")
        a.l("__rt_parse_add_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_add_exit")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # relation/is precedence
        a.l("__rt_parse_relation")
        self._prologue(a, save=(ar.bx, ar.si, ar.di))
        a.e("    call __rt_parse_add")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_rel_fail")
        a.e("    mov ebx, eax")
        a.e("    call __rt_parse_skip_ws")
        # 'is' word
        a.e("    cmp eax, 105") # i
        a.e("    jne __rt_parse_rel_symbol")
        self._arena_to(a, ar.si, INPUT_OFF)
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}+1]")
        a.e("    cmp eax, 115")
        a.e("    jne __rt_parse_rel_none")
        a.e("    add dword ptr [__prolog_parse_pos], 2")
        a.e(f"    mov esi, {self.atom_id('is')}")
        a.e("    jmp __rt_parse_rel_rhs")
        a.l("__rt_parse_rel_symbol")
        a.e("    cmp eax, 61")
        a.e("    je __rt_parse_rel_eq")
        a.e("    cmp eax, 92")
        a.e("    je __rt_parse_rel_ne")
        a.e("    cmp eax, 60")
        a.e("    je __rt_parse_rel_lt")
        a.e("    cmp eax, 62")
        a.e("    je __rt_parse_rel_gt")
        a.e("    jmp __rt_parse_rel_none")
        a.l("__rt_parse_rel_eq")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_skip_ws")
        a.e(f"    mov esi, {self.atom_id('=')}")
        a.e("    cmp eax, 61")
        a.e("    jne __rt_parse_rel_eq_le")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    mov esi, {self.atom_id('==')}")
        a.e("    jmp __rt_parse_rel_rhs")
        a.l("__rt_parse_rel_eq_le")
        a.e("    cmp eax, 60")
        a.e("    jne __rt_parse_rel_rhs")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    mov esi, {self.atom_id('=<')}")
        a.e("    jmp __rt_parse_rel_rhs")
        a.l("__rt_parse_rel_ne")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        self._call1_imm(a,"__rt_parse_consume",61)
        a.e("    test eax, eax")
        a.e("    je __rt_parse_rel_none")
        a.e(f"    mov esi, {self.atom_id('\\=')}")
        a.e("    jmp __rt_parse_rel_rhs")
        a.l("__rt_parse_rel_lt")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_skip_ws")
        a.e(f"    mov esi, {self.atom_id('<')}")
        a.e("    cmp eax, 61")
        a.e("    jne __rt_parse_rel_rhs")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    mov esi, {self.atom_id('=<')}")
        a.e("    jmp __rt_parse_rel_rhs")
        a.l("__rt_parse_rel_gt")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_skip_ws")
        a.e(f"    mov esi, {self.atom_id('>')}")
        a.e("    cmp eax, 61")
        a.e("    jne __rt_parse_rel_rhs")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e(f"    mov esi, {self.atom_id('>=')}")
        a.l("__rt_parse_rel_rhs")
        a.e("    call __rt_parse_add")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_rel_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    {ar.push_reg32('esi')}")
        a.e("    call __rt_make_binary_term")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    jmp __rt_parse_rel_done")
        a.l("__rt_parse_rel_none")
        a.e("    mov eax, ebx")
        a.e("    jmp __rt_parse_rel_done")
        a.l("__rt_parse_rel_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_rel_done")
        self._epilogue(a, save=(ar.bx, ar.si, ar.di))
        a.e()

        # conjunction is tighter than disjunction
        a.l("__rt_parse_conjunction")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e("    call __rt_parse_relation")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_conjunction_fail")
        a.e("    mov ebx, eax")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 44")
        a.e("    jne __rt_parse_conjunction_done")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_conjunction")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_conjunction_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    push {self.atom_id(',')}")
        a.e("    call __rt_make_binary_term")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    jmp __rt_parse_conjunction_exit")
        a.l("__rt_parse_conjunction_done")
        a.e("    mov eax, ebx")
        a.e("    jmp __rt_parse_conjunction_exit")
        a.l("__rt_parse_conjunction_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_conjunction_exit")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        a.l("__rt_parse_disjunction")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e("    call __rt_parse_conjunction")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_disjunction_fail")
        a.e("    mov ebx, eax")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 59")
        a.e("    jne __rt_parse_disjunction_done")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.e("    call __rt_parse_disjunction")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_disjunction_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    push {self.atom_id(';')}")
        a.e("    call __rt_make_binary_term")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    jmp __rt_parse_disjunction_exit")
        a.l("__rt_parse_disjunction_done")
        a.e("    mov eax, ebx")
        a.e("    jmp __rt_parse_disjunction_exit")
        a.l("__rt_parse_disjunction_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_disjunction_exit")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # Nested clause term for assert((Head :- Body)).
        a.l("__rt_parse_rule_expr")
        self._prologue(a, save=(ar.bx, ar.si))
        a.e("    call __rt_parse_disjunction")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_rule_fail")
        a.e("    mov ebx, eax")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 58")
        a.e("    jne __rt_parse_rule_done")
        self._arena_to(a, ar.si, INPUT_OFF)
        a.e("    mov ecx, dword ptr [__prolog_parse_pos]")
        a.e(f"    movzx eax, byte ptr [{ar.si}+{ar.cx}+1]")
        a.e("    cmp eax, 45")
        a.e("    jne __rt_parse_rule_done")
        a.e("    add dword ptr [__prolog_parse_pos], 2")
        a.e("    call __rt_parse_disjunction")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_rule_fail")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e(f"    {ar.push_reg32('ebx')}")
        a.e(f"    push {self.atom_id(':-')}")
        a.e("    call __rt_make_binary_term")
        a.e(f"    {ar.cleanup(3)}")
        a.e("    jmp __rt_parse_rule_exit")
        a.l("__rt_parse_rule_done")
        a.e("    mov eax, ebx")
        a.e("    jmp __rt_parse_rule_exit")
        a.l("__rt_parse_rule_fail")
        a.e(f"    mov eax, {INVALID}")
        a.l("__rt_parse_rule_exit")
        self._epilogue(a, save=(ar.bx, ar.si))
        a.e()

        # Compatibility entry used by older parser helpers.
        a.l("__rt_parse_goal")
        a.e("    jmp __rt_parse_relation")
        a.e()

    def _emit_parse_goal_list(self, a: _A) -> None:
        ar = self.arch
        # Parse the full precedence expression, then flatten only conjunction
        # into ordinary goal links; disjunction remains a ;/2 control goal.
        a.l("__rt_parse_goal_list")
        self._prologue(a)
        a.e("    call __rt_parse_disjunction")
        a.e(f"    cmp eax, {INVALID}")
        a.e("    je __rt_parse_goal_list_done")
        a.e("    push 0")
        a.e(f"    push {INVALID}")
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_goal_expr_to_chain")
        a.e(f"    {ar.cleanup(3)}")
        # optional trailing dot.  After a complete query there must be no
        # additional token.  Previously input such as ``X is 2 2 * 5.`` was
        # silently accepted as ``X is 2`` because the second literal remained
        # unread and the solver received the valid prefix.
        a.e(f"    {ar.push_reg32('eax')}")
        a.e("    call __rt_parse_skip_ws")
        a.e("    cmp eax, 46")
        a.e("    jne __rt_parse_goal_list_after_dot")
        a.e("    inc dword ptr [__prolog_parse_pos]")
        a.l("__rt_parse_goal_list_after_dot")
        a.e("    call __rt_parse_skip_ws")
        a.e("    test eax, eax")
        a.e("    je __rt_parse_goal_list_valid_end")
        # Trailing garbage means the whole interactive query is invalid.
        # Discard the chain handle and return INVALID to the REPL, which emits
        # syntax_error. instead of solving only the valid prefix.
        a.e(f"    pop {ar.cx}")
        a.e(f"    mov eax, {INVALID}")
        a.e("    jmp __rt_parse_goal_list_done")
        a.l("__rt_parse_goal_list_valid_end")
        a.e(f"    pop {ar.ax}")
        a.l("__rt_parse_goal_list_done")
        self._epilogue(a)
        a.e()

    # ------------------------------------------------------------------
    # Start / initialization / data
    # ------------------------------------------------------------------
    def _emit_init(self, a: _A, query_specs: Sequence[Tuple[str, object]]) -> None:
        ar = self.arch
        a.l("_start")
        if not self.is_gui:
            a.e("    call AllocConsole")
            a.e("    push -11")
            a.e("    call GetStdHandle")
            a.e(f"    mov {ar.mem_ptr('__prolog_stdout')}, {ar.ax}")
            a.e("    push -10")
            a.e("    call GetStdHandle")
            a.e(f"    mov {ar.mem_ptr('__prolog_stdin')}, {ar.ax}")
        # VirtualAlloc arena
        a.e("    push 4")
        a.e("    push 12288")
        a.e(f"    push {ARENA_SIZE}")
        a.e("    push 0")
        a.e("    call VirtualAlloc")
        a.e(f"    mov {ar.mem_ptr('__prolog_arena')}, {ar.ax}")
        a.e(f"    test {ar.ax}, {ar.ax}")
        a.e("    jne __prolog_init_ok")
        a.e("    call __rt_fatal")
        a.l("__prolog_init_ok")
        # Two persistent dynamic-heap semispaces.  GC copies active clauses
        # through the transient heap, flips these pointers, then releases the
        # temporary clones by restoring heap_top.
        a.e(f"    mov {ar.di}, {ar.ax}")
        if DYN_HEAP_OFF:
            a.e(f"    add {ar.di}, {DYN_HEAP_OFF}")
        a.e(f"    mov {ar.mem_ptr('__prolog_dyn_base')}, {ar.di}")
        a.e(f"    mov {ar.di}, {ar.ax}")
        a.e(f"    add {ar.di}, {DYN_ALT_OFF}")
        a.e(f"    mov {ar.mem_ptr('__prolog_dyn_alt_base')}, {ar.di}")
        a.e("    mov dword ptr [__prolog_heap_top], 0")
        a.e("    mov dword ptr [__prolog_dyn_heap_top], 0")
        a.e("    mov dword ptr [__prolog_trail_top], 0")
        a.e("    mov dword ptr [__prolog_choice_top], 0")
        a.e("    mov dword ptr [__prolog_dyn_count], 0")
        a.e("    mov dword ptr [__prolog_dyn_atom_count], 0")
        a.e("    mov dword ptr [__prolog_atom_pool_top], 0")
        a.e("    mov dword ptr [__prolog_output_top], 0")
        a.e(f"    mov dword ptr [__prolog_current_cut_barrier], {INVALID}")
        a.e(f"    mov dword ptr [__prolog_cut_active_barrier], {INVALID}")
        a.e("    mov dword ptr [__prolog_build_barrier], 0")
        a.e("    mov dword ptr [__prolog_interactive_mode], 0")
        a.e("    mov dword ptr [__prolog_stop_search], 0")
        a.e("    mov dword ptr [__prolog_requested_more], 0")
        a.e(f"    mov dword ptr [__prolog_verbose], {1 if self.verbose else 0}")
        a.e("    mov dword ptr [__prolog_db_next_id], 1")
        a.e("    mov dword ptr [__prolog_current_db], 0")
        a.e("    mov dword ptr [__prolog_db_loading], 0")
        a.e("    mov dword ptr [__prolog_parser_db_mode], 0")
        a.e("    mov dword ptr [__prolog_emit_to_file], 0")
        a.e("    mov dword ptr [__prolog_emit_file_error], 0")

        if query_specs:
            for name,_q in query_specs:
                a.e("    mov dword ptr [__prolog_heap_top], 0")
                a.e("    mov dword ptr [__prolog_trail_top], 0")
                a.e("    mov dword ptr [__prolog_choice_top], 0")
                a.e(f"    call {name}")
                a.e(f"    {ar.push_reg32('eax')}")
                a.e("    call __rt_run_query")
                a.e(f"    {ar.cleanup(1)}")
        elif not self.is_gui:
            a.e("    call __rt_repl")
        if self.is_gui:
            # show accumulated output once
            self._arena_to(a, ar.ax, OUTPUT_OFF)
            a.e("    push 0")
            a.e("    push __prolog_caption")
            a.e(f"    push {ar.ax}")
            a.e("    push 0")
            a.e("    call MessageBoxA")
        a.e("    push 0")
        a.e("    call ExitProcess")
        a.e()

    @staticmethod
    def _db_bytes(label: str, text: str) -> List[str]:
        raw = text.encode("latin-1", errors="replace") + b"\0"
        lines = [label + ":"]
        for i in range(0, len(raw), 24):
            lines.append("    db " + ", ".join(str(x) for x in raw[i:i+24]))
        return lines

    def _emit_data(self, a: _A) -> None:
        ar = self.arch
        a.e("section .data")
        a.e()
        # static atom pointer table
        a.l("__prolog_static_atom_table")
        directive = "dq" if ar.is64 else "dd"
        for key, atom_id in sorted(self.atom_ids.items(), key=lambda kv: kv[1]):
            a.e(f"    {directive} {self.atom_labels[key]}")
        a.e()
        for key, atom_id in sorted(self.atom_ids.items(), key=lambda kv: kv[1]):
            # Original spelling: keys are casefolded. Good enough for atoms;
            # source strings retain spelling by searching original term value.
            display = key
            for line in self._db_bytes(self.atom_labels[key], display):
                a.e(line)
        for (_qi,_name), label in sorted(self.qvar_labels.items()):
            # recover name from key tuple
            name = _name
            for line in self._db_bytes(label, name):
                a.e(line)
        constants = {
            "__prolog_caption":"d64 PROLOG Runtime",
            "__prolog_fmt_int":"%d",
            "__prolog_text_underscore":"_",
            "__prolog_text_nil":"[]",
            "__prolog_text_lbrack":"[",
            "__prolog_text_rbrack":"]",
            "__prolog_text_bar":" | ",
            "__prolog_text_lparen":"(",
            "__prolog_text_rparen":")",
            "__prolog_text_comma_space":", ",
            "__prolog_text_equals":" = ",
            "__prolog_text_quote":"\"",
            "__prolog_text_dot_nl":".\r\n",
            "__prolog_text_newline":"\r\n",
            "__prolog_text_true_line":"true.\r\n",
            "__prolog_text_false_line":"false.\r\n",
            "__prolog_text_prompt":"?- ",
            "__prolog_text_more_prompt":"; = weitere Lösung, ENTER = fertig: ",
            "__prolog_text_parse_error":"syntax_error.\r\n",
            "__prolog_text_repl_gui":"repl/0 ist nur im Console-Modus verfügbar.\r\n",
            "__prolog_fmt_saved_var":"_V%d",
            "__prolog_text_rule_sep":" :- ",
            "__prolog_text_knowledge_sep":" = ",
            "__prolog_text_clause_end":".\r\n",
            "__prolog_text_op_comma":" , ",
            "__prolog_text_op_semi":" ; ",
            "__prolog_text_op_eq":" = ",
            "__prolog_text_op_ne":" \\= ",
            "__prolog_text_op_strict_eq":" == ",
            "__prolog_text_op_is":" is ",
            "__prolog_text_op_lt":" < ",
            "__prolog_text_op_le":" =< ",
            "__prolog_text_op_gt":" > ",
            "__prolog_text_op_ge":" >= ",
            "__prolog_text_op_plus":" + ",
            "__prolog_text_op_minus":" - ",
            "__prolog_text_op_mul":" * ",
            "__prolog_text_op_div":" / ",
            "__prolog_text_op_mod":" mod ",
        }
        for label,text in constants.items():
            for line in self._db_bytes(label,text):
                a.e(line)
        # writable small globals. PE64 puts zero-initialized globals in .bss;
        # PE32 remains .data because that assembler currently has no BSS model.
        if ar.is64:
            a.e()
            a.e("section .bss")
            for name,size in (
                ("__prolog_arena",8),("__prolog_stdout",8),("__prolog_stdin",8),("__prolog_dyn_base",8),("__prolog_dyn_alt_base",8),("__prolog_db_file_handle",8),("__prolog_emit_file_handle",8),
            ):
                a.e(name+":")
                a.e("    resq 1")
            for name in (
                "__prolog_heap_top","__prolog_dyn_heap_top","__prolog_trail_top","__prolog_choice_top",
                "__prolog_dyn_count","__prolog_dyn_atom_count","__prolog_atom_pool_top","__prolog_output_top",
                "__prolog_query_var_count","__prolog_solution_count","__prolog_read_count","__prolog_parse_pos",
                "__prolog_qname_top","__prolog_written","__prolog_dyn_copy_var_count","__prolog_dyn_clone_var_count",
                "__prolog_current_cut_barrier","__prolog_cut_active_barrier","__prolog_build_barrier",
                "__prolog_interactive_mode","__prolog_stop_search","__prolog_requested_more","__prolog_verbose","__prolog_gc_heap_mark",
                "__prolog_db_next_id","__prolog_current_db","__prolog_db_loading","__prolog_db_file_read","__prolog_db_file_pos","__prolog_db_heap_mark",
                "__prolog_parser_db_mode","__prolog_db_parser_var_count","__prolog_db_parser_name_top","__prolog_save_var_count",
                "__prolog_emit_to_file","__prolog_emit_file_error",
            ):
                a.e(name+":")
                a.e("    resd 1")
            a.e("__prolog_format_buffer:")
            a.e("    resb 64")
        else:
            for name in ("__prolog_arena","__prolog_stdout","__prolog_stdin","__prolog_dyn_base","__prolog_dyn_alt_base","__prolog_db_file_handle","__prolog_emit_file_handle"):
                a.e(name+":")
                a.e("    dd 0")
            for name in (
                "__prolog_heap_top","__prolog_dyn_heap_top","__prolog_trail_top","__prolog_choice_top",
                "__prolog_dyn_count","__prolog_dyn_atom_count","__prolog_atom_pool_top","__prolog_output_top",
                "__prolog_query_var_count","__prolog_solution_count","__prolog_read_count","__prolog_parse_pos",
                "__prolog_qname_top","__prolog_written","__prolog_dyn_copy_var_count","__prolog_dyn_clone_var_count",
                "__prolog_current_cut_barrier","__prolog_cut_active_barrier","__prolog_build_barrier",
                "__prolog_interactive_mode","__prolog_stop_search","__prolog_requested_more","__prolog_verbose","__prolog_gc_heap_mark",
                "__prolog_db_next_id","__prolog_current_db","__prolog_db_loading","__prolog_db_file_read","__prolog_db_file_pos","__prolog_db_heap_mark",
                "__prolog_parser_db_mode","__prolog_db_parser_var_count","__prolog_db_parser_name_top","__prolog_save_var_count",
                "__prolog_emit_to_file","__prolog_emit_file_error",
            ):
                a.e(name+":")
                a.e("    dd 0")
            a.e("__prolog_format_buffer:")
            a.e("    db " + ", ".join("0" for _ in range(64)))

    def emit(self) -> str:
        a = _A()
        ar = self.arch
        a.e("bits 64" if ar.is64 else "bits 32")
        a.e()
        if self.is_gui:
            a.e('import MessageBoxA, "user32.dll", "MessageBoxA"')
        else:
            a.e('import AllocConsole, "kernel32.dll", "AllocConsole"')
            a.e('import GetStdHandle, "kernel32.dll", "GetStdHandle"')
        # File I/O is also used by the external PROLOG database runtime.
        a.e('import WriteFile, "kernel32.dll", "WriteFile"')
        a.e('import ReadFile, "kernel32.dll", "ReadFile"')
        a.e('import CreateFileA, "kernel32.dll", "CreateFileA"')
        a.e('import CloseHandle, "kernel32.dll", "CloseHandle"')
        a.e('import FlushFileBuffers, "kernel32.dll", "FlushFileBuffers"')
        a.e('import MoveFileExA, "kernel32.dll", "MoveFileExA"')
        a.e('import DeleteFileA, "kernel32.dll", "DeleteFileA"')
        a.e('import VirtualAlloc, "kernel32.dll", "VirtualAlloc"')
        a.e('import ExitProcess, "kernel32.dll", "ExitProcess"')
        a.e('import wsprintfA, "user32.dll", "wsprintfA"')
        # Direct native-ABI imports used only by the floating-point runtime.
        a.e('import __prolog_strtod, "msvcrt.dll", "strtod"')
        a.e('import __prolog_gcvt, "msvcrt.dll", "_gcvt"')
        a.e("global _start")
        a.e("entry _start")
        a.e()
        a.e("section .text")
        a.e()

        # Core helpers must exist before start calls them (labels are forward-safe,
        # ordering is for readability only).
        self._emit_runtime_core(a)
        self._emit_dynamic_db(a)
        self._emit_io(a)
        self._emit_parser(a)
        self._emit_database_runtime(a)
        self._emit_solver(a)
        self._emit_repl(a)
        self._emit_clause_builders(a)
        query_specs = self._emit_query_builders(a)
        self._emit_init(a, query_specs)
        self._emit_data(a)
        return a.render()
