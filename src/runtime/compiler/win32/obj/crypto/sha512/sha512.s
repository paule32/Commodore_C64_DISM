	.text
__ZL16sha512_transformPyPKh:
LFB2:
	pushl	%ebp
	movl	%esp, %ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	andl	$-8, %esp
	subl	$800, %esp
	movl	%eax, 136(%esp)
	movl	%edx, %esi
	leal	160(%esp), %edi
	movl	%edi, 152(%esp)
L2:
	movzbl	(%esi), %eax
	movl	%eax, %edx
	sall	$24, %edx
	xorl	%eax, %eax
	movzbl	1(%esi), %ecx
	movl	%ecx, %ebx
	sall	$16, %ebx
	xorl	%ecx, %ecx
	orl	%ecx, %eax
	orl	%ebx, %edx
	movzbl	7(%esi), %ecx
	movl	$0, %ebx
	orl	%eax, %ecx
	orl	%edx, %ebx
	movzbl	2(%esi), %eax
	movl	%eax, %edx
	sall	$8, %edx
	xorl	%eax, %eax
	orl	%eax, %ecx
	orl	%edx, %ebx
	movzbl	3(%esi), %eax
	movl	%eax, %edx
	xorl	%eax, %eax
	orl	%eax, %ecx
	orl	%edx, %ebx
	movzbl	4(%esi), %eax
	movl	$0, %edx
	shldl	$24, %eax, %edx
	sall	$24, %eax
	orl	%eax, %ecx
	orl	%edx, %ebx
	movzbl	5(%esi), %eax
	movl	$0, %edx
	shldl	$16, %eax, %edx
	sall	$16, %eax
	orl	%eax, %ecx
	orl	%edx, %ebx
	movzbl	6(%esi), %eax
	movl	$0, %edx
	shldl	$8, %eax, %edx
	sall	$8, %eax
	orl	%eax, %ecx
	orl	%edx, %ebx
	movl	%ecx, (%edi)
	movl	%ebx, 4(%edi)
	addl	$8, %esi
	addl	$8, %edi
	leal	288(%esp), %eax
	cmpl	%eax, %edi
	jne	L2
	movl	152(%esp), %edi
	leal	512(%edi), %eax
	movl	%eax, 144(%esp)
L3:
	movl	112(%edi), %eax
	movl	116(%edi), %edx
	movl	%eax, %ebx
	movl	%edx, %esi
	movl	%eax, %ecx
	shrdl	$19, %edx, %ebx
	shrdl	$19, %eax, %esi
	movl	%ebx, 152(%esp)
	movl	%esi, 156(%esp)
	movl	%edx, %ebx
	shldl	$3, %edx, %ecx
	shldl	$3, %eax, %ebx
	xorl	152(%esp), %ecx
	xorl	156(%esp), %ebx
	shrdl	$6, %edx, %eax
	shrl	$6, %edx
	xorl	%eax, %ecx
	xorl	%edx, %ebx
	movl	(%edi), %eax
	movl	4(%edi), %edx
	addl	72(%edi), %eax
	adcl	76(%edi), %edx
	addl	%eax, %ecx
	adcl	%edx, %ebx
	movl	%ecx, 152(%esp)
	movl	%ebx, 156(%esp)
	movl	8(%edi), %ebx
	movl	12(%edi), %esi
	movl	%ebx, %eax
	shrdl	$1, %esi, %ebx
	shrdl	$1, %eax, %esi
	movl	%ebx, %ecx
	movl	%esi, %ebx
	movl	8(%edi), %eax
	movl	12(%edi), %edx
	movl	%eax, %esi
	shrdl	$8, %edx, %eax
	shrdl	$8, %esi, %edx
	xorl	%eax, %ecx
	xorl	%edx, %ebx
	movl	8(%edi), %eax
	movl	12(%edi), %edx
	shrdl	$7, %edx, %eax
	shrl	$7, %edx
	xorl	%eax, %ecx
	xorl	%edx, %ebx
	addl	152(%esp), %ecx
	adcl	156(%esp), %ebx
	movl	%ecx, 128(%edi)
	movl	%ebx, 132(%edi)
	addl	$8, %edi
	movl	144(%esp), %eax
	cmpl	%eax, %edi
	jne	L3
	movl	136(%esp), %edi
	movl	(%edi), %eax
	movl	4(%edi), %edx
	movl	%eax, 56(%esp)
	movl	%edx, 60(%esp)
	movl	8(%edi), %ebx
	movl	12(%edi), %esi
	movl	%ebx, 48(%esp)
	movl	%esi, 52(%esp)
	movl	16(%edi), %eax
	movl	20(%edi), %edx
	movl	%eax, 40(%esp)
	movl	%edx, 44(%esp)
	movl	24(%edi), %edx
	movl	28(%edi), %ecx
	movl	%edx, 32(%esp)
	movl	%ecx, 36(%esp)
	movl	32(%edi), %ebx
	movl	36(%edi), %esi
	movl	%ebx, 24(%esp)
	movl	%esi, 28(%esp)
	movl	40(%edi), %edx
	movl	44(%edi), %ecx
	movl	%edx, 16(%esp)
	movl	%ecx, 20(%esp)
	movl	%edi, %edx
	movl	48(%edi), %esi
	movl	52(%edi), %edi
	movl	%esi, 8(%esp)
	movl	%edi, 12(%esp)
	movl	60(%edx), %ecx
	movl	56(%edx), %edx
	movl	%edx, (%esp)
	movl	%ecx, 4(%esp)
	movl	%edx, 96(%esp)
	movl	%ecx, 100(%esp)
	movl	%esi, 112(%esp)
	movl	%edi, 116(%esp)
	movl	16(%esp), %edx
	movl	20(%esp), %ecx
	movl	%edx, 104(%esp)
	movl	%ecx, 108(%esp)
	movl	24(%esp), %ebx
	movl	28(%esp), %esi
	movl	%ebx, 144(%esp)
	movl	%esi, 148(%esp)
	movl	32(%esp), %edx
	movl	36(%esp), %ecx
	movl	%edx, 88(%esp)
	movl	%ecx, 92(%esp)
	movl	40(%esp), %eax
	movl	44(%esp), %edx
	movl	%eax, 120(%esp)
	movl	%edx, 124(%esp)
	movl	48(%esp), %ebx
	movl	52(%esp), %esi
	movl	%ebx, 128(%esp)
	movl	%esi, 132(%esp)
	movl	56(%esp), %eax
	movl	60(%esp), %edx
	movl	%eax, 152(%esp)
	movl	%edx, 156(%esp)
	movl	$0, 140(%esp)
	jmp	L4
L5:
	movl	104(%esp), %eax
	movl	108(%esp), %edx
	movl	%eax, 112(%esp)
	movl	%edx, 116(%esp)
	movl	144(%esp), %eax
	movl	148(%esp), %edx
	movl	%eax, 104(%esp)
	movl	%edx, 108(%esp)
	movl	72(%esp), %eax
	movl	76(%esp), %edx
	movl	%eax, 144(%esp)
	movl	%edx, 148(%esp)
	movl	64(%esp), %eax
	movl	68(%esp), %edx
	movl	%eax, 120(%esp)
	movl	%edx, 124(%esp)
	movl	%esi, 152(%esp)
	movl	%edi, 156(%esp)
L4:
	movl	144(%esp), %edx
	movl	148(%esp), %ecx
	movl	%edx, %esi
	movl	%ecx, %edi
	movl	%edx, %eax
	shrdl	$14, %ecx, %esi
	shrdl	$14, %edx, %edi
	movl	%ecx, %edx
	movl	%eax, %ecx
	shrdl	$18, %edx, %eax
	shrdl	$18, %ecx, %edx
	xorl	%esi, %eax
	xorl	%edi, %edx
	movl	144(%esp), %esi
	movl	148(%esp), %edi
	movl	%esi, %ecx
	shldl	$23, %edi, %esi
	shldl	$23, %ecx, %edi
	xorl	%eax, %esi
	xorl	%edx, %edi
	movl	140(%esp), %ecx
	movl	160(%esp,%ecx,8), %eax
	movl	164(%esp,%ecx,8), %edx
	addl	__ZL8sha512_k(,%ecx,8), %eax
	adcl	__ZL8sha512_k+4(,%ecx,8), %edx
	movl	%esi, %ecx
	movl	%edi, %ebx
	addl	%eax, %ecx
	adcl	%edx, %ebx
	movl	144(%esp), %esi
	movl	148(%esp), %edi
	movl	%esi, %eax
	movl	%edi, %edx
	notl	%eax
	notl	%edx
	andl	112(%esp), %eax
	andl	116(%esp), %edx
	andl	104(%esp), %esi
	andl	108(%esp), %edi
	xorl	%esi, %eax
	xorl	%edi, %edx
	addl	%eax, %ecx
	adcl	%edx, %ebx
	addl	96(%esp), %ecx
	adcl	100(%esp), %ebx
	movl	%ecx, 96(%esp)
	movl	%ebx, 100(%esp)
	movl	152(%esp), %ebx
	movl	156(%esp), %esi
	movl	%ebx, %eax
	movl	%esi, %edx
	shrdl	$28, %esi, %eax
	shrdl	$28, %ebx, %edx
	movl	%esi, %edi
	movl	%ebx, %esi
	shldl	$30, %edi, %esi
	shldl	$30, %ebx, %edi
	xorl	%eax, %esi
	xorl	%edx, %edi
	movl	152(%esp), %eax
	movl	156(%esp), %edx
	movl	%eax, %ecx
	shldl	$25, %edx, %eax
	shldl	$25, %ecx, %edx
	xorl	%eax, %esi
	xorl	%edx, %edi
	movl	%esi, %ecx
	movl	%edi, %ebx
	movl	128(%esp), %eax
	movl	132(%esp), %edx
	movl	%eax, %esi
	movl	%edx, %edi
	xorl	120(%esp), %esi
	xorl	124(%esp), %edi
	andl	152(%esp), %esi
	andl	156(%esp), %edi
	andl	120(%esp), %eax
	andl	124(%esp), %edx
	xorl	%eax, %esi
	xorl	%edx, %edi
	addl	%ecx, %esi
	adcl	%ebx, %edi
	movl	%esi, 80(%esp)
	movl	%edi, 84(%esp)
	movl	88(%esp), %ecx
	movl	92(%esp), %ebx
	movl	96(%esp), %eax
	movl	100(%esp), %edx
	addl	%eax, %ecx
	adcl	%edx, %ebx
	movl	%ecx, 72(%esp)
	movl	%ebx, 76(%esp)
	movl	128(%esp), %ecx
	movl	132(%esp), %ebx
	movl	%ecx, %edi
	shrdl	$2, %ebx, %ecx
	shrdl	$2, %edi, %ebx
	movl	%ecx, 64(%esp)
	movl	%ebx, 68(%esp)
	movl	80(%esp), %esi
	movl	84(%esp), %edi
	addl	%eax, %esi
	adcl	%edx, %edi
	addl	$1, 140(%esp)
	movl	140(%esp), %ecx
	movl	152(%esp), %eax
	movl	156(%esp), %edx
	movl	%eax, 128(%esp)
	movl	%edx, 132(%esp)
	movl	120(%esp), %eax
	movl	124(%esp), %edx
	movl	%eax, 88(%esp)
	movl	%edx, 92(%esp)
	movl	112(%esp), %eax
	movl	116(%esp), %edx
	movl	%eax, 96(%esp)
	movl	%edx, 100(%esp)
	cmpl	$80, %ecx
	jne	L5
	movl	64(%esp), %ecx
	movl	68(%esp), %ebx
	movl	56(%esp), %eax
	movl	60(%esp), %edx
	addl	%esi, %eax
	adcl	%edi, %edx
	movl	136(%esp), %edi
	movl	%eax, (%edi)
	movl	%edx, 4(%edi)
	movl	48(%esp), %eax
	movl	52(%esp), %edx
	addl	152(%esp), %eax
	adcl	156(%esp), %edx
	movl	%eax, 8(%edi)
	movl	%edx, 12(%edi)
	addl	40(%esp), %ecx
	adcl	44(%esp), %ebx
	movl	%ecx, 16(%edi)
	movl	%ebx, 20(%edi)
	movl	32(%esp), %eax
	movl	36(%esp), %edx
	addl	120(%esp), %eax
	adcl	124(%esp), %edx
	movl	%eax, 24(%edi)
	movl	%edx, 28(%edi)
	movl	24(%esp), %eax
	movl	28(%esp), %edx
	addl	72(%esp), %eax
	adcl	76(%esp), %edx
	movl	%eax, 32(%edi)
	movl	%edx, 36(%edi)
	movl	16(%esp), %eax
	movl	20(%esp), %edx
	addl	144(%esp), %eax
	adcl	148(%esp), %edx
	movl	%eax, 40(%edi)
	movl	%edx, 44(%edi)
	movl	8(%esp), %eax
	movl	12(%esp), %edx
	addl	104(%esp), %eax
	adcl	108(%esp), %edx
	movl	%eax, 48(%edi)
	movl	%edx, 52(%edi)
	movl	(%esp), %eax
	movl	4(%esp), %edx
	addl	112(%esp), %eax
	adcl	116(%esp), %edx
	movl	%eax, 56(%edi)
	movl	%edx, 60(%edi)
	leal	-12(%ebp), %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE2:
	.globl	_sha512_init
_sha512_init:
LFB3:
	movl	4(%esp), %eax
	movl	$0, 64(%eax)
	movl	$0, 68(%eax)
	movl	$0, 72(%eax)
	movl	$0, 76(%eax)
	movl	$-205731576, (%eax)
	movl	$1779033703, 4(%eax)
	movl	$-2067093701, 8(%eax)
	movl	$-1150833019, 12(%eax)
	movl	$-23791573, 16(%eax)
	movl	$1013904242, 20(%eax)
	movl	$1595750129, 24(%eax)
	movl	$-1521486534, 28(%eax)
	movl	$-1377402159, 32(%eax)
	movl	$1359893119, 36(%eax)
	movl	$725511199, 40(%eax)
	movl	$-1694144372, 44(%eax)
	movl	$-79577749, 48(%eax)
	movl	$528734635, 52(%eax)
	movl	$327033209, 56(%eax)
	movl	$1541459225, 60(%eax)
	ret
LFE3:
	.globl	_sha512_update
_sha512_update:
LFB4:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$12, %esp
	movl	32(%esp), %edi
	movl	40(%esp), %esi
	movl	72(%edi), %eax
	movl	76(%edi), %edx
	shrdl	$3, %edx, %eax
	shrl	$3, %edx
	movl	%eax, %ebp
	andl	$127, %ebp
	movl	%esi, %ecx
	movl	$0, %ebx
	shldl	$3, %ecx, %ebx
	sall	$3, %ecx
	movl	%ecx, %eax
	movl	%ebx, %edx
	addl	72(%edi), %eax
	adcl	76(%edi), %edx
	movl	%eax, 72(%edi)
	movl	%edx, 76(%edi)
	cmpl	%ecx, %eax
	movl	%edx, %eax
	sbbl	%ebx, %eax
	jnc	L11
	addl	$1, 64(%edi)
	adcl	$0, 68(%edi)
L11:
	movl	$128, %ebx
	subl	%ebp, %ebx
	cmpl	%ebx, %esi
	jnb	L18
	movl	$0, %ebx
L12:
	subl	%ebx, %esi
	movl	%esi, 8(%esp)
	movl	%ebx, %eax
	addl	36(%esp), %eax
	movl	%eax, 4(%esp)
	leal	80(%edi,%ebp), %eax
	movl	%eax, (%esp)
	call	__jit_memcpy
	addl	$12, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
L18:
	movl	%ebx, 8(%esp)
	movl	36(%esp), %eax
	movl	%eax, 4(%esp)
	leal	80(%edi,%ebp), %eax
	movl	%eax, (%esp)
	call	__jit_memcpy
	leal	80(%edi), %edx
	movl	%edi, %eax
	call	__ZL16sha512_transformPyPKh
	movl	$255, %eax
	subl	%ebp, %eax
	cmpl	%esi, %eax
	jnb	L15
	movl	36(%esp), %ebp
L13:
	leal	0(%ebp,%ebx), %edx
	movl	%edi, %eax
	call	__ZL16sha512_transformPyPKh
	movl	%ebx, %eax
	subl	$-128, %ebx
	addl	$255, %eax
	cmpl	%esi, %eax
	jb	L13
	movl	$0, %ebp
	jmp	L12
L15:
	movl	$0, %ebp
	jmp	L12
LFE4:
	.globl	_sha512_final
_sha512_final:
LFB5:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$36, %esp
	movl	56(%esp), %ebx
	movl	60(%esp), %ebp
	movl	64(%ebx), %esi
	movl	68(%ebx), %edi
	movl	%edi, %ecx
	shrl	$24, %ecx
	movb	%cl, 20(%esp)
	movl	%edi, %ecx
	shrl	$16, %ecx
	movb	%cl, 21(%esp)
	movl	%edi, %eax
	movb	%ah, 22(%esp)
	movb	%al, 23(%esp)
	movl	%esi, 12(%esp)
	movl	%edi, 16(%esp)
	movl	%esi, %eax
	movl	%edi, %edx
	shrdl	$24, %edx, %eax
	shrl	$24, %edx
	movb	%al, 24(%esp)
	movl	12(%esp), %esi
	movl	16(%esp), %edi
	movl	%esi, %eax
	movl	%edi, %edx
	shrdl	$16, %edx, %eax
	shrl	$16, %edx
	movb	%al, 25(%esp)
	movl	%esi, %eax
	movb	%ah, 26(%esp)
	movb	%al, 27(%esp)
	movl	72(%ebx), %eax
	movl	76(%ebx), %edx
	movl	%edx, %ecx
	shrl	$24, %ecx
	movb	%cl, 28(%esp)
	movl	%edx, %ecx
	shrl	$16, %ecx
	movb	%cl, 29(%esp)
	movb	%dh, 30(%esp)
	movb	%dl, 31(%esp)
	movl	%eax, %esi
	movl	%edx, %edi
	shrdl	$24, %edi, %esi
	shrl	$24, %edi
	movl	%esi, %ecx
	movb	%cl, 32(%esp)
	movl	%eax, %esi
	movl	%edx, %edi
	shrdl	$16, %edi, %esi
	shrl	$16, %edi
	movl	%esi, %ecx
	movb	%cl, 33(%esp)
	movb	%ah, 34(%esp)
	movb	%al, 35(%esp)
	shrdl	$3, %edx, %eax
	shrl	$3, %edx
	andl	$127, %eax
	movl	$112, %ecx
	subl	%eax, %ecx
	movl	$240, %edx
	subl	%eax, %edx
	cmpl	$111, %eax
	movl	%ecx, %eax
	cmova	%edx, %eax
	movl	%eax, 8(%esp)
	movl	$__ZZ12sha512_finalE7padding, 4(%esp)
	movl	%ebx, (%esp)
	call	_sha512_update
	movl	$16, 8(%esp)
	leal	20(%esp), %eax
	movl	%eax, 4(%esp)
	movl	%ebx, (%esp)
	call	_sha512_update
	movl	%ebx, %edx
	movl	%ebp, %eax
	addl	$64, %ebp
L22:
	movl	(%edx), %ecx
	movl	4(%edx), %ebx
	movl	%ecx, 12(%esp)
	movl	%ebx, 16(%esp)
	movl	16(%esp), %esi
	shrl	$24, %esi
	movl	%esi, %ebx
	movb	%bl, (%eax)
	movl	16(%esp), %esi
	shrl	$16, %esi
	movl	%esi, %ebx
	movb	%bl, 1(%eax)
	movl	16(%esp), %edi
	movl	%edi, %ecx
	movb	%ch, 2(%eax)
	movl	16(%esp), %esi
	movl	%esi, %ebx
	movb	%bl, 3(%eax)
	movl	12(%esp), %ecx
	movl	16(%esp), %ebx
	shrdl	$24, %ebx, %ecx
	shrl	$24, %ebx
	movb	%cl, 4(%eax)
	movl	12(%esp), %ebx
	movl	16(%esp), %esi
	shrdl	$16, %esi, %ebx
	shrl	$16, %esi
	movb	%bl, 5(%eax)
	movl	12(%esp), %esi
	movl	%esi, %ecx
	movb	%ch, 6(%eax)
	movb	%cl, 7(%eax)
	addl	$8, %edx
	addl	$8, %eax
	cmpl	%ebp, %eax
	jne	L22
	addl	$36, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE5:
	.globl	__jit_sha512
__jit_sha512:
LFB6:
	pushl	%ebp
	movl	%esp, %ebp
	pushl	%esi
	pushl	%ebx
	andl	$-8, %esp
	subl	$284, %esp
	movl	$129, (%esp)
	call	__jit_malloc
	movl	%eax, %ebx
	testl	%eax, %eax
	je	L25
	movl	$0, 140(%esp)
	movl	$0, 144(%esp)
	movl	$0, 148(%esp)
	movl	$0, 152(%esp)
	movl	$-205731576, 76(%esp)
	movl	$1779033703, 80(%esp)
	movl	$-2067093701, 84(%esp)
	movl	$-1150833019, 88(%esp)
	movl	$-23791573, 92(%esp)
	movl	$1013904242, 96(%esp)
	movl	$1595750129, 100(%esp)
	movl	$-1521486534, 104(%esp)
	movl	$-1377402159, 108(%esp)
	movl	$1359893119, 112(%esp)
	movl	$725511199, 116(%esp)
	movl	$-1694144372, 120(%esp)
	movl	$-79577749, 124(%esp)
	movl	$528734635, 128(%esp)
	movl	$327033209, 132(%esp)
	movl	$1541459225, 136(%esp)
	movl	12(%ebp), %eax
	movl	%eax, 8(%esp)
	movl	8(%ebp), %eax
	movl	%eax, 4(%esp)
	leal	76(%esp), %esi
	movl	%esi, (%esp)
	call	_sha512_update
	leal	12(%esp), %eax
	movl	%eax, 4(%esp)
	movl	%esi, (%esp)
	call	_sha512_final
	movl	$0, %eax
	.p2align 6
L27:
	movzbl	12(%esp,%eax), %edx
	movl	%edx, %ecx
	shrb	$4, %cl
	movzbl	%cl, %ecx
	movzbl	__ZZ11_jit_sha512E3hex(%ecx), %ecx
	movb	%cl, (%ebx,%eax,2)
	andl	$15, %edx
	movzbl	__ZZ11_jit_sha512E3hex(%edx), %edx
	movb	%dl, 1(%ebx,%eax,2)
	addl	$1, %eax
	cmpl	$64, %eax
	jne	L27
	movb	$0, 128(%ebx)
L25:
	movl	%ebx, %eax
	leal	-8(%ebp), %esp
	popl	%ebx
	popl	%esi
	popl	%ebp
	ret
LFE6:
	.section .rdata,"dr"
	.align 4
__ZZ11_jit_sha512E3hex:
	.ascii "0123456789abcdef\0"
	.align 32
__ZZ12sha512_finalE7padding:
	.ascii "\200\0"
	.space 126
	.align 32
__ZL8sha512_k:
	.long	-685199838
	.long	1116352408
	.long	602891725
	.long	1899447441
	.long	-330482897
	.long	-1245643825
	.long	-2121671748
	.long	-373957723
	.long	-213338824
	.long	961987163
	.long	-1241133031
	.long	1508970993
	.long	-1357295717
	.long	-1841331548
	.long	-630357736
	.long	-1424204075
	.long	-1560083902
	.long	-670586216
	.long	1164996542
	.long	310598401
	.long	1323610764
	.long	607225278
	.long	-704662302
	.long	1426881987
	.long	-226784913
	.long	1925078388
	.long	991336113
	.long	-2132889090
	.long	633803317
	.long	-1680079193
	.long	-815192428
	.long	-1046744716
	.long	-1628353838
	.long	-459576895
	.long	944711139
	.long	-272742522
	.long	-1953704523
	.long	264347078
	.long	2007800933
	.long	604807628
	.long	1495990901
	.long	770255983
	.long	1856431235
	.long	1249150122
	.long	-1119749164
	.long	1555081692
	.long	-2096016459
	.long	1996064986
	.long	-295247957
	.long	-1740746414
	.long	766784016
	.long	-1473132947
	.long	-1728372417
	.long	-1341970488
	.long	-1091629340
	.long	-1084653625
	.long	1034457026
	.long	-958395405
	.long	-1828018395
	.long	-710438585
	.long	-536640913
	.long	113926993
	.long	168717936
	.long	338241895
	.long	1188179964
	.long	666307205
	.long	1546045734
	.long	773529912
	.long	1522805485
	.long	1294757372
	.long	-1651133473
	.long	1396182291
	.long	-1951439906
	.long	1695183700
	.long	1014477480
	.long	1986661051
	.long	1206759142
	.long	-2117940946
	.long	344077627
	.long	-1838011259
	.long	1290863460
	.long	-1564481375
	.long	-1136513023
	.long	-1474664885
	.long	-789014639
	.long	-1035236496
	.long	106217008
	.long	-949202525
	.long	-688958952
	.long	-778901479
	.long	1432725776
	.long	-694614492
	.long	1467031594
	.long	-200395387
	.long	851169720
	.long	275423344
	.long	-1194143544
	.long	430227734
	.long	1363258195
	.long	506948616
	.long	-544281703
	.long	659060556
	.long	-509917016
	.long	883997877
	.long	-976659869
	.long	958139571
	.long	-482243893
	.long	1322822218
	.long	2003034995
	.long	1537002063
	.long	-692930397
	.long	1747873779
	.long	1575990012
	.long	1955562222
	.long	1125592928
	.long	2024104815
	.long	-1578062990
	.long	-2067236844
	.long	442776044
	.long	-1933114872
	.long	593698344
	.long	-1866530822
	.long	-561857047
	.long	-1538233109
	.long	-1295615723
	.long	-1090935817
	.long	-479046869
	.long	-965641998
	.long	-366583396
	.long	-903397682
	.long	566280711
	.long	-779700025
	.long	-840897762
	.long	-354779690
	.long	-294727304
	.long	-176337025
	.long	1914138554
	.long	116418474
	.long	-1563912026
	.long	174292421
	.long	-1090974290
	.long	289380356
	.long	320620315
	.long	460393269
	.long	587496836
	.long	685471733
	.long	1086792851
	.long	852142971
	.long	365543100
	.long	1017036298
	.long	-1676669620
	.long	1126000580
	.long	-885112138
	.long	1288033470
	.long	-60457430
	.long	1501505948
	.long	987167468
	.long	1607167915
	.long	1246189591
	.long	1816402316
	.section .drectve
	.ascii " -export:\"_jit_sha512\""
	.ascii " -export:\"sha512_final\""
	.ascii " -export:\"sha512_update\""
	.ascii " -export:\"sha512_init\""
