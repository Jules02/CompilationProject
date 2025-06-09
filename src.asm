extern printf, atoi, atof, malloc

section .data

X: dq 0
Y: dq 0
Z: dq 0
E: dq 0
p: dq 0, 0
ptrTst: dq 0
buf: dq 0
T: dq 0
LC0: dq 0x3DDB7CDFD9D7BDBB ; 1.0e-10

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

mov rbx, [argv]
mov rdi, [rbx + 24]
call atoi
mov [Z], rax

movsd xmm0, [LC0]

movsd [E], xmm0



lea rax, [Z]

mov [ptrTst], rax



mov rdi, 8
call malloc

mov [buf], rax

loop0:
mov rax, 3

push rax
mov rax, [X]

mov rbx, rax
pop rax
add rax, rbx
cmp rax, 0
jz end0
mov rax, 3

push rax
mov rax, [X]

mov rbx, rax
pop rax
add rax, rbx
mov [T], rax

movsd xmm0, [Y]

mov rdi, fmt_double
mov rax, 1
call printf
mov rax, [X]

push rax
mov rax, 4

mov rbx, rax
pop rax
add rax, rbx
mov [Z], rax

mov rax, [X]

push rax
mov rax, 1

mov rbx, rax
pop rax
sub rax, rbx
mov [X], rax

jmp loop0
end0: nop
mov rax, [Z]


pop rbp
ret


