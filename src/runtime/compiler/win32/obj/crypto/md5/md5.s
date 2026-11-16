	.text
__ZL13md5_transformPjPKh:
LFB0:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$80, %esp
	movl	%eax, %edi
	movl	%edx, %ecx
	movl	(%eax), %eax
	movl	%eax, 12(%esp)
	movl	4(%edi), %ebp
	movl	8(%edi), %eax
	movl	%eax, (%esp)
	movl	12(%edi), %eax
	movl	%eax, 4(%esp)
	movl	$0, %edx
	.p2align 6
L2:
	movzbl	1(%ecx,%edx,4), %eax
	sall	$8, %eax
	movzbl	2(%ecx,%edx,4), %ebx
	sall	$16, %ebx
	orl	%ebx, %eax
	movzbl	(%ecx,%edx,4), %ebx
	orl	%ebx, %eax
	movzbl	3(%ecx,%edx,4), %ebx
	sall	$24, %ebx
	orl	%ebx, %eax
	movl	%eax, 16(%esp,%edx,4)
	addl	$1, %edx
	cmpl	$16, %edx
	jne	L2
	movl	16(%esp), %ecx
	movl	12(%esp), %eax
	leal	-680876936(%ecx,%eax), %edx
	movl	(%esp), %esi
	movl	%esi, %eax
	movl	4(%esp), %ecx
	xorl	%ecx, %eax
	andl	%ebp, %eax
	xorl	%ecx, %eax
	addl	%edx, %eax
	roll	$7, %eax
	addl	%ebp, %eax
	movl	20(%esp), %ebx
	leal	-389564586(%ebx,%ecx), %ecx
	movl	%esi, %edx
	xorl	%ebp, %edx
	andl	%eax, %edx
	xorl	%esi, %edx
	addl	%ecx, %edx
	roll	$12, %edx
	addl	%eax, %edx
	movl	24(%esp), %ebx
	leal	606105819(%ebx,%esi), %ebx
	movl	%ebp, %ecx
	xorl	%eax, %ecx
	andl	%edx, %ecx
	xorl	%ebp, %ecx
	addl	%ebx, %ecx
	rorl	$15, %ecx
	addl	%edx, %ecx
	movl	28(%esp), %ebx
	leal	-1044525330(%ebx,%ebp), %esi
	movl	%eax, %ebx
	xorl	%edx, %ebx
	andl	%ecx, %ebx
	xorl	%eax, %ebx
	addl	%esi, %ebx
	rorl	$10, %ebx
	addl	%ecx, %ebx
	movl	32(%esp), %esi
	leal	-176418897(%esi,%eax), %esi
	movl	%edx, %eax
	xorl	%ecx, %eax
	andl	%ebx, %eax
	xorl	%edx, %eax
	addl	%esi, %eax
	roll	$7, %eax
	addl	%ebx, %eax
	movl	36(%esp), %esi
	leal	1200080426(%esi,%edx), %esi
	movl	%ecx, %edx
	xorl	%ebx, %edx
	andl	%eax, %edx
	xorl	%ecx, %edx
	addl	%esi, %edx
	roll	$12, %edx
	addl	%eax, %edx
	movl	40(%esp), %esi
	leal	-1473231341(%esi,%ecx), %esi
	movl	%ebx, %ecx
	xorl	%eax, %ecx
	andl	%edx, %ecx
	xorl	%ebx, %ecx
	addl	%esi, %ecx
	rorl	$15, %ecx
	addl	%edx, %ecx
	movl	44(%esp), %esi
	leal	-45705983(%esi,%ebx), %esi
	movl	%eax, %ebx
	xorl	%edx, %ebx
	andl	%ecx, %ebx
	xorl	%eax, %ebx
	addl	%esi, %ebx
	rorl	$10, %ebx
	addl	%ecx, %ebx
	movl	48(%esp), %esi
	leal	1770035416(%esi,%eax), %esi
	movl	%edx, %eax
	xorl	%ecx, %eax
	andl	%ebx, %eax
	xorl	%edx, %eax
	addl	%esi, %eax
	roll	$7, %eax
	addl	%ebx, %eax
	movl	52(%esp), %esi
	leal	-1958414417(%esi,%edx), %esi
	movl	%ecx, %edx
	xorl	%ebx, %edx
	andl	%eax, %edx
	xorl	%ecx, %edx
	addl	%esi, %edx
	roll	$12, %edx
	addl	%eax, %edx
	movl	56(%esp), %esi
	leal	-42063(%esi,%ecx), %esi
	movl	%ebx, %ecx
	xorl	%eax, %ecx
	andl	%edx, %ecx
	xorl	%ebx, %ecx
	addl	%esi, %ecx
	rorl	$15, %ecx
	addl	%edx, %ecx
	movl	60(%esp), %esi
	leal	-1990404162(%esi,%ebx), %esi
	movl	%eax, %ebx
	xorl	%edx, %ebx
	andl	%ecx, %ebx
	xorl	%eax, %ebx
	addl	%esi, %ebx
	rorl	$10, %ebx
	addl	%ecx, %ebx
	movl	64(%esp), %esi
	leal	1804603682(%esi,%eax), %esi
	movl	%edx, %eax
	xorl	%ecx, %eax
	andl	%ebx, %eax
	xorl	%edx, %eax
	addl	%esi, %eax
	roll	$7, %eax
	addl	%ebx, %eax
	movl	68(%esp), %esi
	leal	-40341101(%esi,%edx), %esi
	movl	%ecx, %edx
	xorl	%ebx, %edx
	andl	%eax, %edx
	xorl	%ecx, %edx
	addl	%esi, %edx
	roll	$12, %edx
	addl	%eax, %edx
	movl	72(%esp), %esi
	leal	-1502002290(%esi,%ecx), %esi
	movl	%ebx, %ecx
	xorl	%eax, %ecx
	andl	%edx, %ecx
	xorl	%ebx, %ecx
	addl	%esi, %ecx
	rorl	$15, %ecx
	addl	%edx, %ecx
	movl	76(%esp), %esi
	leal	1236535329(%esi,%ebx), %esi
	movl	%eax, %ebx
	xorl	%edx, %ebx
	andl	%ecx, %ebx
	xorl	%eax, %ebx
	addl	%esi, %ebx
	rorl	$10, %ebx
	addl	%ecx, %ebx
	movl	20(%esp), %esi
	leal	-165796510(%esi,%eax), %esi
	movl	%ecx, %eax
	xorl	%ebx, %eax
	andl	%edx, %eax
	xorl	%ecx, %eax
	addl	%esi, %eax
	roll	$5, %eax
	addl	%ebx, %eax
	movl	40(%esp), %esi
	leal	-1069501632(%esi,%edx), %esi
	movl	%ebx, %edx
	xorl	%eax, %edx
	andl	%ecx, %edx
	xorl	%ebx, %edx
	addl	%esi, %edx
	roll	$9, %edx
	addl	%eax, %edx
	movl	60(%esp), %esi
	leal	643717713(%esi,%ecx), %esi
	movl	%eax, %ecx
	xorl	%edx, %ecx
	andl	%ebx, %ecx
	xorl	%eax, %ecx
	addl	%esi, %ecx
	roll	$14, %ecx
	addl	%edx, %ecx
	movl	16(%esp), %esi
	leal	-373897302(%esi,%ebx), %esi
	movl	%edx, %ebx
	xorl	%ecx, %ebx
	andl	%eax, %ebx
	xorl	%edx, %ebx
	addl	%esi, %ebx
	rorl	$12, %ebx
	addl	%ecx, %ebx
	movl	36(%esp), %esi
	leal	-701558691(%esi,%eax), %esi
	movl	%ecx, %eax
	xorl	%ebx, %eax
	andl	%edx, %eax
	xorl	%ecx, %eax
	addl	%esi, %eax
	roll	$5, %eax
	addl	%ebx, %eax
	movl	56(%esp), %esi
	leal	38016083(%esi,%edx), %esi
	movl	%ebx, %edx
	xorl	%eax, %edx
	andl	%ecx, %edx
	xorl	%ebx, %edx
	addl	%esi, %edx
	roll	$9, %edx
	addl	%eax, %edx
	movl	76(%esp), %esi
	leal	-660478335(%esi,%ecx), %esi
	movl	%eax, %ecx
	xorl	%edx, %ecx
	andl	%ebx, %ecx
	xorl	%eax, %ecx
	addl	%esi, %ecx
	roll	$14, %ecx
	addl	%edx, %ecx
	movl	32(%esp), %esi
	leal	-405537848(%esi,%ebx), %esi
	movl	%edx, %ebx
	xorl	%ecx, %ebx
	andl	%eax, %ebx
	xorl	%edx, %ebx
	addl	%esi, %ebx
	rorl	$12, %ebx
	addl	%ecx, %ebx
	movl	52(%esp), %esi
	leal	568446438(%esi,%eax), %esi
	movl	%ecx, %eax
	xorl	%ebx, %eax
	andl	%edx, %eax
	xorl	%ecx, %eax
	addl	%esi, %eax
	roll	$5, %eax
	addl	%ebx, %eax
	movl	72(%esp), %esi
	leal	-1019803690(%esi,%edx), %esi
	movl	%ebx, %edx
	xorl	%eax, %edx
	andl	%ecx, %edx
	xorl	%ebx, %edx
	addl	%esi, %edx
	roll	$9, %edx
	addl	%eax, %edx
	movl	28(%esp), %esi
	leal	-187363961(%esi,%ecx), %esi
	movl	%eax, %ecx
	xorl	%edx, %ecx
	andl	%ebx, %ecx
	xorl	%eax, %ecx
	addl	%esi, %ecx
	roll	$14, %ecx
	addl	%edx, %ecx
	movl	48(%esp), %esi
	leal	1163531501(%esi,%ebx), %esi
	movl	%edx, %ebx
	xorl	%ecx, %ebx
	andl	%eax, %ebx
	xorl	%edx, %ebx
	addl	%esi, %ebx
	rorl	$12, %ebx
	leal	(%ecx,%ebx), %esi
	movl	68(%esp), %ebx
	leal	-1444681467(%ebx,%eax), %ebx
	movl	%ecx, %eax
	xorl	%esi, %eax
	andl	%edx, %eax
	xorl	%ecx, %eax
	addl	%ebx, %eax
	roll	$5, %eax
	addl	%esi, %eax
	movl	24(%esp), %ebx
	leal	-51403784(%ebx,%edx), %ebx
	movl	%esi, %edx
	xorl	%eax, %edx
	andl	%ecx, %edx
	xorl	%esi, %edx
	addl	%ebx, %edx
	roll	$9, %edx
	addl	%eax, %edx
	movl	44(%esp), %ebx
	leal	1735328473(%ebx,%ecx), %ebx
	movl	%eax, %ecx
	xorl	%edx, %ecx
	andl	%esi, %ecx
	xorl	%eax, %ecx
	addl	%ebx, %ecx
	roll	$14, %ecx
	leal	(%edx,%ecx), %ebx
	movl	%edx, %ecx
	movl	%ebx, 8(%esp)
	xorl	%ebx, %ecx
	movl	64(%esp), %ebx
	leal	-1926607734(%ebx,%esi), %ebx
	movl	%eax, %esi
	andl	%ecx, %esi
	xorl	%edx, %esi
	addl	%ebx, %esi
	rorl	$12, %esi
	movl	8(%esp), %ebx
	addl	%ebx, %esi
	movl	36(%esp), %ebx
	leal	-378558(%ebx,%eax), %eax
	xorl	%esi, %ecx
	addl	%eax, %ecx
	roll	$4, %ecx
	leal	(%esi,%ecx), %eax
	movl	48(%esp), %ebx
	leal	-2022574463(%ebx,%edx), %ecx
	movl	8(%esp), %edx
	xorl	%esi, %edx
	xorl	%eax, %edx
	addl	%ecx, %edx
	roll	$11, %edx
	addl	%eax, %edx
	movl	60(%esp), %ebx
	movl	8(%esp), %ecx
	leal	1839030562(%ebx,%ecx), %ebx
	movl	%esi, %ecx
	xorl	%eax, %ecx
	xorl	%edx, %ecx
	addl	%ebx, %ecx
	roll	$16, %ecx
	addl	%edx, %ecx
	movl	72(%esp), %ebx
	leal	-35309556(%ebx,%esi), %esi
	movl	%eax, %ebx
	xorl	%edx, %ebx
	xorl	%ecx, %ebx
	addl	%esi, %ebx
	rorl	$9, %ebx
	addl	%ecx, %ebx
	movl	20(%esp), %esi
	leal	-1530992060(%esi,%eax), %esi
	movl	%edx, %eax
	xorl	%ecx, %eax
	xorl	%ebx, %eax
	addl	%esi, %eax
	roll	$4, %eax
	addl	%ebx, %eax
	movl	32(%esp), %esi
	leal	1272893353(%esi,%edx), %esi
	movl	%ecx, %edx
	xorl	%ebx, %edx
	xorl	%eax, %edx
	addl	%esi, %edx
	roll	$11, %edx
	leal	(%eax,%edx), %esi
	movl	44(%esp), %edx
	leal	-155497632(%edx,%ecx), %ecx
	movl	%ebx, %edx
	xorl	%eax, %edx
	xorl	%esi, %edx
	addl	%ecx, %edx
	roll	$16, %edx
	leal	(%esi,%edx), %ecx
	movl	56(%esp), %edx
	leal	-1094730640(%edx,%ebx), %ebx
	movl	%eax, %edx
	xorl	%esi, %edx
	xorl	%ecx, %edx
	addl	%ebx, %edx
	rorl	$9, %edx
	addl	%ecx, %edx
	movl	68(%esp), %ebx
	leal	681279174(%ebx,%eax), %ebx
	movl	%esi, %eax
	xorl	%ecx, %eax
	xorl	%edx, %eax
	addl	%ebx, %eax
	roll	$4, %eax
	leal	(%edx,%eax), %ebx
	movl	16(%esp), %eax
	leal	-358537222(%eax,%esi), %esi
	movl	%ecx, %eax
	xorl	%edx, %eax
	xorl	%ebx, %eax
	addl	%esi, %eax
	roll	$11, %eax
	leal	(%ebx,%eax), %esi
	movl	28(%esp), %eax
	leal	-722521979(%eax,%ecx), %ecx
	movl	%edx, %eax
	xorl	%ebx, %eax
	xorl	%esi, %eax
	addl	%ecx, %eax
	roll	$16, %eax
	addl	%esi, %eax
	movl	40(%esp), %ecx
	leal	76029189(%ecx,%edx), %ecx
	movl	%ebx, %edx
	xorl	%esi, %edx
	xorl	%eax, %edx
	addl	%ecx, %edx
	rorl	$9, %edx
	leal	(%eax,%edx), %ecx
	movl	52(%esp), %edx
	leal	-640364487(%edx,%ebx), %ebx
	movl	%esi, %edx
	xorl	%eax, %edx
	xorl	%ecx, %edx
	addl	%ebx, %edx
	roll	$4, %edx
	leal	(%ecx,%edx), %ebx
	movl	64(%esp), %edx
	leal	-421815835(%edx,%esi), %esi
	movl	%eax, %edx
	xorl	%ecx, %edx
	xorl	%ebx, %edx
	addl	%esi, %edx
	roll	$11, %edx
	addl	%ebx, %edx
	movl	76(%esp), %esi
	leal	530742520(%esi,%eax), %esi
	movl	%ecx, %eax
	xorl	%ebx, %eax
	xorl	%edx, %eax
	addl	%esi, %eax
	roll	$16, %eax
	leal	(%edx,%eax), %esi
	movl	24(%esp), %eax
	leal	-995338651(%eax,%ecx), %ecx
	movl	%ebx, %eax
	xorl	%edx, %eax
	xorl	%esi, %eax
	addl	%ecx, %eax
	rorl	$9, %eax
	leal	(%esi,%eax), %ecx
	movl	16(%esp), %eax
	leal	-198630844(%eax,%ebx), %ebx
	movl	%edx, %eax
	notl	%eax
	orl	%ecx, %eax
	xorl	%esi, %eax
	addl	%ebx, %eax
	roll	$6, %eax
	addl	%ecx, %eax
	movl	44(%esp), %ebx
	leal	1126891415(%ebx,%edx), %ebx
	movl	%esi, %edx
	notl	%edx
	orl	%eax, %edx
	xorl	%ecx, %edx
	addl	%ebx, %edx
	roll	$10, %edx
	leal	(%eax,%edx), %ebx
	movl	72(%esp), %edx
	leal	-1416354905(%edx,%esi), %esi
	movl	%ecx, %edx
	notl	%edx
	orl	%ebx, %edx
	xorl	%eax, %edx
	addl	%esi, %edx
	roll	$15, %edx
	leal	(%ebx,%edx), %esi
	movl	36(%esp), %edx
	leal	-57434055(%edx,%ecx), %ecx
	movl	%eax, %edx
	notl	%edx
	orl	%esi, %edx
	xorl	%ebx, %edx
	addl	%ecx, %edx
	rorl	$11, %edx
	addl	%esi, %edx
	movl	64(%esp), %ecx
	leal	1700485571(%ecx,%eax), %ecx
	movl	%ebx, %eax
	notl	%eax
	orl	%edx, %eax
	xorl	%esi, %eax
	addl	%ecx, %eax
	roll	$6, %eax
	leal	(%edx,%eax), %ecx
	movl	28(%esp), %eax
	leal	-1894986606(%eax,%ebx), %ebx
	movl	%esi, %eax
	notl	%eax
	orl	%ecx, %eax
	xorl	%edx, %eax
	addl	%ebx, %eax
	roll	$10, %eax
	leal	(%ecx,%eax), %ebx
	movl	56(%esp), %eax
	leal	-1051523(%eax,%esi), %esi
	movl	%edx, %eax
	notl	%eax
	orl	%ebx, %eax
	xorl	%ecx, %eax
	addl	%esi, %eax
	roll	$15, %eax
	addl	%ebx, %eax
	movl	20(%esp), %esi
	leal	-2054922799(%esi,%edx), %esi
	movl	%ecx, %edx
	notl	%edx
	orl	%eax, %edx
	xorl	%ebx, %edx
	addl	%esi, %edx
	rorl	$11, %edx
	leal	(%eax,%edx), %esi
	movl	48(%esp), %edx
	leal	1873313359(%edx,%ecx), %ecx
	movl	%ebx, %edx
	notl	%edx
	orl	%esi, %edx
	xorl	%eax, %edx
	addl	%ecx, %edx
	roll	$6, %edx
	leal	(%esi,%edx), %ecx
	movl	76(%esp), %edx
	leal	-30611744(%edx,%ebx), %ebx
	movl	%eax, %edx
	notl	%edx
	orl	%ecx, %edx
	xorl	%esi, %edx
	addl	%ebx, %edx
	roll	$10, %edx
	addl	%ecx, %edx
	movl	40(%esp), %ebx
	leal	-1560198380(%ebx,%eax), %ebx
	movl	%esi, %eax
	notl	%eax
	orl	%edx, %eax
	xorl	%ecx, %eax
	addl	%ebx, %eax
	roll	$15, %eax
	leal	(%edx,%eax), %ebx
	movl	68(%esp), %eax
	leal	1309151649(%eax,%esi), %esi
	movl	%ecx, %eax
	notl	%eax
	orl	%ebx, %eax
	xorl	%edx, %eax
	addl	%esi, %eax
	rorl	$11, %eax
	leal	(%ebx,%eax), %esi
	movl	32(%esp), %eax
	leal	-145523070(%eax,%ecx), %ecx
	movl	%edx, %eax
	notl	%eax
	orl	%esi, %eax
	xorl	%ebx, %eax
	addl	%ecx, %eax
	roll	$6, %eax
	addl	%esi, %eax
	movl	60(%esp), %ecx
	leal	-1120210379(%ecx,%edx), %ecx
	movl	%ebx, %edx
	notl	%edx
	orl	%eax, %edx
	xorl	%esi, %edx
	addl	%ecx, %edx
	roll	$10, %edx
	addl	%eax, %edx
	movl	24(%esp), %ecx
	leal	718787259(%ecx,%ebx), %ebx
	movl	%esi, %ecx
	notl	%ecx
	orl	%edx, %ecx
	xorl	%eax, %ecx
	addl	%ebx, %ecx
	roll	$15, %ecx
	addl	%edx, %ecx
	movl	52(%esp), %ebx
	leal	-343485551(%ebx,%esi), %esi
	movl	%eax, %ebx
	notl	%ebx
	orl	%ecx, %ebx
	xorl	%edx, %ebx
	addl	%esi, %ebx
	movl	12(%esp), %esi
	addl	%esi, %eax
	movl	%eax, (%edi)
	rorl	$11, %ebx
	leal	0(%ebp,%ecx), %eax
	addl	%eax, %ebx
	movl	%ebx, 4(%edi)
	movl	(%esp), %esi
	leal	(%esi,%ecx), %eax
	movl	%eax, 8(%edi)
	movl	4(%esp), %ecx
	leal	(%ecx,%edx), %eax
	movl	%eax, 12(%edi)
	addl	$80, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE0:
	.globl	__jit_md5_init
__jit_md5_init:
LFB1:
	movl	4(%esp), %eax
	movl	$0, 16(%eax)
	movl	$0, 20(%eax)
	movl	$1732584193, (%eax)
	movl	$-271733879, 4(%eax)
	movl	$-1732584194, 8(%eax)
	movl	$271733878, 12(%eax)
	ret
LFE1:
	.globl	__jit_md5_update
__jit_md5_update:
LFB2:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$12, %esp
	movl	32(%esp), %edi
	movl	40(%esp), %esi
	movl	16(%edi), %ecx
	movl	20(%edi), %ebx
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
	movl	%eax, 16(%edi)
	movl	%edx, 20(%edi)
	movl	$64, %ebx
	subl	%ebp, %ebx
	cmpl	%ebx, %esi
	jnb	L13
	movl	$0, %ebx
L7:
	subl	%ebx, %esi
	movl	%esi, 8(%esp)
	movl	%ebx, %eax
	addl	36(%esp), %eax
	movl	%eax, 4(%esp)
	leal	24(%edi,%ebp), %eax
	movl	%eax, (%esp)
	call	__jit_memcpy
	addl	$12, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
L13:
	movl	%ebx, 8(%esp)
	movl	36(%esp), %eax
	movl	%eax, 4(%esp)
	leal	24(%edi,%ebp), %eax
	movl	%eax, (%esp)
	call	__jit_memcpy
	leal	24(%edi), %edx
	movl	%edi, %eax
	call	__ZL13md5_transformPjPKh
	movl	$127, %eax
	subl	%ebp, %eax
	cmpl	%esi, %eax
	jnb	L10
	movl	36(%esp), %ebp
L8:
	leal	0(%ebp,%ebx), %edx
	movl	%edi, %eax
	call	__ZL13md5_transformPjPKh
	movl	%ebx, %eax
	addl	$64, %ebx
	addl	$127, %eax
	cmpl	%esi, %eax
	jb	L8
	movl	$0, %ebp
	jmp	L7
L10:
	movl	$0, %ebp
	jmp	L7
LFE2:
	.globl	__jit_md5_final
__jit_md5_final:
LFB3:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$28, %esp
	movl	48(%esp), %ebx
	movl	16(%ebx), %eax
	movl	20(%ebx), %edx
	movl	%eax, 12(%esp)
	movl	%edx, 16(%esp)
	movl	$0, %edi
	movl	%ebx, %ebp
	movl	%eax, %ebx
	movl	%edx, %esi
	.p2align 6
L15:
	leal	0(,%edi,8), %ecx
	movl	%ebx, %eax
	movl	%esi, %edx
	shrdl	%cl, %edx, %eax
	shrl	%cl, %edx
	testb	$32, %cl
	je	L22
	movl	%edx, %eax
	xorl	%edx, %edx
L22:
	movb	%al, 20(%esp,%edi)
	addl	$1, %edi
	cmpl	$8, %edi
	jne	L15
	movl	%ebp, %ebx
	movl	52(%esp), %esi
	movl	12(%esp), %eax
	movl	16(%esp), %edx
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
	movl	$__ZZ14_jit_md5_finalE7padding, 4(%esp)
	movl	%ebp, (%esp)
	call	__jit_md5_update
	movl	$8, 8(%esp)
	leal	20(%esp), %eax
	movl	%eax, 4(%esp)
	movl	%ebp, (%esp)
	call	__jit_md5_update
	movl	$0, %eax
L18:
	movl	(%ebx,%eax,4), %edx
	movb	%dl, (%esi,%eax,4)
	movl	(%ebx,%eax,4), %edx
	movb	%dh, 1(%esi,%eax,4)
	movzwl	2(%ebx,%eax,4), %edx
	movb	%dl, 2(%esi,%eax,4)
	movzbl	3(%ebx,%eax,4), %edx
	movb	%dl, 3(%esi,%eax,4)
	addl	$1, %eax
	cmpl	$4, %eax
	jne	L18
	addl	$28, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE3:
	.globl	__jit_md5
__jit_md5:
LFB5:
	pushl	%ebp
	movl	%esp, %ebp
	pushl	%ebx
	andl	$-8, %esp
	subl	$116, %esp
	movl	$0, 44(%esp)
	movl	$0, 48(%esp)
	movl	$1732584193, 28(%esp)
	movl	$-271733879, 32(%esp)
	movl	$-1732584194, 36(%esp)
	movl	$271733878, 40(%esp)
	movl	12(%ebp), %eax
	movl	%eax, 8(%esp)
	movl	8(%ebp), %eax
	movl	%eax, 4(%esp)
	leal	28(%esp), %ebx
	movl	%ebx, (%esp)
	call	__jit_md5_update
	leal	12(%esp), %eax
	movl	%eax, 4(%esp)
	movl	%ebx, (%esp)
	call	__jit_md5_final
	movl	$33, (%esp)
	call	__jit_malloc
	movl	%eax, %ebx
	testl	%eax, %eax
	je	L23
	movl	$0, %eax
	.p2align 6
L25:
	movzbl	12(%esp,%eax), %edx
	movl	%edx, %ecx
	shrb	$4, %cl
	movzbl	%cl, %ecx
	movzbl	__ZZL18bytes_to_hex_allocPKhjE3hex(%ecx), %ecx
	movb	%cl, (%ebx,%eax,2)
	andl	$15, %edx
	movzbl	__ZZL18bytes_to_hex_allocPKhjE3hex(%edx), %edx
	movb	%dl, 1(%ebx,%eax,2)
	addl	$1, %eax
	cmpl	$16, %eax
	jne	L25
	movb	$0, 32(%ebx)
L23:
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
__ZZ14_jit_md5_finalE7padding:
	.ascii "\200\0"
	.space 62
	.section .drectve
	.ascii " -export:\"_jit_md5\""
	.ascii " -export:\"_jit_md5_final\""
	.ascii " -export:\"_jit_md5_update\""
	.ascii " -export:\"_jit_md5_init\""
