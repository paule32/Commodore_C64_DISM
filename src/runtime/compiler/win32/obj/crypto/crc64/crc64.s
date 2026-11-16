	.text
	.globl	_crc64_init
_crc64_init:
LFB0:
	movl	4(%esp), %eax
	movl	$0, (%eax)
	movl	$0, 4(%eax)
	ret
LFE0:
	.globl	_crc64_update
_crc64_update:
LFB1:
	leal	-12(%esp), %esp
	movl	%ebx, (%esp)
	movl	%esi, 4(%esp)
	movl	16(%esp), %esi
	movl	20(%esp), %ebx
	movl	24(%esp), %eax
	testl	%eax, %eax
	je	L2
	movl	%edi, 8(%esp)
	leal	(%ebx,%eax), %edi
	jmp	L7
	.p2align 5
L12:
	addl	%eax, %eax
	adcl	%edx, %edx
	xorl	$-1444268397, %eax
	xorl	$1123082731, %edx
L5:
	subl	$1, %ecx
	je	L11
L6:
	testl	%edx, %edx
	js	L12
	addl	%eax, %eax
	adcl	%edx, %edx
	jmp	L5
L11:
	movl	%eax, (%esi)
	movl	%edx, 4(%esi)
	cmpl	%ebx, %edi
	je	L13
L7:
	addl	$1, %ebx
	movzbl	-1(%ebx), %eax
	movl	%eax, %edx
	sall	$24, %edx
	xorl	%eax, %eax
	xorl	(%esi), %eax
	xorl	4(%esi), %edx
	movl	$8, %ecx
	jmp	L6
L13:
	movl	8(%esp), %edi
L2:
	movl	(%esp), %ebx
	movl	4(%esp), %esi
	leal	12(%esp), %esp
	ret
LFE1:
	.globl	_crc64_final
_crc64_final:
LFB2:
	pushl	%ebp
	movl	%esp, %ebp
	movl	8(%ebp), %eax
	movl	4(%eax), %edx
	movl	(%eax), %eax
	popl	%ebp
	ret
LFE2:
	.globl	_crc64_calc
_crc64_calc:
LFB3:
	pushl	%ebp
	movl	%esp, %ebp
	subl	$20, %esp
	movl	$0, 12(%esp)
	movl	$0, 16(%esp)
	movl	12(%ebp), %eax
	movl	%eax, 8(%esp)
	movl	8(%ebp), %eax
	movl	%eax, 4(%esp)
	leal	12(%esp), %eax
	movl	%eax, (%esp)
	call	_crc64_update
	movl	12(%esp), %eax
	movl	16(%esp), %edx
	leave
	ret
LFE3:
	.section .rdata,"dr"
LC0:
	.ascii "%016llX\0"
	.text
	.globl	__jit_crc64
__jit_crc64:
LFB4:
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$28, %esp
	movl	$0, 20(%esp)
	movl	$0, 24(%esp)
	movl	48(%esp), %eax
	movl	%eax, 8(%esp)
	movl	44(%esp), %eax
	movl	%eax, 4(%esp)
	leal	20(%esp), %eax
	movl	%eax, (%esp)
	call	_crc64_update
	movl	20(%esp), %esi
	movl	24(%esp), %edi
	movl	$17, (%esp)
	call	__jit_malloc
	movl	%eax, %ebx
	testl	%eax, %eax
	je	L18
	movl	%esi, 12(%esp)
	movl	%edi, 16(%esp)
	movl	$LC0, 8(%esp)
	movl	$17, 4(%esp)
	movl	%eax, (%esp)
	call	__jit_snprintf
L18:
	movl	%ebx, %eax
	addl	$28, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	ret
LFE4:
	.section .drectve
	.ascii " -export:\"_jit_crc64\""
	.ascii " -export:\"crc64_update\""
	.ascii " -export:\"crc64_init\""
