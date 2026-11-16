	.text
	.align 2
	.globl	__ZNSt7ostreamC2Ev
__ZNSt7ostreamC2Ev:
LFB1:
	ret
LFE1:
	.globl	__ZNSt7ostreamC1Ev
	.set	__ZNSt7ostreamC1Ev,__ZNSt7ostreamC2Ev
	.align 2
	.globl	__ZNSt7ostreamlsEi
__ZNSt7ostreamlsEi:
LFB3:
	pushl	%ebx
	subl	$4, %esp
	movl	%ecx, %ebx
	movl	12(%esp), %eax
	movl	%eax, (%esp)
	call	__jit_print_int
	movl	%ebx, %eax
	addl	$4, %esp
	popl	%ebx
	ret	$4
LFE3:
	.align 2
	.globl	__ZNSt7ostreamlsEj
__ZNSt7ostreamlsEj:
LFB4:
	pushl	%ebx
	subl	$4, %esp
	movl	%ecx, %ebx
	movl	12(%esp), %eax
	movl	%eax, (%esp)
	call	__jit_print_int
	movl	%ebx, %eax
	addl	$4, %esp
	popl	%ebx
	ret	$4
LFE4:
	.align 2
	.globl	__ZNSt7ostreamlsEd
__ZNSt7ostreamlsEd:
LFB5:
	pushl	%ebp
	movl	%esp, %ebp
	pushl	%ebx
	andl	$-8, %esp
	subl	$8, %esp
	movl	%ecx, %ebx
	movsd	8(%ebp), %xmm0
	movsd	%xmm0, (%esp)
	call	__jit_print_double
	movl	%ebx, %eax
	movl	-4(%ebp), %ebx
	leave
	ret	$8
LFE5:
	.align 2
	.globl	__ZNSt7ostreamlsEc
__ZNSt7ostreamlsEc:
LFB6:
	pushl	%ebx
	subl	$4, %esp
	movl	%ecx, %ebx
	movsbl	12(%esp), %eax
	movl	%eax, (%esp)
	call	__jit_print_char
	movl	%ebx, %eax
	addl	$4, %esp
	popl	%ebx
	ret	$4
LFE6:
	.align 2
	.globl	__ZNSt7ostreamlsEPKc
__ZNSt7ostreamlsEPKc:
LFB7:
	pushl	%ebx
	subl	$4, %esp
	movl	%ecx, %ebx
	movl	12(%esp), %eax
	movl	%eax, (%esp)
	call	__jit_print_text
	movl	%ebx, %eax
	addl	$4, %esp
	popl	%ebx
	ret	$4
LFE7:
	.align 2
	.globl	__ZNSt7ostreamlsEPFRS_S0_E
__ZNSt7ostreamlsEPFRS_S0_E:
LFB8:
	subl	$4, %esp
	movl	%ecx, (%esp)
	call	*8(%esp)
	addl	$4, %esp
	ret	$4
LFE8:
	.globl	__ZSt4endlRSt7ostream
__ZSt4endlRSt7ostream:
LFB9:
	call	__jit_print_newline
	movl	4(%esp), %eax
	ret
LFE9:
	.globl	__ZSt4cout
	.bss
__ZSt4cout:
	.space 1
