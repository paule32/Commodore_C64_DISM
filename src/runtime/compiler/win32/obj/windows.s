	.text
	.globl	_LoadLibraryA@4
_LoadLibraryA@4:
LFB0:
	subl	$4, %esp
	movl	8(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_LoadLibraryA
	subl	$4, %esp
	addl	$4, %esp
	ret	$4
LFE0:
	.globl	_MessageBoxA@16
_MessageBoxA@16:
LFB1:
	subl	$16, %esp
	movl	32(%esp), %eax
	movl	%eax, 12(%esp)
	movl	28(%esp), %eax
	movl	%eax, 8(%esp)
	movl	24(%esp), %eax
	movl	%eax, 4(%esp)
	movl	20(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_MessageBoxA
	subl	$16, %esp
	addl	$16, %esp
	ret	$16
LFE1:
	.globl	__jit_ExitProcess
__jit_ExitProcess:
LFB2:
	subl	$4, %esp
	movl	8(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_ExitProcess
	subl	$4, %esp
	addl	$4, %esp
	ret
LFE2:
	.globl	_ExitProcess@4
_ExitProcess@4:
LFB3:
	subl	$4, %esp
	movl	8(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_ExitProcess
	subl	$4, %esp
	addl	$4, %esp
	ret	$4
LFE3:
	.globl	_GetLastError@0
_GetLastError@0:
LFB4:
	call	*_p_GetLastError
	ret
LFE4:
	.globl	_SetLastError@4
_SetLastError@4:
LFB5:
	subl	$4, %esp
	movl	8(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_SetLastError
	subl	$4, %esp
	addl	$4, %esp
	ret	$4
LFE5:
	.globl	_WriteFile@20
_WriteFile@20:
LFB6:
	subl	$20, %esp
	movl	40(%esp), %eax
	movl	%eax, 16(%esp)
	movl	36(%esp), %eax
	movl	%eax, 12(%esp)
	movl	32(%esp), %eax
	movl	%eax, 8(%esp)
	movl	28(%esp), %eax
	movl	%eax, 4(%esp)
	movl	24(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_WriteFile
	subl	$20, %esp
	addl	$20, %esp
	ret	$20
LFE6:
	.globl	_ReadFile@20
_ReadFile@20:
LFB7:
	subl	$20, %esp
	movl	40(%esp), %eax
	movl	%eax, 16(%esp)
	movl	36(%esp), %eax
	movl	%eax, 12(%esp)
	movl	32(%esp), %eax
	movl	%eax, 8(%esp)
	movl	28(%esp), %eax
	movl	%eax, 4(%esp)
	movl	24(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_ReadFile
	subl	$20, %esp
	addl	$20, %esp
	ret	$20
LFE7:
	.globl	__jit_print_text
__jit_print_text:
LFB9:
	leal	-32(%esp), %esp
	movl	%ebx, 24(%esp)
	movl	36(%esp), %ebx
	testl	%ebx, %ebx
	je	L16
	movl	$-11, (%esp)
	call	*_p_GetStdHandle
	subl	$4, %esp
	testl	%eax, %eax
	je	L16
	movl	%esi, 28(%esp)
	movl	$0, 20(%esp)
	movl	_p_WriteFile, %ecx
	cmpb	$0, (%ebx)
	je	L20
	movl	$0, %edx
	.p2align 4
L19:
	addl	$1, %edx
	cmpb	$0, (%ebx,%edx)
	jne	L19
L18:
	movl	$0, 16(%esp)
	leal	20(%esp), %esi
	movl	%esi, 12(%esp)
	movl	%edx, 8(%esp)
	movl	%ebx, 4(%esp)
	movl	%eax, (%esp)
	call	*%ecx
	subl	$20, %esp
	movl	28(%esp), %esi
L16:
	movl	24(%esp), %ebx
	leal	32(%esp), %esp
	ret
L20:
	movl	$0, %edx
	jmp	L18
LFE9:
	.globl	_GetCommandLineA@0
_GetCommandLineA@0:
LFB10:
	call	*_p_GetCommandLineA
	ret
LFE10:
	.globl	_GetStdHandle@4
_GetStdHandle@4:
LFB11:
	subl	$4, %esp
	movl	8(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_GetStdHandle
	subl	$4, %esp
	addl	$4, %esp
	ret	$4
LFE11:
	.globl	_GetProcAddress@8
_GetProcAddress@8:
LFB12:
	subl	$8, %esp
	movl	16(%esp), %eax
	movl	%eax, 4(%esp)
	movl	12(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_GetProcAddress
	subl	$8, %esp
	addl	$8, %esp
	ret	$8
LFE12:
	.globl	_GetDriveTypeA@4
_GetDriveTypeA@4:
LFB13:
	subl	$4, %esp
	movl	8(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_GetDriveTypeA
	subl	$4, %esp
	addl	$4, %esp
	ret	$4
LFE13:
	.globl	_GetDiskFreeSpaceExA@16
_GetDiskFreeSpaceExA@16:
LFB14:
	subl	$16, %esp
	movl	32(%esp), %eax
	movl	%eax, 12(%esp)
	movl	28(%esp), %eax
	movl	%eax, 8(%esp)
	movl	24(%esp), %eax
	movl	%eax, 4(%esp)
	movl	20(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_GetDiskFreeSpaceExA
	subl	$16, %esp
	addl	$16, %esp
	ret	$16
LFE14:
	.globl	_GetDiskFreeSpaceA@20
_GetDiskFreeSpaceA@20:
LFB15:
	subl	$20, %esp
	movl	40(%esp), %eax
	movl	%eax, 16(%esp)
	movl	36(%esp), %eax
	movl	%eax, 12(%esp)
	movl	32(%esp), %eax
	movl	%eax, 8(%esp)
	movl	28(%esp), %eax
	movl	%eax, 4(%esp)
	movl	24(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_GetDiskFreeSpaceA
	subl	$20, %esp
	addl	$20, %esp
	ret	$20
LFE15:
	.globl	_GetVolumeInformationA@32
_GetVolumeInformationA@32:
LFB16:
	subl	$32, %esp
	movl	64(%esp), %eax
	movl	%eax, 28(%esp)
	movl	60(%esp), %eax
	movl	%eax, 24(%esp)
	movl	56(%esp), %eax
	movl	%eax, 20(%esp)
	movl	52(%esp), %eax
	movl	%eax, 16(%esp)
	movl	48(%esp), %eax
	movl	%eax, 12(%esp)
	movl	44(%esp), %eax
	movl	%eax, 8(%esp)
	movl	40(%esp), %eax
	movl	%eax, 4(%esp)
	movl	36(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_GetVolumeInformationA
	subl	$32, %esp
	addl	$32, %esp
	ret	$32
LFE16:
	.globl	_WNetGetConnectionA@12
_WNetGetConnectionA@12:
LFB17:
	subl	$12, %esp
	movl	24(%esp), %eax
	movl	%eax, 8(%esp)
	movl	20(%esp), %eax
	movl	%eax, 4(%esp)
	movl	16(%esp), %eax
	movl	%eax, (%esp)
	call	*_p_WNetGetConnectionA
	subl	$12, %esp
	addl	$12, %esp
	ret	$12
LFE17:
	.globl	_p_WNetGetConnectionA
	.bss
	.align 4
_p_WNetGetConnectionA:
	.space 4
	.globl	_p_GetVolumeInformationA
	.align 4
_p_GetVolumeInformationA:
	.space 4
	.globl	_p_GetDiskFreeSpaceA
	.align 4
_p_GetDiskFreeSpaceA:
	.space 4
	.globl	_p_GetDiskFreeSpaceExA
	.align 4
_p_GetDiskFreeSpaceExA:
	.space 4
	.globl	_p_GetDriveTypeA
	.align 4
_p_GetDriveTypeA:
	.space 4
	.globl	_p_WriteFile
	.align 4
_p_WriteFile:
	.space 4
	.globl	_p_ReadFile
	.align 4
_p_ReadFile:
	.space 4
	.globl	_p_GetSystemDefaultLCID
	.align 4
_p_GetSystemDefaultLCID:
	.space 4
	.globl	_p_GetUserDefaultLCID
	.align 4
_p_GetUserDefaultLCID:
	.space 4
	.globl	_p_MessageBoxA
	.align 4
_p_MessageBoxA:
	.space 4
	.globl	_p_GetCommandLineA
	.align 4
_p_GetCommandLineA:
	.space 4
	.globl	_p_ExitProcess
	.align 4
_p_ExitProcess:
	.space 4
	.globl	_p_GetStdHandle
	.align 4
_p_GetStdHandle:
	.space 4
	.globl	_p_GetProcAddress
	.align 4
_p_GetProcAddress:
	.space 4
	.globl	_p_SetLastError
	.align 4
_p_SetLastError:
	.space 4
	.globl	_p_GetLastError
	.align 4
_p_GetLastError:
	.space 4
	.section .drectve
	.ascii " -export:\"WNetGetConnectionA@12\""
	.ascii " -export:\"GetVolumeInformationA@32\""
	.ascii " -export:\"GetDiskFreeSpaceA@20\""
	.ascii " -export:\"GetDiskFreeSpaceExA@16\""
	.ascii " -export:\"GetDriveTypeA@4\""
	.ascii " -export:\"GetProcAddress@8\""
	.ascii " -export:\"GetStdHandle@4\""
	.ascii " -export:\"GetCommandLineA@0\""
	.ascii " -export:\"ReadFile@20\""
	.ascii " -export:\"WriteFile@20\""
	.ascii " -export:\"SetLastError@4\""
	.ascii " -export:\"GetLastError@0\""
	.ascii " -export:\"ExitProcess@4\""
	.ascii " -export:\"_jit_ExitProcess\""
	.ascii " -export:\"MessageBoxA@16\""
	.ascii " -export:\"LoadLibraryA@4\""
