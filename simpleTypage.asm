extern printf, atoi, atof

section .data

X: dq 0
Y: dq 0

argv: dq 0
fmt_int:db "%d", 10, 0
fmt_double: db "%.12f", 10, 0

global main
section .text

main:
push rbp
mov [argv], rsi

mov rbx, [argv]
mov rdi, [rbx + 8]
call atoi
mov [X], rax
mov rbx, [argv]
mov rdi, [rbx + 16]
call atof
movsd [Y], xmm0

movsd xmm0, [Y]
movsd xmm1, xmm0
mov rax, [X]
cvtsi2sd xmm0, rax
addsd xmm0, xmm1
movsd [Y], xmm0

movsd xmm0, [Y]
mov rdi, fmt_double
mov rax, 1
call printf


pop rbp
ret


