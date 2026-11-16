	.text
__ZL16sha224_transformPjPKh:
LFB0:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$316, %esp
	movl	%eax, 32(%esp)
	movl	%edx, %ecx
	movl	$0, %edx
	.p2align 6
L2:
	movzbl	(%ecx,%edx,4), %eax
	sall	$24, %eax
	movzbl	1(%ecx,%edx,4), %ebx
	sall	$16, %ebx
	orl	%ebx, %eax
	movzbl	3(%ecx,%edx,4), %ebx
	orl	%ebx, %eax
	movzbl	2(%ecx,%edx,4), %ebx
	sall	$8, %ebx
	orl	%ebx, %eax
	movl	%eax, 60(%esp,%edx,4)
	addl	$1, %edx
	cmpl	$16, %edx
	jne	L2
	leal	60(%esp), %edx
	leal	252(%esp), %ebx
	.p2align 6
L3:
	movl	56(%edx), %ecx
	movl	4(%edx), %esi
	movl	%ecx, %eax
	roll	$15, %eax
	movl	%ecx, %edi
	roll	$13, %edi
	xorl	%edi, %eax
	shrl	$10, %ecx
	xorl	%ecx, %eax
	movl	(%edx), %ecx
	addl	36(%edx), %ecx
	addl	%ecx, %eax
	movl	%esi, %ecx
	rorl	$7, %ecx
	movl	%esi, %edi
	roll	$14, %edi
	xorl	%edi, %ecx
	shrl	$3, %esi
	xorl	%esi, %ecx
	addl	%ecx, %eax
	movl	%eax, 64(%edx)
	addl	$4, %edx
	cmpl	%ebx, %edx
	jne	L3
	movl	32(%esp), %eax
	movl	(%eax), %edx
	movl	4(%eax), %ebx
	movl	%ebx, 36(%esp)
	movl	8(%eax), %edi
	movl	%edi, 40(%esp)
	movl	12(%eax), %esi
	movl	%esi, 44(%esp)
	movl	16(%eax), %ecx
	movl	%ecx, 48(%esp)
	movl	20(%eax), %ebp
	movl	%ebp, 24(%esp)
	movl	24(%eax), %ebp
	movl	%ebp, 28(%esp)
	movl	28(%eax), %eax
	movl	%eax, 52(%esp)
	movl	%eax, %ebp
	movl	28(%esp), %eax
	movl	%eax, 4(%esp)
	movl	24(%esp), %eax
	movl	%eax, 12(%esp)
	movl	%esi, 16(%esp)
	movl	%edi, 20(%esp)
	movl	%ebx, 8(%esp)
	movl	%edx, %ebx
	movl	$0, %edi
	movl	%edx, 56(%esp)
	movl	%edi, (%esp)
	jmp	L4
L5:
	movl	12(%esp), %edi
	movl	%edi, 4(%esp)
	movl	%ecx, 12(%esp)
	movl	%esi, %ecx
	movl	8(%esp), %edi
	movl	%edi, 20(%esp)
	movl	%ebx, 8(%esp)
	movl	%eax, %ebx
L4:
	movl	%ecx, %edx
	rorl	$6, %edx
	movl	%ecx, %eax
	rorl	$11, %eax
	xorl	%edx, %eax
	movl	%ecx, %edx
	roll	$7, %edx
	xorl	%edx, %eax
	movl	(%esp), %esi
	movl	60(%esp,%esi,4), %edx
	addl	__ZL8sha224_k(,%esi,4), %edx
	addl	%edx, %eax
	movl	%ecx, %edx
	notl	%edx
	movl	4(%esp), %edi
	andl	%edi, %edx
	movl	12(%esp), %esi
	andl	%ecx, %esi
	xorl	%esi, %edx
	addl	%edx, %eax
	addl	%ebp, %eax
	movl	%ebx, %edx
	rorl	$2, %edx
	movl	%ebx, %esi
	rorl	$13, %esi
	xorl	%edx, %esi
	movl	%ebx, %edx
	roll	$10, %edx
	xorl	%edx, %esi
	movl	8(%esp), %ebp
	movl	%ebp, %edx
	movl	20(%esp), %edi
	xorl	%edi, %edx
	andl	%ebx, %edx
	andl	%edi, %ebp
	xorl	%ebp, %edx
	addl	%esi, %edx
	movl	16(%esp), %esi
	addl	%eax, %esi
	addl	%edx, %eax
	addl	$1, (%esp)
	movl	(%esp), %edx
	movl	%edi, 16(%esp)
	movl	4(%esp), %ebp
	cmpl	$64, %edx
	jne	L5
	movl	56(%esp), %edx
	addl	%edx, %eax
	movl	32(%esp), %edi
	movl	%eax, (%edi)
	movl	36(%esp), %eax
	addl	%ebx, %eax
	movl	%edi, %ebx
	movl	%eax, 4(%edi)
	movl	40(%esp), %eax
	movl	8(%esp), %edi
	addl	%edi, %eax
	movl	%eax, 8(%ebx)
	movl	44(%esp), %eax
	movl	20(%esp), %edi
	addl	%edi, %eax
	movl	%eax, 12(%ebx)
	movl	48(%esp), %eax
	addl	%esi, %eax
	movl	%eax, 16(%ebx)
	movl	24(%esp), %eax
	addl	%ecx, %eax
	movl	%eax, 20(%ebx)
	movl	28(%esp), %eax
	movl	12(%esp), %edi
	addl	%edi, %eax
	movl	%eax, 24(%ebx)
	movl	52(%esp), %eax
	addl	%ebp, %eax
	movl	%eax, 28(%ebx)
	addl	$316, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE0:
	.globl	_sha224_init
_sha224_init:
LFB1:
	movl	4(%esp), %eax
	movl	$0, 32(%eax)
	movl	$0, 36(%eax)
	movl	$-1056596264, (%eax)
	movl	$914150663, 4(%eax)
	movl	$812702999, 8(%eax)
	movl	$-150054599, 12(%eax)
	movl	$-4191439, 16(%eax)
	movl	$1750603025, 20(%eax)
	movl	$1694076839, 24(%eax)
	movl	$-1090891868, 28(%eax)
	ret
LFE1:
	.globl	_sha224_update
_sha224_update:
LFB2:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$12, %esp
	movl	32(%esp), %edi
	movl	40(%esp), %esi
	movl	32(%edi), %ecx
	movl	36(%edi), %ebx
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
	movl	%eax, 32(%edi)
	movl	%edx, 36(%edi)
	movl	$64, %ebx
	subl	%ebp, %ebx
	cmpl	%ebx, %esi
	jnb	L17
	movl	$0, %ebx
L11:
	subl	%ebx, %esi
	movl	%esi, 8(%esp)
	movl	%ebx, %eax
	addl	36(%esp), %eax
	movl	%eax, 4(%esp)
	leal	40(%edi,%ebp), %eax
	movl	%eax, (%esp)
	call	__jit_memcpy
	addl	$12, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
L17:
	movl	%ebx, 8(%esp)
	movl	36(%esp), %eax
	movl	%eax, 4(%esp)
	leal	40(%edi,%ebp), %eax
	movl	%eax, (%esp)
	call	__jit_memcpy
	leal	40(%edi), %edx
	movl	%edi, %eax
	call	__ZL16sha224_transformPjPKh
	movl	$127, %eax
	subl	%ebp, %eax
	cmpl	%esi, %eax
	jnb	L14
	movl	36(%esp), %ebp
L12:
	leal	0(%ebp,%ebx), %edx
	movl	%edi, %eax
	call	__ZL16sha224_transformPjPKh
	movl	%ebx, %eax
	addl	$64, %ebx
	addl	$127, %eax
	cmpl	%esi, %eax
	jb	L12
	movl	$0, %ebp
	jmp	L11
L14:
	movl	$0, %ebp
	jmp	L11
LFE2:
	.globl	_sha224_final
_sha224_final:
LFB3:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$20, %esp
	movl	40(%esp), %eax
	movl	36(%eax), %edx
	movl	32(%eax), %eax
	leal	19(%esp), %ebp
	movl	$0, %ecx
	.p2align 6
L19:
	movl	%eax, %esi
	movl	%edx, %edi
	shrdl	%cl, %edi, %esi
	shrl	%cl, %edi
	testb	$32, %cl
	je	L26
	movl	%edi, %esi
	xorl	%edi, %edi
L26:
	movl	%esi, %ebx
	movb	%bl, 0(%ebp)
	addl	$8, %ecx
	subl	$1, %ebp
	cmpl	$64, %ecx
	jne	L19
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
	movl	$__ZZ12sha224_finalE7padding, 4(%esp)
	movl	40(%esp), %eax
	movl	%eax, (%esp)
	call	_sha224_update
	movl	$8, 8(%esp)
	leal	12(%esp), %eax
	movl	%eax, 4(%esp)
	movl	40(%esp), %eax
	movl	%eax, (%esp)
	call	_sha224_update
	movl	40(%esp), %eax
	movl	44(%esp), %edx
	leal	28(%eax), %ebx
	.p2align 6
L22:
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
	jne	L22
	addl	$20, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE3:
	.globl	__jit_sha224
__jit_sha224:
LFB4:
	pushl	%ebp
	movl	%esp, %ebp
	pushl	%esi
	pushl	%ebx
	andl	$-8, %esp
	subl	$148, %esp
	movl	$57, (%esp)
	call	__jit_malloc
	movl	%eax, %ebx
	testl	%eax, %eax
	je	L27
	movl	$0, 76(%esp)
	movl	$0, 80(%esp)
	movl	$-1056596264, 44(%esp)
	movl	$914150663, 48(%esp)
	movl	$812702999, 52(%esp)
	movl	$-150054599, 56(%esp)
	movl	$-4191439, 60(%esp)
	movl	$1750603025, 64(%esp)
	movl	$1694076839, 68(%esp)
	movl	$-1090891868, 72(%esp)
	movl	12(%ebp), %eax
	movl	%eax, 8(%esp)
	movl	8(%ebp), %eax
	movl	%eax, 4(%esp)
	leal	44(%esp), %esi
	movl	%esi, (%esp)
	call	_sha224_update
	leal	16(%esp), %eax
	movl	%eax, 4(%esp)
	movl	%esi, (%esp)
	call	_sha224_final
	movl	$0, %eax
	.p2align 6
L29:
	movzbl	16(%esp,%eax), %edx
	movl	%edx, %ecx
	shrb	$4, %cl
	movzbl	%cl, %ecx
	movzbl	__ZZ11_jit_sha224E3hex(%ecx), %ecx
	movb	%cl, (%ebx,%eax,2)
	andl	$15, %edx
	movzbl	__ZZ11_jit_sha224E3hex(%edx), %edx
	movb	%dl, 1(%ebx,%eax,2)
	addl	$1, %eax
	cmpl	$28, %eax
	jne	L29
	movb	$0, 56(%ebx)
L27:
	movl	%ebx, %eax
	leal	-8(%ebp), %esp
	popl	%ebx
	popl	%esi
	popl	%ebp
	ret
LFE4:
	.section .rdata,"dr"
	.align 4
__ZZ11_jit_sha224E3hex:
	.ascii "0123456789abcdef\0"
	.align 32
__ZZ12sha224_finalE7padding:
	.ascii "\200\0"
	.space 62
	.align 32
__ZL8sha224_k:
	.long	1116352408
	.long	1899447441
	.long	-1245643825
	.long	-373957723
	.long	961987163
	.long	1508970993
	.long	-1841331548
	.long	-1424204075
	.long	-670586216
	.long	310598401
	.long	607225278
	.long	1426881987
	.long	1925078388
	.long	-2132889090
	.long	-1680079193
	.long	-1046744716
	.long	-459576895
	.long	-272742522
	.long	264347078
	.long	604807628
	.long	770255983
	.long	1249150122
	.long	1555081692
	.long	1996064986
	.long	-1740746414
	.long	-1473132947
	.long	-1341970488
	.long	-1084653625
	.long	-958395405
	.long	-710438585
	.long	113926993
	.long	338241895
	.long	666307205
	.long	773529912
	.long	1294757372
	.long	1396182291
	.long	1695183700
	.long	1986661051
	.long	-2117940946
	.long	-1838011259
	.long	-1564481375
	.long	-1474664885
	.long	-1035236496
	.long	-949202525
	.long	-778901479
	.long	-694614492
	.long	-200395387
	.long	275423344
	.long	430227734
	.long	506948616
	.long	659060556
	.long	883997877
	.long	958139571
	.long	1322822218
	.long	1537002063
	.long	1747873779
	.long	1955562222
	.long	2024104815
	.long	-2067236844
	.long	-1933114872
	.long	-1866530822
	.long	-1538233109
	.long	-1090935817
	.long	-965641998
	.section .drectve
	.ascii " -export:\"_jit_sha224\""
	.ascii " -export:\"sha224_final\""
	.ascii " -export:\"sha224_update\""
	.ascii " -export:\"sha224_init\""
