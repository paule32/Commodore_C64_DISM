// Stage 602: dBASE TObject demo, executes methods defined in System.Objects.prg.
#include "System.Objects.prg"

LOCAL Obj AS TObject
Obj = new TObject()

? Obj.ClassName()
class_bytes = Obj.InstanceSize()
? class_bytes
? Obj.InheritsFrom(TObject)

// Raw native pointers remain full-width, also on PE64.
class_vmt = Obj.ClassType()
class_parent = Obj.ClassParent()
name_ptr = Obj.ClassNameAddress()

Obj.Free()
