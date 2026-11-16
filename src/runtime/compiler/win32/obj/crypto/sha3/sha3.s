	.text
__ZL9load_le64PKh:
LFB0:
	pushl	%ebp
	movl	%esp, %ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	andl	$-8, %esp
	subl	$8, %esp
	movl	%eax, %edx
	movzbl	1(%eax), %ecx
	movl	$0, %ebx
	movl	%ecx, %esi
	movl	%ebx, %edi
	shldl	$8, %esi, %edi
	sall	$8, %esi
	movzbl	2(%eax), %ecx
	movl	$0, %ebx
	shldl	$16, %ecx, %ebx
	sall	$16, %ecx
	orl	%esi, %ecx
	orl	%edi, %ebx
	movzbl	(%eax), %eax
	movl	%eax, (%esp)
	movl	$0, 4(%esp)
	movl	%ecx, %esi
	movl	%ebx, %edi
	orl	(%esp), %esi
	orl	4(%esp), %edi
	movzbl	3(%edx), %ecx
	movl	$0, %ebx
	shldl	$24, %ecx, %ebx
	sall	$24, %ecx
	orl	%esi, %ecx
	orl	%edi, %ebx
	movl	%ecx, %esi
	movl	%ebx, %edi
	movzbl	4(%edx), %ecx
	movl	%ecx, %ebx
	xorl	%ecx, %ecx
	orl	%esi, %ecx
	orl	%edi, %ebx
	movl	%ecx, %esi
	movl	%ebx, %edi
	movzbl	5(%edx), %ecx
	movl	%ecx, %ebx
	sall	$8, %ebx
	xorl	%ecx, %ecx
	orl	%esi, %ecx
	orl	%edi, %ebx
	movl	%ecx, %esi
	movl	%ebx, %edi
	movzbl	6(%edx), %ecx
	movl	%ecx, %ebx
	sall	$16, %ebx
	xorl	%ecx, %ecx
	orl	%esi, %ecx
	orl	%edi, %ebx
	movzbl	7(%edx), %eax
	movl	%eax, %edx
	sall	$24, %edx
	xorl	%eax, %eax
	orl	%ecx, %eax
	orl	%ebx, %edx
	leal	-12(%ebp), %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE0:
__ZL7keccakfPy:
LFB2:
	pushl	%ebp
	movl	%esp, %ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	andl	$-8, %esp
	subl	$72, %esp
	movl	%eax, 8(%esp)
	movl	$0, %esi
	movl	%esi, %edi
L4:
	movl	$0, %ecx
	movl	8(%esp), %ebx
L5:
	movl	(%ebx,%ecx,8), %eax
	movl	4(%ebx,%ecx,8), %edx
	xorl	40(%ebx,%ecx,8), %eax
	xorl	44(%ebx,%ecx,8), %edx
	xorl	80(%ebx,%ecx,8), %eax
	xorl	84(%ebx,%ecx,8), %edx
	xorl	120(%ebx,%ecx,8), %eax
	xorl	124(%ebx,%ecx,8), %edx
	xorl	160(%ebx,%ecx,8), %eax
	xorl	164(%ebx,%ecx,8), %edx
	movl	%eax, 32(%esp,%ecx,8)
	movl	%edx, 36(%esp,%ecx,8)
	addl	$1, %ecx
	cmpl	$5, %ecx
	jne	L5
	movl	8(%esp), %eax
	leal	200(%eax), %ecx
	movl	$0, %ebx
	movl	%edi, 28(%esp)
	movl	%eax, 16(%esp)
L7:
	leal	4(%ebx), %esi
	movl	$1717986919, %eax
	imull	%esi
	sarl	%edx
	movl	%esi, %eax
	sarl	$31, %eax
	subl	%eax, %edx
	leal	(%edx,%edx,4), %eax
	subl	%eax, %esi
	addl	$1, %ebx
	movl	$1717986919, %eax
	imull	%ebx
	sarl	%edx
	movl	%ebx, %eax
	sarl	$31, %eax
	subl	%eax, %edx
	leal	(%edx,%edx,4), %edx
	movl	%ebx, %eax
	subl	%edx, %eax
	movl	36(%esp,%eax,8), %edx
	movl	32(%esp,%eax,8), %eax
	movl	%eax, %edi
	shldl	$1, %edx, %eax
	shldl	$1, %edi, %edx
	xorl	32(%esp,%esi,8), %eax
	xorl	36(%esp,%esi,8), %edx
	leal	-200(%ecx), %esi
L6:
	xorl	%eax, (%esi)
	xorl	%edx, 4(%esi)
	addl	$40, %esi
	cmpl	%ecx, %esi
	jne	L6
	addl	$8, %ecx
	cmpl	$5, %ebx
	jne	L7
	movl	28(%esp), %edi
	movl	16(%esp), %esi
	movl	8(%esp), %ecx
	movl	8(%ecx), %eax
	movl	12(%ecx), %edx
	movl	%eax, 16(%esp)
	movl	%edx, 20(%esp)
	movl	$0, %ebx
	movl	%edi, 12(%esp)
	movl	%esi, 4(%esp)
	movl	%ecx, 24(%esp)
L8:
	movl	__ZL12keccakf_piln(,%ebx,4), %eax
	movl	24(%esp), %edi
	leal	(%edi,%eax,8), %edi
	movl	16(%esp), %eax
	movl	20(%esp), %edx
	movl	%edi, 28(%esp)
	movl	(%edi), %esi
	movl	4(%edi), %edi
	movl	%esi, 16(%esp)
	movl	%edi, 20(%esp)
	movl	__ZL12keccakf_rotc(,%ebx,4), %ecx
	movl	%eax, %esi
	movl	%edx, %edi
	shldl	%cl, %esi, %edi
	sall	%cl, %esi
	testb	$32, %cl
	je	L21
	movl	%esi, %edi
	xorl	%esi, %esi
L21:
	negl	%ecx
	shrdl	%cl, %edx, %eax
	shrl	%cl, %edx
	testb	$32, %cl
	je	L22
	movl	%edx, %eax
	xorl	%edx, %edx
L22:
	orl	%esi, %eax
	orl	%edi, %edx
	movl	28(%esp), %edi
	movl	%eax, (%edi)
	movl	%edx, 4(%edi)
	addl	$1, %ebx
	cmpl	$24, %ebx
	jne	L8
	movl	12(%esp), %edi
	movl	4(%esp), %esi
	movl	16(%esp), %eax
	movl	20(%esp), %edx
	movl	%eax, 32(%esp)
	movl	%edx, 36(%esp)
	movl	$0, %eax
	movl	%edi, 4(%esp)
L9:
	movl	$0, %edx
	movl	%esi, 28(%esp)
L10:
	movl	(%esi,%edx,8), %ecx
	movl	4(%esi,%edx,8), %ebx
	movl	%ecx, 32(%esp,%edx,8)
	movl	%ebx, 36(%esp,%edx,8)
	addl	$1, %edx
	cmpl	$5, %edx
	jne	L10
	movl	$0, %edi
	movl	%eax, 24(%esp)
	movl	%esi, 12(%esp)
L11:
	movl	28(%esp), %eax
	movl	4(%eax,%edi,8), %edx
	movl	(%eax,%edi,8), %eax
	movl	%eax, 16(%esp)
	movl	%edx, 20(%esp)
	movl	%edi, %esi
	addl	$1, %edi
	movl	$1717986919, %eax
	imull	%edi
	sarl	%edx
	movl	%edi, %ebx
	sarl	$31, %ebx
	subl	%ebx, %edx
	leal	(%edx,%edx,4), %edx
	movl	%edi, %ebx
	subl	%edx, %ebx
	movl	32(%esp,%ebx,8), %ecx
	movl	36(%esp,%ebx,8), %ebx
	addl	$2, %esi
	movl	$1717986919, %eax
	imull	%esi
	sarl	%edx
	movl	%esi, %eax
	sarl	$31, %eax
	subl	%eax, %edx
	leal	(%edx,%edx,4), %eax
	subl	%eax, %esi
	notl	%ecx
	notl	%ebx
	andl	32(%esp,%esi,8), %ecx
	andl	36(%esp,%esi,8), %ebx
	xorl	16(%esp), %ecx
	xorl	20(%esp), %ebx
	movl	28(%esp), %eax
	movl	%ecx, -8(%eax,%edi,8)
	movl	%ebx, -4(%eax,%edi,8)
	cmpl	$5, %edi
	jne	L11
	movl	24(%esp), %eax
	movl	12(%esp), %esi
	addl	$5, %eax
	addl	$40, %esi
	cmpl	$25, %eax
	jne	L9
	movl	4(%esp), %edi
	movl	__ZL12keccakf_rndc(,%edi,8), %eax
	movl	__ZL12keccakf_rndc+4(,%edi,8), %edx
	movl	8(%esp), %ebx
	xorl	%eax, (%ebx)
	xorl	%edx, 4(%ebx)
	addl	$1, %edi
	cmpl	$24, %edi
	jne	L4
	leal	-12(%ebp), %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE2:
	.globl	_sha3_init
_sha3_init:
LFB3:
	pushl	%ebx
	subl	$12, %esp
	movl	20(%esp), %ebx
	movl	$416, 8(%esp)
	movl	$0, 4(%esp)
	movl	%ebx, (%esp)
	call	__jit_memset
	movl	24(%esp), %eax
	movl	%eax, 400(%ebx)
	movl	28(%esp), %eax
	movl	%eax, 408(%ebx)
	movl	$0, 404(%ebx)
	addl	$12, %esp
	popl	%ebx
	ret
LFE3:
	.globl	_sha3_update
_sha3_update:
LFB4:
	leal	-32(%esp), %esp
	movl	%esi, 20(%esp)
	movl	%edi, 24(%esp)
	movl	%ebp, 28(%esp)
	movl	36(%esp), %esi
	movl	40(%esp), %ebp
	movl	44(%esp), %edi
	testl	%edi, %edi
	je	L25
	movl	%ebx, 16(%esp)
	leal	200(%esi), %eax
	movl	%eax, 12(%esp)
	jmp	L30
L28:
	movl	%esi, %eax
	call	__ZL7keccakfPy
	movl	400(%esi), %eax
	movl	%eax, 8(%esp)
	movl	$0, 4(%esp)
	movl	12(%esp), %eax
	movl	%eax, (%esp)
	call	__jit_memset
	movl	$0, 404(%esi)
L27:
	testl	%edi, %edi
	je	L34
L30:
	movl	404(%esi), %eax
	movl	400(%esi), %ebx
	subl	%eax, %ebx
	cmpl	%edi, %ebx
	cmova	%edi, %ebx
	movl	%ebx, 8(%esp)
	movl	%ebp, 4(%esp)
	movl	12(%esp), %ecx
	addl	%ecx, %eax
	movl	%eax, (%esp)
	call	__jit_memcpy
	movl	%ebx, %eax
	addl	404(%esi), %eax
	movl	%eax, 404(%esi)
	addl	%ebx, %ebp
	subl	%ebx, %edi
	movl	400(%esi), %edx
	cmpl	%edx, %eax
	jne	L27
	shrl	$3, %edx
	je	L28
	leal	200(%esi), %ebx
	leal	(%ebx,%edx,8), %eax
	movl	%esi, 36(%esp)
	movl	%eax, %esi
L29:
	movl	%ebx, %eax
	call	__ZL9load_le64PKh
	xorl	%eax, -200(%ebx)
	xorl	%edx, -196(%ebx)
	addl	$8, %ebx
	cmpl	%esi, %ebx
	jne	L29
	movl	36(%esp), %esi
	jmp	L28
L34:
	movl	16(%esp), %ebx
L25:
	movl	20(%esp), %esi
	movl	24(%esp), %edi
	movl	28(%esp), %ebp
	leal	32(%esp), %esp
	ret
LFE4:
	.globl	_sha3_final
_sha3_final:
LFB5:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$212, %esp
	movl	232(%esp), %esi
	movl	404(%esi), %eax
	xorb	$6, 200(%esi,%eax)
	movl	400(%esi), %eax
	addb	$-128, 199(%esi,%eax)
	shrl	$3, %eax
	je	L36
	leal	200(%esi), %ebx
	leal	(%ebx,%eax,8), %edi
L37:
	movl	%ebx, %eax
	call	__ZL9load_le64PKh
	xorl	%eax, -200(%ebx)
	xorl	%edx, -196(%ebx)
	addl	$8, %ebx
	cmpl	%edi, %ebx
	jne	L37
L36:
	movl	%esi, %eax
	call	__ZL7keccakfPy
	movl	%esi, %ebp
	leal	12(%esp), %eax
	movl	%esi, %edx
L38:
	movl	0(%ebp), %esi
	movl	4(%ebp), %edi
	movl	%esi, %ebx
	movb	%bl, (%eax)
	movl	%esi, %ebx
	movb	%bh, 1(%eax)
	movl	%esi, %ecx
	movl	%edi, %ebx
	shrdl	$16, %ebx, %ecx
	shrl	$16, %ebx
	movb	%cl, 2(%eax)
	movl	%esi, %ecx
	movl	%edi, %ebx
	shrdl	$24, %ebx, %ecx
	shrl	$24, %ebx
	movb	%cl, 3(%eax)
	movl	%edi, %ecx
	movb	%cl, 4(%eax)
	movb	%ch, 5(%eax)
	shrl	$16, %ecx
	movb	%cl, 6(%eax)
	movl	%edi, %ecx
	shrl	$24, %ecx
	movb	%cl, 7(%eax)
	addl	$8, %ebp
	addl	$8, %eax
	leal	212(%esp), %edi
	cmpl	%edi, %eax
	jne	L38
	movl	408(%edx), %eax
	movl	%eax, 8(%esp)
	leal	12(%esp), %eax
	movl	%eax, 4(%esp)
	movl	236(%esp), %eax
	movl	%eax, (%esp)
	call	__jit_memcpy
	addl	$212, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE5:
	.globl	__jit_sha3
__jit_sha3:
LFB6:
	pushl	%ebp
	movl	%esp, %ebp
	pushl	%esi
	pushl	%ebx
	andl	$-8, %esp
	subl	$460, %esp
	movl	$65, (%esp)
	call	__jit_malloc
	movl	%eax, %ebx
	testl	%eax, %eax
	je	L42
	movl	$416, 8(%esp)
	movl	$0, 4(%esp)
	leal	44(%esp), %esi
	movl	%esi, (%esp)
	call	__jit_memset
	movl	$136, 444(%esp)
	movl	$32, 452(%esp)
	movl	$0, 448(%esp)
	movl	12(%ebp), %eax
	movl	%eax, 8(%esp)
	movl	8(%ebp), %eax
	movl	%eax, 4(%esp)
	movl	%esi, (%esp)
	call	_sha3_update
	leal	12(%esp), %eax
	movl	%eax, 4(%esp)
	movl	%esi, (%esp)
	call	_sha3_final
	movl	$0, %eax
	.p2align 6
L44:
	movzbl	12(%esp,%eax), %edx
	shrb	$4, %dl
	movzbl	%dl, %edx
	movzbl	__ZZ9_jit_sha3E3hex(%edx), %edx
	movb	%dl, (%ebx,%eax,2)
	movzbl	12(%esp,%eax), %edx
	andl	$15, %edx
	movzbl	__ZZ9_jit_sha3E3hex(%edx), %edx
	movb	%dl, 1(%ebx,%eax,2)
	addl	$1, %eax
	cmpl	$32, %eax
	jne	L44
	movb	$0, 64(%ebx)
L42:
	movl	%ebx, %eax
	leal	-8(%ebp), %esp
	popl	%ebx
	popl	%esi
	popl	%ebp
	ret
LFE6:
	.section .rdata,"dr"
	.align 4
__ZZ9_jit_sha3E3hex:
	.ascii "0123456789abcdef\0"
	.align 32
__ZL12keccakf_piln:
	.long	10
	.long	7
	.long	11
	.long	17
	.long	18
	.long	3
	.long	5
	.long	16
	.long	8
	.long	21
	.long	24
	.long	4
	.long	15
	.long	23
	.long	19
	.long	13
	.long	12
	.long	2
	.long	20
	.long	14
	.long	22
	.long	9
	.long	6
	.long	1
	.align 32
__ZL12keccakf_rotc:
	.long	1
	.long	3
	.long	6
	.long	10
	.long	15
	.long	21
	.long	28
	.long	36
	.long	45
	.long	55
	.long	2
	.long	14
	.long	27
	.long	41
	.long	56
	.long	8
	.long	25
	.long	43
	.long	62
	.long	18
	.long	39
	.long	61
	.long	20
	.long	44
	.align 32
__ZL12keccakf_rndc:
	.long	1
	.long	0
	.long	32898
	.long	0
	.long	32906
	.long	-2147483648
	.long	-2147450880
	.long	-2147483648
	.long	32907
	.long	0
	.long	-2147483647
	.long	0
	.long	-2147450751
	.long	-2147483648
	.long	32777
	.long	-2147483648
	.long	138
	.long	0
	.long	136
	.long	0
	.long	-2147450871
	.long	0
	.long	-2147483638
	.long	0
	.long	-2147450741
	.long	0
	.long	139
	.long	-2147483648
	.long	32905
	.long	-2147483648
	.long	32771
	.long	-2147483648
	.long	32770
	.long	-2147483648
	.long	128
	.long	-2147483648
	.long	32778
	.long	0
	.long	-2147483638
	.long	-2147483648
	.long	-2147450751
	.long	-2147483648
	.long	32896
	.long	-2147483648
	.long	-2147483647
	.long	0
	.long	-2147450872
	.long	-2147483648
	.section .drectve
	.ascii " -export:\"_jit_sha3\""
	.ascii " -export:\"sha3_final\""
	.ascii " -export:\"sha3_update\""
	.ascii " -export:\"sha3_init\""
