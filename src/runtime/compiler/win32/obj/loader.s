	.text
	.globl	_get_peb32
_get_peb32:
LFB0:
/APP
 # 147 "loader.cc" 1
	movl %fs:0x30, %eax
 # 0 "" 2
/NO_APP
	ret
LFE0:
	.globl	__Z13ascii_toloweri
__Z13ascii_toloweri:
LFB1:
	movl	4(%esp), %eax
	leal	-65(%eax), %ecx
	leal	32(%eax), %edx
	cmpl	$26, %ecx
	cmovb	%edx, %eax
	ret
LFE1:
	.globl	__Z21wide_ascii_endswith_iPKtiPKc
__Z21wide_ascii_endswith_iPKtiPKc:
LFB2:
	leal	-20(%esp), %esp
	movl	%ebx, 4(%esp)
	movl	24(%esp), %ecx
	movl	28(%esp), %edx
	movl	32(%esp), %ebx
	cmpb	$0, (%ebx)
	je	L12
	movl	$0, %eax
	.p2align 4
L6:
	addl	$1, %eax
	cmpb	$0, (%ebx,%eax)
	jne	L6
L5:
	cmpl	%eax, %edx
	jl	L10
	testl	%eax, %eax
	jle	L9
	movl	%esi, 8(%esp)
	movl	%edi, 12(%esp)
	movl	%ebp, 16(%esp)
	movl	%edx, %esi
	subl	%eax, %esi
	leal	(%ecx,%esi,2), %edi
	leal	(%ecx,%edx,2), %ebp
L11:
	movsbl	(%edi), %eax
	movl	%eax, (%esp)
	call	__Z13ascii_toloweri
	movl	%eax, %esi
	movsbl	(%ebx), %eax
	movl	%eax, (%esp)
	call	__Z13ascii_toloweri
	cmpl	%eax, %esi
	jne	L16
	addl	$2, %edi
	addl	$1, %ebx
	cmpl	%ebp, %edi
	jne	L11
	movl	8(%esp), %esi
	movl	12(%esp), %edi
	movl	16(%esp), %ebp
L9:
	movl	$1, %eax
	jmp	L4
L12:
	movl	$0, %eax
	jmp	L5
L16:
	movl	8(%esp), %esi
	movl	12(%esp), %edi
	movl	16(%esp), %ebp
L10:
	movl	$0, %eax
L4:
	movl	4(%esp), %ebx
	leal	20(%esp), %esp
	ret
LFE2:
	.globl	__Z9str_equalPKcS0_
__Z9str_equalPKcS0_:
LFB3:
	pushl	%ebx
	movl	8(%esp), %edx
	movl	12(%esp), %ecx
	movzbl	(%edx), %eax
	testb	%al, %al
	je	L19
L18:
	movzbl	(%ecx), %ebx
	testb	%bl, %bl
	je	L26
	cmpb	%al, %bl
	jne	L23
	addl	$1, %edx
	addl	$1, %ecx
	movzbl	(%edx), %eax
	testb	%al, %al
	jne	L18
L19:
	cmpb	$0, (%ecx)
	sete	%al
L22:
	movzbl	%al, %eax
L17:
	popl	%ebx
	ret
L26:
	movl	$0, %eax
	jmp	L22
L23:
	movl	$0, %eax
	jmp	L17
LFE3:
	.globl	__Z11find_exportPvPKc
__Z11find_exportPvPKc:
LFB4:
	leal	-28(%esp), %esp
	movl	%esi, 16(%esp)
	movl	32(%esp), %esi
	cmpw	$23117, (%esi)
	jne	L30
	movl	%esi, %eax
	addl	60(%esi), %eax
	cmpl	$17744, (%eax)
	jne	L30
	movl	120(%eax), %edx
	cmpl	$0, 124(%eax)
	je	L30
	testl	%edx, %edx
	je	L30
	movl	%edi, 20(%esp)
	leal	(%esi,%edx), %eax
	movl	%eax, 8(%esp)
	movl	24(%eax), %edi
	testl	%edi, %edi
	je	L35
	movl	%ebx, 12(%esp)
	movl	%ebp, 24(%esp)
	movl	$0, %ebx
	movl	%esi, %ebp
	addl	32(%eax), %ebp
L32:
	movl	36(%esp), %eax
	movl	%eax, 4(%esp)
	movl	%esi, %eax
	addl	0(%ebp,%ebx,4), %eax
	movl	%eax, (%esp)
	call	__Z9str_equalPKcS0_
	testl	%eax, %eax
	jne	L36
	addl	$1, %ebx
	cmpl	%edi, %ebx
	jne	L32
	movl	12(%esp), %ebx
	movl	20(%esp), %edi
	movl	24(%esp), %ebp
L30:
	movl	$0, %eax
L27:
	movl	16(%esp), %esi
	leal	28(%esp), %esp
	ret
L35:
	movl	20(%esp), %edi
	jmp	L30
L36:
	leal	(%esi,%ebx,2), %eax
	movl	8(%esp), %ecx
	addl	36(%ecx), %eax
	movzwl	(%eax), %eax
	leal	(%esi,%eax,4), %eax
	addl	28(%ecx), %eax
	addl	(%eax), %esi
	movl	%esi, %eax
	movl	12(%esp), %ebx
	movl	20(%esp), %edi
	movl	24(%esp), %ebp
	jmp	L27
LFE4:
	.section .rdata,"dr"
LC0:
	.ascii "kernel32.dll\0"
	.text
	.globl	__Z13find_kernel32v
__Z13find_kernel32v:
LFB5:
/APP
 # 147 "loader.cc" 1
	movl %fs:0x30, %edx
 # 0 "" 2
/NO_APP
	movl	%edx, %eax
	testl	%edx, %edx
	je	L45
	movl	12(%edx), %eax
	testl	%eax, %eax
	je	L45
	pushl	%esi
	pushl	%ebx
	subl	$12, %esp
	leal	12(%eax), %esi
	movl	12(%eax), %ebx
	cmpl	%ebx, %esi
	je	L39
	testl	%ebx, %ebx
	jne	L41
L39:
	movl	$0, %eax
L37:
	addl	$12, %esp
	popl	%ebx
	popl	%esi
	ret
L40:
	movl	(%ebx), %ebx
	testl	%ebx, %ebx
	je	L39
	cmpl	%ebx, %esi
	je	L39
L41:
	movl	48(%ebx), %edx
	testl	%edx, %edx
	je	L40
	movl	$LC0, 8(%esp)
	movzwl	44(%ebx), %eax
	shrw	%ax
	movzwl	%ax, %eax
	movl	%eax, 4(%esp)
	movl	%edx, (%esp)
	call	__Z21wide_ascii_endswith_iPKtiPKc
	testl	%eax, %eax
	je	L40
	movl	24(%ebx), %eax
	jmp	L37
L45:
	ret
LFE5:
	.section .rdata,"dr"
LC1:
	.ascii "LoadLibraryA\0"
LC2:
	.ascii "GetProcAddress\0"
LC3:
	.ascii "GetStdHandle\0"
LC4:
	.ascii "GetCommandLineA\0"
LC5:
	.ascii "GetUserDefaultLCID\0"
LC6:
	.ascii "GetSystemDefaultLCID\0"
LC7:
	.ascii "WriteFile\0"
LC8:
	.ascii "ReadFile\0"
LC9:
	.ascii "user32.dll\0"
LC10:
	.ascii "MessageBoxA\0"
	.text
	.globl	_init_loader
_init_loader:
LFB6:
	leal	-16(%esp), %esp
	call	__Z13find_kernel32v
	testl	%eax, %eax
	je	L51
	movl	%ebx, 8(%esp)
	movl	%esi, 12(%esp)
	movl	%eax, %ebx
	movl	$LC1, 4(%esp)
	movl	%eax, (%esp)
	call	__Z11find_exportPvPKc
	movl	%eax, %esi
	movl	%eax, _p_LoadLibraryA
	movl	$LC2, 4(%esp)
	movl	%ebx, (%esp)
	call	__Z11find_exportPvPKc
	movl	%eax, _p_GetProcAddress
	testl	%eax, %eax
	je	L53
	testl	%esi, %esi
	je	L54
	movl	$LC3, 4(%esp)
	movl	%ebx, (%esp)
	call	*%eax
	subl	$8, %esp
	movl	%eax, _p_GetStdHandle
	movl	$LC4, 4(%esp)
	movl	%ebx, (%esp)
	call	*_p_GetProcAddress
	subl	$8, %esp
	movl	%eax, _p_GetCommandLineA
	movl	$LC5, 4(%esp)
	movl	%ebx, (%esp)
	call	*_p_GetProcAddress
	subl	$8, %esp
	movl	%eax, _p_GetUserDefaultLCID
	movl	$LC6, 4(%esp)
	movl	%ebx, (%esp)
	call	*_p_GetProcAddress
	subl	$8, %esp
	movl	%eax, _p_GetSystemDefaultLCID
	movl	$LC7, 4(%esp)
	movl	%ebx, (%esp)
	call	*_p_GetProcAddress
	subl	$8, %esp
	movl	%eax, _p_WriteFile
	movl	$LC8, 4(%esp)
	movl	%ebx, (%esp)
	call	*_p_GetProcAddress
	subl	$8, %esp
	movl	%eax, _p_ReadFile
	movl	$LC9, (%esp)
	call	*_p_LoadLibraryA
	subl	$4, %esp
	testl	%eax, %eax
	je	L55
	movl	$LC10, 4(%esp)
	movl	%eax, (%esp)
	call	*_p_GetProcAddress
	subl	$8, %esp
	movl	%eax, _p_MessageBoxA
	testl	%eax, %eax
	setne	%al
	movzbl	%al, %eax
	movl	8(%esp), %ebx
	movl	12(%esp), %esi
	jmp	L48
L53:
	movl	8(%esp), %ebx
	movl	12(%esp), %esi
	jmp	L51
L54:
	movl	8(%esp), %ebx
	movl	12(%esp), %esi
L51:
	movl	$0, %eax
L48:
	leal	16(%esp), %esp
	ret
L55:
	movl	8(%esp), %ebx
	movl	12(%esp), %esi
	jmp	L51
LFE6:
	.globl	_p_LoadLibraryA
	.bss
	.align 4
_p_LoadLibraryA:
	.space 4
