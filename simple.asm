extern printf, atoi

section .data

x: dq 0
y: dq 0
result: dq 0
double_0: dq 0x3EFF75104D551D69 ; 3.0e-5

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
mov [x], rax
mov rbx, [argv]
mov rdi, [rbx + 16]
call atoi
mov [y], rax
mov rbx, [argv]
mov rdi, [rbx + 24]
call atoi
mov [result], rax

mov rax, 3
mov [x], rax
 movsd xmm0, [double_0]
movsd [y], xmm0
 movsd xmm0, [y]
movsd xmm1, xmm0
mov rax, [x]
cvtsi2sd xmm0, rax
addsd xmm0, xmm1
movsd [result], xmm0
 movsd xmm0, [result]
mov rdi, fmt_double
mov rax, 1
call printf

movsd xmm0, [result]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf

pop rbp
ret


