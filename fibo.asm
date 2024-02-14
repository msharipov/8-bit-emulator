; Fills the RAM with Fibonacci's sequence starting with address at R3
; until the addition overflows
DATA    R0, 0       ; 0
DATA    R1, 1       ; 2
DATA    R2, 1       ; 4
DATA    R3, 0x40    ; 6

; Decide if R0 >= R1
COMP    R0, R1      ; 8
JAE     17          ; 9
; When R0 < R1
    ADD     R1, R0     ; 11
    ; Exit if result overflows
    JC      25         ; 12
 
    STORE   R3, R0     ; 14
    JUMP    21         ; 15
; When R0 >= R1
    ADD     R0, R1     ; 17
    ; Exit if result overflows
    JC      25         ; 18
 
    STORE   R3, R1     ; 20
    
; Update RAM counter
CLF                 ; 21
ADD     R2, R3      ; 22
; Loop back
JUMP    8           ; 23
END                 ; 25
