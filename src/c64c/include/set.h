#ifndef DBASE2MANY_C_SET_H
#define DBASE2MANY_C_SET_H

#include <stdbool.h>

/*
 * Eine Menge ist ein 16-Bit-Bitfeld. Gültige Elemente liegen im Bereich
 * 0..15. Für benannte Mengen kann die Compiler-Erweiterung verwendet werden:
 *
 *     typedef set<TColor> TColorSet;
 */
typedef unsigned int CSet;

#pragma link "../runtime/set_runtime.c"

CSet SetEmpty(void);
CSet SetOf(int element);
CSet SetAdd(CSet value, int element);
CSet SetRemove(CSet value, int element);
CSet SetUnion(CSet left, CSet right);
CSet SetIntersection(CSet left, CSet right);
CSet SetDifference(CSet left, CSet right);
bool SetContains(CSet value, int element);

#define SET_EMPTY()              SetEmpty()
#define SET_OF(element)          SetOf(element)
#define SET_ADD(value, element)  SetAdd((value), (element))
#define SET_REMOVE(value, item)  SetRemove((value), (item))
#define SET_HAS(value, item)     SetContains((value), (item))

#endif
