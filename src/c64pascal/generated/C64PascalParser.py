# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,71,444,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,26,
        2,27,7,27,2,28,7,28,2,29,7,29,2,30,7,30,2,31,7,31,2,32,7,32,2,33,
        7,33,2,34,7,34,2,35,7,35,2,36,7,36,2,37,7,37,2,38,7,38,2,39,7,39,
        2,40,7,40,2,41,7,41,2,42,7,42,2,43,7,43,2,44,7,44,2,45,7,45,2,46,
        7,46,2,47,7,47,1,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,3,1,106,8,1,1,
        1,1,1,1,1,1,1,1,2,5,2,113,8,2,10,2,12,2,116,9,2,1,2,5,2,119,8,2,
        10,2,12,2,122,9,2,1,2,1,2,1,3,1,3,1,3,3,3,129,8,3,1,4,1,4,4,4,133,
        8,4,11,4,12,4,134,1,5,1,5,1,5,1,5,1,5,1,6,1,6,4,6,144,8,6,11,6,12,
        6,145,1,7,1,7,1,7,1,7,1,7,1,8,1,8,1,8,1,8,1,8,3,8,158,8,8,1,9,1,
        9,1,9,1,9,1,10,1,10,5,10,166,8,10,10,10,12,10,169,9,10,1,10,1,10,
        1,11,1,11,1,11,1,11,1,11,1,11,1,11,1,11,1,11,1,12,1,12,1,12,1,12,
        1,12,3,12,187,8,12,1,12,5,12,190,8,12,10,12,12,12,193,9,12,1,12,
        1,12,1,13,1,13,1,13,3,13,200,8,13,1,14,1,14,1,15,1,15,1,15,1,15,
        1,15,1,16,1,16,1,16,3,16,212,8,16,1,16,1,16,3,16,216,8,16,1,16,1,
        16,1,17,1,17,1,17,1,17,1,17,3,17,225,8,17,1,17,1,17,3,17,229,8,17,
        1,17,1,17,1,17,1,17,1,18,1,18,1,19,1,19,3,19,239,8,19,1,19,1,19,
        1,20,1,20,1,20,5,20,246,8,20,10,20,12,20,249,9,20,1,21,3,21,252,
        8,21,1,21,1,21,1,21,1,21,1,22,3,22,259,8,22,1,22,1,22,1,23,1,23,
        4,23,265,8,23,11,23,12,23,266,1,24,1,24,1,24,1,24,1,24,3,24,274,
        8,24,1,24,1,24,1,25,1,25,1,25,5,25,281,8,25,10,25,12,25,284,9,25,
        1,26,1,26,1,27,1,27,3,27,290,8,27,1,27,1,27,1,28,1,28,1,28,5,28,
        297,8,28,10,28,12,28,300,9,28,1,28,3,28,303,8,28,1,29,1,29,1,29,
        1,29,1,29,1,29,1,29,1,29,1,29,3,29,314,8,29,1,30,1,30,1,30,1,30,
        1,31,1,31,1,31,3,31,323,8,31,1,31,3,31,326,8,31,1,32,1,32,1,32,1,
        32,1,32,1,32,3,32,334,8,32,1,33,1,33,1,33,1,33,1,33,1,34,1,34,3,
        34,343,8,34,1,34,1,34,1,34,1,35,1,35,1,35,1,35,1,35,1,35,1,35,1,
        35,1,35,1,36,1,36,5,36,359,8,36,10,36,12,36,362,9,36,1,37,1,37,1,
        37,1,37,1,37,1,37,3,37,370,8,37,1,38,1,38,1,38,5,38,375,8,38,10,
        38,12,38,378,9,38,1,39,1,39,1,40,1,40,1,40,5,40,385,8,40,10,40,12,
        40,388,9,40,1,41,1,41,1,41,5,41,393,8,41,10,41,12,41,396,9,41,1,
        42,1,42,1,42,3,42,401,8,42,1,43,1,43,1,43,5,43,406,8,43,10,43,12,
        43,409,9,43,1,44,1,44,1,44,5,44,414,8,44,10,44,12,44,417,9,44,1,
        45,1,45,1,45,3,45,422,8,45,1,46,1,46,1,46,1,46,1,46,1,46,1,46,3,
        46,431,8,46,1,46,1,46,1,46,1,46,1,46,1,46,1,46,3,46,440,8,46,1,47,
        1,47,1,47,0,0,48,0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,
        36,38,40,42,44,46,48,50,52,54,56,58,60,62,64,66,68,70,72,74,76,78,
        80,82,84,86,88,90,92,94,0,11,1,0,23,26,1,0,27,30,2,0,2,2,4,4,2,0,
        31,34,67,67,1,0,15,16,1,0,40,41,1,0,44,49,1,0,50,51,2,0,37,38,52,
        53,2,0,42,42,50,51,1,0,63,65,453,0,96,1,0,0,0,2,99,1,0,0,0,4,114,
        1,0,0,0,6,128,1,0,0,0,8,130,1,0,0,0,10,136,1,0,0,0,12,141,1,0,0,
        0,14,147,1,0,0,0,16,157,1,0,0,0,18,159,1,0,0,0,20,163,1,0,0,0,22,
        172,1,0,0,0,24,181,1,0,0,0,26,199,1,0,0,0,28,201,1,0,0,0,30,203,
        1,0,0,0,32,208,1,0,0,0,34,219,1,0,0,0,36,234,1,0,0,0,38,236,1,0,
        0,0,40,242,1,0,0,0,42,251,1,0,0,0,44,258,1,0,0,0,46,262,1,0,0,0,
        48,268,1,0,0,0,50,277,1,0,0,0,52,285,1,0,0,0,54,287,1,0,0,0,56,293,
        1,0,0,0,58,313,1,0,0,0,60,315,1,0,0,0,62,319,1,0,0,0,64,327,1,0,
        0,0,66,335,1,0,0,0,68,340,1,0,0,0,70,347,1,0,0,0,72,356,1,0,0,0,
        74,369,1,0,0,0,76,371,1,0,0,0,78,379,1,0,0,0,80,381,1,0,0,0,82,389,
        1,0,0,0,84,397,1,0,0,0,86,402,1,0,0,0,88,410,1,0,0,0,90,421,1,0,
        0,0,92,439,1,0,0,0,94,441,1,0,0,0,96,97,3,2,1,0,97,98,5,0,0,1,98,
        1,1,0,0,0,99,100,5,1,0,0,100,105,5,67,0,0,101,102,5,54,0,0,102,103,
        3,50,25,0,103,104,5,55,0,0,104,106,1,0,0,0,105,101,1,0,0,0,105,106,
        1,0,0,0,106,107,1,0,0,0,107,108,5,60,0,0,108,109,3,4,2,0,109,110,
        5,62,0,0,110,3,1,0,0,0,111,113,3,6,3,0,112,111,1,0,0,0,113,116,1,
        0,0,0,114,112,1,0,0,0,114,115,1,0,0,0,115,120,1,0,0,0,116,114,1,
        0,0,0,117,119,3,34,17,0,118,117,1,0,0,0,119,122,1,0,0,0,120,118,
        1,0,0,0,120,121,1,0,0,0,121,123,1,0,0,0,122,120,1,0,0,0,123,124,
        3,54,27,0,124,5,1,0,0,0,125,129,3,8,4,0,126,129,3,12,6,0,127,129,
        3,46,23,0,128,125,1,0,0,0,128,126,1,0,0,0,128,127,1,0,0,0,129,7,
        1,0,0,0,130,132,5,2,0,0,131,133,3,10,5,0,132,131,1,0,0,0,133,134,
        1,0,0,0,134,132,1,0,0,0,134,135,1,0,0,0,135,9,1,0,0,0,136,137,5,
        67,0,0,137,138,5,47,0,0,138,139,3,78,39,0,139,140,5,60,0,0,140,11,
        1,0,0,0,141,143,5,3,0,0,142,144,3,14,7,0,143,142,1,0,0,0,144,145,
        1,0,0,0,145,143,1,0,0,0,145,146,1,0,0,0,146,13,1,0,0,0,147,148,5,
        67,0,0,148,149,5,47,0,0,149,150,3,16,8,0,150,151,5,60,0,0,151,15,
        1,0,0,0,152,158,3,52,26,0,153,158,3,18,9,0,154,158,3,20,10,0,155,
        158,3,22,11,0,156,158,3,24,12,0,157,152,1,0,0,0,157,153,1,0,0,0,
        157,154,1,0,0,0,157,155,1,0,0,0,157,156,1,0,0,0,158,17,1,0,0,0,159,
        160,5,54,0,0,160,161,3,50,25,0,161,162,5,55,0,0,162,19,1,0,0,0,163,
        167,5,19,0,0,164,166,3,30,15,0,165,164,1,0,0,0,166,169,1,0,0,0,167,
        165,1,0,0,0,167,168,1,0,0,0,168,170,1,0,0,0,169,167,1,0,0,0,170,
        171,5,6,0,0,171,21,1,0,0,0,172,173,5,20,0,0,173,174,5,56,0,0,174,
        175,3,78,39,0,175,176,5,61,0,0,176,177,3,78,39,0,177,178,5,57,0,
        0,178,179,5,21,0,0,179,180,3,52,26,0,180,23,1,0,0,0,181,186,5,22,
        0,0,182,183,5,54,0,0,183,184,3,52,26,0,184,185,5,55,0,0,185,187,
        1,0,0,0,186,182,1,0,0,0,186,187,1,0,0,0,187,191,1,0,0,0,188,190,
        3,26,13,0,189,188,1,0,0,0,190,193,1,0,0,0,191,189,1,0,0,0,191,192,
        1,0,0,0,192,194,1,0,0,0,193,191,1,0,0,0,194,195,5,6,0,0,195,25,1,
        0,0,0,196,200,3,28,14,0,197,200,3,30,15,0,198,200,3,32,16,0,199,
        196,1,0,0,0,199,197,1,0,0,0,199,198,1,0,0,0,200,27,1,0,0,0,201,202,
        7,0,0,0,202,29,1,0,0,0,203,204,3,50,25,0,204,205,5,59,0,0,205,206,
        3,52,26,0,206,207,5,60,0,0,207,31,1,0,0,0,208,209,3,36,18,0,209,
        211,5,67,0,0,210,212,3,38,19,0,211,210,1,0,0,0,211,212,1,0,0,0,212,
        215,1,0,0,0,213,214,5,59,0,0,214,216,3,52,26,0,215,213,1,0,0,0,215,
        216,1,0,0,0,216,217,1,0,0,0,217,218,5,60,0,0,218,33,1,0,0,0,219,
        220,3,36,18,0,220,221,5,67,0,0,221,222,5,62,0,0,222,224,5,67,0,0,
        223,225,3,38,19,0,224,223,1,0,0,0,224,225,1,0,0,0,225,228,1,0,0,
        0,226,227,5,59,0,0,227,229,3,52,26,0,228,226,1,0,0,0,228,229,1,0,
        0,0,229,230,1,0,0,0,230,231,5,60,0,0,231,232,3,44,22,0,232,233,5,
        60,0,0,233,35,1,0,0,0,234,235,7,1,0,0,235,37,1,0,0,0,236,238,5,54,
        0,0,237,239,3,40,20,0,238,237,1,0,0,0,238,239,1,0,0,0,239,240,1,
        0,0,0,240,241,5,55,0,0,241,39,1,0,0,0,242,247,3,42,21,0,243,244,
        5,60,0,0,244,246,3,42,21,0,245,243,1,0,0,0,246,249,1,0,0,0,247,245,
        1,0,0,0,247,248,1,0,0,0,248,41,1,0,0,0,249,247,1,0,0,0,250,252,7,
        2,0,0,251,250,1,0,0,0,251,252,1,0,0,0,252,253,1,0,0,0,253,254,3,
        50,25,0,254,255,5,59,0,0,255,256,3,52,26,0,256,43,1,0,0,0,257,259,
        3,46,23,0,258,257,1,0,0,0,258,259,1,0,0,0,259,260,1,0,0,0,260,261,
        3,54,27,0,261,45,1,0,0,0,262,264,5,4,0,0,263,265,3,48,24,0,264,263,
        1,0,0,0,265,266,1,0,0,0,266,264,1,0,0,0,266,267,1,0,0,0,267,47,1,
        0,0,0,268,269,3,50,25,0,269,270,5,59,0,0,270,273,3,52,26,0,271,272,
        5,43,0,0,272,274,3,78,39,0,273,271,1,0,0,0,273,274,1,0,0,0,274,275,
        1,0,0,0,275,276,5,60,0,0,276,49,1,0,0,0,277,282,5,67,0,0,278,279,
        5,58,0,0,279,281,5,67,0,0,280,278,1,0,0,0,281,284,1,0,0,0,282,280,
        1,0,0,0,282,283,1,0,0,0,283,51,1,0,0,0,284,282,1,0,0,0,285,286,7,
        3,0,0,286,53,1,0,0,0,287,289,5,5,0,0,288,290,3,56,28,0,289,288,1,
        0,0,0,289,290,1,0,0,0,290,291,1,0,0,0,291,292,5,6,0,0,292,55,1,0,
        0,0,293,298,3,58,29,0,294,295,5,60,0,0,295,297,3,58,29,0,296,294,
        1,0,0,0,297,300,1,0,0,0,298,296,1,0,0,0,298,299,1,0,0,0,299,302,
        1,0,0,0,300,298,1,0,0,0,301,303,5,60,0,0,302,301,1,0,0,0,302,303,
        1,0,0,0,303,57,1,0,0,0,304,314,3,54,27,0,305,314,3,60,30,0,306,314,
        3,62,31,0,307,314,3,64,32,0,308,314,3,66,33,0,309,314,3,68,34,0,
        310,314,3,70,35,0,311,314,5,17,0,0,312,314,5,18,0,0,313,304,1,0,
        0,0,313,305,1,0,0,0,313,306,1,0,0,0,313,307,1,0,0,0,313,308,1,0,
        0,0,313,309,1,0,0,0,313,310,1,0,0,0,313,311,1,0,0,0,313,312,1,0,
        0,0,314,59,1,0,0,0,315,316,3,72,36,0,316,317,5,43,0,0,317,318,3,
        78,39,0,318,61,1,0,0,0,319,325,3,72,36,0,320,322,5,54,0,0,321,323,
        3,76,38,0,322,321,1,0,0,0,322,323,1,0,0,0,323,324,1,0,0,0,324,326,
        5,55,0,0,325,320,1,0,0,0,325,326,1,0,0,0,326,63,1,0,0,0,327,328,
        5,7,0,0,328,329,3,78,39,0,329,330,5,8,0,0,330,333,3,58,29,0,331,
        332,5,9,0,0,332,334,3,58,29,0,333,331,1,0,0,0,333,334,1,0,0,0,334,
        65,1,0,0,0,335,336,5,10,0,0,336,337,3,78,39,0,337,338,5,11,0,0,338,
        339,3,58,29,0,339,67,1,0,0,0,340,342,5,12,0,0,341,343,3,56,28,0,
        342,341,1,0,0,0,342,343,1,0,0,0,343,344,1,0,0,0,344,345,5,13,0,0,
        345,346,3,78,39,0,346,69,1,0,0,0,347,348,5,14,0,0,348,349,5,67,0,
        0,349,350,5,43,0,0,350,351,3,78,39,0,351,352,7,4,0,0,352,353,3,78,
        39,0,353,354,5,11,0,0,354,355,3,58,29,0,355,71,1,0,0,0,356,360,5,
        67,0,0,357,359,3,74,37,0,358,357,1,0,0,0,359,362,1,0,0,0,360,358,
        1,0,0,0,360,361,1,0,0,0,361,73,1,0,0,0,362,360,1,0,0,0,363,364,5,
        62,0,0,364,370,5,67,0,0,365,366,5,56,0,0,366,367,3,78,39,0,367,368,
        5,57,0,0,368,370,1,0,0,0,369,363,1,0,0,0,369,365,1,0,0,0,370,75,
        1,0,0,0,371,376,3,78,39,0,372,373,5,58,0,0,373,375,3,78,39,0,374,
        372,1,0,0,0,375,378,1,0,0,0,376,374,1,0,0,0,376,377,1,0,0,0,377,
        77,1,0,0,0,378,376,1,0,0,0,379,380,3,80,40,0,380,79,1,0,0,0,381,
        386,3,82,41,0,382,383,7,5,0,0,383,385,3,82,41,0,384,382,1,0,0,0,
        385,388,1,0,0,0,386,384,1,0,0,0,386,387,1,0,0,0,387,81,1,0,0,0,388,
        386,1,0,0,0,389,394,3,84,42,0,390,391,5,39,0,0,391,393,3,84,42,0,
        392,390,1,0,0,0,393,396,1,0,0,0,394,392,1,0,0,0,394,395,1,0,0,0,
        395,83,1,0,0,0,396,394,1,0,0,0,397,400,3,86,43,0,398,399,7,6,0,0,
        399,401,3,86,43,0,400,398,1,0,0,0,400,401,1,0,0,0,401,85,1,0,0,0,
        402,407,3,88,44,0,403,404,7,7,0,0,404,406,3,88,44,0,405,403,1,0,
        0,0,406,409,1,0,0,0,407,405,1,0,0,0,407,408,1,0,0,0,408,87,1,0,0,
        0,409,407,1,0,0,0,410,415,3,90,45,0,411,412,7,8,0,0,412,414,3,90,
        45,0,413,411,1,0,0,0,414,417,1,0,0,0,415,413,1,0,0,0,415,416,1,0,
        0,0,416,89,1,0,0,0,417,415,1,0,0,0,418,419,7,9,0,0,419,422,3,90,
        45,0,420,422,3,92,46,0,421,418,1,0,0,0,421,420,1,0,0,0,422,91,1,
        0,0,0,423,440,3,94,47,0,424,440,5,66,0,0,425,440,5,35,0,0,426,440,
        5,36,0,0,427,428,3,72,36,0,428,430,5,54,0,0,429,431,3,76,38,0,430,
        429,1,0,0,0,430,431,1,0,0,0,431,432,1,0,0,0,432,433,5,55,0,0,433,
        440,1,0,0,0,434,440,3,72,36,0,435,436,5,54,0,0,436,437,3,78,39,0,
        437,438,5,55,0,0,438,440,1,0,0,0,439,423,1,0,0,0,439,424,1,0,0,0,
        439,425,1,0,0,0,439,426,1,0,0,0,439,427,1,0,0,0,439,434,1,0,0,0,
        439,435,1,0,0,0,440,93,1,0,0,0,441,442,7,10,0,0,442,95,1,0,0,0,41,
        105,114,120,128,134,145,157,167,186,191,199,211,215,224,228,238,
        247,251,258,266,273,282,289,298,302,313,322,325,333,342,360,369,
        376,386,394,400,407,415,421,430,439
    ]

class C64PascalParser ( Parser ):

    grammarFileName = "C64PascalParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'PROGRAM'", "'CONST'", "'TYPE'", "'VAR'", 
                     "'BEGIN'", "'END'", "'IF'", "'THEN'", "'ELSE'", "'WHILE'", 
                     "'DO'", "'REPEAT'", "'UNTIL'", "'FOR'", "'TO'", "'DOWNTO'", 
                     "'BREAK'", "'CONTINUE'", "'RECORD'", "'ARRAY'", "'OF'", 
                     "'CLASS'", "'PRIVATE'", "'PROTECTED'", "'PUBLIC'", 
                     "'PUBLISHED'", "'PROCEDURE'", "'FUNCTION'", "'CONSTRUCTOR'", 
                     "'DESTRUCTOR'", "'INTEGER'", "'BYTE'", "'CHAR'", "'BOOLEAN'", 
                     "'TRUE'", "'FALSE'", "'DIV'", "'MOD'", "'AND'", "'OR'", 
                     "'XOR'", "'NOT'", "':='", "'<='", "'>='", "'<>'", "'='", 
                     "'<'", "'>'", "'+'", "'-'", "'*'", "'/'", "'('", "')'", 
                     "'['", "']'", "','", "':'", "';'", "'..'", "'.'" ]

    symbolicNames = [ "<INVALID>", "PROGRAM", "CONST", "TYPE", "VAR", "BEGIN", 
                      "END", "IF", "THEN", "ELSE", "WHILE", "DO", "REPEAT", 
                      "UNTIL", "FOR", "TO", "DOWNTO", "BREAK", "CONTINUE", 
                      "RECORD", "ARRAY", "OF", "CLASS", "PRIVATE", "PROTECTED", 
                      "PUBLIC", "PUBLISHED", "PROCEDURE", "FUNCTION", "CONSTRUCTOR", 
                      "DESTRUCTOR", "INTEGER_TYPE", "BYTE_TYPE", "CHAR_TYPE", 
                      "BOOLEAN_TYPE", "TRUE", "FALSE", "DIV", "MOD", "AND", 
                      "OR", "XOR", "NOT", "ASSIGN", "LE", "GE", "NE", "EQ", 
                      "LT", "GT", "PLUS", "MINUS", "STAR", "SLASH", "LPAREN", 
                      "RPAREN", "LBRACK", "RBRACK", "COMMA", "COLON", "SEMI", 
                      "DOTDOT", "DOT", "HEX_INTEGER", "BINARY_INTEGER", 
                      "DECIMAL_INTEGER", "STRING_LITERAL", "IDENTIFIER", 
                      "BRACE_COMMENT", "PAREN_COMMENT", "LINE_COMMENT", 
                      "WS" ]

    RULE_compilationUnit = 0
    RULE_programUnit = 1
    RULE_block = 2
    RULE_declarationSection = 3
    RULE_constSection = 4
    RULE_constDefinition = 5
    RULE_typeSection = 6
    RULE_typeDefinition = 7
    RULE_typeSpecification = 8
    RULE_enumType = 9
    RULE_recordType = 10
    RULE_arrayType = 11
    RULE_classType = 12
    RULE_classMember = 13
    RULE_visibilitySpecifier = 14
    RULE_fieldDeclaration = 15
    RULE_methodDeclaration = 16
    RULE_methodImplementation = 17
    RULE_routineKind = 18
    RULE_formalParameters = 19
    RULE_formalParameterList = 20
    RULE_formalParameterGroup = 21
    RULE_routineBlock = 22
    RULE_varSection = 23
    RULE_varDeclaration = 24
    RULE_identifierList = 25
    RULE_typeIdentifier = 26
    RULE_compoundStatement = 27
    RULE_statementSequence = 28
    RULE_statement = 29
    RULE_assignmentStatement = 30
    RULE_callStatement = 31
    RULE_ifStatement = 32
    RULE_whileStatement = 33
    RULE_repeatStatement = 34
    RULE_forStatement = 35
    RULE_designator = 36
    RULE_designatorSuffix = 37
    RULE_argumentList = 38
    RULE_expression = 39
    RULE_orExpression = 40
    RULE_andExpression = 41
    RULE_comparisonExpression = 42
    RULE_additiveExpression = 43
    RULE_multiplicativeExpression = 44
    RULE_unaryExpression = 45
    RULE_primaryExpression = 46
    RULE_integerLiteral = 47

    ruleNames =  [ "compilationUnit", "programUnit", "block", "declarationSection", 
                   "constSection", "constDefinition", "typeSection", "typeDefinition", 
                   "typeSpecification", "enumType", "recordType", "arrayType", 
                   "classType", "classMember", "visibilitySpecifier", "fieldDeclaration", 
                   "methodDeclaration", "methodImplementation", "routineKind", 
                   "formalParameters", "formalParameterList", "formalParameterGroup", 
                   "routineBlock", "varSection", "varDeclaration", "identifierList", 
                   "typeIdentifier", "compoundStatement", "statementSequence", 
                   "statement", "assignmentStatement", "callStatement", 
                   "ifStatement", "whileStatement", "repeatStatement", "forStatement", 
                   "designator", "designatorSuffix", "argumentList", "expression", 
                   "orExpression", "andExpression", "comparisonExpression", 
                   "additiveExpression", "multiplicativeExpression", "unaryExpression", 
                   "primaryExpression", "integerLiteral" ]

    EOF = Token.EOF
    PROGRAM=1
    CONST=2
    TYPE=3
    VAR=4
    BEGIN=5
    END=6
    IF=7
    THEN=8
    ELSE=9
    WHILE=10
    DO=11
    REPEAT=12
    UNTIL=13
    FOR=14
    TO=15
    DOWNTO=16
    BREAK=17
    CONTINUE=18
    RECORD=19
    ARRAY=20
    OF=21
    CLASS=22
    PRIVATE=23
    PROTECTED=24
    PUBLIC=25
    PUBLISHED=26
    PROCEDURE=27
    FUNCTION=28
    CONSTRUCTOR=29
    DESTRUCTOR=30
    INTEGER_TYPE=31
    BYTE_TYPE=32
    CHAR_TYPE=33
    BOOLEAN_TYPE=34
    TRUE=35
    FALSE=36
    DIV=37
    MOD=38
    AND=39
    OR=40
    XOR=41
    NOT=42
    ASSIGN=43
    LE=44
    GE=45
    NE=46
    EQ=47
    LT=48
    GT=49
    PLUS=50
    MINUS=51
    STAR=52
    SLASH=53
    LPAREN=54
    RPAREN=55
    LBRACK=56
    RBRACK=57
    COMMA=58
    COLON=59
    SEMI=60
    DOTDOT=61
    DOT=62
    HEX_INTEGER=63
    BINARY_INTEGER=64
    DECIMAL_INTEGER=65
    STRING_LITERAL=66
    IDENTIFIER=67
    BRACE_COMMENT=68
    PAREN_COMMENT=69
    LINE_COMMENT=70
    WS=71

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class CompilationUnitContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def programUnit(self):
            return self.getTypedRuleContext(C64PascalParser.ProgramUnitContext,0)


        def EOF(self):
            return self.getToken(C64PascalParser.EOF, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_compilationUnit

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompilationUnit" ):
                return visitor.visitCompilationUnit(self)
            else:
                return visitor.visitChildren(self)




    def compilationUnit(self):

        localctx = C64PascalParser.CompilationUnitContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_compilationUnit)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 96
            self.programUnit()
            self.state = 97
            self.match(C64PascalParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ProgramUnitContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PROGRAM(self):
            return self.getToken(C64PascalParser.PROGRAM, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def block(self):
            return self.getTypedRuleContext(C64PascalParser.BlockContext,0)


        def DOT(self):
            return self.getToken(C64PascalParser.DOT, 0)

        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def identifierList(self):
            return self.getTypedRuleContext(C64PascalParser.IdentifierListContext,0)


        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_programUnit

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitProgramUnit" ):
                return visitor.visitProgramUnit(self)
            else:
                return visitor.visitChildren(self)




    def programUnit(self):

        localctx = C64PascalParser.ProgramUnitContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_programUnit)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 99
            self.match(C64PascalParser.PROGRAM)
            self.state = 100
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 105
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==54:
                self.state = 101
                self.match(C64PascalParser.LPAREN)
                self.state = 102
                self.identifierList()
                self.state = 103
                self.match(C64PascalParser.RPAREN)


            self.state = 107
            self.match(C64PascalParser.SEMI)
            self.state = 108
            self.block()
            self.state = 109
            self.match(C64PascalParser.DOT)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BlockContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def compoundStatement(self):
            return self.getTypedRuleContext(C64PascalParser.CompoundStatementContext,0)


        def declarationSection(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.DeclarationSectionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.DeclarationSectionContext,i)


        def methodImplementation(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.MethodImplementationContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.MethodImplementationContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_block

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBlock" ):
                return visitor.visitBlock(self)
            else:
                return visitor.visitChildren(self)




    def block(self):

        localctx = C64PascalParser.BlockContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_block)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 114
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 28) != 0):
                self.state = 111
                self.declarationSection()
                self.state = 116
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 120
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 2013265920) != 0):
                self.state = 117
                self.methodImplementation()
                self.state = 122
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 123
            self.compoundStatement()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DeclarationSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def constSection(self):
            return self.getTypedRuleContext(C64PascalParser.ConstSectionContext,0)


        def typeSection(self):
            return self.getTypedRuleContext(C64PascalParser.TypeSectionContext,0)


        def varSection(self):
            return self.getTypedRuleContext(C64PascalParser.VarSectionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_declarationSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDeclarationSection" ):
                return visitor.visitDeclarationSection(self)
            else:
                return visitor.visitChildren(self)




    def declarationSection(self):

        localctx = C64PascalParser.DeclarationSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_declarationSection)
        try:
            self.state = 128
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [2]:
                self.enterOuterAlt(localctx, 1)
                self.state = 125
                self.constSection()
                pass
            elif token in [3]:
                self.enterOuterAlt(localctx, 2)
                self.state = 126
                self.typeSection()
                pass
            elif token in [4]:
                self.enterOuterAlt(localctx, 3)
                self.state = 127
                self.varSection()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConstSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CONST(self):
            return self.getToken(C64PascalParser.CONST, 0)

        def constDefinition(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.ConstDefinitionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.ConstDefinitionContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_constSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConstSection" ):
                return visitor.visitConstSection(self)
            else:
                return visitor.visitChildren(self)




    def constSection(self):

        localctx = C64PascalParser.ConstSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_constSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 130
            self.match(C64PascalParser.CONST)
            self.state = 132 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 131
                self.constDefinition()
                self.state = 134 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==67):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConstDefinitionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def EQ(self):
            return self.getToken(C64PascalParser.EQ, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_constDefinition

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConstDefinition" ):
                return visitor.visitConstDefinition(self)
            else:
                return visitor.visitChildren(self)




    def constDefinition(self):

        localctx = C64PascalParser.ConstDefinitionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_constDefinition)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 136
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 137
            self.match(C64PascalParser.EQ)
            self.state = 138
            self.expression()
            self.state = 139
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TypeSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def TYPE(self):
            return self.getToken(C64PascalParser.TYPE, 0)

        def typeDefinition(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.TypeDefinitionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.TypeDefinitionContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_typeSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeSection" ):
                return visitor.visitTypeSection(self)
            else:
                return visitor.visitChildren(self)




    def typeSection(self):

        localctx = C64PascalParser.TypeSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_typeSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 141
            self.match(C64PascalParser.TYPE)
            self.state = 143 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 142
                self.typeDefinition()
                self.state = 145 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==67):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TypeDefinitionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def EQ(self):
            return self.getToken(C64PascalParser.EQ, 0)

        def typeSpecification(self):
            return self.getTypedRuleContext(C64PascalParser.TypeSpecificationContext,0)


        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_typeDefinition

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeDefinition" ):
                return visitor.visitTypeDefinition(self)
            else:
                return visitor.visitChildren(self)




    def typeDefinition(self):

        localctx = C64PascalParser.TypeDefinitionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_typeDefinition)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 147
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 148
            self.match(C64PascalParser.EQ)
            self.state = 149
            self.typeSpecification()
            self.state = 150
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TypeSpecificationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def enumType(self):
            return self.getTypedRuleContext(C64PascalParser.EnumTypeContext,0)


        def recordType(self):
            return self.getTypedRuleContext(C64PascalParser.RecordTypeContext,0)


        def arrayType(self):
            return self.getTypedRuleContext(C64PascalParser.ArrayTypeContext,0)


        def classType(self):
            return self.getTypedRuleContext(C64PascalParser.ClassTypeContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_typeSpecification

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeSpecification" ):
                return visitor.visitTypeSpecification(self)
            else:
                return visitor.visitChildren(self)




    def typeSpecification(self):

        localctx = C64PascalParser.TypeSpecificationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_typeSpecification)
        try:
            self.state = 157
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [31, 32, 33, 34, 67]:
                self.enterOuterAlt(localctx, 1)
                self.state = 152
                self.typeIdentifier()
                pass
            elif token in [54]:
                self.enterOuterAlt(localctx, 2)
                self.state = 153
                self.enumType()
                pass
            elif token in [19]:
                self.enterOuterAlt(localctx, 3)
                self.state = 154
                self.recordType()
                pass
            elif token in [20]:
                self.enterOuterAlt(localctx, 4)
                self.state = 155
                self.arrayType()
                pass
            elif token in [22]:
                self.enterOuterAlt(localctx, 5)
                self.state = 156
                self.classType()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class EnumTypeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def identifierList(self):
            return self.getTypedRuleContext(C64PascalParser.IdentifierListContext,0)


        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_enumType

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitEnumType" ):
                return visitor.visitEnumType(self)
            else:
                return visitor.visitChildren(self)




    def enumType(self):

        localctx = C64PascalParser.EnumTypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_enumType)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 159
            self.match(C64PascalParser.LPAREN)
            self.state = 160
            self.identifierList()
            self.state = 161
            self.match(C64PascalParser.RPAREN)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RecordTypeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def RECORD(self):
            return self.getToken(C64PascalParser.RECORD, 0)

        def END(self):
            return self.getToken(C64PascalParser.END, 0)

        def fieldDeclaration(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.FieldDeclarationContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.FieldDeclarationContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_recordType

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRecordType" ):
                return visitor.visitRecordType(self)
            else:
                return visitor.visitChildren(self)




    def recordType(self):

        localctx = C64PascalParser.RecordTypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_recordType)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 163
            self.match(C64PascalParser.RECORD)
            self.state = 167
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==67:
                self.state = 164
                self.fieldDeclaration()
                self.state = 169
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 170
            self.match(C64PascalParser.END)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ArrayTypeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ARRAY(self):
            return self.getToken(C64PascalParser.ARRAY, 0)

        def LBRACK(self):
            return self.getToken(C64PascalParser.LBRACK, 0)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.ExpressionContext,i)


        def DOTDOT(self):
            return self.getToken(C64PascalParser.DOTDOT, 0)

        def RBRACK(self):
            return self.getToken(C64PascalParser.RBRACK, 0)

        def OF(self):
            return self.getToken(C64PascalParser.OF, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_arrayType

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArrayType" ):
                return visitor.visitArrayType(self)
            else:
                return visitor.visitChildren(self)




    def arrayType(self):

        localctx = C64PascalParser.ArrayTypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_arrayType)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 172
            self.match(C64PascalParser.ARRAY)
            self.state = 173
            self.match(C64PascalParser.LBRACK)
            self.state = 174
            self.expression()
            self.state = 175
            self.match(C64PascalParser.DOTDOT)
            self.state = 176
            self.expression()
            self.state = 177
            self.match(C64PascalParser.RBRACK)
            self.state = 178
            self.match(C64PascalParser.OF)
            self.state = 179
            self.typeIdentifier()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ClassTypeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CLASS(self):
            return self.getToken(C64PascalParser.CLASS, 0)

        def END(self):
            return self.getToken(C64PascalParser.END, 0)

        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def classMember(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.ClassMemberContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.ClassMemberContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_classType

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitClassType" ):
                return visitor.visitClassType(self)
            else:
                return visitor.visitChildren(self)




    def classType(self):

        localctx = C64PascalParser.ClassTypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_classType)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 181
            self.match(C64PascalParser.CLASS)
            self.state = 186
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==54:
                self.state = 182
                self.match(C64PascalParser.LPAREN)
                self.state = 183
                self.typeIdentifier()
                self.state = 184
                self.match(C64PascalParser.RPAREN)


            self.state = 191
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while ((((_la - 23)) & ~0x3f) == 0 and ((1 << (_la - 23)) & 17592186044671) != 0):
                self.state = 188
                self.classMember()
                self.state = 193
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 194
            self.match(C64PascalParser.END)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ClassMemberContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def visibilitySpecifier(self):
            return self.getTypedRuleContext(C64PascalParser.VisibilitySpecifierContext,0)


        def fieldDeclaration(self):
            return self.getTypedRuleContext(C64PascalParser.FieldDeclarationContext,0)


        def methodDeclaration(self):
            return self.getTypedRuleContext(C64PascalParser.MethodDeclarationContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_classMember

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitClassMember" ):
                return visitor.visitClassMember(self)
            else:
                return visitor.visitChildren(self)




    def classMember(self):

        localctx = C64PascalParser.ClassMemberContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_classMember)
        try:
            self.state = 199
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [23, 24, 25, 26]:
                self.enterOuterAlt(localctx, 1)
                self.state = 196
                self.visibilitySpecifier()
                pass
            elif token in [67]:
                self.enterOuterAlt(localctx, 2)
                self.state = 197
                self.fieldDeclaration()
                pass
            elif token in [27, 28, 29, 30]:
                self.enterOuterAlt(localctx, 3)
                self.state = 198
                self.methodDeclaration()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VisibilitySpecifierContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PRIVATE(self):
            return self.getToken(C64PascalParser.PRIVATE, 0)

        def PROTECTED(self):
            return self.getToken(C64PascalParser.PROTECTED, 0)

        def PUBLIC(self):
            return self.getToken(C64PascalParser.PUBLIC, 0)

        def PUBLISHED(self):
            return self.getToken(C64PascalParser.PUBLISHED, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_visibilitySpecifier

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVisibilitySpecifier" ):
                return visitor.visitVisibilitySpecifier(self)
            else:
                return visitor.visitChildren(self)




    def visibilitySpecifier(self):

        localctx = C64PascalParser.VisibilitySpecifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_visibilitySpecifier)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 201
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 125829120) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FieldDeclarationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def identifierList(self):
            return self.getTypedRuleContext(C64PascalParser.IdentifierListContext,0)


        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_fieldDeclaration

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFieldDeclaration" ):
                return visitor.visitFieldDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def fieldDeclaration(self):

        localctx = C64PascalParser.FieldDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_fieldDeclaration)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 203
            self.identifierList()
            self.state = 204
            self.match(C64PascalParser.COLON)
            self.state = 205
            self.typeIdentifier()
            self.state = 206
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MethodDeclarationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def routineKind(self):
            return self.getTypedRuleContext(C64PascalParser.RoutineKindContext,0)


        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def formalParameters(self):
            return self.getTypedRuleContext(C64PascalParser.FormalParametersContext,0)


        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_methodDeclaration

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMethodDeclaration" ):
                return visitor.visitMethodDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def methodDeclaration(self):

        localctx = C64PascalParser.MethodDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_methodDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 208
            self.routineKind()
            self.state = 209
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 211
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==54:
                self.state = 210
                self.formalParameters()


            self.state = 215
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==59:
                self.state = 213
                self.match(C64PascalParser.COLON)
                self.state = 214
                self.typeIdentifier()


            self.state = 217
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MethodImplementationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def routineKind(self):
            return self.getTypedRuleContext(C64PascalParser.RoutineKindContext,0)


        def IDENTIFIER(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.IDENTIFIER)
            else:
                return self.getToken(C64PascalParser.IDENTIFIER, i)

        def DOT(self):
            return self.getToken(C64PascalParser.DOT, 0)

        def SEMI(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.SEMI)
            else:
                return self.getToken(C64PascalParser.SEMI, i)

        def routineBlock(self):
            return self.getTypedRuleContext(C64PascalParser.RoutineBlockContext,0)


        def formalParameters(self):
            return self.getTypedRuleContext(C64PascalParser.FormalParametersContext,0)


        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_methodImplementation

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMethodImplementation" ):
                return visitor.visitMethodImplementation(self)
            else:
                return visitor.visitChildren(self)




    def methodImplementation(self):

        localctx = C64PascalParser.MethodImplementationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_methodImplementation)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 219
            self.routineKind()
            self.state = 220
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 221
            self.match(C64PascalParser.DOT)
            self.state = 222
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 224
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==54:
                self.state = 223
                self.formalParameters()


            self.state = 228
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==59:
                self.state = 226
                self.match(C64PascalParser.COLON)
                self.state = 227
                self.typeIdentifier()


            self.state = 230
            self.match(C64PascalParser.SEMI)
            self.state = 231
            self.routineBlock()
            self.state = 232
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RoutineKindContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PROCEDURE(self):
            return self.getToken(C64PascalParser.PROCEDURE, 0)

        def FUNCTION(self):
            return self.getToken(C64PascalParser.FUNCTION, 0)

        def CONSTRUCTOR(self):
            return self.getToken(C64PascalParser.CONSTRUCTOR, 0)

        def DESTRUCTOR(self):
            return self.getToken(C64PascalParser.DESTRUCTOR, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_routineKind

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRoutineKind" ):
                return visitor.visitRoutineKind(self)
            else:
                return visitor.visitChildren(self)




    def routineKind(self):

        localctx = C64PascalParser.RoutineKindContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_routineKind)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 234
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 2013265920) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FormalParametersContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def formalParameterList(self):
            return self.getTypedRuleContext(C64PascalParser.FormalParameterListContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_formalParameters

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFormalParameters" ):
                return visitor.visitFormalParameters(self)
            else:
                return visitor.visitChildren(self)




    def formalParameters(self):

        localctx = C64PascalParser.FormalParametersContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_formalParameters)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 236
            self.match(C64PascalParser.LPAREN)
            self.state = 238
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==2 or _la==4 or _la==67:
                self.state = 237
                self.formalParameterList()


            self.state = 240
            self.match(C64PascalParser.RPAREN)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FormalParameterListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def formalParameterGroup(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.FormalParameterGroupContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.FormalParameterGroupContext,i)


        def SEMI(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.SEMI)
            else:
                return self.getToken(C64PascalParser.SEMI, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_formalParameterList

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFormalParameterList" ):
                return visitor.visitFormalParameterList(self)
            else:
                return visitor.visitChildren(self)




    def formalParameterList(self):

        localctx = C64PascalParser.FormalParameterListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 40, self.RULE_formalParameterList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 242
            self.formalParameterGroup()
            self.state = 247
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==60:
                self.state = 243
                self.match(C64PascalParser.SEMI)
                self.state = 244
                self.formalParameterGroup()
                self.state = 249
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FormalParameterGroupContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def identifierList(self):
            return self.getTypedRuleContext(C64PascalParser.IdentifierListContext,0)


        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def CONST(self):
            return self.getToken(C64PascalParser.CONST, 0)

        def VAR(self):
            return self.getToken(C64PascalParser.VAR, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_formalParameterGroup

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFormalParameterGroup" ):
                return visitor.visitFormalParameterGroup(self)
            else:
                return visitor.visitChildren(self)




    def formalParameterGroup(self):

        localctx = C64PascalParser.FormalParameterGroupContext(self, self._ctx, self.state)
        self.enterRule(localctx, 42, self.RULE_formalParameterGroup)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 251
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==2 or _la==4:
                self.state = 250
                _la = self._input.LA(1)
                if not(_la==2 or _la==4):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()


            self.state = 253
            self.identifierList()
            self.state = 254
            self.match(C64PascalParser.COLON)
            self.state = 255
            self.typeIdentifier()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RoutineBlockContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def compoundStatement(self):
            return self.getTypedRuleContext(C64PascalParser.CompoundStatementContext,0)


        def varSection(self):
            return self.getTypedRuleContext(C64PascalParser.VarSectionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_routineBlock

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRoutineBlock" ):
                return visitor.visitRoutineBlock(self)
            else:
                return visitor.visitChildren(self)




    def routineBlock(self):

        localctx = C64PascalParser.RoutineBlockContext(self, self._ctx, self.state)
        self.enterRule(localctx, 44, self.RULE_routineBlock)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 258
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==4:
                self.state = 257
                self.varSection()


            self.state = 260
            self.compoundStatement()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VarSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def VAR(self):
            return self.getToken(C64PascalParser.VAR, 0)

        def varDeclaration(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.VarDeclarationContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.VarDeclarationContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_varSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVarSection" ):
                return visitor.visitVarSection(self)
            else:
                return visitor.visitChildren(self)




    def varSection(self):

        localctx = C64PascalParser.VarSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 46, self.RULE_varSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 262
            self.match(C64PascalParser.VAR)
            self.state = 264 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 263
                self.varDeclaration()
                self.state = 266 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==67):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VarDeclarationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def identifierList(self):
            return self.getTypedRuleContext(C64PascalParser.IdentifierListContext,0)


        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def ASSIGN(self):
            return self.getToken(C64PascalParser.ASSIGN, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_varDeclaration

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVarDeclaration" ):
                return visitor.visitVarDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def varDeclaration(self):

        localctx = C64PascalParser.VarDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 48, self.RULE_varDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 268
            self.identifierList()
            self.state = 269
            self.match(C64PascalParser.COLON)
            self.state = 270
            self.typeIdentifier()
            self.state = 273
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==43:
                self.state = 271
                self.match(C64PascalParser.ASSIGN)
                self.state = 272
                self.expression()


            self.state = 275
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IdentifierListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.IDENTIFIER)
            else:
                return self.getToken(C64PascalParser.IDENTIFIER, i)

        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.COMMA)
            else:
                return self.getToken(C64PascalParser.COMMA, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_identifierList

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIdentifierList" ):
                return visitor.visitIdentifierList(self)
            else:
                return visitor.visitChildren(self)




    def identifierList(self):

        localctx = C64PascalParser.IdentifierListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 50, self.RULE_identifierList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 277
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 282
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==58:
                self.state = 278
                self.match(C64PascalParser.COMMA)
                self.state = 279
                self.match(C64PascalParser.IDENTIFIER)
                self.state = 284
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TypeIdentifierContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INTEGER_TYPE(self):
            return self.getToken(C64PascalParser.INTEGER_TYPE, 0)

        def BYTE_TYPE(self):
            return self.getToken(C64PascalParser.BYTE_TYPE, 0)

        def CHAR_TYPE(self):
            return self.getToken(C64PascalParser.CHAR_TYPE, 0)

        def BOOLEAN_TYPE(self):
            return self.getToken(C64PascalParser.BOOLEAN_TYPE, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_typeIdentifier

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeIdentifier" ):
                return visitor.visitTypeIdentifier(self)
            else:
                return visitor.visitChildren(self)




    def typeIdentifier(self):

        localctx = C64PascalParser.TypeIdentifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 52, self.RULE_typeIdentifier)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 285
            _la = self._input.LA(1)
            if not(((((_la - 31)) & ~0x3f) == 0 and ((1 << (_la - 31)) & 68719476751) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CompoundStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def BEGIN(self):
            return self.getToken(C64PascalParser.BEGIN, 0)

        def END(self):
            return self.getToken(C64PascalParser.END, 0)

        def statementSequence(self):
            return self.getTypedRuleContext(C64PascalParser.StatementSequenceContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_compoundStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompoundStatement" ):
                return visitor.visitCompoundStatement(self)
            else:
                return visitor.visitChildren(self)




    def compoundStatement(self):

        localctx = C64PascalParser.CompoundStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 54, self.RULE_compoundStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 287
            self.match(C64PascalParser.BEGIN)
            self.state = 289
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if ((((_la - 5)) & ~0x3f) == 0 and ((1 << (_la - 5)) & 4611686018427400869) != 0):
                self.state = 288
                self.statementSequence()


            self.state = 291
            self.match(C64PascalParser.END)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StatementSequenceContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.StatementContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.StatementContext,i)


        def SEMI(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.SEMI)
            else:
                return self.getToken(C64PascalParser.SEMI, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_statementSequence

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStatementSequence" ):
                return visitor.visitStatementSequence(self)
            else:
                return visitor.visitChildren(self)




    def statementSequence(self):

        localctx = C64PascalParser.StatementSequenceContext(self, self._ctx, self.state)
        self.enterRule(localctx, 56, self.RULE_statementSequence)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 293
            self.statement()
            self.state = 298
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,23,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 294
                    self.match(C64PascalParser.SEMI)
                    self.state = 295
                    self.statement() 
                self.state = 300
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,23,self._ctx)

            self.state = 302
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==60:
                self.state = 301
                self.match(C64PascalParser.SEMI)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return C64PascalParser.RULE_statement

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class CompoundStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def compoundStatement(self):
            return self.getTypedRuleContext(C64PascalParser.CompoundStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompoundStatementNode" ):
                return visitor.visitCompoundStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class AssignmentStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def assignmentStatement(self):
            return self.getTypedRuleContext(C64PascalParser.AssignmentStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAssignmentStatementNode" ):
                return visitor.visitAssignmentStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class CallStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def callStatement(self):
            return self.getTypedRuleContext(C64PascalParser.CallStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCallStatementNode" ):
                return visitor.visitCallStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class IfStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ifStatement(self):
            return self.getTypedRuleContext(C64PascalParser.IfStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIfStatementNode" ):
                return visitor.visitIfStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class WhileStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def whileStatement(self):
            return self.getTypedRuleContext(C64PascalParser.WhileStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWhileStatementNode" ):
                return visitor.visitWhileStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class RepeatStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def repeatStatement(self):
            return self.getTypedRuleContext(C64PascalParser.RepeatStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRepeatStatementNode" ):
                return visitor.visitRepeatStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class ForStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def forStatement(self):
            return self.getTypedRuleContext(C64PascalParser.ForStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitForStatementNode" ):
                return visitor.visitForStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class BreakStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def BREAK(self):
            return self.getToken(C64PascalParser.BREAK, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBreakStatementNode" ):
                return visitor.visitBreakStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class ContinueStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def CONTINUE(self):
            return self.getToken(C64PascalParser.CONTINUE, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitContinueStatementNode" ):
                return visitor.visitContinueStatementNode(self)
            else:
                return visitor.visitChildren(self)



    def statement(self):

        localctx = C64PascalParser.StatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 58, self.RULE_statement)
        try:
            self.state = 313
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,25,self._ctx)
            if la_ == 1:
                localctx = C64PascalParser.CompoundStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 304
                self.compoundStatement()
                pass

            elif la_ == 2:
                localctx = C64PascalParser.AssignmentStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 305
                self.assignmentStatement()
                pass

            elif la_ == 3:
                localctx = C64PascalParser.CallStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 306
                self.callStatement()
                pass

            elif la_ == 4:
                localctx = C64PascalParser.IfStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 307
                self.ifStatement()
                pass

            elif la_ == 5:
                localctx = C64PascalParser.WhileStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 308
                self.whileStatement()
                pass

            elif la_ == 6:
                localctx = C64PascalParser.RepeatStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 309
                self.repeatStatement()
                pass

            elif la_ == 7:
                localctx = C64PascalParser.ForStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 310
                self.forStatement()
                pass

            elif la_ == 8:
                localctx = C64PascalParser.BreakStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 8)
                self.state = 311
                self.match(C64PascalParser.BREAK)
                pass

            elif la_ == 9:
                localctx = C64PascalParser.ContinueStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 9)
                self.state = 312
                self.match(C64PascalParser.CONTINUE)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AssignmentStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def designator(self):
            return self.getTypedRuleContext(C64PascalParser.DesignatorContext,0)


        def ASSIGN(self):
            return self.getToken(C64PascalParser.ASSIGN, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_assignmentStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAssignmentStatement" ):
                return visitor.visitAssignmentStatement(self)
            else:
                return visitor.visitChildren(self)




    def assignmentStatement(self):

        localctx = C64PascalParser.AssignmentStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 60, self.RULE_assignmentStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 315
            self.designator()
            self.state = 316
            self.match(C64PascalParser.ASSIGN)
            self.state = 317
            self.expression()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CallStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def designator(self):
            return self.getTypedRuleContext(C64PascalParser.DesignatorContext,0)


        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def argumentList(self):
            return self.getTypedRuleContext(C64PascalParser.ArgumentListContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_callStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCallStatement" ):
                return visitor.visitCallStatement(self)
            else:
                return visitor.visitChildren(self)




    def callStatement(self):

        localctx = C64PascalParser.CallStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 62, self.RULE_callStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 319
            self.designator()
            self.state = 325
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==54:
                self.state = 320
                self.match(C64PascalParser.LPAREN)
                self.state = 322
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if ((((_la - 35)) & ~0x3f) == 0 and ((1 << (_la - 35)) & 8322121859) != 0):
                    self.state = 321
                    self.argumentList()


                self.state = 324
                self.match(C64PascalParser.RPAREN)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IfStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IF(self):
            return self.getToken(C64PascalParser.IF, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def THEN(self):
            return self.getToken(C64PascalParser.THEN, 0)

        def statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.StatementContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.StatementContext,i)


        def ELSE(self):
            return self.getToken(C64PascalParser.ELSE, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_ifStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIfStatement" ):
                return visitor.visitIfStatement(self)
            else:
                return visitor.visitChildren(self)




    def ifStatement(self):

        localctx = C64PascalParser.IfStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 64, self.RULE_ifStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 327
            self.match(C64PascalParser.IF)
            self.state = 328
            self.expression()
            self.state = 329
            self.match(C64PascalParser.THEN)
            self.state = 330
            self.statement()
            self.state = 333
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,28,self._ctx)
            if la_ == 1:
                self.state = 331
                self.match(C64PascalParser.ELSE)
                self.state = 332
                self.statement()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class WhileStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WHILE(self):
            return self.getToken(C64PascalParser.WHILE, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def DO(self):
            return self.getToken(C64PascalParser.DO, 0)

        def statement(self):
            return self.getTypedRuleContext(C64PascalParser.StatementContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_whileStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWhileStatement" ):
                return visitor.visitWhileStatement(self)
            else:
                return visitor.visitChildren(self)




    def whileStatement(self):

        localctx = C64PascalParser.WhileStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 66, self.RULE_whileStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 335
            self.match(C64PascalParser.WHILE)
            self.state = 336
            self.expression()
            self.state = 337
            self.match(C64PascalParser.DO)
            self.state = 338
            self.statement()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RepeatStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def REPEAT(self):
            return self.getToken(C64PascalParser.REPEAT, 0)

        def UNTIL(self):
            return self.getToken(C64PascalParser.UNTIL, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def statementSequence(self):
            return self.getTypedRuleContext(C64PascalParser.StatementSequenceContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_repeatStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRepeatStatement" ):
                return visitor.visitRepeatStatement(self)
            else:
                return visitor.visitChildren(self)




    def repeatStatement(self):

        localctx = C64PascalParser.RepeatStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 68, self.RULE_repeatStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 340
            self.match(C64PascalParser.REPEAT)
            self.state = 342
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if ((((_la - 5)) & ~0x3f) == 0 and ((1 << (_la - 5)) & 4611686018427400869) != 0):
                self.state = 341
                self.statementSequence()


            self.state = 344
            self.match(C64PascalParser.UNTIL)
            self.state = 345
            self.expression()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ForStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def FOR(self):
            return self.getToken(C64PascalParser.FOR, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def ASSIGN(self):
            return self.getToken(C64PascalParser.ASSIGN, 0)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.ExpressionContext,i)


        def DO(self):
            return self.getToken(C64PascalParser.DO, 0)

        def statement(self):
            return self.getTypedRuleContext(C64PascalParser.StatementContext,0)


        def TO(self):
            return self.getToken(C64PascalParser.TO, 0)

        def DOWNTO(self):
            return self.getToken(C64PascalParser.DOWNTO, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_forStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitForStatement" ):
                return visitor.visitForStatement(self)
            else:
                return visitor.visitChildren(self)




    def forStatement(self):

        localctx = C64PascalParser.ForStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 70, self.RULE_forStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 347
            self.match(C64PascalParser.FOR)
            self.state = 348
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 349
            self.match(C64PascalParser.ASSIGN)
            self.state = 350
            self.expression()
            self.state = 351
            _la = self._input.LA(1)
            if not(_la==15 or _la==16):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 352
            self.expression()
            self.state = 353
            self.match(C64PascalParser.DO)
            self.state = 354
            self.statement()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DesignatorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def designatorSuffix(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.DesignatorSuffixContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.DesignatorSuffixContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_designator

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDesignator" ):
                return visitor.visitDesignator(self)
            else:
                return visitor.visitChildren(self)




    def designator(self):

        localctx = C64PascalParser.DesignatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 72, self.RULE_designator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 356
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 360
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==56 or _la==62:
                self.state = 357
                self.designatorSuffix()
                self.state = 362
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DesignatorSuffixContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def DOT(self):
            return self.getToken(C64PascalParser.DOT, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def LBRACK(self):
            return self.getToken(C64PascalParser.LBRACK, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def RBRACK(self):
            return self.getToken(C64PascalParser.RBRACK, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_designatorSuffix

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDesignatorSuffix" ):
                return visitor.visitDesignatorSuffix(self)
            else:
                return visitor.visitChildren(self)




    def designatorSuffix(self):

        localctx = C64PascalParser.DesignatorSuffixContext(self, self._ctx, self.state)
        self.enterRule(localctx, 74, self.RULE_designatorSuffix)
        try:
            self.state = 369
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [62]:
                self.enterOuterAlt(localctx, 1)
                self.state = 363
                self.match(C64PascalParser.DOT)
                self.state = 364
                self.match(C64PascalParser.IDENTIFIER)
                pass
            elif token in [56]:
                self.enterOuterAlt(localctx, 2)
                self.state = 365
                self.match(C64PascalParser.LBRACK)
                self.state = 366
                self.expression()
                self.state = 367
                self.match(C64PascalParser.RBRACK)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ArgumentListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.ExpressionContext,i)


        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.COMMA)
            else:
                return self.getToken(C64PascalParser.COMMA, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_argumentList

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArgumentList" ):
                return visitor.visitArgumentList(self)
            else:
                return visitor.visitChildren(self)




    def argumentList(self):

        localctx = C64PascalParser.ArgumentListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 76, self.RULE_argumentList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 371
            self.expression()
            self.state = 376
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==58:
                self.state = 372
                self.match(C64PascalParser.COMMA)
                self.state = 373
                self.expression()
                self.state = 378
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def orExpression(self):
            return self.getTypedRuleContext(C64PascalParser.OrExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_expression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExpression" ):
                return visitor.visitExpression(self)
            else:
                return visitor.visitChildren(self)




    def expression(self):

        localctx = C64PascalParser.ExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 78, self.RULE_expression)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 379
            self.orExpression()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OrExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def andExpression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.AndExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.AndExpressionContext,i)


        def OR(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.OR)
            else:
                return self.getToken(C64PascalParser.OR, i)

        def XOR(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.XOR)
            else:
                return self.getToken(C64PascalParser.XOR, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_orExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOrExpression" ):
                return visitor.visitOrExpression(self)
            else:
                return visitor.visitChildren(self)




    def orExpression(self):

        localctx = C64PascalParser.OrExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 80, self.RULE_orExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 381
            self.andExpression()
            self.state = 386
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==40 or _la==41:
                self.state = 382
                _la = self._input.LA(1)
                if not(_la==40 or _la==41):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 383
                self.andExpression()
                self.state = 388
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AndExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def comparisonExpression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.ComparisonExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.ComparisonExpressionContext,i)


        def AND(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.AND)
            else:
                return self.getToken(C64PascalParser.AND, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_andExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAndExpression" ):
                return visitor.visitAndExpression(self)
            else:
                return visitor.visitChildren(self)




    def andExpression(self):

        localctx = C64PascalParser.AndExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 82, self.RULE_andExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 389
            self.comparisonExpression()
            self.state = 394
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==39:
                self.state = 390
                self.match(C64PascalParser.AND)
                self.state = 391
                self.comparisonExpression()
                self.state = 396
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ComparisonExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def additiveExpression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.AdditiveExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.AdditiveExpressionContext,i)


        def EQ(self):
            return self.getToken(C64PascalParser.EQ, 0)

        def NE(self):
            return self.getToken(C64PascalParser.NE, 0)

        def LT(self):
            return self.getToken(C64PascalParser.LT, 0)

        def LE(self):
            return self.getToken(C64PascalParser.LE, 0)

        def GT(self):
            return self.getToken(C64PascalParser.GT, 0)

        def GE(self):
            return self.getToken(C64PascalParser.GE, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_comparisonExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitComparisonExpression" ):
                return visitor.visitComparisonExpression(self)
            else:
                return visitor.visitChildren(self)




    def comparisonExpression(self):

        localctx = C64PascalParser.ComparisonExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 84, self.RULE_comparisonExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 397
            self.additiveExpression()
            self.state = 400
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 1108307720798208) != 0):
                self.state = 398
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 1108307720798208) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 399
                self.additiveExpression()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AdditiveExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def multiplicativeExpression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.MultiplicativeExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.MultiplicativeExpressionContext,i)


        def PLUS(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.PLUS)
            else:
                return self.getToken(C64PascalParser.PLUS, i)

        def MINUS(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.MINUS)
            else:
                return self.getToken(C64PascalParser.MINUS, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_additiveExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAdditiveExpression" ):
                return visitor.visitAdditiveExpression(self)
            else:
                return visitor.visitChildren(self)




    def additiveExpression(self):

        localctx = C64PascalParser.AdditiveExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 86, self.RULE_additiveExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 402
            self.multiplicativeExpression()
            self.state = 407
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==50 or _la==51:
                self.state = 403
                _la = self._input.LA(1)
                if not(_la==50 or _la==51):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 404
                self.multiplicativeExpression()
                self.state = 409
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MultiplicativeExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def unaryExpression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.UnaryExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.UnaryExpressionContext,i)


        def STAR(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.STAR)
            else:
                return self.getToken(C64PascalParser.STAR, i)

        def SLASH(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.SLASH)
            else:
                return self.getToken(C64PascalParser.SLASH, i)

        def DIV(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.DIV)
            else:
                return self.getToken(C64PascalParser.DIV, i)

        def MOD(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.MOD)
            else:
                return self.getToken(C64PascalParser.MOD, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_multiplicativeExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMultiplicativeExpression" ):
                return visitor.visitMultiplicativeExpression(self)
            else:
                return visitor.visitChildren(self)




    def multiplicativeExpression(self):

        localctx = C64PascalParser.MultiplicativeExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 88, self.RULE_multiplicativeExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 410
            self.unaryExpression()
            self.state = 415
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 13511211198971904) != 0):
                self.state = 411
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 13511211198971904) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 412
                self.unaryExpression()
                self.state = 417
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class UnaryExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def unaryExpression(self):
            return self.getTypedRuleContext(C64PascalParser.UnaryExpressionContext,0)


        def PLUS(self):
            return self.getToken(C64PascalParser.PLUS, 0)

        def MINUS(self):
            return self.getToken(C64PascalParser.MINUS, 0)

        def NOT(self):
            return self.getToken(C64PascalParser.NOT, 0)

        def primaryExpression(self):
            return self.getTypedRuleContext(C64PascalParser.PrimaryExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_unaryExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUnaryExpression" ):
                return visitor.visitUnaryExpression(self)
            else:
                return visitor.visitChildren(self)




    def unaryExpression(self):

        localctx = C64PascalParser.UnaryExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 90, self.RULE_unaryExpression)
        self._la = 0 # Token type
        try:
            self.state = 421
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [42, 50, 51]:
                self.enterOuterAlt(localctx, 1)
                self.state = 418
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 3382097767038976) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 419
                self.unaryExpression()
                pass
            elif token in [35, 36, 54, 63, 64, 65, 66, 67]:
                self.enterOuterAlt(localctx, 2)
                self.state = 420
                self.primaryExpression()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PrimaryExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def integerLiteral(self):
            return self.getTypedRuleContext(C64PascalParser.IntegerLiteralContext,0)


        def STRING_LITERAL(self):
            return self.getToken(C64PascalParser.STRING_LITERAL, 0)

        def TRUE(self):
            return self.getToken(C64PascalParser.TRUE, 0)

        def FALSE(self):
            return self.getToken(C64PascalParser.FALSE, 0)

        def designator(self):
            return self.getTypedRuleContext(C64PascalParser.DesignatorContext,0)


        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def argumentList(self):
            return self.getTypedRuleContext(C64PascalParser.ArgumentListContext,0)


        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_primaryExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPrimaryExpression" ):
                return visitor.visitPrimaryExpression(self)
            else:
                return visitor.visitChildren(self)




    def primaryExpression(self):

        localctx = C64PascalParser.PrimaryExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 92, self.RULE_primaryExpression)
        self._la = 0 # Token type
        try:
            self.state = 439
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,40,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 423
                self.integerLiteral()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 424
                self.match(C64PascalParser.STRING_LITERAL)
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 425
                self.match(C64PascalParser.TRUE)
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 426
                self.match(C64PascalParser.FALSE)
                pass

            elif la_ == 5:
                self.enterOuterAlt(localctx, 5)
                self.state = 427
                self.designator()
                self.state = 428
                self.match(C64PascalParser.LPAREN)
                self.state = 430
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if ((((_la - 35)) & ~0x3f) == 0 and ((1 << (_la - 35)) & 8322121859) != 0):
                    self.state = 429
                    self.argumentList()


                self.state = 432
                self.match(C64PascalParser.RPAREN)
                pass

            elif la_ == 6:
                self.enterOuterAlt(localctx, 6)
                self.state = 434
                self.designator()
                pass

            elif la_ == 7:
                self.enterOuterAlt(localctx, 7)
                self.state = 435
                self.match(C64PascalParser.LPAREN)
                self.state = 436
                self.expression()
                self.state = 437
                self.match(C64PascalParser.RPAREN)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IntegerLiteralContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def HEX_INTEGER(self):
            return self.getToken(C64PascalParser.HEX_INTEGER, 0)

        def BINARY_INTEGER(self):
            return self.getToken(C64PascalParser.BINARY_INTEGER, 0)

        def DECIMAL_INTEGER(self):
            return self.getToken(C64PascalParser.DECIMAL_INTEGER, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_integerLiteral

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIntegerLiteral" ):
                return visitor.visitIntegerLiteral(self)
            else:
                return visitor.visitChildren(self)




    def integerLiteral(self):

        localctx = C64PascalParser.IntegerLiteralContext(self, self._ctx, self.state)
        self.enterRule(localctx, 94, self.RULE_integerLiteral)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 441
            _la = self._input.LA(1)
            if not(((((_la - 63)) & ~0x3f) == 0 and ((1 << (_la - 63)) & 7) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





