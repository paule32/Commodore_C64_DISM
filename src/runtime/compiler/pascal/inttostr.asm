; ---------------------------------------------------------------------------
; File:   inttostr.asm
; Target: Windows PE32 / i386
; ABI:    cdecl
;
; Pascal:
;   function IntToStr(Value: Integer): String; cdecl; external;
;
; Eingabe:
;   [ebp+8] = signed 32-bit Integer
;
; Ausgabe:
;   eax = dynamischer Pascal-String
; ---------------------------------------------------------------------------

bits 32

section .text

; Die Runtime-Funktion erzeugt aus dem temporären C-String
; einen dynamischen Pascal-String.
extern _jit_dynstring_from_cstr

; Beide Namen zeigen auf dieselbe Funktion.
; Damit funktionieren sowohl unverzierte als auch typische
; C/COFF-Symbolnamen.
global IntToStr
global _IntToStr


IntToStr:
_IntToStr:
    push ebp
    mov  ebp, esp

    ; cdecl: EBX und EDI müssen vom Callee erhalten bleiben.
    push ebx
    push edi

    ; Maximaler Integer:
    ;
    ;   -2147483648
    ;
    ; 11 Zeichen plus Nullbyte. 16 Byte reichen bequem aus.
    sub  esp, 16

    ; EDI zeigt zunächst hinter das letzte mögliche Zeichen.
    lea  edi, [esp + 15]
    mov  byte [edi], 0

    ; Eingabewert laden.
    mov  eax, [ebp + 8]

    ; BL = 0: positiv
    ; BL = 1: negativ
    xor  ebx, ebx

    test eax, eax
    jns  .magnitude_ready

    mov  bl, 1
    neg  eax

    ; Auch INT_MIN funktioniert:
    ; NEG 80000000h ergibt zwar einen Overflow-Flag,
    ; der Bitwert 80000000h entspricht aber als unsigned
    ; weiterhin dem Betrag 2147483648.

.magnitude_ready:

    ; Sonderfall 0
    test eax, eax
    jnz  .convert_digits

    dec  edi
    mov  byte [edi], '0'
    jmp  .add_sign


.convert_digits:
    mov  ecx, 10

.next_digit:
    xor  edx, edx
    div  ecx

    ; EAX = Quotient
    ; EDX = Rest 0..9
    add  dl, '0'

    dec  edi
    mov  byte [edi], dl

    test eax, eax
    jnz  .next_digit


.add_sign:
    test bl, bl
    jz   .make_pascal_string

    dec  edi
    mov  byte [edi], '-'


.make_pascal_string:
    ; _jit_dynstring_from_cstr(const char* text)
    ;
    ; Die Funktion kopiert den Stackpuffer in einen
    ; dynamischen Pascal-String.
    push edi
    call _jit_dynstring_from_cstr
    add  esp, 4

    ; EAX enthält jetzt den dynamischen String-Datenzeiger.

    add  esp, 16
    pop  edi
    pop  ebx
    pop  ebp
    ret
