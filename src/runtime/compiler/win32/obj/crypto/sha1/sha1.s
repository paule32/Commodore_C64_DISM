	.text
__ZL14sha1_transformPjPKh:
LFB0:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$352, %esp
	movl	%eax, %ebx
	movl	%edx, %ecx
	movl	$0, %edx
	.p2align 6
L2:
	movzbl	(%ecx,%edx,4), %eax
	sall	$24, %eax
	movzbl	1(%ecx,%edx,4), %esi
	sall	$16, %esi
	orl	%esi, %eax
	movzbl	3(%ecx,%edx,4), %esi
	orl	%esi, %eax
	movzbl	2(%ecx,%edx,4), %esi
	sall	$8, %esi
	orl	%esi, %eax
	movl	%eax, 32(%esp,%edx,4)
	addl	$1, %edx
	cmpl	$16, %edx
	jne	L2
	leal	32(%esp), %edx
	leal	288(%esp), %ecx
	.p2align 5
L3:
	movl	52(%edx), %eax
	xorl	32(%edx), %eax
	xorl	8(%edx), %eax
	xorl	(%edx), %eax
	roll	%eax
	movl	%eax, 64(%edx)
	addl	$4, %edx
	cmpl	%ecx, %edx
	jne	L3
	movl	(%ebx), %ebp
	movl	%ebp, 8(%esp)
	movl	4(%ebx), %ecx
	movl	%ecx, 12(%esp)
	movl	8(%ebx), %edi
	movl	%edi, 16(%esp)
	movl	12(%ebx), %esi
	movl	%esi, 20(%esp)
	movl	16(%ebx), %eax
	movl	%eax, 24(%esp)
	movl	%eax, (%esp)
	movl	$0, %edx
	movl	%ebx, 28(%esp)
	jmp	L9
L15:
	movl	%edi, %ebx
	xorl	%esi, %ebx
	andl	%ecx, %ebx
	xorl	%esi, %ebx
	movl	$1518500249, 4(%esp)
	jmp	L5
L6:
	cmpl	$59, %edx
	jg	L7
	movl	%edi, %ebx
	orl	%esi, %ebx
	andl	%ecx, %ebx
	movl	%edi, %eax
	andl	%esi, %eax
	orl	%eax, %ebx
	movl	$-1894007588, 4(%esp)
L5:
	movl	%ebp, %eax
	roll	$5, %eax
	addl	32(%esp,%edx,4), %eax
	addl	%ebx, %eax
	movl	4(%esp), %ebx
	addl	%ebx, %eax
	movl	(%esp), %ebx
	addl	%ebx, %eax
	rorl	$2, %ecx
	addl	$1, %edx
L10:
	movl	%esi, (%esp)
	movl	%edi, %esi
	movl	%ecx, %edi
	movl	%ebp, %ecx
	movl	%eax, %ebp
L9:
	cmpl	$19, %edx
	jle	L15
	cmpl	$39, %edx
	jg	L6
	movl	%ecx, %ebx
	xorl	%edi, %ebx
	xorl	%esi, %ebx
	movl	$1859775393, 4(%esp)
	jmp	L5
L7:
	movl	%ebp, %ebx
	roll	$5, %ebx
	addl	32(%esp,%edx,4), %ebx
	movl	%ecx, %eax
	xorl	%edi, %eax
	xorl	%esi, %eax
	leal	-899497514(%ebx,%eax), %eax
	movl	(%esp), %ebx
	addl	%ebx, %eax
	rorl	$2, %ecx
	addl	$1, %edx
	cmpl	$80, %edx
	jne	L10
	movl	28(%esp), %ebx
	movl	8(%esp), %edx
	addl	%eax, %edx
	movl	%edx, (%ebx)
	movl	12(%esp), %eax
	addl	%ebp, %eax
	movl	%eax, 4(%ebx)
	movl	16(%esp), %eax
	addl	%ecx, %eax
	movl	%eax, 8(%ebx)
	movl	20(%esp), %eax
	addl	%edi, %eax
	movl	%eax, 12(%ebx)
	movl	24(%esp), %eax
	addl	%esi, %eax
	movl	%eax, 16(%ebx)
	addl	$352, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE0:
	.globl	_sha1_init
_sha1_init:
LFB1:
	movl	4(%esp), %eax
	movl	$0, 24(%eax)
	movl	$0, 28(%eax)
	movl	$1732584193, (%eax)
	movl	$-271733879, 4(%eax)
	movl	$-1732584194, 8(%eax)
	movl	$271733878, 12(%eax)
	movl	$-1009589776, 16(%eax)
	ret
LFE1:
	.globl	_sha1_update
_sha1_update:
LFB2:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$12, %esp
	movl	32(%esp), %edi
	movl	40(%esp), %esi
	movl	24(%edi), %ecx
	movl	28(%edi), %ebx
	movl	%ecx, %eax
	movl	%ebx, %edx
	shrdl	$3, %edx, %eax
	shrl	$3, %edx
	movl	%eax, %ebp
	andl	$63, %ebp
	movl	%esi, %eax
	movl	$0, %edx
	shldl	$3, %eax, %edx
	sall	$3, %eax
	addl	%ecx, %eax
	adcl	%ebx, %edx
	movl	%eax, 24(%edi)
	movl	%edx, 28(%edi)
	movl	$64, %ebx
	subl	%ebp, %ebx
	cmpl	%ebx, %esi
	jnb	L24
	movl	$0, %ebx
L18:
	subl	%ebx, %esi
	movl	%esi, 8(%esp)
	movl	%ebx, %eax
	addl	36(%esp), %eax
	movl	%eax, 4(%esp)
	leal	32(%edi,%ebp), %eax
	movl	%eax, (%esp)
	call	__jit_memcpy
	addl	$12, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
L24:
	movl	%ebx, 8(%esp)
	movl	36(%esp), %eax
	movl	%eax, 4(%esp)
	leal	32(%edi,%ebp), %eax
	movl	%eax, (%esp)
	call	__jit_memcpy
	leal	32(%edi), %edx
	movl	%edi, %eax
	call	__ZL14sha1_transformPjPKh
	movl	$127, %eax
	subl	%ebp, %eax
	cmpl	%esi, %eax
	jnb	L21
	movl	36(%esp), %ebp
L19:
	leal	0(%ebp,%ebx), %edx
	movl	%edi, %eax
	call	__ZL14sha1_transformPjPKh
	movl	%ebx, %eax
	addl	$64, %ebx
	addl	$127, %eax
	cmpl	%esi, %eax
	jb	L19
	movl	$0, %ebp
	jmp	L18
L21:
	movl	$0, %ebp
	jmp	L18
LFE2:
	.globl	_sha1_final
_sha1_final:
LFB3:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$20, %esp
	movl	40(%esp), %eax
	movl	28(%eax), %edx
	movl	24(%eax), %eax
	leal	19(%esp), %ebp
	movl	$0, %ecx
	.p2align 6
L26:
	movl	%eax, %esi
	movl	%edx, %edi
	shrdl	%cl, %edi, %esi
	shrl	%cl, %edi
	testb	$32, %cl
	je	L33
	movl	%edi, %esi
	xorl	%edi, %edi
L33:
	movl	%esi, %ebx
	movb	%bl, 0(%ebp)
	addl	$8, %ecx
	subl	$1, %ebp
	cmpl	$64, %ecx
	jne	L26
	shrdl	$3, %edx, %eax
	shrl	$3, %edx
	andl	$63, %eax
	movl	$56, %ecx
	subl	%eax, %ecx
	movl	$120, %edx
	subl	%eax, %edx
	cmpl	$55, %eax
	movl	%ecx, %eax
	cmova	%edx, %eax
	movl	%eax, 8(%esp)
	movl	$__ZZ10sha1_finalE7padding, 4(%esp)
	movl	40(%esp), %eax
	movl	%eax, (%esp)
	call	_sha1_update
	movl	$8, 8(%esp)
	leal	12(%esp), %eax
	movl	%eax, 4(%esp)
	movl	40(%esp), %eax
	movl	%eax, (%esp)
	call	_sha1_update
	movl	40(%esp), %eax
	movl	44(%esp), %edx
	leal	20(%eax), %ebx
L29:
	movl	(%eax), %ecx
	shrl	$24, %ecx
	movb	%cl, (%edx)
	movl	(%eax), %ecx
	shrl	$16, %ecx
	movb	%cl, 1(%edx)
	movl	(%eax), %ecx
	movb	%ch, 2(%edx)
	movl	(%eax), %ecx
	movb	%cl, 3(%edx)
	addl	$4, %eax
	addl	$4, %edx
	cmpl	%ebx, %eax
	jne	L29
	addl	$20, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE3:
	.globl	__jit_sha1
__jit_sha1:
LFB5:
	pushl	%ebp
	movl	%esp, %ebp
	pushl	%ebx
	andl	$-8, %esp
	subl	$132, %esp
	movl	$0, 60(%esp)
	movl	$0, 64(%esp)
	movl	$1732584193, 36(%esp)
	movl	$-271733879, 40(%esp)
	movl	$-1732584194, 44(%esp)
	movl	$271733878, 48(%esp)
	movl	$-1009589776, 52(%esp)
	movl	12(%ebp), %eax
	movl	%eax, 8(%esp)
	movl	8(%ebp), %eax
	movl	%eax, 4(%esp)
	leal	36(%esp), %ebx
	movl	%ebx, (%esp)
	call	_sha1_update
	leal	16(%esp), %eax
	movl	%eax, 4(%esp)
	movl	%ebx, (%esp)
	call	_sha1_final
	movl	$41, (%esp)
	call	__jit_malloc
	movl	%eax, %ebx
	testl	%eax, %eax
	je	L34
	movl	$0, %eax
	.p2align 6
L36:
	movzbl	16(%esp,%eax), %edx
	movl	%edx, %ecx
	shrb	$4, %cl
	movzbl	%cl, %ecx
	movzbl	__ZZL18bytes_to_hex_allocPKhjE3hex(%ecx), %ecx
	movb	%cl, (%ebx,%eax,2)
	andl	$15, %edx
	movzbl	__ZZL18bytes_to_hex_allocPKhjE3hex(%edx), %edx
	movb	%dl, 1(%ebx,%eax,2)
	addl	$1, %eax
	cmpl	$20, %eax
	jne	L36
	movb	$0, 40(%ebx)
L34:
	movl	%ebx, %eax
	movl	-4(%ebp), %ebx
	leave
	ret
LFE5:
	.section .rdata,"dr"
	.align 4
__ZZL18bytes_to_hex_allocPKhjE3hex:
	.ascii "0123456789abcdef\0"
	.align 32
__ZZ10sha1_finalE7padding:
	.ascii "\200\0"
	.space 62
	.section .drectve
	.ascii " -export:\"_jit_sha1\""
	.ascii " -export:\"sha1_final\""
	.ascii " -export:\"sha1_update\""
	.ascii " -export:\"sha1_init\""
