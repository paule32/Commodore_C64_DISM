# Generated from c64pascal/grammar/C64PascalParser.g4 by ANTLR 4.13.2
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
        4,1,108,749,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,
        7,6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,
        13,2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,
        20,7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,
        26,2,27,7,27,2,28,7,28,2,29,7,29,2,30,7,30,2,31,7,31,2,32,7,32,2,
        33,7,33,2,34,7,34,2,35,7,35,2,36,7,36,2,37,7,37,2,38,7,38,2,39,7,
        39,2,40,7,40,2,41,7,41,2,42,7,42,2,43,7,43,2,44,7,44,2,45,7,45,2,
        46,7,46,2,47,7,47,2,48,7,48,2,49,7,49,2,50,7,50,2,51,7,51,2,52,7,
        52,2,53,7,53,2,54,7,54,2,55,7,55,2,56,7,56,2,57,7,57,2,58,7,58,2,
        59,7,59,2,60,7,60,2,61,7,61,2,62,7,62,2,63,7,63,2,64,7,64,2,65,7,
        65,2,66,7,66,2,67,7,67,2,68,7,68,2,69,7,69,2,70,7,70,1,0,1,0,3,0,
        145,8,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,3,1,155,8,1,1,1,1,1,1,1,
        1,1,1,2,1,2,1,2,1,2,1,2,3,2,166,8,2,1,2,5,2,169,8,2,10,2,12,2,172,
        9,2,1,2,5,2,175,8,2,10,2,12,2,178,9,2,1,2,1,2,3,2,182,8,2,1,2,5,
        2,185,8,2,10,2,12,2,188,9,2,1,2,1,2,1,2,5,2,193,8,2,10,2,12,2,196,
        9,2,1,2,1,2,1,2,1,2,1,2,3,2,203,8,2,1,3,1,3,1,3,1,3,5,3,209,8,3,
        10,3,12,3,212,9,3,1,3,1,3,1,4,1,4,1,4,5,4,219,8,4,10,4,12,4,222,
        9,4,1,5,5,5,225,8,5,10,5,12,5,228,9,5,1,5,1,5,1,5,5,5,233,8,5,10,
        5,12,5,236,9,5,1,5,1,5,1,6,1,6,1,6,3,6,243,8,6,1,7,1,7,4,7,247,8,
        7,11,7,12,7,248,1,8,1,8,1,8,1,8,1,8,1,9,1,9,4,9,258,8,9,11,9,12,
        9,259,1,10,1,10,1,10,1,10,1,10,1,11,1,11,1,12,1,12,1,12,1,12,1,12,
        1,12,1,12,3,12,276,8,12,1,13,1,13,1,13,1,13,1,14,1,14,1,14,1,15,
        3,15,286,8,15,1,15,1,15,1,16,1,16,1,16,1,16,1,17,1,17,5,17,296,8,
        17,10,17,12,17,299,9,17,1,17,1,17,1,18,1,18,1,18,1,18,1,18,1,18,
        1,18,1,18,1,18,1,19,1,19,1,19,1,19,1,19,3,19,317,8,19,1,19,5,19,
        320,8,19,10,19,12,19,323,9,19,1,19,1,19,1,20,1,20,1,20,1,20,3,20,
        331,8,20,1,21,1,21,1,22,1,22,1,22,1,22,1,22,1,23,1,23,1,23,3,23,
        343,8,23,1,23,1,23,1,23,5,23,348,8,23,10,23,12,23,351,9,23,1,23,
        1,23,1,24,1,24,3,24,357,8,24,1,24,1,24,1,25,1,25,1,25,1,25,1,25,
        1,25,1,25,1,25,1,25,3,25,370,8,25,1,26,1,26,1,26,5,26,375,8,26,10,
        26,12,26,378,9,26,1,27,3,27,381,8,27,1,27,1,27,1,27,3,27,386,8,27,
        1,27,1,27,3,27,390,8,27,1,27,1,27,5,27,394,8,27,10,27,12,27,397,
        9,27,1,28,1,28,1,28,1,29,1,29,1,29,3,29,405,8,29,1,29,1,29,3,29,
        409,8,29,1,29,1,29,3,29,413,8,29,1,30,1,30,1,30,3,30,418,8,30,1,
        30,1,30,3,30,422,8,30,1,30,1,30,3,30,426,8,30,1,30,1,30,3,30,430,
        8,30,1,30,3,30,433,8,30,1,30,1,30,1,31,1,31,1,31,3,31,440,8,31,1,
        32,1,32,1,32,3,32,445,8,32,1,32,1,32,3,32,449,8,32,1,32,1,32,3,32,
        453,8,32,1,32,1,32,1,32,1,33,1,33,1,33,1,34,3,34,462,8,34,1,34,1,
        34,1,34,1,34,1,34,3,34,469,8,34,1,34,1,34,3,34,473,8,34,1,34,1,34,
        1,34,1,34,1,35,1,35,1,36,1,36,3,36,483,8,36,1,36,1,36,1,37,1,37,
        1,37,5,37,490,8,37,10,37,12,37,493,9,37,1,38,3,38,496,8,38,1,38,
        1,38,1,38,1,38,1,39,3,39,503,8,39,1,39,1,39,1,40,1,40,4,40,509,8,
        40,11,40,12,40,510,1,41,1,41,1,41,1,41,1,41,3,41,518,8,41,1,41,1,
        41,1,42,1,42,1,42,5,42,525,8,42,10,42,12,42,528,9,42,1,43,1,43,1,
        44,1,44,3,44,534,8,44,1,44,1,44,1,45,1,45,1,45,5,45,541,8,45,10,
        45,12,45,544,9,45,1,45,3,45,547,8,45,1,46,1,46,1,46,1,46,1,46,1,
        46,1,46,1,46,1,46,1,46,1,46,1,46,1,46,3,46,562,8,46,1,47,1,47,1,
        47,1,47,1,48,1,48,1,48,3,48,571,8,48,1,48,3,48,574,8,48,1,49,1,49,
        3,49,578,8,49,1,50,1,50,3,50,582,8,50,1,50,1,50,3,50,586,8,50,1,
        50,1,50,1,50,3,50,591,8,50,1,50,1,50,3,50,595,8,50,1,50,3,50,598,
        8,50,1,51,1,51,1,51,1,51,3,51,604,8,51,1,51,3,51,607,8,51,3,51,609,
        8,51,1,52,1,52,1,52,1,52,1,52,1,52,3,52,617,8,52,1,53,1,53,1,53,
        1,53,1,53,1,54,1,54,3,54,626,8,54,1,54,1,54,1,54,1,55,1,55,1,55,
        1,55,1,55,1,55,1,55,1,55,1,55,1,56,1,56,5,56,642,8,56,10,56,12,56,
        645,9,56,1,57,1,57,1,57,1,57,1,57,1,57,1,57,3,57,654,8,57,1,58,1,
        58,1,58,5,58,659,8,58,10,58,12,58,662,9,58,1,59,1,59,1,60,1,60,1,
        60,5,60,669,8,60,10,60,12,60,672,9,60,1,61,1,61,1,61,5,61,677,8,
        61,10,61,12,61,680,9,61,1,62,1,62,1,62,3,62,685,8,62,1,63,1,63,1,
        63,5,63,690,8,63,10,63,12,63,693,9,63,1,64,1,64,1,64,5,64,698,8,
        64,10,64,12,64,701,9,64,1,65,1,65,1,65,1,65,1,65,3,65,708,8,65,1,
        66,1,66,1,66,1,66,1,66,1,66,1,66,1,66,1,66,1,66,3,66,720,8,66,1,
        66,1,66,1,66,1,66,1,66,1,66,1,66,3,66,729,8,66,1,67,1,67,1,67,1,
        67,3,67,735,8,67,1,67,3,67,738,8,67,1,68,1,68,1,68,1,68,1,68,1,69,
        1,69,1,70,1,70,1,70,0,0,71,0,2,4,6,8,10,12,14,16,18,20,22,24,26,
        28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62,64,66,68,70,
        72,74,76,78,80,82,84,86,88,90,92,94,96,98,100,102,104,106,108,110,
        112,114,116,118,120,122,124,126,128,130,132,134,136,138,140,0,18,
        2,0,61,67,104,104,1,0,84,85,1,0,33,36,2,0,68,69,104,104,2,0,47,50,
        53,59,1,0,43,44,1,0,103,104,1,0,49,50,1,0,43,46,2,0,7,7,9,9,1,0,
        20,21,2,0,70,70,104,104,1,0,74,75,1,0,78,83,2,0,71,72,86,87,2,0,
        76,76,84,85,1,0,61,67,2,0,99,100,102,102,796,0,144,1,0,0,0,2,148,
        1,0,0,0,4,160,1,0,0,0,6,204,1,0,0,0,8,215,1,0,0,0,10,226,1,0,0,0,
        12,242,1,0,0,0,14,244,1,0,0,0,16,250,1,0,0,0,18,255,1,0,0,0,20,261,
        1,0,0,0,22,266,1,0,0,0,24,275,1,0,0,0,26,277,1,0,0,0,28,281,1,0,
        0,0,30,285,1,0,0,0,32,289,1,0,0,0,34,293,1,0,0,0,36,302,1,0,0,0,
        38,311,1,0,0,0,40,330,1,0,0,0,42,332,1,0,0,0,44,334,1,0,0,0,46,339,
        1,0,0,0,48,354,1,0,0,0,50,369,1,0,0,0,52,371,1,0,0,0,54,380,1,0,
        0,0,56,398,1,0,0,0,58,401,1,0,0,0,60,414,1,0,0,0,62,436,1,0,0,0,
        64,441,1,0,0,0,66,457,1,0,0,0,68,461,1,0,0,0,70,478,1,0,0,0,72,480,
        1,0,0,0,74,486,1,0,0,0,76,495,1,0,0,0,78,502,1,0,0,0,80,506,1,0,
        0,0,82,512,1,0,0,0,84,521,1,0,0,0,86,529,1,0,0,0,88,531,1,0,0,0,
        90,537,1,0,0,0,92,561,1,0,0,0,94,563,1,0,0,0,96,567,1,0,0,0,98,575,
        1,0,0,0,100,597,1,0,0,0,102,599,1,0,0,0,104,610,1,0,0,0,106,618,
        1,0,0,0,108,623,1,0,0,0,110,630,1,0,0,0,112,639,1,0,0,0,114,653,
        1,0,0,0,116,655,1,0,0,0,118,663,1,0,0,0,120,665,1,0,0,0,122,673,
        1,0,0,0,124,681,1,0,0,0,126,686,1,0,0,0,128,694,1,0,0,0,130,707,
        1,0,0,0,132,728,1,0,0,0,134,730,1,0,0,0,136,739,1,0,0,0,138,744,
        1,0,0,0,140,746,1,0,0,0,142,145,3,2,1,0,143,145,3,4,2,0,144,142,
        1,0,0,0,144,143,1,0,0,0,145,146,1,0,0,0,146,147,5,0,0,1,147,1,1,
        0,0,0,148,149,5,1,0,0,149,154,5,104,0,0,150,151,5,90,0,0,151,152,
        3,84,42,0,152,153,5,91,0,0,153,155,1,0,0,0,154,150,1,0,0,0,154,155,
        1,0,0,0,155,156,1,0,0,0,156,157,5,96,0,0,157,158,3,10,5,0,158,159,
        5,98,0,0,159,3,1,0,0,0,160,161,5,2,0,0,161,162,3,8,4,0,162,163,5,
        96,0,0,163,165,5,3,0,0,164,166,3,6,3,0,165,164,1,0,0,0,165,166,1,
        0,0,0,166,170,1,0,0,0,167,169,3,12,6,0,168,167,1,0,0,0,169,172,1,
        0,0,0,170,168,1,0,0,0,170,171,1,0,0,0,171,176,1,0,0,0,172,170,1,
        0,0,0,173,175,3,58,29,0,174,173,1,0,0,0,175,178,1,0,0,0,176,174,
        1,0,0,0,176,177,1,0,0,0,177,179,1,0,0,0,178,176,1,0,0,0,179,181,
        5,4,0,0,180,182,3,6,3,0,181,180,1,0,0,0,181,182,1,0,0,0,182,186,
        1,0,0,0,183,185,3,12,6,0,184,183,1,0,0,0,185,188,1,0,0,0,186,184,
        1,0,0,0,186,187,1,0,0,0,187,194,1,0,0,0,188,186,1,0,0,0,189,193,
        3,60,30,0,190,193,3,64,32,0,191,193,3,68,34,0,192,189,1,0,0,0,192,
        190,1,0,0,0,192,191,1,0,0,0,193,196,1,0,0,0,194,192,1,0,0,0,194,
        195,1,0,0,0,195,202,1,0,0,0,196,194,1,0,0,0,197,198,3,88,44,0,198,
        199,5,98,0,0,199,203,1,0,0,0,200,201,5,11,0,0,201,203,5,98,0,0,202,
        197,1,0,0,0,202,200,1,0,0,0,203,5,1,0,0,0,204,205,5,5,0,0,205,210,
        3,8,4,0,206,207,5,94,0,0,207,209,3,8,4,0,208,206,1,0,0,0,209,212,
        1,0,0,0,210,208,1,0,0,0,210,211,1,0,0,0,211,213,1,0,0,0,212,210,
        1,0,0,0,213,214,5,96,0,0,214,7,1,0,0,0,215,220,5,104,0,0,216,217,
        5,98,0,0,217,219,5,104,0,0,218,216,1,0,0,0,219,222,1,0,0,0,220,218,
        1,0,0,0,220,221,1,0,0,0,221,9,1,0,0,0,222,220,1,0,0,0,223,225,3,
        12,6,0,224,223,1,0,0,0,225,228,1,0,0,0,226,224,1,0,0,0,226,227,1,
        0,0,0,227,234,1,0,0,0,228,226,1,0,0,0,229,233,3,60,30,0,230,233,
        3,64,32,0,231,233,3,68,34,0,232,229,1,0,0,0,232,230,1,0,0,0,232,
        231,1,0,0,0,233,236,1,0,0,0,234,232,1,0,0,0,234,235,1,0,0,0,235,
        237,1,0,0,0,236,234,1,0,0,0,237,238,3,88,44,0,238,11,1,0,0,0,239,
        243,3,14,7,0,240,243,3,18,9,0,241,243,3,80,40,0,242,239,1,0,0,0,
        242,240,1,0,0,0,242,241,1,0,0,0,243,13,1,0,0,0,244,246,5,7,0,0,245,
        247,3,16,8,0,246,245,1,0,0,0,247,248,1,0,0,0,248,246,1,0,0,0,248,
        249,1,0,0,0,249,15,1,0,0,0,250,251,5,104,0,0,251,252,5,81,0,0,252,
        253,3,118,59,0,253,254,5,96,0,0,254,17,1,0,0,0,255,257,5,8,0,0,256,
        258,3,20,10,0,257,256,1,0,0,0,258,259,1,0,0,0,259,257,1,0,0,0,259,
        260,1,0,0,0,260,19,1,0,0,0,261,262,3,22,11,0,262,263,5,81,0,0,263,
        264,3,24,12,0,264,265,5,96,0,0,265,21,1,0,0,0,266,267,7,0,0,0,267,
        23,1,0,0,0,268,276,3,86,43,0,269,276,3,26,13,0,270,276,3,28,14,0,
        271,276,3,32,16,0,272,276,3,34,17,0,273,276,3,36,18,0,274,276,3,
        38,19,0,275,268,1,0,0,0,275,269,1,0,0,0,275,270,1,0,0,0,275,271,
        1,0,0,0,275,272,1,0,0,0,275,273,1,0,0,0,275,274,1,0,0,0,276,25,1,
        0,0,0,277,278,3,30,15,0,278,279,5,97,0,0,279,280,3,30,15,0,280,27,
        1,0,0,0,281,282,5,88,0,0,282,283,3,86,43,0,283,29,1,0,0,0,284,286,
        7,1,0,0,285,284,1,0,0,0,285,286,1,0,0,0,286,287,1,0,0,0,287,288,
        3,140,70,0,288,31,1,0,0,0,289,290,5,90,0,0,290,291,3,84,42,0,291,
        292,5,91,0,0,292,33,1,0,0,0,293,297,5,29,0,0,294,296,3,44,22,0,295,
        294,1,0,0,0,296,299,1,0,0,0,297,295,1,0,0,0,297,298,1,0,0,0,298,
        300,1,0,0,0,299,297,1,0,0,0,300,301,5,11,0,0,301,35,1,0,0,0,302,
        303,5,30,0,0,303,304,5,92,0,0,304,305,3,118,59,0,305,306,5,97,0,
        0,306,307,3,118,59,0,307,308,5,93,0,0,308,309,5,31,0,0,309,310,3,
        86,43,0,310,37,1,0,0,0,311,316,5,32,0,0,312,313,5,90,0,0,313,314,
        3,86,43,0,314,315,5,91,0,0,315,317,1,0,0,0,316,312,1,0,0,0,316,317,
        1,0,0,0,317,321,1,0,0,0,318,320,3,40,20,0,319,318,1,0,0,0,320,323,
        1,0,0,0,321,319,1,0,0,0,321,322,1,0,0,0,322,324,1,0,0,0,323,321,
        1,0,0,0,324,325,5,11,0,0,325,39,1,0,0,0,326,331,3,42,21,0,327,331,
        3,44,22,0,328,331,3,54,27,0,329,331,3,46,23,0,330,326,1,0,0,0,330,
        327,1,0,0,0,330,328,1,0,0,0,330,329,1,0,0,0,331,41,1,0,0,0,332,333,
        7,2,0,0,333,43,1,0,0,0,334,335,3,84,42,0,335,336,5,95,0,0,336,337,
        3,86,43,0,337,338,5,96,0,0,338,45,1,0,0,0,339,340,5,37,0,0,340,342,
        5,104,0,0,341,343,3,48,24,0,342,341,1,0,0,0,342,343,1,0,0,0,343,
        344,1,0,0,0,344,345,5,95,0,0,345,349,3,86,43,0,346,348,3,50,25,0,
        347,346,1,0,0,0,348,351,1,0,0,0,349,347,1,0,0,0,349,350,1,0,0,0,
        350,352,1,0,0,0,351,349,1,0,0,0,352,353,5,96,0,0,353,47,1,0,0,0,
        354,356,5,92,0,0,355,357,3,74,37,0,356,355,1,0,0,0,356,357,1,0,0,
        0,357,358,1,0,0,0,358,359,5,93,0,0,359,49,1,0,0,0,360,361,5,38,0,
        0,361,370,3,52,26,0,362,363,5,39,0,0,363,370,3,52,26,0,364,365,5,
        40,0,0,365,370,7,3,0,0,366,367,5,41,0,0,367,370,3,118,59,0,368,370,
        5,42,0,0,369,360,1,0,0,0,369,362,1,0,0,0,369,364,1,0,0,0,369,366,
        1,0,0,0,369,368,1,0,0,0,370,51,1,0,0,0,371,376,5,104,0,0,372,373,
        5,98,0,0,373,375,5,104,0,0,374,372,1,0,0,0,375,378,1,0,0,0,376,374,
        1,0,0,0,376,377,1,0,0,0,377,53,1,0,0,0,378,376,1,0,0,0,379,381,5,
        32,0,0,380,379,1,0,0,0,380,381,1,0,0,0,381,382,1,0,0,0,382,383,3,
        70,35,0,383,385,5,104,0,0,384,386,3,72,36,0,385,384,1,0,0,0,385,
        386,1,0,0,0,386,389,1,0,0,0,387,388,5,95,0,0,388,390,3,86,43,0,389,
        387,1,0,0,0,389,390,1,0,0,0,390,391,1,0,0,0,391,395,5,96,0,0,392,
        394,3,56,28,0,393,392,1,0,0,0,394,397,1,0,0,0,395,393,1,0,0,0,395,
        396,1,0,0,0,396,55,1,0,0,0,397,395,1,0,0,0,398,399,7,4,0,0,399,400,
        5,96,0,0,400,57,1,0,0,0,401,402,7,5,0,0,402,404,5,104,0,0,403,405,
        3,72,36,0,404,403,1,0,0,0,404,405,1,0,0,0,405,408,1,0,0,0,406,407,
        5,95,0,0,407,409,3,86,43,0,408,406,1,0,0,0,408,409,1,0,0,0,409,410,
        1,0,0,0,410,412,5,96,0,0,411,413,3,66,33,0,412,411,1,0,0,0,412,413,
        1,0,0,0,413,59,1,0,0,0,414,415,7,5,0,0,415,417,5,104,0,0,416,418,
        3,72,36,0,417,416,1,0,0,0,417,418,1,0,0,0,418,421,1,0,0,0,419,420,
        5,95,0,0,420,422,3,86,43,0,421,419,1,0,0,0,421,422,1,0,0,0,422,423,
        1,0,0,0,423,425,5,96,0,0,424,426,3,66,33,0,425,424,1,0,0,0,425,426,
        1,0,0,0,426,432,1,0,0,0,427,429,5,51,0,0,428,430,3,62,31,0,429,428,
        1,0,0,0,429,430,1,0,0,0,430,433,1,0,0,0,431,433,5,53,0,0,432,427,
        1,0,0,0,432,431,1,0,0,0,433,434,1,0,0,0,434,435,5,96,0,0,435,61,
        1,0,0,0,436,439,7,6,0,0,437,438,5,52,0,0,438,440,5,103,0,0,439,437,
        1,0,0,0,439,440,1,0,0,0,440,63,1,0,0,0,441,442,7,5,0,0,442,444,5,
        104,0,0,443,445,3,72,36,0,444,443,1,0,0,0,444,445,1,0,0,0,445,448,
        1,0,0,0,446,447,5,95,0,0,447,449,3,86,43,0,448,446,1,0,0,0,448,449,
        1,0,0,0,449,450,1,0,0,0,450,452,5,96,0,0,451,453,3,66,33,0,452,451,
        1,0,0,0,452,453,1,0,0,0,453,454,1,0,0,0,454,455,3,78,39,0,455,456,
        5,96,0,0,456,65,1,0,0,0,457,458,7,7,0,0,458,459,5,96,0,0,459,67,
        1,0,0,0,460,462,5,32,0,0,461,460,1,0,0,0,461,462,1,0,0,0,462,463,
        1,0,0,0,463,464,3,70,35,0,464,465,5,104,0,0,465,466,5,98,0,0,466,
        468,5,104,0,0,467,469,3,72,36,0,468,467,1,0,0,0,468,469,1,0,0,0,
        469,472,1,0,0,0,470,471,5,95,0,0,471,473,3,86,43,0,472,470,1,0,0,
        0,472,473,1,0,0,0,473,474,1,0,0,0,474,475,5,96,0,0,475,476,3,78,
        39,0,476,477,5,96,0,0,477,69,1,0,0,0,478,479,7,8,0,0,479,71,1,0,
        0,0,480,482,5,90,0,0,481,483,3,74,37,0,482,481,1,0,0,0,482,483,1,
        0,0,0,483,484,1,0,0,0,484,485,5,91,0,0,485,73,1,0,0,0,486,491,3,
        76,38,0,487,488,5,96,0,0,488,490,3,76,38,0,489,487,1,0,0,0,490,493,
        1,0,0,0,491,489,1,0,0,0,491,492,1,0,0,0,492,75,1,0,0,0,493,491,1,
        0,0,0,494,496,7,9,0,0,495,494,1,0,0,0,495,496,1,0,0,0,496,497,1,
        0,0,0,497,498,3,84,42,0,498,499,5,95,0,0,499,500,3,86,43,0,500,77,
        1,0,0,0,501,503,3,80,40,0,502,501,1,0,0,0,502,503,1,0,0,0,503,504,
        1,0,0,0,504,505,3,88,44,0,505,79,1,0,0,0,506,508,5,9,0,0,507,509,
        3,82,41,0,508,507,1,0,0,0,509,510,1,0,0,0,510,508,1,0,0,0,510,511,
        1,0,0,0,511,81,1,0,0,0,512,513,3,84,42,0,513,514,5,95,0,0,514,517,
        3,86,43,0,515,516,5,77,0,0,516,518,3,118,59,0,517,515,1,0,0,0,517,
        518,1,0,0,0,518,519,1,0,0,0,519,520,5,96,0,0,520,83,1,0,0,0,521,
        526,5,104,0,0,522,523,5,94,0,0,523,525,5,104,0,0,524,522,1,0,0,0,
        525,528,1,0,0,0,526,524,1,0,0,0,526,527,1,0,0,0,527,85,1,0,0,0,528,
        526,1,0,0,0,529,530,7,0,0,0,530,87,1,0,0,0,531,533,5,10,0,0,532,
        534,3,90,45,0,533,532,1,0,0,0,533,534,1,0,0,0,534,535,1,0,0,0,535,
        536,5,11,0,0,536,89,1,0,0,0,537,542,3,92,46,0,538,539,5,96,0,0,539,
        541,3,92,46,0,540,538,1,0,0,0,541,544,1,0,0,0,542,540,1,0,0,0,542,
        543,1,0,0,0,543,546,1,0,0,0,544,542,1,0,0,0,545,547,5,96,0,0,546,
        545,1,0,0,0,546,547,1,0,0,0,547,91,1,0,0,0,548,562,3,88,44,0,549,
        562,3,94,47,0,550,562,3,102,51,0,551,562,3,96,48,0,552,562,3,98,
        49,0,553,562,3,100,50,0,554,562,3,104,52,0,555,562,3,106,53,0,556,
        562,3,108,54,0,557,562,3,110,55,0,558,562,5,22,0,0,559,562,5,23,
        0,0,560,562,5,24,0,0,561,548,1,0,0,0,561,549,1,0,0,0,561,550,1,0,
        0,0,561,551,1,0,0,0,561,552,1,0,0,0,561,553,1,0,0,0,561,554,1,0,
        0,0,561,555,1,0,0,0,561,556,1,0,0,0,561,557,1,0,0,0,561,558,1,0,
        0,0,561,559,1,0,0,0,561,560,1,0,0,0,562,93,1,0,0,0,563,564,3,112,
        56,0,564,565,5,77,0,0,565,566,3,118,59,0,566,95,1,0,0,0,567,573,
        3,112,56,0,568,570,5,90,0,0,569,571,3,116,58,0,570,569,1,0,0,0,570,
        571,1,0,0,0,571,572,1,0,0,0,572,574,5,91,0,0,573,568,1,0,0,0,573,
        574,1,0,0,0,574,97,1,0,0,0,575,577,5,25,0,0,576,578,3,118,59,0,577,
        576,1,0,0,0,577,578,1,0,0,0,578,99,1,0,0,0,579,581,5,26,0,0,580,
        582,3,90,45,0,581,580,1,0,0,0,581,582,1,0,0,0,582,583,1,0,0,0,583,
        585,5,27,0,0,584,586,3,90,45,0,585,584,1,0,0,0,585,586,1,0,0,0,586,
        587,1,0,0,0,587,598,5,11,0,0,588,590,5,26,0,0,589,591,3,90,45,0,
        590,589,1,0,0,0,590,591,1,0,0,0,591,592,1,0,0,0,592,594,5,28,0,0,
        593,595,3,90,45,0,594,593,1,0,0,0,594,595,1,0,0,0,595,596,1,0,0,
        0,596,598,5,11,0,0,597,579,1,0,0,0,597,588,1,0,0,0,598,101,1,0,0,
        0,599,608,5,60,0,0,600,606,5,104,0,0,601,603,5,90,0,0,602,604,3,
        116,58,0,603,602,1,0,0,0,603,604,1,0,0,0,604,605,1,0,0,0,605,607,
        5,91,0,0,606,601,1,0,0,0,606,607,1,0,0,0,607,609,1,0,0,0,608,600,
        1,0,0,0,608,609,1,0,0,0,609,103,1,0,0,0,610,611,5,12,0,0,611,612,
        3,118,59,0,612,613,5,13,0,0,613,616,3,92,46,0,614,615,5,14,0,0,615,
        617,3,92,46,0,616,614,1,0,0,0,616,617,1,0,0,0,617,105,1,0,0,0,618,
        619,5,15,0,0,619,620,3,118,59,0,620,621,5,16,0,0,621,622,3,92,46,
        0,622,107,1,0,0,0,623,625,5,17,0,0,624,626,3,90,45,0,625,624,1,0,
        0,0,625,626,1,0,0,0,626,627,1,0,0,0,627,628,5,18,0,0,628,629,3,118,
        59,0,629,109,1,0,0,0,630,631,5,19,0,0,631,632,5,104,0,0,632,633,
        5,77,0,0,633,634,3,118,59,0,634,635,7,10,0,0,635,636,3,118,59,0,
        636,637,5,16,0,0,637,638,3,92,46,0,638,111,1,0,0,0,639,643,7,11,
        0,0,640,642,3,114,57,0,641,640,1,0,0,0,642,645,1,0,0,0,643,641,1,
        0,0,0,643,644,1,0,0,0,644,113,1,0,0,0,645,643,1,0,0,0,646,647,5,
        98,0,0,647,654,5,104,0,0,648,649,5,92,0,0,649,650,3,118,59,0,650,
        651,5,93,0,0,651,654,1,0,0,0,652,654,5,88,0,0,653,646,1,0,0,0,653,
        648,1,0,0,0,653,652,1,0,0,0,654,115,1,0,0,0,655,660,3,118,59,0,656,
        657,5,94,0,0,657,659,3,118,59,0,658,656,1,0,0,0,659,662,1,0,0,0,
        660,658,1,0,0,0,660,661,1,0,0,0,661,117,1,0,0,0,662,660,1,0,0,0,
        663,664,3,120,60,0,664,119,1,0,0,0,665,670,3,122,61,0,666,667,7,
        12,0,0,667,669,3,122,61,0,668,666,1,0,0,0,669,672,1,0,0,0,670,668,
        1,0,0,0,670,671,1,0,0,0,671,121,1,0,0,0,672,670,1,0,0,0,673,678,
        3,124,62,0,674,675,5,73,0,0,675,677,3,124,62,0,676,674,1,0,0,0,677,
        680,1,0,0,0,678,676,1,0,0,0,678,679,1,0,0,0,679,123,1,0,0,0,680,
        678,1,0,0,0,681,684,3,126,63,0,682,683,7,13,0,0,683,685,3,126,63,
        0,684,682,1,0,0,0,684,685,1,0,0,0,685,125,1,0,0,0,686,691,3,128,
        64,0,687,688,7,1,0,0,688,690,3,128,64,0,689,687,1,0,0,0,690,693,
        1,0,0,0,691,689,1,0,0,0,691,692,1,0,0,0,692,127,1,0,0,0,693,691,
        1,0,0,0,694,699,3,130,65,0,695,696,7,14,0,0,696,698,3,130,65,0,697,
        695,1,0,0,0,698,701,1,0,0,0,699,697,1,0,0,0,699,700,1,0,0,0,700,
        129,1,0,0,0,701,699,1,0,0,0,702,703,7,15,0,0,703,708,3,130,65,0,
        704,705,5,89,0,0,705,708,3,112,56,0,706,708,3,132,66,0,707,702,1,
        0,0,0,707,704,1,0,0,0,707,706,1,0,0,0,708,131,1,0,0,0,709,729,3,
        140,70,0,710,729,5,103,0,0,711,729,5,68,0,0,712,729,5,69,0,0,713,
        729,5,70,0,0,714,729,3,136,68,0,715,729,3,134,67,0,716,717,3,112,
        56,0,717,719,5,90,0,0,718,720,3,116,58,0,719,718,1,0,0,0,719,720,
        1,0,0,0,720,721,1,0,0,0,721,722,5,91,0,0,722,729,1,0,0,0,723,729,
        3,112,56,0,724,725,5,90,0,0,725,726,3,118,59,0,726,727,5,91,0,0,
        727,729,1,0,0,0,728,709,1,0,0,0,728,710,1,0,0,0,728,711,1,0,0,0,
        728,712,1,0,0,0,728,713,1,0,0,0,728,714,1,0,0,0,728,715,1,0,0,0,
        728,716,1,0,0,0,728,723,1,0,0,0,728,724,1,0,0,0,729,133,1,0,0,0,
        730,731,5,60,0,0,731,737,5,104,0,0,732,734,5,90,0,0,733,735,3,116,
        58,0,734,733,1,0,0,0,734,735,1,0,0,0,735,736,1,0,0,0,736,738,5,91,
        0,0,737,732,1,0,0,0,737,738,1,0,0,0,738,135,1,0,0,0,739,740,3,138,
        69,0,740,741,5,90,0,0,741,742,3,118,59,0,742,743,5,91,0,0,743,137,
        1,0,0,0,744,745,7,16,0,0,745,139,1,0,0,0,746,747,7,17,0,0,747,141,
        1,0,0,0,85,144,154,165,170,176,181,186,192,194,202,210,220,226,232,
        234,242,248,259,275,285,297,316,321,330,342,349,356,369,376,380,
        385,389,395,404,408,412,417,421,425,429,432,439,444,448,452,461,
        468,472,482,491,495,502,510,517,526,533,542,546,561,570,573,577,
        581,585,590,594,597,603,606,608,616,625,643,653,660,670,678,684,
        691,699,707,719,728,734,737
    ]

class C64PascalParser ( Parser ):

    grammarFileName = "C64PascalParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'PROGRAM'", "'UNIT'", "'INTERFACE'", 
                     "'IMPLEMENTATION'", "'USES'", "'LIBRARY'", "'CONST'", 
                     "'TYPE'", "'VAR'", "'BEGIN'", "'END'", "'IF'", "'THEN'", 
                     "'ELSE'", "'WHILE'", "'DO'", "'REPEAT'", "'UNTIL'", 
                     "'FOR'", "'TO'", "'DOWNTO'", "'BREAK'", "'CONTINUE'", 
                     "'EXIT'", "'RAISE'", "'TRY'", "'EXCEPT'", "'FINALLY'", 
                     "'RECORD'", "'ARRAY'", "'OF'", "'CLASS'", "'PRIVATE'", 
                     "'PROTECTED'", "'PUBLIC'", "'PUBLISHED'", "'PROPERTY'", 
                     "'READ'", "'WRITE'", "'STORED'", "'DEFAULT'", "'NODEFAULT'", 
                     "'PROCEDURE'", "'FUNCTION'", "'CONSTRUCTOR'", "'DESTRUCTOR'", 
                     "'VIRTUAL'", "'OVERRIDE'", "'CDECL'", "'STDCALL'", 
                     "'EXTERNAL'", "'NAME'", "'FORWARD'", "'STATIC'", "'ABSTRACT'", 
                     "'OVERLOAD'", "'REINTRODUCE'", "'INLINE'", "'DYNAMIC'", 
                     "'INHERITED'", "'INTEGER'", "'BYTE'", "'CHAR'", "'BOOLEAN'", 
                     "'POINTER'", "'STRING'", "'DOUBLE'", "'TRUE'", "'FALSE'", 
                     "'NIL'", "'DIV'", "'MOD'", "'AND'", "'OR'", "'XOR'", 
                     "'NOT'", "':='", "'<='", "'>='", "'<>'", "'='", "'<'", 
                     "'>'", "'+'", "'-'", "'*'", "'/'", "'^'", "'@'", "'('", 
                     "')'", "'['", "']'", "','", "':'", "';'", "'..'", "'.'" ]

    symbolicNames = [ "<INVALID>", "PROGRAM", "UNIT", "INTERFACE", "IMPLEMENTATION", 
                      "USES", "LIBRARY", "CONST", "TYPE", "VAR", "BEGIN", 
                      "END", "IF", "THEN", "ELSE", "WHILE", "DO", "REPEAT", 
                      "UNTIL", "FOR", "TO", "DOWNTO", "BREAK", "CONTINUE", 
                      "EXIT", "RAISE", "TRY", "EXCEPT", "FINALLY", "RECORD", 
                      "ARRAY", "OF", "CLASS", "PRIVATE", "PROTECTED", "PUBLIC", 
                      "PUBLISHED", "PROPERTY", "READ", "WRITE", "STORED", 
                      "DEFAULT", "NODEFAULT", "PROCEDURE", "FUNCTION", "CONSTRUCTOR", 
                      "DESTRUCTOR", "VIRTUAL", "OVERRIDE", "CDECL", "STDCALL", 
                      "EXTERNAL", "NAME", "FORWARD", "STATIC", "ABSTRACT", 
                      "OVERLOAD", "REINTRODUCE", "INLINE", "DYNAMIC", "INHERITED", 
                      "INTEGER_TYPE", "BYTE_TYPE", "CHAR_TYPE", "BOOLEAN_TYPE", 
                      "POINTER_TYPE", "STRING_TYPE", "DOUBLE_TYPE", "TRUE", 
                      "FALSE", "NIL", "DIV", "MOD", "AND", "OR", "XOR", 
                      "NOT", "ASSIGN", "LE", "GE", "NE", "EQ", "LT", "GT", 
                      "PLUS", "MINUS", "STAR", "SLASH", "CARET", "AT", "LPAREN", 
                      "RPAREN", "LBRACK", "RBRACK", "COMMA", "COLON", "SEMI", 
                      "DOTDOT", "DOT", "HEX_INTEGER", "BINARY_INTEGER", 
                      "REAL_LITERAL", "DECIMAL_INTEGER", "STRING_LITERAL", 
                      "IDENTIFIER", "BRACE_COMMENT", "PAREN_COMMENT", "LINE_COMMENT", 
                      "WS" ]

    RULE_compilationUnit = 0
    RULE_programUnit = 1
    RULE_unitUnit = 2
    RULE_usesClause = 3
    RULE_qualifiedIdentifier = 4
    RULE_block = 5
    RULE_declarationSection = 6
    RULE_constSection = 7
    RULE_constDefinition = 8
    RULE_typeSection = 9
    RULE_typeDefinition = 10
    RULE_typeName = 11
    RULE_typeSpecification = 12
    RULE_subrangeType = 13
    RULE_pointerType = 14
    RULE_signedIntegerLiteral = 15
    RULE_enumType = 16
    RULE_recordType = 17
    RULE_arrayType = 18
    RULE_classType = 19
    RULE_classMember = 20
    RULE_visibilitySpecifier = 21
    RULE_fieldDeclaration = 22
    RULE_propertyDeclaration = 23
    RULE_propertyIndexParameters = 24
    RULE_propertySpecifier = 25
    RULE_propertyAccessor = 26
    RULE_methodDeclaration = 27
    RULE_methodDirective = 28
    RULE_globalRoutinePrototype = 29
    RULE_globalRoutineDeclaration = 30
    RULE_externalImportSpecification = 31
    RULE_globalRoutineImplementation = 32
    RULE_globalRoutineCallingConvention = 33
    RULE_methodImplementation = 34
    RULE_routineKind = 35
    RULE_formalParameters = 36
    RULE_formalParameterList = 37
    RULE_formalParameterGroup = 38
    RULE_routineBlock = 39
    RULE_varSection = 40
    RULE_varDeclaration = 41
    RULE_identifierList = 42
    RULE_typeIdentifier = 43
    RULE_compoundStatement = 44
    RULE_statementSequence = 45
    RULE_statement = 46
    RULE_assignmentStatement = 47
    RULE_callStatement = 48
    RULE_raiseStatement = 49
    RULE_tryStatement = 50
    RULE_inheritedStatement = 51
    RULE_ifStatement = 52
    RULE_whileStatement = 53
    RULE_repeatStatement = 54
    RULE_forStatement = 55
    RULE_designator = 56
    RULE_designatorSuffix = 57
    RULE_argumentList = 58
    RULE_expression = 59
    RULE_orExpression = 60
    RULE_andExpression = 61
    RULE_comparisonExpression = 62
    RULE_additiveExpression = 63
    RULE_multiplicativeExpression = 64
    RULE_unaryExpression = 65
    RULE_primaryExpression = 66
    RULE_inheritedExpression = 67
    RULE_typeCastExpression = 68
    RULE_builtinCastType = 69
    RULE_integerLiteral = 70

    ruleNames =  [ "compilationUnit", "programUnit", "unitUnit", "usesClause", 
                   "qualifiedIdentifier", "block", "declarationSection", 
                   "constSection", "constDefinition", "typeSection", "typeDefinition", 
                   "typeName", "typeSpecification", "subrangeType", "pointerType", 
                   "signedIntegerLiteral", "enumType", "recordType", "arrayType", 
                   "classType", "classMember", "visibilitySpecifier", "fieldDeclaration", 
                   "propertyDeclaration", "propertyIndexParameters", "propertySpecifier", 
                   "propertyAccessor", "methodDeclaration", "methodDirective", 
                   "globalRoutinePrototype", "globalRoutineDeclaration", 
                   "externalImportSpecification", "globalRoutineImplementation", 
                   "globalRoutineCallingConvention", "methodImplementation", 
                   "routineKind", "formalParameters", "formalParameterList", 
                   "formalParameterGroup", "routineBlock", "varSection", 
                   "varDeclaration", "identifierList", "typeIdentifier", 
                   "compoundStatement", "statementSequence", "statement", 
                   "assignmentStatement", "callStatement", "raiseStatement", 
                   "tryStatement", "inheritedStatement", "ifStatement", 
                   "whileStatement", "repeatStatement", "forStatement", 
                   "designator", "designatorSuffix", "argumentList", "expression", 
                   "orExpression", "andExpression", "comparisonExpression", 
                   "additiveExpression", "multiplicativeExpression", "unaryExpression", 
                   "primaryExpression", "inheritedExpression", "typeCastExpression", 
                   "builtinCastType", "integerLiteral" ]

    EOF = Token.EOF
    PROGRAM=1
    UNIT=2
    INTERFACE=3
    IMPLEMENTATION=4
    USES=5
    LIBRARY=6
    CONST=7
    TYPE=8
    VAR=9
    BEGIN=10
    END=11
    IF=12
    THEN=13
    ELSE=14
    WHILE=15
    DO=16
    REPEAT=17
    UNTIL=18
    FOR=19
    TO=20
    DOWNTO=21
    BREAK=22
    CONTINUE=23
    EXIT=24
    RAISE=25
    TRY=26
    EXCEPT=27
    FINALLY=28
    RECORD=29
    ARRAY=30
    OF=31
    CLASS=32
    PRIVATE=33
    PROTECTED=34
    PUBLIC=35
    PUBLISHED=36
    PROPERTY=37
    READ=38
    WRITE=39
    STORED=40
    DEFAULT=41
    NODEFAULT=42
    PROCEDURE=43
    FUNCTION=44
    CONSTRUCTOR=45
    DESTRUCTOR=46
    VIRTUAL=47
    OVERRIDE=48
    CDECL=49
    STDCALL=50
    EXTERNAL=51
    NAME=52
    FORWARD=53
    STATIC=54
    ABSTRACT=55
    OVERLOAD=56
    REINTRODUCE=57
    INLINE=58
    DYNAMIC=59
    INHERITED=60
    INTEGER_TYPE=61
    BYTE_TYPE=62
    CHAR_TYPE=63
    BOOLEAN_TYPE=64
    POINTER_TYPE=65
    STRING_TYPE=66
    DOUBLE_TYPE=67
    TRUE=68
    FALSE=69
    NIL=70
    DIV=71
    MOD=72
    AND=73
    OR=74
    XOR=75
    NOT=76
    ASSIGN=77
    LE=78
    GE=79
    NE=80
    EQ=81
    LT=82
    GT=83
    PLUS=84
    MINUS=85
    STAR=86
    SLASH=87
    CARET=88
    AT=89
    LPAREN=90
    RPAREN=91
    LBRACK=92
    RBRACK=93
    COMMA=94
    COLON=95
    SEMI=96
    DOTDOT=97
    DOT=98
    HEX_INTEGER=99
    BINARY_INTEGER=100
    REAL_LITERAL=101
    DECIMAL_INTEGER=102
    STRING_LITERAL=103
    IDENTIFIER=104
    BRACE_COMMENT=105
    PAREN_COMMENT=106
    LINE_COMMENT=107
    WS=108

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

        def EOF(self):
            return self.getToken(C64PascalParser.EOF, 0)

        def programUnit(self):
            return self.getTypedRuleContext(C64PascalParser.ProgramUnitContext,0)


        def unitUnit(self):
            return self.getTypedRuleContext(C64PascalParser.UnitUnitContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_compilationUnit

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCompilationUnit" ):
                listener.enterCompilationUnit(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCompilationUnit" ):
                listener.exitCompilationUnit(self)

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
            self.state = 144
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [1]:
                self.state = 142
                self.programUnit()
                pass
            elif token in [2]:
                self.state = 143
                self.unitUnit()
                pass
            else:
                raise NoViableAltException(self)

            self.state = 146
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterProgramUnit" ):
                listener.enterProgramUnit(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitProgramUnit" ):
                listener.exitProgramUnit(self)

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
            self.state = 148
            self.match(C64PascalParser.PROGRAM)
            self.state = 149
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 154
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==90:
                self.state = 150
                self.match(C64PascalParser.LPAREN)
                self.state = 151
                self.identifierList()
                self.state = 152
                self.match(C64PascalParser.RPAREN)


            self.state = 156
            self.match(C64PascalParser.SEMI)
            self.state = 157
            self.block()
            self.state = 158
            self.match(C64PascalParser.DOT)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class UnitUnitContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def UNIT(self):
            return self.getToken(C64PascalParser.UNIT, 0)

        def qualifiedIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.QualifiedIdentifierContext,0)


        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def INTERFACE(self):
            return self.getToken(C64PascalParser.INTERFACE, 0)

        def IMPLEMENTATION(self):
            return self.getToken(C64PascalParser.IMPLEMENTATION, 0)

        def compoundStatement(self):
            return self.getTypedRuleContext(C64PascalParser.CompoundStatementContext,0)


        def DOT(self):
            return self.getToken(C64PascalParser.DOT, 0)

        def END(self):
            return self.getToken(C64PascalParser.END, 0)

        def usesClause(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.UsesClauseContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.UsesClauseContext,i)


        def declarationSection(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.DeclarationSectionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.DeclarationSectionContext,i)


        def globalRoutinePrototype(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.GlobalRoutinePrototypeContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.GlobalRoutinePrototypeContext,i)


        def globalRoutineDeclaration(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.GlobalRoutineDeclarationContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.GlobalRoutineDeclarationContext,i)


        def globalRoutineImplementation(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.GlobalRoutineImplementationContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.GlobalRoutineImplementationContext,i)


        def methodImplementation(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.MethodImplementationContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.MethodImplementationContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_unitUnit

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterUnitUnit" ):
                listener.enterUnitUnit(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitUnitUnit" ):
                listener.exitUnitUnit(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUnitUnit" ):
                return visitor.visitUnitUnit(self)
            else:
                return visitor.visitChildren(self)




    def unitUnit(self):

        localctx = C64PascalParser.UnitUnitContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_unitUnit)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 160
            self.match(C64PascalParser.UNIT)
            self.state = 161
            self.qualifiedIdentifier()
            self.state = 162
            self.match(C64PascalParser.SEMI)
            self.state = 163
            self.match(C64PascalParser.INTERFACE)
            self.state = 165
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 164
                self.usesClause()


            self.state = 170
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 896) != 0):
                self.state = 167
                self.declarationSection()
                self.state = 172
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 176
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==43 or _la==44:
                self.state = 173
                self.globalRoutinePrototype()
                self.state = 178
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 179
            self.match(C64PascalParser.IMPLEMENTATION)
            self.state = 181
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 180
                self.usesClause()


            self.state = 186
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 896) != 0):
                self.state = 183
                self.declarationSection()
                self.state = 188
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 194
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 131945690300416) != 0):
                self.state = 192
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input,7,self._ctx)
                if la_ == 1:
                    self.state = 189
                    self.globalRoutineDeclaration()
                    pass

                elif la_ == 2:
                    self.state = 190
                    self.globalRoutineImplementation()
                    pass

                elif la_ == 3:
                    self.state = 191
                    self.methodImplementation()
                    pass


                self.state = 196
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 202
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [10]:
                self.state = 197
                self.compoundStatement()
                self.state = 198
                self.match(C64PascalParser.DOT)
                pass
            elif token in [11]:
                self.state = 200
                self.match(C64PascalParser.END)
                self.state = 201
                self.match(C64PascalParser.DOT)
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


    class UsesClauseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def USES(self):
            return self.getToken(C64PascalParser.USES, 0)

        def qualifiedIdentifier(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.QualifiedIdentifierContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.QualifiedIdentifierContext,i)


        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.COMMA)
            else:
                return self.getToken(C64PascalParser.COMMA, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_usesClause

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterUsesClause" ):
                listener.enterUsesClause(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitUsesClause" ):
                listener.exitUsesClause(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUsesClause" ):
                return visitor.visitUsesClause(self)
            else:
                return visitor.visitChildren(self)




    def usesClause(self):

        localctx = C64PascalParser.UsesClauseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_usesClause)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 204
            self.match(C64PascalParser.USES)
            self.state = 205
            self.qualifiedIdentifier()
            self.state = 210
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==94:
                self.state = 206
                self.match(C64PascalParser.COMMA)
                self.state = 207
                self.qualifiedIdentifier()
                self.state = 212
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 213
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class QualifiedIdentifierContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.IDENTIFIER)
            else:
                return self.getToken(C64PascalParser.IDENTIFIER, i)

        def DOT(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.DOT)
            else:
                return self.getToken(C64PascalParser.DOT, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_qualifiedIdentifier

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterQualifiedIdentifier" ):
                listener.enterQualifiedIdentifier(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitQualifiedIdentifier" ):
                listener.exitQualifiedIdentifier(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitQualifiedIdentifier" ):
                return visitor.visitQualifiedIdentifier(self)
            else:
                return visitor.visitChildren(self)




    def qualifiedIdentifier(self):

        localctx = C64PascalParser.QualifiedIdentifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_qualifiedIdentifier)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 215
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 220
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==98:
                self.state = 216
                self.match(C64PascalParser.DOT)
                self.state = 217
                self.match(C64PascalParser.IDENTIFIER)
                self.state = 222
                self._errHandler.sync(self)
                _la = self._input.LA(1)

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


        def globalRoutineDeclaration(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.GlobalRoutineDeclarationContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.GlobalRoutineDeclarationContext,i)


        def globalRoutineImplementation(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.GlobalRoutineImplementationContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.GlobalRoutineImplementationContext,i)


        def methodImplementation(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.MethodImplementationContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.MethodImplementationContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_block

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterBlock" ):
                listener.enterBlock(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitBlock" ):
                listener.exitBlock(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBlock" ):
                return visitor.visitBlock(self)
            else:
                return visitor.visitChildren(self)




    def block(self):

        localctx = C64PascalParser.BlockContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_block)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 226
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 896) != 0):
                self.state = 223
                self.declarationSection()
                self.state = 228
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 234
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 131945690300416) != 0):
                self.state = 232
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input,13,self._ctx)
                if la_ == 1:
                    self.state = 229
                    self.globalRoutineDeclaration()
                    pass

                elif la_ == 2:
                    self.state = 230
                    self.globalRoutineImplementation()
                    pass

                elif la_ == 3:
                    self.state = 231
                    self.methodImplementation()
                    pass


                self.state = 236
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 237
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDeclarationSection" ):
                listener.enterDeclarationSection(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDeclarationSection" ):
                listener.exitDeclarationSection(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDeclarationSection" ):
                return visitor.visitDeclarationSection(self)
            else:
                return visitor.visitChildren(self)




    def declarationSection(self):

        localctx = C64PascalParser.DeclarationSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_declarationSection)
        try:
            self.state = 242
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [7]:
                self.enterOuterAlt(localctx, 1)
                self.state = 239
                self.constSection()
                pass
            elif token in [8]:
                self.enterOuterAlt(localctx, 2)
                self.state = 240
                self.typeSection()
                pass
            elif token in [9]:
                self.enterOuterAlt(localctx, 3)
                self.state = 241
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConstSection" ):
                listener.enterConstSection(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConstSection" ):
                listener.exitConstSection(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConstSection" ):
                return visitor.visitConstSection(self)
            else:
                return visitor.visitChildren(self)




    def constSection(self):

        localctx = C64PascalParser.ConstSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_constSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 244
            self.match(C64PascalParser.CONST)
            self.state = 246 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 245
                self.constDefinition()
                self.state = 248 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==104):
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConstDefinition" ):
                listener.enterConstDefinition(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConstDefinition" ):
                listener.exitConstDefinition(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConstDefinition" ):
                return visitor.visitConstDefinition(self)
            else:
                return visitor.visitChildren(self)




    def constDefinition(self):

        localctx = C64PascalParser.ConstDefinitionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_constDefinition)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 250
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 251
            self.match(C64PascalParser.EQ)
            self.state = 252
            self.expression()
            self.state = 253
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTypeSection" ):
                listener.enterTypeSection(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTypeSection" ):
                listener.exitTypeSection(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeSection" ):
                return visitor.visitTypeSection(self)
            else:
                return visitor.visitChildren(self)




    def typeSection(self):

        localctx = C64PascalParser.TypeSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_typeSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 255
            self.match(C64PascalParser.TYPE)
            self.state = 257 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 256
                self.typeDefinition()
                self.state = 259 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (((((_la - 61)) & ~0x3f) == 0 and ((1 << (_la - 61)) & 8796093022335) != 0)):
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

        def typeName(self):
            return self.getTypedRuleContext(C64PascalParser.TypeNameContext,0)


        def EQ(self):
            return self.getToken(C64PascalParser.EQ, 0)

        def typeSpecification(self):
            return self.getTypedRuleContext(C64PascalParser.TypeSpecificationContext,0)


        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_typeDefinition

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTypeDefinition" ):
                listener.enterTypeDefinition(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTypeDefinition" ):
                listener.exitTypeDefinition(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeDefinition" ):
                return visitor.visitTypeDefinition(self)
            else:
                return visitor.visitChildren(self)




    def typeDefinition(self):

        localctx = C64PascalParser.TypeDefinitionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_typeDefinition)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 261
            self.typeName()
            self.state = 262
            self.match(C64PascalParser.EQ)
            self.state = 263
            self.typeSpecification()
            self.state = 264
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TypeNameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def INTEGER_TYPE(self):
            return self.getToken(C64PascalParser.INTEGER_TYPE, 0)

        def BYTE_TYPE(self):
            return self.getToken(C64PascalParser.BYTE_TYPE, 0)

        def CHAR_TYPE(self):
            return self.getToken(C64PascalParser.CHAR_TYPE, 0)

        def BOOLEAN_TYPE(self):
            return self.getToken(C64PascalParser.BOOLEAN_TYPE, 0)

        def POINTER_TYPE(self):
            return self.getToken(C64PascalParser.POINTER_TYPE, 0)

        def STRING_TYPE(self):
            return self.getToken(C64PascalParser.STRING_TYPE, 0)

        def DOUBLE_TYPE(self):
            return self.getToken(C64PascalParser.DOUBLE_TYPE, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_typeName

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTypeName" ):
                listener.enterTypeName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTypeName" ):
                listener.exitTypeName(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeName" ):
                return visitor.visitTypeName(self)
            else:
                return visitor.visitChildren(self)




    def typeName(self):

        localctx = C64PascalParser.TypeNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_typeName)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 266
            _la = self._input.LA(1)
            if not(((((_la - 61)) & ~0x3f) == 0 and ((1 << (_la - 61)) & 8796093022335) != 0)):
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


    class TypeSpecificationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def subrangeType(self):
            return self.getTypedRuleContext(C64PascalParser.SubrangeTypeContext,0)


        def pointerType(self):
            return self.getTypedRuleContext(C64PascalParser.PointerTypeContext,0)


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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTypeSpecification" ):
                listener.enterTypeSpecification(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTypeSpecification" ):
                listener.exitTypeSpecification(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeSpecification" ):
                return visitor.visitTypeSpecification(self)
            else:
                return visitor.visitChildren(self)




    def typeSpecification(self):

        localctx = C64PascalParser.TypeSpecificationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_typeSpecification)
        try:
            self.state = 275
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [61, 62, 63, 64, 65, 66, 67, 104]:
                self.enterOuterAlt(localctx, 1)
                self.state = 268
                self.typeIdentifier()
                pass
            elif token in [84, 85, 99, 100, 102]:
                self.enterOuterAlt(localctx, 2)
                self.state = 269
                self.subrangeType()
                pass
            elif token in [88]:
                self.enterOuterAlt(localctx, 3)
                self.state = 270
                self.pointerType()
                pass
            elif token in [90]:
                self.enterOuterAlt(localctx, 4)
                self.state = 271
                self.enumType()
                pass
            elif token in [29]:
                self.enterOuterAlt(localctx, 5)
                self.state = 272
                self.recordType()
                pass
            elif token in [30]:
                self.enterOuterAlt(localctx, 6)
                self.state = 273
                self.arrayType()
                pass
            elif token in [32]:
                self.enterOuterAlt(localctx, 7)
                self.state = 274
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


    class SubrangeTypeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def signedIntegerLiteral(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.SignedIntegerLiteralContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.SignedIntegerLiteralContext,i)


        def DOTDOT(self):
            return self.getToken(C64PascalParser.DOTDOT, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_subrangeType

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSubrangeType" ):
                listener.enterSubrangeType(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSubrangeType" ):
                listener.exitSubrangeType(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSubrangeType" ):
                return visitor.visitSubrangeType(self)
            else:
                return visitor.visitChildren(self)




    def subrangeType(self):

        localctx = C64PascalParser.SubrangeTypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_subrangeType)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 277
            self.signedIntegerLiteral()
            self.state = 278
            self.match(C64PascalParser.DOTDOT)
            self.state = 279
            self.signedIntegerLiteral()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PointerTypeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CARET(self):
            return self.getToken(C64PascalParser.CARET, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_pointerType

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPointerType" ):
                listener.enterPointerType(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPointerType" ):
                listener.exitPointerType(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPointerType" ):
                return visitor.visitPointerType(self)
            else:
                return visitor.visitChildren(self)




    def pointerType(self):

        localctx = C64PascalParser.PointerTypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_pointerType)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 281
            self.match(C64PascalParser.CARET)
            self.state = 282
            self.typeIdentifier()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class SignedIntegerLiteralContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def integerLiteral(self):
            return self.getTypedRuleContext(C64PascalParser.IntegerLiteralContext,0)


        def PLUS(self):
            return self.getToken(C64PascalParser.PLUS, 0)

        def MINUS(self):
            return self.getToken(C64PascalParser.MINUS, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_signedIntegerLiteral

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSignedIntegerLiteral" ):
                listener.enterSignedIntegerLiteral(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSignedIntegerLiteral" ):
                listener.exitSignedIntegerLiteral(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSignedIntegerLiteral" ):
                return visitor.visitSignedIntegerLiteral(self)
            else:
                return visitor.visitChildren(self)




    def signedIntegerLiteral(self):

        localctx = C64PascalParser.SignedIntegerLiteralContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_signedIntegerLiteral)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 285
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==84 or _la==85:
                self.state = 284
                _la = self._input.LA(1)
                if not(_la==84 or _la==85):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()


            self.state = 287
            self.integerLiteral()
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterEnumType" ):
                listener.enterEnumType(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitEnumType" ):
                listener.exitEnumType(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitEnumType" ):
                return visitor.visitEnumType(self)
            else:
                return visitor.visitChildren(self)




    def enumType(self):

        localctx = C64PascalParser.EnumTypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_enumType)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 289
            self.match(C64PascalParser.LPAREN)
            self.state = 290
            self.identifierList()
            self.state = 291
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRecordType" ):
                listener.enterRecordType(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRecordType" ):
                listener.exitRecordType(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRecordType" ):
                return visitor.visitRecordType(self)
            else:
                return visitor.visitChildren(self)




    def recordType(self):

        localctx = C64PascalParser.RecordTypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_recordType)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 293
            self.match(C64PascalParser.RECORD)
            self.state = 297
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==104:
                self.state = 294
                self.fieldDeclaration()
                self.state = 299
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 300
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterArrayType" ):
                listener.enterArrayType(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitArrayType" ):
                listener.exitArrayType(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArrayType" ):
                return visitor.visitArrayType(self)
            else:
                return visitor.visitChildren(self)




    def arrayType(self):

        localctx = C64PascalParser.ArrayTypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_arrayType)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 302
            self.match(C64PascalParser.ARRAY)
            self.state = 303
            self.match(C64PascalParser.LBRACK)
            self.state = 304
            self.expression()
            self.state = 305
            self.match(C64PascalParser.DOTDOT)
            self.state = 306
            self.expression()
            self.state = 307
            self.match(C64PascalParser.RBRACK)
            self.state = 308
            self.match(C64PascalParser.OF)
            self.state = 309
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterClassType" ):
                listener.enterClassType(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitClassType" ):
                listener.exitClassType(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitClassType" ):
                return visitor.visitClassType(self)
            else:
                return visitor.visitChildren(self)




    def classType(self):

        localctx = C64PascalParser.ClassTypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_classType)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 311
            self.match(C64PascalParser.CLASS)
            self.state = 316
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==90:
                self.state = 312
                self.match(C64PascalParser.LPAREN)
                self.state = 313
                self.typeIdentifier()
                self.state = 314
                self.match(C64PascalParser.RPAREN)


            self.state = 321
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 132211978272768) != 0) or _la==104:
                self.state = 318
                self.classMember()
                self.state = 323
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 324
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


        def propertyDeclaration(self):
            return self.getTypedRuleContext(C64PascalParser.PropertyDeclarationContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_classMember

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterClassMember" ):
                listener.enterClassMember(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitClassMember" ):
                listener.exitClassMember(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitClassMember" ):
                return visitor.visitClassMember(self)
            else:
                return visitor.visitChildren(self)




    def classMember(self):

        localctx = C64PascalParser.ClassMemberContext(self, self._ctx, self.state)
        self.enterRule(localctx, 40, self.RULE_classMember)
        try:
            self.state = 330
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [33, 34, 35, 36]:
                self.enterOuterAlt(localctx, 1)
                self.state = 326
                self.visibilitySpecifier()
                pass
            elif token in [104]:
                self.enterOuterAlt(localctx, 2)
                self.state = 327
                self.fieldDeclaration()
                pass
            elif token in [32, 43, 44, 45, 46]:
                self.enterOuterAlt(localctx, 3)
                self.state = 328
                self.methodDeclaration()
                pass
            elif token in [37]:
                self.enterOuterAlt(localctx, 4)
                self.state = 329
                self.propertyDeclaration()
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVisibilitySpecifier" ):
                listener.enterVisibilitySpecifier(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVisibilitySpecifier" ):
                listener.exitVisibilitySpecifier(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVisibilitySpecifier" ):
                return visitor.visitVisibilitySpecifier(self)
            else:
                return visitor.visitChildren(self)




    def visibilitySpecifier(self):

        localctx = C64PascalParser.VisibilitySpecifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 42, self.RULE_visibilitySpecifier)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 332
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 128849018880) != 0)):
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFieldDeclaration" ):
                listener.enterFieldDeclaration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFieldDeclaration" ):
                listener.exitFieldDeclaration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFieldDeclaration" ):
                return visitor.visitFieldDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def fieldDeclaration(self):

        localctx = C64PascalParser.FieldDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 44, self.RULE_fieldDeclaration)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 334
            self.identifierList()
            self.state = 335
            self.match(C64PascalParser.COLON)
            self.state = 336
            self.typeIdentifier()
            self.state = 337
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PropertyDeclarationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PROPERTY(self):
            return self.getToken(C64PascalParser.PROPERTY, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def propertyIndexParameters(self):
            return self.getTypedRuleContext(C64PascalParser.PropertyIndexParametersContext,0)


        def propertySpecifier(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.PropertySpecifierContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.PropertySpecifierContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_propertyDeclaration

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPropertyDeclaration" ):
                listener.enterPropertyDeclaration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPropertyDeclaration" ):
                listener.exitPropertyDeclaration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPropertyDeclaration" ):
                return visitor.visitPropertyDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def propertyDeclaration(self):

        localctx = C64PascalParser.PropertyDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 46, self.RULE_propertyDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 339
            self.match(C64PascalParser.PROPERTY)
            self.state = 340
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 342
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==92:
                self.state = 341
                self.propertyIndexParameters()


            self.state = 344
            self.match(C64PascalParser.COLON)
            self.state = 345
            self.typeIdentifier()
            self.state = 349
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 8521215115264) != 0):
                self.state = 346
                self.propertySpecifier()
                self.state = 351
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 352
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PropertyIndexParametersContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LBRACK(self):
            return self.getToken(C64PascalParser.LBRACK, 0)

        def RBRACK(self):
            return self.getToken(C64PascalParser.RBRACK, 0)

        def formalParameterList(self):
            return self.getTypedRuleContext(C64PascalParser.FormalParameterListContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_propertyIndexParameters

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPropertyIndexParameters" ):
                listener.enterPropertyIndexParameters(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPropertyIndexParameters" ):
                listener.exitPropertyIndexParameters(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPropertyIndexParameters" ):
                return visitor.visitPropertyIndexParameters(self)
            else:
                return visitor.visitChildren(self)




    def propertyIndexParameters(self):

        localctx = C64PascalParser.PropertyIndexParametersContext(self, self._ctx, self.state)
        self.enterRule(localctx, 48, self.RULE_propertyIndexParameters)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 354
            self.match(C64PascalParser.LBRACK)
            self.state = 356
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==7 or _la==9 or _la==104:
                self.state = 355
                self.formalParameterList()


            self.state = 358
            self.match(C64PascalParser.RBRACK)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PropertySpecifierContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def READ(self):
            return self.getToken(C64PascalParser.READ, 0)

        def propertyAccessor(self):
            return self.getTypedRuleContext(C64PascalParser.PropertyAccessorContext,0)


        def WRITE(self):
            return self.getToken(C64PascalParser.WRITE, 0)

        def STORED(self):
            return self.getToken(C64PascalParser.STORED, 0)

        def TRUE(self):
            return self.getToken(C64PascalParser.TRUE, 0)

        def FALSE(self):
            return self.getToken(C64PascalParser.FALSE, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def DEFAULT(self):
            return self.getToken(C64PascalParser.DEFAULT, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def NODEFAULT(self):
            return self.getToken(C64PascalParser.NODEFAULT, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_propertySpecifier

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPropertySpecifier" ):
                listener.enterPropertySpecifier(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPropertySpecifier" ):
                listener.exitPropertySpecifier(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPropertySpecifier" ):
                return visitor.visitPropertySpecifier(self)
            else:
                return visitor.visitChildren(self)




    def propertySpecifier(self):

        localctx = C64PascalParser.PropertySpecifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 50, self.RULE_propertySpecifier)
        self._la = 0 # Token type
        try:
            self.state = 369
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [38]:
                self.enterOuterAlt(localctx, 1)
                self.state = 360
                self.match(C64PascalParser.READ)
                self.state = 361
                self.propertyAccessor()
                pass
            elif token in [39]:
                self.enterOuterAlt(localctx, 2)
                self.state = 362
                self.match(C64PascalParser.WRITE)
                self.state = 363
                self.propertyAccessor()
                pass
            elif token in [40]:
                self.enterOuterAlt(localctx, 3)
                self.state = 364
                self.match(C64PascalParser.STORED)
                self.state = 365
                _la = self._input.LA(1)
                if not(((((_la - 68)) & ~0x3f) == 0 and ((1 << (_la - 68)) & 68719476739) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                pass
            elif token in [41]:
                self.enterOuterAlt(localctx, 4)
                self.state = 366
                self.match(C64PascalParser.DEFAULT)
                self.state = 367
                self.expression()
                pass
            elif token in [42]:
                self.enterOuterAlt(localctx, 5)
                self.state = 368
                self.match(C64PascalParser.NODEFAULT)
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


    class PropertyAccessorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.IDENTIFIER)
            else:
                return self.getToken(C64PascalParser.IDENTIFIER, i)

        def DOT(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.DOT)
            else:
                return self.getToken(C64PascalParser.DOT, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_propertyAccessor

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPropertyAccessor" ):
                listener.enterPropertyAccessor(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPropertyAccessor" ):
                listener.exitPropertyAccessor(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPropertyAccessor" ):
                return visitor.visitPropertyAccessor(self)
            else:
                return visitor.visitChildren(self)




    def propertyAccessor(self):

        localctx = C64PascalParser.PropertyAccessorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 52, self.RULE_propertyAccessor)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 371
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 376
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==98:
                self.state = 372
                self.match(C64PascalParser.DOT)
                self.state = 373
                self.match(C64PascalParser.IDENTIFIER)
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

        def CLASS(self):
            return self.getToken(C64PascalParser.CLASS, 0)

        def formalParameters(self):
            return self.getTypedRuleContext(C64PascalParser.FormalParametersContext,0)


        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def methodDirective(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.MethodDirectiveContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.MethodDirectiveContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_methodDeclaration

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMethodDeclaration" ):
                listener.enterMethodDeclaration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMethodDeclaration" ):
                listener.exitMethodDeclaration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMethodDeclaration" ):
                return visitor.visitMethodDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def methodDeclaration(self):

        localctx = C64PascalParser.MethodDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 54, self.RULE_methodDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 380
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==32:
                self.state = 379
                self.match(C64PascalParser.CLASS)


            self.state = 382
            self.routineKind()
            self.state = 383
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 385
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==90:
                self.state = 384
                self.formalParameters()


            self.state = 389
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==95:
                self.state = 387
                self.match(C64PascalParser.COLON)
                self.state = 388
                self.typeIdentifier()


            self.state = 391
            self.match(C64PascalParser.SEMI)
            self.state = 395
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 1146025367677435904) != 0):
                self.state = 392
                self.methodDirective()
                self.state = 397
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MethodDirectiveContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def VIRTUAL(self):
            return self.getToken(C64PascalParser.VIRTUAL, 0)

        def OVERRIDE(self):
            return self.getToken(C64PascalParser.OVERRIDE, 0)

        def CDECL(self):
            return self.getToken(C64PascalParser.CDECL, 0)

        def STDCALL(self):
            return self.getToken(C64PascalParser.STDCALL, 0)

        def FORWARD(self):
            return self.getToken(C64PascalParser.FORWARD, 0)

        def STATIC(self):
            return self.getToken(C64PascalParser.STATIC, 0)

        def ABSTRACT(self):
            return self.getToken(C64PascalParser.ABSTRACT, 0)

        def OVERLOAD(self):
            return self.getToken(C64PascalParser.OVERLOAD, 0)

        def REINTRODUCE(self):
            return self.getToken(C64PascalParser.REINTRODUCE, 0)

        def INLINE(self):
            return self.getToken(C64PascalParser.INLINE, 0)

        def DYNAMIC(self):
            return self.getToken(C64PascalParser.DYNAMIC, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_methodDirective

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMethodDirective" ):
                listener.enterMethodDirective(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMethodDirective" ):
                listener.exitMethodDirective(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMethodDirective" ):
                return visitor.visitMethodDirective(self)
            else:
                return visitor.visitChildren(self)




    def methodDirective(self):

        localctx = C64PascalParser.MethodDirectiveContext(self, self._ctx, self.state)
        self.enterRule(localctx, 56, self.RULE_methodDirective)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 398
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 1146025367677435904) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 399
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class GlobalRoutinePrototypeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def PROCEDURE(self):
            return self.getToken(C64PascalParser.PROCEDURE, 0)

        def FUNCTION(self):
            return self.getToken(C64PascalParser.FUNCTION, 0)

        def formalParameters(self):
            return self.getTypedRuleContext(C64PascalParser.FormalParametersContext,0)


        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def globalRoutineCallingConvention(self):
            return self.getTypedRuleContext(C64PascalParser.GlobalRoutineCallingConventionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_globalRoutinePrototype

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterGlobalRoutinePrototype" ):
                listener.enterGlobalRoutinePrototype(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitGlobalRoutinePrototype" ):
                listener.exitGlobalRoutinePrototype(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitGlobalRoutinePrototype" ):
                return visitor.visitGlobalRoutinePrototype(self)
            else:
                return visitor.visitChildren(self)




    def globalRoutinePrototype(self):

        localctx = C64PascalParser.GlobalRoutinePrototypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 58, self.RULE_globalRoutinePrototype)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 401
            _la = self._input.LA(1)
            if not(_la==43 or _la==44):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 402
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 404
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==90:
                self.state = 403
                self.formalParameters()


            self.state = 408
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==95:
                self.state = 406
                self.match(C64PascalParser.COLON)
                self.state = 407
                self.typeIdentifier()


            self.state = 410
            self.match(C64PascalParser.SEMI)
            self.state = 412
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==49 or _la==50:
                self.state = 411
                self.globalRoutineCallingConvention()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class GlobalRoutineDeclarationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def SEMI(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.SEMI)
            else:
                return self.getToken(C64PascalParser.SEMI, i)

        def PROCEDURE(self):
            return self.getToken(C64PascalParser.PROCEDURE, 0)

        def FUNCTION(self):
            return self.getToken(C64PascalParser.FUNCTION, 0)

        def EXTERNAL(self):
            return self.getToken(C64PascalParser.EXTERNAL, 0)

        def FORWARD(self):
            return self.getToken(C64PascalParser.FORWARD, 0)

        def formalParameters(self):
            return self.getTypedRuleContext(C64PascalParser.FormalParametersContext,0)


        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def globalRoutineCallingConvention(self):
            return self.getTypedRuleContext(C64PascalParser.GlobalRoutineCallingConventionContext,0)


        def externalImportSpecification(self):
            return self.getTypedRuleContext(C64PascalParser.ExternalImportSpecificationContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_globalRoutineDeclaration

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterGlobalRoutineDeclaration" ):
                listener.enterGlobalRoutineDeclaration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitGlobalRoutineDeclaration" ):
                listener.exitGlobalRoutineDeclaration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitGlobalRoutineDeclaration" ):
                return visitor.visitGlobalRoutineDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def globalRoutineDeclaration(self):

        localctx = C64PascalParser.GlobalRoutineDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 60, self.RULE_globalRoutineDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 414
            _la = self._input.LA(1)
            if not(_la==43 or _la==44):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 415
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 417
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==90:
                self.state = 416
                self.formalParameters()


            self.state = 421
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==95:
                self.state = 419
                self.match(C64PascalParser.COLON)
                self.state = 420
                self.typeIdentifier()


            self.state = 423
            self.match(C64PascalParser.SEMI)
            self.state = 425
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==49 or _la==50:
                self.state = 424
                self.globalRoutineCallingConvention()


            self.state = 432
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [51]:
                self.state = 427
                self.match(C64PascalParser.EXTERNAL)
                self.state = 429
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==103 or _la==104:
                    self.state = 428
                    self.externalImportSpecification()


                pass
            elif token in [53]:
                self.state = 431
                self.match(C64PascalParser.FORWARD)
                pass
            else:
                raise NoViableAltException(self)

            self.state = 434
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExternalImportSpecificationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def STRING_LITERAL(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.STRING_LITERAL)
            else:
                return self.getToken(C64PascalParser.STRING_LITERAL, i)

        def NAME(self):
            return self.getToken(C64PascalParser.NAME, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_externalImportSpecification

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterExternalImportSpecification" ):
                listener.enterExternalImportSpecification(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitExternalImportSpecification" ):
                listener.exitExternalImportSpecification(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExternalImportSpecification" ):
                return visitor.visitExternalImportSpecification(self)
            else:
                return visitor.visitChildren(self)




    def externalImportSpecification(self):

        localctx = C64PascalParser.ExternalImportSpecificationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 62, self.RULE_externalImportSpecification)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 436
            _la = self._input.LA(1)
            if not(_la==103 or _la==104):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 439
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==52:
                self.state = 437
                self.match(C64PascalParser.NAME)
                self.state = 438
                self.match(C64PascalParser.STRING_LITERAL)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class GlobalRoutineImplementationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def SEMI(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.SEMI)
            else:
                return self.getToken(C64PascalParser.SEMI, i)

        def routineBlock(self):
            return self.getTypedRuleContext(C64PascalParser.RoutineBlockContext,0)


        def PROCEDURE(self):
            return self.getToken(C64PascalParser.PROCEDURE, 0)

        def FUNCTION(self):
            return self.getToken(C64PascalParser.FUNCTION, 0)

        def formalParameters(self):
            return self.getTypedRuleContext(C64PascalParser.FormalParametersContext,0)


        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def globalRoutineCallingConvention(self):
            return self.getTypedRuleContext(C64PascalParser.GlobalRoutineCallingConventionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_globalRoutineImplementation

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterGlobalRoutineImplementation" ):
                listener.enterGlobalRoutineImplementation(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitGlobalRoutineImplementation" ):
                listener.exitGlobalRoutineImplementation(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitGlobalRoutineImplementation" ):
                return visitor.visitGlobalRoutineImplementation(self)
            else:
                return visitor.visitChildren(self)




    def globalRoutineImplementation(self):

        localctx = C64PascalParser.GlobalRoutineImplementationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 64, self.RULE_globalRoutineImplementation)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 441
            _la = self._input.LA(1)
            if not(_la==43 or _la==44):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 442
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 444
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==90:
                self.state = 443
                self.formalParameters()


            self.state = 448
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==95:
                self.state = 446
                self.match(C64PascalParser.COLON)
                self.state = 447
                self.typeIdentifier()


            self.state = 450
            self.match(C64PascalParser.SEMI)
            self.state = 452
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==49 or _la==50:
                self.state = 451
                self.globalRoutineCallingConvention()


            self.state = 454
            self.routineBlock()
            self.state = 455
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class GlobalRoutineCallingConventionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def CDECL(self):
            return self.getToken(C64PascalParser.CDECL, 0)

        def STDCALL(self):
            return self.getToken(C64PascalParser.STDCALL, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_globalRoutineCallingConvention

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterGlobalRoutineCallingConvention" ):
                listener.enterGlobalRoutineCallingConvention(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitGlobalRoutineCallingConvention" ):
                listener.exitGlobalRoutineCallingConvention(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitGlobalRoutineCallingConvention" ):
                return visitor.visitGlobalRoutineCallingConvention(self)
            else:
                return visitor.visitChildren(self)




    def globalRoutineCallingConvention(self):

        localctx = C64PascalParser.GlobalRoutineCallingConventionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 66, self.RULE_globalRoutineCallingConvention)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 457
            _la = self._input.LA(1)
            if not(_la==49 or _la==50):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 458
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


        def CLASS(self):
            return self.getToken(C64PascalParser.CLASS, 0)

        def formalParameters(self):
            return self.getTypedRuleContext(C64PascalParser.FormalParametersContext,0)


        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_methodImplementation

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMethodImplementation" ):
                listener.enterMethodImplementation(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMethodImplementation" ):
                listener.exitMethodImplementation(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMethodImplementation" ):
                return visitor.visitMethodImplementation(self)
            else:
                return visitor.visitChildren(self)




    def methodImplementation(self):

        localctx = C64PascalParser.MethodImplementationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 68, self.RULE_methodImplementation)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 461
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==32:
                self.state = 460
                self.match(C64PascalParser.CLASS)


            self.state = 463
            self.routineKind()
            self.state = 464
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 465
            self.match(C64PascalParser.DOT)
            self.state = 466
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 468
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==90:
                self.state = 467
                self.formalParameters()


            self.state = 472
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==95:
                self.state = 470
                self.match(C64PascalParser.COLON)
                self.state = 471
                self.typeIdentifier()


            self.state = 474
            self.match(C64PascalParser.SEMI)
            self.state = 475
            self.routineBlock()
            self.state = 476
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRoutineKind" ):
                listener.enterRoutineKind(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRoutineKind" ):
                listener.exitRoutineKind(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRoutineKind" ):
                return visitor.visitRoutineKind(self)
            else:
                return visitor.visitChildren(self)




    def routineKind(self):

        localctx = C64PascalParser.RoutineKindContext(self, self._ctx, self.state)
        self.enterRule(localctx, 70, self.RULE_routineKind)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 478
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 131941395333120) != 0)):
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFormalParameters" ):
                listener.enterFormalParameters(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFormalParameters" ):
                listener.exitFormalParameters(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFormalParameters" ):
                return visitor.visitFormalParameters(self)
            else:
                return visitor.visitChildren(self)




    def formalParameters(self):

        localctx = C64PascalParser.FormalParametersContext(self, self._ctx, self.state)
        self.enterRule(localctx, 72, self.RULE_formalParameters)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 480
            self.match(C64PascalParser.LPAREN)
            self.state = 482
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==7 or _la==9 or _la==104:
                self.state = 481
                self.formalParameterList()


            self.state = 484
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFormalParameterList" ):
                listener.enterFormalParameterList(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFormalParameterList" ):
                listener.exitFormalParameterList(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFormalParameterList" ):
                return visitor.visitFormalParameterList(self)
            else:
                return visitor.visitChildren(self)




    def formalParameterList(self):

        localctx = C64PascalParser.FormalParameterListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 74, self.RULE_formalParameterList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 486
            self.formalParameterGroup()
            self.state = 491
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==96:
                self.state = 487
                self.match(C64PascalParser.SEMI)
                self.state = 488
                self.formalParameterGroup()
                self.state = 493
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFormalParameterGroup" ):
                listener.enterFormalParameterGroup(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFormalParameterGroup" ):
                listener.exitFormalParameterGroup(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFormalParameterGroup" ):
                return visitor.visitFormalParameterGroup(self)
            else:
                return visitor.visitChildren(self)




    def formalParameterGroup(self):

        localctx = C64PascalParser.FormalParameterGroupContext(self, self._ctx, self.state)
        self.enterRule(localctx, 76, self.RULE_formalParameterGroup)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 495
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==7 or _la==9:
                self.state = 494
                _la = self._input.LA(1)
                if not(_la==7 or _la==9):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()


            self.state = 497
            self.identifierList()
            self.state = 498
            self.match(C64PascalParser.COLON)
            self.state = 499
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRoutineBlock" ):
                listener.enterRoutineBlock(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRoutineBlock" ):
                listener.exitRoutineBlock(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRoutineBlock" ):
                return visitor.visitRoutineBlock(self)
            else:
                return visitor.visitChildren(self)




    def routineBlock(self):

        localctx = C64PascalParser.RoutineBlockContext(self, self._ctx, self.state)
        self.enterRule(localctx, 78, self.RULE_routineBlock)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 502
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==9:
                self.state = 501
                self.varSection()


            self.state = 504
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVarSection" ):
                listener.enterVarSection(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVarSection" ):
                listener.exitVarSection(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVarSection" ):
                return visitor.visitVarSection(self)
            else:
                return visitor.visitChildren(self)




    def varSection(self):

        localctx = C64PascalParser.VarSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 80, self.RULE_varSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 506
            self.match(C64PascalParser.VAR)
            self.state = 508 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 507
                self.varDeclaration()
                self.state = 510 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==104):
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVarDeclaration" ):
                listener.enterVarDeclaration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVarDeclaration" ):
                listener.exitVarDeclaration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVarDeclaration" ):
                return visitor.visitVarDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def varDeclaration(self):

        localctx = C64PascalParser.VarDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 82, self.RULE_varDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 512
            self.identifierList()
            self.state = 513
            self.match(C64PascalParser.COLON)
            self.state = 514
            self.typeIdentifier()
            self.state = 517
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==77:
                self.state = 515
                self.match(C64PascalParser.ASSIGN)
                self.state = 516
                self.expression()


            self.state = 519
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIdentifierList" ):
                listener.enterIdentifierList(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIdentifierList" ):
                listener.exitIdentifierList(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIdentifierList" ):
                return visitor.visitIdentifierList(self)
            else:
                return visitor.visitChildren(self)




    def identifierList(self):

        localctx = C64PascalParser.IdentifierListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 84, self.RULE_identifierList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 521
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 526
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==94:
                self.state = 522
                self.match(C64PascalParser.COMMA)
                self.state = 523
                self.match(C64PascalParser.IDENTIFIER)
                self.state = 528
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

        def POINTER_TYPE(self):
            return self.getToken(C64PascalParser.POINTER_TYPE, 0)

        def STRING_TYPE(self):
            return self.getToken(C64PascalParser.STRING_TYPE, 0)

        def DOUBLE_TYPE(self):
            return self.getToken(C64PascalParser.DOUBLE_TYPE, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_typeIdentifier

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTypeIdentifier" ):
                listener.enterTypeIdentifier(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTypeIdentifier" ):
                listener.exitTypeIdentifier(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeIdentifier" ):
                return visitor.visitTypeIdentifier(self)
            else:
                return visitor.visitChildren(self)




    def typeIdentifier(self):

        localctx = C64PascalParser.TypeIdentifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 86, self.RULE_typeIdentifier)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 529
            _la = self._input.LA(1)
            if not(((((_la - 61)) & ~0x3f) == 0 and ((1 << (_la - 61)) & 8796093022335) != 0)):
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCompoundStatement" ):
                listener.enterCompoundStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCompoundStatement" ):
                listener.exitCompoundStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompoundStatement" ):
                return visitor.visitCompoundStatement(self)
            else:
                return visitor.visitChildren(self)




    def compoundStatement(self):

        localctx = C64PascalParser.CompoundStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 88, self.RULE_compoundStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 531
            self.match(C64PascalParser.BEGIN)
            self.state = 533
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 1152921504737563648) != 0) or _la==70 or _la==104:
                self.state = 532
                self.statementSequence()


            self.state = 535
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStatementSequence" ):
                listener.enterStatementSequence(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStatementSequence" ):
                listener.exitStatementSequence(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStatementSequence" ):
                return visitor.visitStatementSequence(self)
            else:
                return visitor.visitChildren(self)




    def statementSequence(self):

        localctx = C64PascalParser.StatementSequenceContext(self, self._ctx, self.state)
        self.enterRule(localctx, 90, self.RULE_statementSequence)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 537
            self.statement()
            self.state = 542
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,56,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 538
                    self.match(C64PascalParser.SEMI)
                    self.state = 539
                    self.statement() 
                self.state = 544
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,56,self._ctx)

            self.state = 546
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==96:
                self.state = 545
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



    class CallStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def callStatement(self):
            return self.getTypedRuleContext(C64PascalParser.CallStatementContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCallStatementNode" ):
                listener.enterCallStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCallStatementNode" ):
                listener.exitCallStatementNode(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCallStatementNode" ):
                return visitor.visitCallStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class InheritedStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def inheritedStatement(self):
            return self.getTypedRuleContext(C64PascalParser.InheritedStatementContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterInheritedStatementNode" ):
                listener.enterInheritedStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitInheritedStatementNode" ):
                listener.exitInheritedStatementNode(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInheritedStatementNode" ):
                return visitor.visitInheritedStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class ForStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def forStatement(self):
            return self.getTypedRuleContext(C64PascalParser.ForStatementContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterForStatementNode" ):
                listener.enterForStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitForStatementNode" ):
                listener.exitForStatementNode(self)

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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterBreakStatementNode" ):
                listener.enterBreakStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitBreakStatementNode" ):
                listener.exitBreakStatementNode(self)

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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterContinueStatementNode" ):
                listener.enterContinueStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitContinueStatementNode" ):
                listener.exitContinueStatementNode(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitContinueStatementNode" ):
                return visitor.visitContinueStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class TryStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def tryStatement(self):
            return self.getTypedRuleContext(C64PascalParser.TryStatementContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTryStatementNode" ):
                listener.enterTryStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTryStatementNode" ):
                listener.exitTryStatementNode(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTryStatementNode" ):
                return visitor.visitTryStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class IfStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ifStatement(self):
            return self.getTypedRuleContext(C64PascalParser.IfStatementContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIfStatementNode" ):
                listener.enterIfStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIfStatementNode" ):
                listener.exitIfStatementNode(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIfStatementNode" ):
                return visitor.visitIfStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class CompoundStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def compoundStatement(self):
            return self.getTypedRuleContext(C64PascalParser.CompoundStatementContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCompoundStatementNode" ):
                listener.enterCompoundStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCompoundStatementNode" ):
                listener.exitCompoundStatementNode(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompoundStatementNode" ):
                return visitor.visitCompoundStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class ExitStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def EXIT(self):
            return self.getToken(C64PascalParser.EXIT, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterExitStatementNode" ):
                listener.enterExitStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitExitStatementNode" ):
                listener.exitExitStatementNode(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExitStatementNode" ):
                return visitor.visitExitStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class RaiseStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def raiseStatement(self):
            return self.getTypedRuleContext(C64PascalParser.RaiseStatementContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRaiseStatementNode" ):
                listener.enterRaiseStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRaiseStatementNode" ):
                listener.exitRaiseStatementNode(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRaiseStatementNode" ):
                return visitor.visitRaiseStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class WhileStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def whileStatement(self):
            return self.getTypedRuleContext(C64PascalParser.WhileStatementContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterWhileStatementNode" ):
                listener.enterWhileStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitWhileStatementNode" ):
                listener.exitWhileStatementNode(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWhileStatementNode" ):
                return visitor.visitWhileStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class AssignmentStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def assignmentStatement(self):
            return self.getTypedRuleContext(C64PascalParser.AssignmentStatementContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAssignmentStatementNode" ):
                listener.enterAssignmentStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAssignmentStatementNode" ):
                listener.exitAssignmentStatementNode(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAssignmentStatementNode" ):
                return visitor.visitAssignmentStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class RepeatStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def repeatStatement(self):
            return self.getTypedRuleContext(C64PascalParser.RepeatStatementContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRepeatStatementNode" ):
                listener.enterRepeatStatementNode(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRepeatStatementNode" ):
                listener.exitRepeatStatementNode(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRepeatStatementNode" ):
                return visitor.visitRepeatStatementNode(self)
            else:
                return visitor.visitChildren(self)



    def statement(self):

        localctx = C64PascalParser.StatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 92, self.RULE_statement)
        try:
            self.state = 561
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,58,self._ctx)
            if la_ == 1:
                localctx = C64PascalParser.CompoundStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 548
                self.compoundStatement()
                pass

            elif la_ == 2:
                localctx = C64PascalParser.AssignmentStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 549
                self.assignmentStatement()
                pass

            elif la_ == 3:
                localctx = C64PascalParser.InheritedStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 550
                self.inheritedStatement()
                pass

            elif la_ == 4:
                localctx = C64PascalParser.CallStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 551
                self.callStatement()
                pass

            elif la_ == 5:
                localctx = C64PascalParser.RaiseStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 552
                self.raiseStatement()
                pass

            elif la_ == 6:
                localctx = C64PascalParser.TryStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 553
                self.tryStatement()
                pass

            elif la_ == 7:
                localctx = C64PascalParser.IfStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 554
                self.ifStatement()
                pass

            elif la_ == 8:
                localctx = C64PascalParser.WhileStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 8)
                self.state = 555
                self.whileStatement()
                pass

            elif la_ == 9:
                localctx = C64PascalParser.RepeatStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 9)
                self.state = 556
                self.repeatStatement()
                pass

            elif la_ == 10:
                localctx = C64PascalParser.ForStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 10)
                self.state = 557
                self.forStatement()
                pass

            elif la_ == 11:
                localctx = C64PascalParser.BreakStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 11)
                self.state = 558
                self.match(C64PascalParser.BREAK)
                pass

            elif la_ == 12:
                localctx = C64PascalParser.ContinueStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 12)
                self.state = 559
                self.match(C64PascalParser.CONTINUE)
                pass

            elif la_ == 13:
                localctx = C64PascalParser.ExitStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 13)
                self.state = 560
                self.match(C64PascalParser.EXIT)
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAssignmentStatement" ):
                listener.enterAssignmentStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAssignmentStatement" ):
                listener.exitAssignmentStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAssignmentStatement" ):
                return visitor.visitAssignmentStatement(self)
            else:
                return visitor.visitChildren(self)




    def assignmentStatement(self):

        localctx = C64PascalParser.AssignmentStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 94, self.RULE_assignmentStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 563
            self.designator()
            self.state = 564
            self.match(C64PascalParser.ASSIGN)
            self.state = 565
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCallStatement" ):
                listener.enterCallStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCallStatement" ):
                listener.exitCallStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCallStatement" ):
                return visitor.visitCallStatement(self)
            else:
                return visitor.visitChildren(self)




    def callStatement(self):

        localctx = C64PascalParser.CallStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 96, self.RULE_callStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 567
            self.designator()
            self.state = 573
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==90:
                self.state = 568
                self.match(C64PascalParser.LPAREN)
                self.state = 570
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if ((((_la - 60)) & ~0x3f) == 0 and ((1 << (_la - 60)) & 32437254031359) != 0):
                    self.state = 569
                    self.argumentList()


                self.state = 572
                self.match(C64PascalParser.RPAREN)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RaiseStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def RAISE(self):
            return self.getToken(C64PascalParser.RAISE, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_raiseStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRaiseStatement" ):
                listener.enterRaiseStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRaiseStatement" ):
                listener.exitRaiseStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRaiseStatement" ):
                return visitor.visitRaiseStatement(self)
            else:
                return visitor.visitChildren(self)




    def raiseStatement(self):

        localctx = C64PascalParser.RaiseStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 98, self.RULE_raiseStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 575
            self.match(C64PascalParser.RAISE)
            self.state = 577
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if ((((_la - 60)) & ~0x3f) == 0 and ((1 << (_la - 60)) & 32437254031359) != 0):
                self.state = 576
                self.expression()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TryStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def TRY(self):
            return self.getToken(C64PascalParser.TRY, 0)

        def EXCEPT(self):
            return self.getToken(C64PascalParser.EXCEPT, 0)

        def END(self):
            return self.getToken(C64PascalParser.END, 0)

        def statementSequence(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.StatementSequenceContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.StatementSequenceContext,i)


        def FINALLY(self):
            return self.getToken(C64PascalParser.FINALLY, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_tryStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTryStatement" ):
                listener.enterTryStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTryStatement" ):
                listener.exitTryStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTryStatement" ):
                return visitor.visitTryStatement(self)
            else:
                return visitor.visitChildren(self)




    def tryStatement(self):

        localctx = C64PascalParser.TryStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 100, self.RULE_tryStatement)
        self._la = 0 # Token type
        try:
            self.state = 597
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,66,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 579
                self.match(C64PascalParser.TRY)
                self.state = 581
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if (((_la) & ~0x3f) == 0 and ((1 << _la) & 1152921504737563648) != 0) or _la==70 or _la==104:
                    self.state = 580
                    self.statementSequence()


                self.state = 583
                self.match(C64PascalParser.EXCEPT)
                self.state = 585
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if (((_la) & ~0x3f) == 0 and ((1 << _la) & 1152921504737563648) != 0) or _la==70 or _la==104:
                    self.state = 584
                    self.statementSequence()


                self.state = 587
                self.match(C64PascalParser.END)
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 588
                self.match(C64PascalParser.TRY)
                self.state = 590
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if (((_la) & ~0x3f) == 0 and ((1 << _la) & 1152921504737563648) != 0) or _la==70 or _la==104:
                    self.state = 589
                    self.statementSequence()


                self.state = 592
                self.match(C64PascalParser.FINALLY)
                self.state = 594
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if (((_la) & ~0x3f) == 0 and ((1 << _la) & 1152921504737563648) != 0) or _la==70 or _la==104:
                    self.state = 593
                    self.statementSequence()


                self.state = 596
                self.match(C64PascalParser.END)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class InheritedStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INHERITED(self):
            return self.getToken(C64PascalParser.INHERITED, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def argumentList(self):
            return self.getTypedRuleContext(C64PascalParser.ArgumentListContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_inheritedStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterInheritedStatement" ):
                listener.enterInheritedStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitInheritedStatement" ):
                listener.exitInheritedStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInheritedStatement" ):
                return visitor.visitInheritedStatement(self)
            else:
                return visitor.visitChildren(self)




    def inheritedStatement(self):

        localctx = C64PascalParser.InheritedStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 102, self.RULE_inheritedStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 599
            self.match(C64PascalParser.INHERITED)
            self.state = 608
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==104:
                self.state = 600
                self.match(C64PascalParser.IDENTIFIER)
                self.state = 606
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==90:
                    self.state = 601
                    self.match(C64PascalParser.LPAREN)
                    self.state = 603
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if ((((_la - 60)) & ~0x3f) == 0 and ((1 << (_la - 60)) & 32437254031359) != 0):
                        self.state = 602
                        self.argumentList()


                    self.state = 605
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIfStatement" ):
                listener.enterIfStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIfStatement" ):
                listener.exitIfStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIfStatement" ):
                return visitor.visitIfStatement(self)
            else:
                return visitor.visitChildren(self)




    def ifStatement(self):

        localctx = C64PascalParser.IfStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 104, self.RULE_ifStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 610
            self.match(C64PascalParser.IF)
            self.state = 611
            self.expression()
            self.state = 612
            self.match(C64PascalParser.THEN)
            self.state = 613
            self.statement()
            self.state = 616
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,70,self._ctx)
            if la_ == 1:
                self.state = 614
                self.match(C64PascalParser.ELSE)
                self.state = 615
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterWhileStatement" ):
                listener.enterWhileStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitWhileStatement" ):
                listener.exitWhileStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWhileStatement" ):
                return visitor.visitWhileStatement(self)
            else:
                return visitor.visitChildren(self)




    def whileStatement(self):

        localctx = C64PascalParser.WhileStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 106, self.RULE_whileStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 618
            self.match(C64PascalParser.WHILE)
            self.state = 619
            self.expression()
            self.state = 620
            self.match(C64PascalParser.DO)
            self.state = 621
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRepeatStatement" ):
                listener.enterRepeatStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRepeatStatement" ):
                listener.exitRepeatStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRepeatStatement" ):
                return visitor.visitRepeatStatement(self)
            else:
                return visitor.visitChildren(self)




    def repeatStatement(self):

        localctx = C64PascalParser.RepeatStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 108, self.RULE_repeatStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 623
            self.match(C64PascalParser.REPEAT)
            self.state = 625
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 1152921504737563648) != 0) or _la==70 or _la==104:
                self.state = 624
                self.statementSequence()


            self.state = 627
            self.match(C64PascalParser.UNTIL)
            self.state = 628
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterForStatement" ):
                listener.enterForStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitForStatement" ):
                listener.exitForStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitForStatement" ):
                return visitor.visitForStatement(self)
            else:
                return visitor.visitChildren(self)




    def forStatement(self):

        localctx = C64PascalParser.ForStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 110, self.RULE_forStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 630
            self.match(C64PascalParser.FOR)
            self.state = 631
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 632
            self.match(C64PascalParser.ASSIGN)
            self.state = 633
            self.expression()
            self.state = 634
            _la = self._input.LA(1)
            if not(_la==20 or _la==21):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 635
            self.expression()
            self.state = 636
            self.match(C64PascalParser.DO)
            self.state = 637
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

        def NIL(self):
            return self.getToken(C64PascalParser.NIL, 0)

        def designatorSuffix(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.DesignatorSuffixContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.DesignatorSuffixContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_designator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDesignator" ):
                listener.enterDesignator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDesignator" ):
                listener.exitDesignator(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDesignator" ):
                return visitor.visitDesignator(self)
            else:
                return visitor.visitChildren(self)




    def designator(self):

        localctx = C64PascalParser.DesignatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 112, self.RULE_designator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 639
            _la = self._input.LA(1)
            if not(_la==70 or _la==104):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 643
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while ((((_la - 88)) & ~0x3f) == 0 and ((1 << (_la - 88)) & 1041) != 0):
                self.state = 640
                self.designatorSuffix()
                self.state = 645
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

        def CARET(self):
            return self.getToken(C64PascalParser.CARET, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_designatorSuffix

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDesignatorSuffix" ):
                listener.enterDesignatorSuffix(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDesignatorSuffix" ):
                listener.exitDesignatorSuffix(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDesignatorSuffix" ):
                return visitor.visitDesignatorSuffix(self)
            else:
                return visitor.visitChildren(self)




    def designatorSuffix(self):

        localctx = C64PascalParser.DesignatorSuffixContext(self, self._ctx, self.state)
        self.enterRule(localctx, 114, self.RULE_designatorSuffix)
        try:
            self.state = 653
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [98]:
                self.enterOuterAlt(localctx, 1)
                self.state = 646
                self.match(C64PascalParser.DOT)
                self.state = 647
                self.match(C64PascalParser.IDENTIFIER)
                pass
            elif token in [92]:
                self.enterOuterAlt(localctx, 2)
                self.state = 648
                self.match(C64PascalParser.LBRACK)
                self.state = 649
                self.expression()
                self.state = 650
                self.match(C64PascalParser.RBRACK)
                pass
            elif token in [88]:
                self.enterOuterAlt(localctx, 3)
                self.state = 652
                self.match(C64PascalParser.CARET)
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterArgumentList" ):
                listener.enterArgumentList(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitArgumentList" ):
                listener.exitArgumentList(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArgumentList" ):
                return visitor.visitArgumentList(self)
            else:
                return visitor.visitChildren(self)




    def argumentList(self):

        localctx = C64PascalParser.ArgumentListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 116, self.RULE_argumentList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 655
            self.expression()
            self.state = 660
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==94:
                self.state = 656
                self.match(C64PascalParser.COMMA)
                self.state = 657
                self.expression()
                self.state = 662
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterExpression" ):
                listener.enterExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitExpression" ):
                listener.exitExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExpression" ):
                return visitor.visitExpression(self)
            else:
                return visitor.visitChildren(self)




    def expression(self):

        localctx = C64PascalParser.ExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 118, self.RULE_expression)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 663
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOrExpression" ):
                listener.enterOrExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOrExpression" ):
                listener.exitOrExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOrExpression" ):
                return visitor.visitOrExpression(self)
            else:
                return visitor.visitChildren(self)




    def orExpression(self):

        localctx = C64PascalParser.OrExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 120, self.RULE_orExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 665
            self.andExpression()
            self.state = 670
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==74 or _la==75:
                self.state = 666
                _la = self._input.LA(1)
                if not(_la==74 or _la==75):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 667
                self.andExpression()
                self.state = 672
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAndExpression" ):
                listener.enterAndExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAndExpression" ):
                listener.exitAndExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAndExpression" ):
                return visitor.visitAndExpression(self)
            else:
                return visitor.visitChildren(self)




    def andExpression(self):

        localctx = C64PascalParser.AndExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 122, self.RULE_andExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 673
            self.comparisonExpression()
            self.state = 678
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==73:
                self.state = 674
                self.match(C64PascalParser.AND)
                self.state = 675
                self.comparisonExpression()
                self.state = 680
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterComparisonExpression" ):
                listener.enterComparisonExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitComparisonExpression" ):
                listener.exitComparisonExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitComparisonExpression" ):
                return visitor.visitComparisonExpression(self)
            else:
                return visitor.visitChildren(self)




    def comparisonExpression(self):

        localctx = C64PascalParser.ComparisonExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 124, self.RULE_comparisonExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 681
            self.additiveExpression()
            self.state = 684
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if ((((_la - 78)) & ~0x3f) == 0 and ((1 << (_la - 78)) & 63) != 0):
                self.state = 682
                _la = self._input.LA(1)
                if not(((((_la - 78)) & ~0x3f) == 0 and ((1 << (_la - 78)) & 63) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 683
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAdditiveExpression" ):
                listener.enterAdditiveExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAdditiveExpression" ):
                listener.exitAdditiveExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAdditiveExpression" ):
                return visitor.visitAdditiveExpression(self)
            else:
                return visitor.visitChildren(self)




    def additiveExpression(self):

        localctx = C64PascalParser.AdditiveExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 126, self.RULE_additiveExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 686
            self.multiplicativeExpression()
            self.state = 691
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==84 or _la==85:
                self.state = 687
                _la = self._input.LA(1)
                if not(_la==84 or _la==85):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 688
                self.multiplicativeExpression()
                self.state = 693
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMultiplicativeExpression" ):
                listener.enterMultiplicativeExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMultiplicativeExpression" ):
                listener.exitMultiplicativeExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMultiplicativeExpression" ):
                return visitor.visitMultiplicativeExpression(self)
            else:
                return visitor.visitChildren(self)




    def multiplicativeExpression(self):

        localctx = C64PascalParser.MultiplicativeExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 128, self.RULE_multiplicativeExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 694
            self.unaryExpression()
            self.state = 699
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while ((((_la - 71)) & ~0x3f) == 0 and ((1 << (_la - 71)) & 98307) != 0):
                self.state = 695
                _la = self._input.LA(1)
                if not(((((_la - 71)) & ~0x3f) == 0 and ((1 << (_la - 71)) & 98307) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 696
                self.unaryExpression()
                self.state = 701
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

        def AT(self):
            return self.getToken(C64PascalParser.AT, 0)

        def designator(self):
            return self.getTypedRuleContext(C64PascalParser.DesignatorContext,0)


        def primaryExpression(self):
            return self.getTypedRuleContext(C64PascalParser.PrimaryExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_unaryExpression

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterUnaryExpression" ):
                listener.enterUnaryExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitUnaryExpression" ):
                listener.exitUnaryExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUnaryExpression" ):
                return visitor.visitUnaryExpression(self)
            else:
                return visitor.visitChildren(self)




    def unaryExpression(self):

        localctx = C64PascalParser.UnaryExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 130, self.RULE_unaryExpression)
        self._la = 0 # Token type
        try:
            self.state = 707
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [76, 84, 85]:
                self.enterOuterAlt(localctx, 1)
                self.state = 702
                _la = self._input.LA(1)
                if not(((((_la - 76)) & ~0x3f) == 0 and ((1 << (_la - 76)) & 769) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 703
                self.unaryExpression()
                pass
            elif token in [89]:
                self.enterOuterAlt(localctx, 2)
                self.state = 704
                self.match(C64PascalParser.AT)
                self.state = 705
                self.designator()
                pass
            elif token in [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 90, 99, 100, 102, 103, 104]:
                self.enterOuterAlt(localctx, 3)
                self.state = 706
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

        def NIL(self):
            return self.getToken(C64PascalParser.NIL, 0)

        def typeCastExpression(self):
            return self.getTypedRuleContext(C64PascalParser.TypeCastExpressionContext,0)


        def inheritedExpression(self):
            return self.getTypedRuleContext(C64PascalParser.InheritedExpressionContext,0)


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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPrimaryExpression" ):
                listener.enterPrimaryExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPrimaryExpression" ):
                listener.exitPrimaryExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPrimaryExpression" ):
                return visitor.visitPrimaryExpression(self)
            else:
                return visitor.visitChildren(self)




    def primaryExpression(self):

        localctx = C64PascalParser.PrimaryExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 132, self.RULE_primaryExpression)
        self._la = 0 # Token type
        try:
            self.state = 728
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,82,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 709
                self.integerLiteral()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 710
                self.match(C64PascalParser.STRING_LITERAL)
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 711
                self.match(C64PascalParser.TRUE)
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 712
                self.match(C64PascalParser.FALSE)
                pass

            elif la_ == 5:
                self.enterOuterAlt(localctx, 5)
                self.state = 713
                self.match(C64PascalParser.NIL)
                pass

            elif la_ == 6:
                self.enterOuterAlt(localctx, 6)
                self.state = 714
                self.typeCastExpression()
                pass

            elif la_ == 7:
                self.enterOuterAlt(localctx, 7)
                self.state = 715
                self.inheritedExpression()
                pass

            elif la_ == 8:
                self.enterOuterAlt(localctx, 8)
                self.state = 716
                self.designator()
                self.state = 717
                self.match(C64PascalParser.LPAREN)
                self.state = 719
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if ((((_la - 60)) & ~0x3f) == 0 and ((1 << (_la - 60)) & 32437254031359) != 0):
                    self.state = 718
                    self.argumentList()


                self.state = 721
                self.match(C64PascalParser.RPAREN)
                pass

            elif la_ == 9:
                self.enterOuterAlt(localctx, 9)
                self.state = 723
                self.designator()
                pass

            elif la_ == 10:
                self.enterOuterAlt(localctx, 10)
                self.state = 724
                self.match(C64PascalParser.LPAREN)
                self.state = 725
                self.expression()
                self.state = 726
                self.match(C64PascalParser.RPAREN)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class InheritedExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INHERITED(self):
            return self.getToken(C64PascalParser.INHERITED, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def argumentList(self):
            return self.getTypedRuleContext(C64PascalParser.ArgumentListContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_inheritedExpression

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterInheritedExpression" ):
                listener.enterInheritedExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitInheritedExpression" ):
                listener.exitInheritedExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInheritedExpression" ):
                return visitor.visitInheritedExpression(self)
            else:
                return visitor.visitChildren(self)




    def inheritedExpression(self):

        localctx = C64PascalParser.InheritedExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 134, self.RULE_inheritedExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 730
            self.match(C64PascalParser.INHERITED)
            self.state = 731
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 737
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==90:
                self.state = 732
                self.match(C64PascalParser.LPAREN)
                self.state = 734
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if ((((_la - 60)) & ~0x3f) == 0 and ((1 << (_la - 60)) & 32437254031359) != 0):
                    self.state = 733
                    self.argumentList()


                self.state = 736
                self.match(C64PascalParser.RPAREN)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TypeCastExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def builtinCastType(self):
            return self.getTypedRuleContext(C64PascalParser.BuiltinCastTypeContext,0)


        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_typeCastExpression

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTypeCastExpression" ):
                listener.enterTypeCastExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTypeCastExpression" ):
                listener.exitTypeCastExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeCastExpression" ):
                return visitor.visitTypeCastExpression(self)
            else:
                return visitor.visitChildren(self)




    def typeCastExpression(self):

        localctx = C64PascalParser.TypeCastExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 136, self.RULE_typeCastExpression)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 739
            self.builtinCastType()
            self.state = 740
            self.match(C64PascalParser.LPAREN)
            self.state = 741
            self.expression()
            self.state = 742
            self.match(C64PascalParser.RPAREN)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BuiltinCastTypeContext(ParserRuleContext):
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

        def POINTER_TYPE(self):
            return self.getToken(C64PascalParser.POINTER_TYPE, 0)

        def STRING_TYPE(self):
            return self.getToken(C64PascalParser.STRING_TYPE, 0)

        def DOUBLE_TYPE(self):
            return self.getToken(C64PascalParser.DOUBLE_TYPE, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_builtinCastType

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterBuiltinCastType" ):
                listener.enterBuiltinCastType(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitBuiltinCastType" ):
                listener.exitBuiltinCastType(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBuiltinCastType" ):
                return visitor.visitBuiltinCastType(self)
            else:
                return visitor.visitChildren(self)




    def builtinCastType(self):

        localctx = C64PascalParser.BuiltinCastTypeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 138, self.RULE_builtinCastType)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 744
            _la = self._input.LA(1)
            if not(((((_la - 61)) & ~0x3f) == 0 and ((1 << (_la - 61)) & 127) != 0)):
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

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIntegerLiteral" ):
                listener.enterIntegerLiteral(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIntegerLiteral" ):
                listener.exitIntegerLiteral(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIntegerLiteral" ):
                return visitor.visitIntegerLiteral(self)
            else:
                return visitor.visitChildren(self)




    def integerLiteral(self):

        localctx = C64PascalParser.IntegerLiteralContext(self, self._ctx, self.state)
        self.enterRule(localctx, 140, self.RULE_integerLiteral)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 746
            _la = self._input.LA(1)
            if not(((((_la - 99)) & ~0x3f) == 0 and ((1 << (_la - 99)) & 11) != 0)):
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





