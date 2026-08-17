# PROLOG Stage 51 - Datenbank-SIGSEGV und PE32-Nullblock

## 1. SIGSEGV bei 0x004066dd

Die mit Stage 50 reproduzierte `arzt_patient.exe` stuerzte in `__rt_try_dynamic` ab.
Die alte Sequenz war sinngemaess:

```asm
mov eax, [edi+12]        ; persistenter Klausel-Handle
push ecx
mov edx, [__prolog_choice_top]
push edx
call __rt_choice_push    ; ueberschreibt EAX
push eax                 ; FEHLER: jetzt Choice-Slot statt Klausel-Handle
call __rt_dyn_clone
mov edx, eax
call __rt_node_ptr
cmp dword ptr [edi], 7   ; SIGSEGV bei INVALID-Handle
```

Stage 51 sichert den Klausel-Handle vor `__rt_choice_push` im von diesem Helper
erhaltenen DI-Register und verwendet genau diesen Wert fuer `__rt_dyn_clone`.
Ausserdem wird `INVALID` vor `__rt_node_ptr` abgefangen und `__rt_dyn_clone`
weist INVALID/out-of-range Handles selbst zurueck.

## 2. Grosser Nullblock

Stage 50 emittierte bei PE32 die nullinitialisierten Datenbanktabellen als echte
Bytes, weil der alte PE32-Assembler noch kein separates `.bss`-Modell besitzt.
Bei `arzt_patient.pl` entstand dadurch ein zusammenhaengender Nullbereich von
9.720 Bytes und eine EXE von 37.376 Bytes.

Diese Tabellen werden in Stage 51 nicht mehr in das PE32-Image geschrieben.
Sie liegen jetzt im bereits vorhandenen, von `VirtualAlloc` gelieferten Arena-
Speicher. Der Bereich `0xBC000..0xC0000` war frei und liegt direkt vor dem
Output-Puffer.

Layout:

```text
0xBC000 DB_ACTIVE       32 dwords
0xBC080 DB_IDS          32 dwords
0xBC100 DB_MODES        32 dwords
0xBC180 DB_KINDS        32 dwords
0xBC200 DB_MODIFIED     32 dwords
0xBC280 DB_FILENAMES    32 * 260 bytes
        DB_TEMP_PATH    260 bytes
        DB_OLD_PATH     260 bytes
0xBE508 Ende
0xC0000 OUTPUT beginnt
```

Es bleiben 6.904 Bytes Reserve bis zum Output-Bereich.

## 3. Ergebnis fuer das Beispiel

Mit derselben internen PE32-Toolchain:

```text
Stage 50: 37.376 Bytes, laengster Nullblock 9.720 Bytes
Stage 51: 28.160 Bytes, laengster Nullblock   511 Bytes
```

Der verbleibende kleine Nullbereich ist normales PE/File-Alignment bzw. Import-
Padding und kein reservierter PROLOG-Datenbankpuffer.

## 4. Tests

Stage 51 fuegt `tests/test_prolog_database_runtime_stage51.py` hinzu. Geprueft
werden:

- Klausel-Handle bleibt ueber `__rt_choice_push` erhalten.
- INVALID/out-of-range Handles gelangen nicht in `__rt_node_ptr`.
- DB-Metadaten liegen im VirtualAlloc-Arena-Gap.
- PE32-Beispiel hat keinen Nullblock >= 1 KiB.
- `arzt_patient.pl` linkt weiterhin als PE32 und PE32+.

Gesamter Regressionslauf: 546/546 erfolgreich.

Hinweis: Die erzeugte Windows-EXE wurde in dieser Linux-Umgebung nicht nativ
ausgefuehrt. Der alte GDB-Absturzpfad wurde anhand der reproduzierten PE32-
Maschinencodes und Symboloffsets exakt lokalisiert und korrigiert.
