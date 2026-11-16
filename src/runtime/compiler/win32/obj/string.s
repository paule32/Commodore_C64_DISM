	.text
	.align 2
	.globl	__ZNSt6stringC2Ev
__ZNSt6stringC2Ev:
LFB1:
	ret
LFE1:
	.globl	__ZNSt6stringC1Ev
	.set	__ZNSt6stringC1Ev,__ZNSt6stringC2Ev
	.align 2
	.globl	__ZNSt6stringC2EPKc
__ZNSt6stringC2EPKc:
LFB4:
	pushl	%ebx
	subl	$12, %esp
	movl	%ecx, %ebx
	movl	20(%esp), %eax
	movl	%eax, (%esp)
	call	__jit_strlen
	movl	%eax, 4(%ebx)
	addl	$1, %eax
	movl	%eax, (%esp)
	call	__jit_malloc
	movl	%eax, (%ebx)
	movl	4(%ebx), %edx
	addl	$1, %edx
	movl	%edx, 8(%esp)
	movl	20(%esp), %ecx
	movl	%ecx, 4(%esp)
	movl	%eax, (%esp)
	call	__jit_memcpy
	addl	$12, %esp
	popl	%ebx
	ret	$4
LFE4:
	.globl	__ZNSt6stringC1EPKc
	.set	__ZNSt6stringC1EPKc,__ZNSt6stringC2EPKc
	.align 2
	.globl	__ZNSt6stringD2Ev
__ZNSt6stringD2Ev:
LFB7:
	subl	$4, %esp
	movl	(%ecx), %eax
	movl	%eax, (%esp)
	call	__jit_free
	addl	$4, %esp
	ret
LFE7:
	.globl	__ZNSt6stringD1Ev
	.set	__ZNSt6stringD1Ev,__ZNSt6stringD2Ev
	.section .rdata,"dr"
LC0:
	.ascii "\0"
	.text
	.align 2
	.globl	__ZNKSt6string5c_strEv
__ZNKSt6string5c_strEv:
LFB9:
	movl	(%ecx), %eax
	testl	%eax, %eax
	movl	$LC0, %edx
	cmove	%edx, %eax
	ret
LFE9:
	.align 2
	.globl	__ZNKSt6string6lengthEv
__ZNKSt6string6lengthEv:
LFB10:
	movl	4(%ecx), %eax
	ret
LFE10:
	.globl	__jit_strncpy
__jit_strncpy:
LFB11:
	pushl	%esi
	pushl	%ebx
	movl	12(%esp), %ebx
	movl	16(%esp), %esi
	movl	20(%esp), %ecx
	movl	$0, %eax
	testl	%ecx, %ecx
	je	L11
	.p2align 5
L10:
	movzbl	(%esi,%eax), %edx
	testb	%dl, %dl
	je	L18
	movb	%dl, (%ebx,%eax)
	addl	$1, %eax
	cmpl	%eax, %ecx
	jne	L10
	jmp	L11
L18:
	cmpl	%ecx, %eax
	jnb	L11
	addl	%ebx, %eax
	addl	%ebx, %ecx
	.p2align 4
L13:
	movb	$0, (%eax)
	addl	$1, %eax
	cmpl	%ecx, %eax
	jne	L13
L11:
	movl	%ebx, %eax
	popl	%ebx
	popl	%esi
	ret
LFE11:
	.globl	_strlen
_strlen:
LFB12:
	subl	$4, %esp
	movl	8(%esp), %eax
	movl	%eax, (%esp)
	call	__jit_strlen
	addl	$4, %esp
	ret
LFE12:
	.section .drectve
	.ascii " -export:\"strlen\""
	.ascii " -export:\"_jit_strncpy\""
