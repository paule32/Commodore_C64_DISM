	.text
	.section	.text
	.align 2
	.globl	__ZNSt9AllocatorIcE5allocEj
__ZNSt9AllocatorIcE5allocEj:
LFB3:
/APP
 # 20 "allocator.cc" 1
	pushl  4(%esp)         
	call   __jit_malloc    
	addl   $4, %esp        
	ret    $4              
	
 # 0 "" 2
/NO_APP
LFE3:
	.section	.text
	.align 2
	.globl	__ZNSt9AllocatorIcE7reallocEPcj
__ZNSt9AllocatorIcE7reallocEPcj:
LFB4:
/APP
 # 51 "allocator.cc" 1
	movl  8(%esp), %eax    
	sall  $3, %eax         
	pushl %eax             
	pushl 8(%esp)          
	call  __jit_realloc    
	addl  $8, %esp         
	ret   $8               
	
 # 0 "" 2
/NO_APP
LFE4:
	.section	.text
	.align 2
	.globl	__ZNSt9AllocatorIcE4freeEPc
__ZNSt9AllocatorIcE4freeEPc:
LFB5:
/APP
 # 98 "allocator.cc" 1
	pushl 4(%esp)      
	call  __jit_free   
	addl  $4, %esp     
	ret   $4           
	
 # 0 "" 2
/NO_APP
	ret	$4
LFE5:
	.section	.text
	.align 2
	.globl	__ZNSt9AllocatorIiE5allocEj
__ZNSt9AllocatorIiE5allocEj:
LFB6:
/APP
 # 20 "allocator.cc" 1
	pushl  4(%esp)         
	call   __jit_malloc    
	addl   $4, %esp        
	ret    $4              
	
 # 0 "" 2
/NO_APP
LFE6:
	.section	.text
	.align 2
	.globl	__ZNSt9AllocatorIiE7reallocEPij
__ZNSt9AllocatorIiE7reallocEPij:
LFB7:
/APP
 # 51 "allocator.cc" 1
	movl  8(%esp), %eax    
	sall  $3, %eax         
	pushl %eax             
	pushl 8(%esp)          
	call  __jit_realloc    
	addl  $8, %esp         
	ret   $8               
	
 # 0 "" 2
/NO_APP
LFE7:
	.section	.text
	.align 2
	.globl	__ZNSt9AllocatorIiE4freeEPi
__ZNSt9AllocatorIiE4freeEPi:
LFB8:
/APP
 # 98 "allocator.cc" 1
	pushl 4(%esp)      
	call  __jit_free   
	addl  $4, %esp     
	ret   $4           
	
 # 0 "" 2
/NO_APP
	ret	$4
LFE8:
	.section	.text
	.align 2
	.globl	__ZNSt9AllocatorIdE5allocEj
__ZNSt9AllocatorIdE5allocEj:
LFB9:
/APP
 # 20 "allocator.cc" 1
	pushl  4(%esp)         
	call   __jit_malloc    
	addl   $4, %esp        
	ret    $4              
	
 # 0 "" 2
/NO_APP
LFE9:
	.section	.text
	.align 2
	.globl	__ZNSt9AllocatorIdE7reallocEPdj
__ZNSt9AllocatorIdE7reallocEPdj:
LFB10:
/APP
 # 51 "allocator.cc" 1
	movl  8(%esp), %eax    
	sall  $3, %eax         
	pushl %eax             
	pushl 8(%esp)          
	call  __jit_realloc    
	addl  $8, %esp         
	ret   $8               
	
 # 0 "" 2
/NO_APP
LFE10:
	.section	.text
	.align 2
	.globl	__ZNSt9AllocatorIdE4freeEPd
__ZNSt9AllocatorIdE4freeEPd:
LFB11:
/APP
 # 98 "allocator.cc" 1
	pushl 4(%esp)      
	call  __jit_free   
	addl  $4, %esp     
	ret   $4           
	
 # 0 "" 2
/NO_APP
	ret	$4
LFE11:
