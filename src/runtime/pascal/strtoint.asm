; ---------------------------------------------------------------------------
; File:   strtoint.asm
; Target: Windows PE32 / i386
; ABI:    cdecl
;
; Pascal:
;
;   function StrToInt(S: String): Integer; cdecl; external;
;
; Eingabe:
;   [ebp+8] = Pointer auf nullterminierten String
;
; Ausgabe:
;   eax = 32-Bit Integer
;
; Bei ungültiger Eingabe oder Überlauf:
;   eax = 0
; ---------------------------------------------------------------------------

bits 32

section .text

global StrToInt
global _StrToInt


StrToInt:
_StrToInt:
    push ebp
    mov  ebp, esp

    push ebx
    push esi
    push edi

    ; ESI = String-Datenzeiger
    mov  esi, [ebp + 8]

    ; NIL-String ergibt 0
    test esi, esi
    jz   .invalid

    ; EDI = Vorzeichen:
    ;   0 = positiv
    ;   1 = negativ
    xor  edi, edi


.skip_leading_space:
    movzx ebx, byte [esi]

    cmp  bl, ' '
    je   .skip_one_space

    cmp  bl, 9          ; TAB
    je   .skip_one_space

    cmp  bl, 10         ; LF
    je   .skip_one_space

    cmp  bl, 13         ; CR
    je   .skip_one_space

    jmp  .check_sign


.skip_one_space:
    inc  esi
    jmp  .skip_leading_space


.check_sign:
    movzx ebx, byte [esi]

    cmp  bl, '-'
    jne  .check_plus

    mov  edi, 1
    inc  esi
    jmp  .prepare_digits


.check_plus:
    cmp  bl, '+'
    jne  .prepare_digits

    inc  esi


.prepare_digits:
    ; EAX = positiver Betrag
    xor  eax, eax

    ; EDX = Anzahl gelesener Ziffern
    xor  edx, edx


.digit_loop:
    movzx ebx, byte [esi]

    cmp  bl, '0'
    jb   .digits_done

    cmp  bl, '9'
    ja   .digits_done

    sub  ebx, '0'

    ; ------------------------------------------------------------
    ; Überlaufprüfung
    ;
    ; Positiv:
    ;   maximal 2147483647
    ;
    ; Negativ:
    ;   maximaler Betrag 2147483648
    ; ------------------------------------------------------------

    cmp  eax, 214748364
    ja   .invalid

    jne  .append_digit

    ; EAX ist genau 214748364.
    ; Jetzt hängt das erlaubte letzte Zeichen vom Vorzeichen ab.

    test edi, edi
    jnz  .check_negative_last_digit

    ; Positiv darf die letzte Ziffer höchstens 7 sein.
    cmp  ebx, 7
    ja   .invalid

    jmp  .append_digit


.check_negative_last_digit:
    ; Negativ darf der Betrag bis 2147483648 gehen.
    cmp  ebx, 8
    ja   .invalid


.append_digit:
    imul eax, eax, 10
    add  eax, ebx

    inc  esi
    inc  edx

    jmp  .digit_loop


.digits_done:
    ; Mindestens eine Ziffer muss vorhanden sein.
    test edx, edx
    jz   .invalid


.skip_trailing_space:
    movzx ebx, byte [esi]

    ; Nullterminator: gültiges Ende
    test bl, bl
    jz   .apply_sign

    cmp  bl, ' '
    je   .skip_one_trailing

    cmp  bl, 9
    je   .skip_one_trailing

    cmp  bl, 10
    je   .skip_one_trailing

    cmp  bl, 13
    je   .skip_one_trailing

    ; Nicht-Leerzeichen hinter der Zahl
    jmp  .invalid


.skip_one_trailing:
    inc  esi
    jmp  .skip_trailing_space


.apply_sign:
    test edi, edi
    jz   .done

    ; Bei 2147483648 ergibt NEG den Bitwert 80000000h,
    ; also korrekt -2147483648.
    neg  eax

    jmp  .done


.invalid:
    xor  eax, eax


.done:
    pop  edi
    pop  esi
    pop  ebx

    pop  ebp
    ret
