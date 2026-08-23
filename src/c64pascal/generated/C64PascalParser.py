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
        4,1,99,694,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,26,
        2,27,7,27,2,28,7,28,2,29,7,29,2,30,7,30,2,31,7,31,2,32,7,32,2,33,
        7,33,2,34,7,34,2,35,7,35,2,36,7,36,2,37,7,37,2,38,7,38,2,39,7,39,
        2,40,7,40,2,41,7,41,2,42,7,42,2,43,7,43,2,44,7,44,2,45,7,45,2,46,
        7,46,2,47,7,47,2,48,7,48,2,49,7,49,2,50,7,50,2,51,7,51,2,52,7,52,
        2,53,7,53,2,54,7,54,2,55,7,55,2,56,7,56,2,57,7,57,2,58,7,58,2,59,
        7,59,2,60,7,60,2,61,7,61,2,62,7,62,2,63,7,63,2,64,7,64,2,65,7,65,
        2,66,7,66,1,0,1,0,3,0,137,8,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,3,
        1,147,8,1,1,1,1,1,1,1,1,1,1,2,1,2,1,2,1,2,1,2,3,2,158,8,2,1,2,5,
        2,161,8,2,10,2,12,2,164,9,2,1,2,5,2,167,8,2,10,2,12,2,170,9,2,1,
        2,1,2,3,2,174,8,2,1,2,5,2,177,8,2,10,2,12,2,180,9,2,1,2,5,2,183,
        8,2,10,2,12,2,186,9,2,1,2,1,2,5,2,190,8,2,10,2,12,2,193,9,2,1,2,
        1,2,1,2,1,2,1,2,3,2,200,8,2,1,3,1,3,1,3,1,3,5,3,206,8,3,10,3,12,
        3,209,9,3,1,3,1,3,1,4,1,4,1,4,5,4,216,8,4,10,4,12,4,219,9,4,1,5,
        5,5,222,8,5,10,5,12,5,225,9,5,1,5,5,5,228,8,5,10,5,12,5,231,9,5,
        1,5,1,5,5,5,235,8,5,10,5,12,5,238,9,5,1,5,1,5,1,6,1,6,1,6,3,6,245,
        8,6,1,7,1,7,4,7,249,8,7,11,7,12,7,250,1,8,1,8,1,8,1,8,1,8,1,9,1,
        9,4,9,260,8,9,11,9,12,9,261,1,10,1,10,1,10,1,10,1,10,1,11,1,11,1,
        12,1,12,1,12,1,12,1,12,1,12,1,12,3,12,278,8,12,1,13,1,13,1,13,1,
        13,1,14,1,14,1,14,1,15,3,15,288,8,15,1,15,1,15,1,16,1,16,1,16,1,
        16,1,17,1,17,5,17,298,8,17,10,17,12,17,301,9,17,1,17,1,17,1,18,1,
        18,1,18,1,18,1,18,1,18,1,18,1,18,1,18,1,19,1,19,1,19,1,19,1,19,3,
        19,319,8,19,1,19,5,19,322,8,19,10,19,12,19,325,9,19,1,19,1,19,1,
        20,1,20,1,20,1,20,3,20,333,8,20,1,21,1,21,1,22,1,22,1,22,1,22,1,
        22,1,23,1,23,1,23,3,23,345,8,23,1,23,1,23,1,23,5,23,350,8,23,10,
        23,12,23,353,9,23,1,23,1,23,1,24,1,24,3,24,359,8,24,1,24,1,24,1,
        25,1,25,1,25,1,25,1,25,1,25,1,25,1,25,1,25,3,25,372,8,25,1,26,1,
        26,1,26,5,26,377,8,26,10,26,12,26,380,9,26,1,27,3,27,383,8,27,1,
        27,1,27,1,27,3,27,388,8,27,1,27,1,27,3,27,392,8,27,1,27,1,27,5,27,
        396,8,27,10,27,12,27,399,9,27,1,28,1,28,1,28,1,29,1,29,1,29,3,29,
        407,8,29,1,29,1,29,3,29,411,8,29,1,29,1,29,1,30,1,30,1,30,3,30,418,
        8,30,1,30,1,30,3,30,422,8,30,1,30,1,30,4,30,426,8,30,11,30,12,30,
        427,1,31,1,31,1,31,3,31,433,8,31,1,31,1,31,3,31,437,8,31,1,31,1,
        31,1,31,1,31,1,32,1,32,1,32,1,33,3,33,447,8,33,1,33,1,33,1,33,1,
        33,1,33,3,33,454,8,33,1,33,1,33,3,33,458,8,33,1,33,1,33,1,33,1,33,
        1,34,1,34,1,35,1,35,3,35,468,8,35,1,35,1,35,1,36,1,36,1,36,5,36,
        475,8,36,10,36,12,36,478,9,36,1,37,3,37,481,8,37,1,37,1,37,1,37,
        1,37,1,38,3,38,488,8,38,1,38,1,38,1,39,1,39,4,39,494,8,39,11,39,
        12,39,495,1,40,1,40,1,40,1,40,1,40,3,40,503,8,40,1,40,1,40,1,41,
        1,41,1,41,5,41,510,8,41,10,41,12,41,513,9,41,1,42,1,42,1,43,1,43,
        3,43,519,8,43,1,43,1,43,1,44,1,44,1,44,5,44,526,8,44,10,44,12,44,
        529,9,44,1,44,3,44,532,8,44,1,45,1,45,1,45,1,45,1,45,1,45,1,45,1,
        45,1,45,1,45,3,45,544,8,45,1,46,1,46,1,46,1,46,1,47,1,47,1,47,3,
        47,553,8,47,1,47,3,47,556,8,47,1,48,1,48,1,48,1,48,3,48,562,8,48,
        1,48,3,48,565,8,48,3,48,567,8,48,1,49,1,49,1,49,1,49,1,49,1,49,3,
        49,575,8,49,1,50,1,50,1,50,1,50,1,50,1,51,1,51,3,51,584,8,51,1,51,
        1,51,1,51,1,52,1,52,1,52,1,52,1,52,1,52,1,52,1,52,1,52,1,53,1,53,
        5,53,600,8,53,10,53,12,53,603,9,53,1,54,1,54,1,54,1,54,1,54,1,54,
        3,54,611,8,54,1,55,1,55,1,55,5,55,616,8,55,10,55,12,55,619,9,55,
        1,56,1,56,1,57,1,57,1,57,5,57,626,8,57,10,57,12,57,629,9,57,1,58,
        1,58,1,58,5,58,634,8,58,10,58,12,58,637,9,58,1,59,1,59,1,59,3,59,
        642,8,59,1,60,1,60,1,60,5,60,647,8,60,10,60,12,60,650,9,60,1,61,
        1,61,1,61,5,61,655,8,61,10,61,12,61,658,9,61,1,62,1,62,1,62,3,62,
        663,8,62,1,63,1,63,1,63,1,63,1,63,1,63,1,63,1,63,1,63,3,63,674,8,
        63,1,63,1,63,1,63,1,63,1,63,1,63,1,63,3,63,683,8,63,1,64,1,64,1,
        64,1,64,1,64,1,65,1,65,1,66,1,66,1,66,0,0,67,0,2,4,6,8,10,12,14,
        16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,
        60,62,64,66,68,70,72,74,76,78,80,82,84,86,88,90,92,94,96,98,100,
        102,104,106,108,110,112,114,116,118,120,122,124,126,128,130,132,
        0,17,2,0,54,60,95,95,1,0,77,78,1,0,28,31,2,0,61,62,95,95,2,0,42,
        44,46,52,1,0,38,39,1,0,44,46,1,0,38,41,2,0,7,7,9,9,1,0,20,21,2,0,
        63,63,95,95,1,0,67,68,1,0,71,76,2,0,64,65,79,80,2,0,69,69,77,78,
        1,0,54,60,1,0,91,93,726,0,136,1,0,0,0,2,140,1,0,0,0,4,152,1,0,0,
        0,6,201,1,0,0,0,8,212,1,0,0,0,10,223,1,0,0,0,12,244,1,0,0,0,14,246,
        1,0,0,0,16,252,1,0,0,0,18,257,1,0,0,0,20,263,1,0,0,0,22,268,1,0,
        0,0,24,277,1,0,0,0,26,279,1,0,0,0,28,283,1,0,0,0,30,287,1,0,0,0,
        32,291,1,0,0,0,34,295,1,0,0,0,36,304,1,0,0,0,38,313,1,0,0,0,40,332,
        1,0,0,0,42,334,1,0,0,0,44,336,1,0,0,0,46,341,1,0,0,0,48,356,1,0,
        0,0,50,371,1,0,0,0,52,373,1,0,0,0,54,382,1,0,0,0,56,400,1,0,0,0,
        58,403,1,0,0,0,60,414,1,0,0,0,62,429,1,0,0,0,64,442,1,0,0,0,66,446,
        1,0,0,0,68,463,1,0,0,0,70,465,1,0,0,0,72,471,1,0,0,0,74,480,1,0,
        0,0,76,487,1,0,0,0,78,491,1,0,0,0,80,497,1,0,0,0,82,506,1,0,0,0,
        84,514,1,0,0,0,86,516,1,0,0,0,88,522,1,0,0,0,90,543,1,0,0,0,92,545,
        1,0,0,0,94,549,1,0,0,0,96,557,1,0,0,0,98,568,1,0,0,0,100,576,1,0,
        0,0,102,581,1,0,0,0,104,588,1,0,0,0,106,597,1,0,0,0,108,610,1,0,
        0,0,110,612,1,0,0,0,112,620,1,0,0,0,114,622,1,0,0,0,116,630,1,0,
        0,0,118,638,1,0,0,0,120,643,1,0,0,0,122,651,1,0,0,0,124,662,1,0,
        0,0,126,682,1,0,0,0,128,684,1,0,0,0,130,689,1,0,0,0,132,691,1,0,
        0,0,134,137,3,2,1,0,135,137,3,4,2,0,136,134,1,0,0,0,136,135,1,0,
        0,0,137,138,1,0,0,0,138,139,5,0,0,1,139,1,1,0,0,0,140,141,5,1,0,
        0,141,146,5,95,0,0,142,143,5,82,0,0,143,144,3,82,41,0,144,145,5,
        83,0,0,145,147,1,0,0,0,146,142,1,0,0,0,146,147,1,0,0,0,147,148,1,
        0,0,0,148,149,5,88,0,0,149,150,3,10,5,0,150,151,5,90,0,0,151,3,1,
        0,0,0,152,153,5,2,0,0,153,154,3,8,4,0,154,155,5,88,0,0,155,157,5,
        3,0,0,156,158,3,6,3,0,157,156,1,0,0,0,157,158,1,0,0,0,158,162,1,
        0,0,0,159,161,3,12,6,0,160,159,1,0,0,0,161,164,1,0,0,0,162,160,1,
        0,0,0,162,163,1,0,0,0,163,168,1,0,0,0,164,162,1,0,0,0,165,167,3,
        58,29,0,166,165,1,0,0,0,167,170,1,0,0,0,168,166,1,0,0,0,168,169,
        1,0,0,0,169,171,1,0,0,0,170,168,1,0,0,0,171,173,5,4,0,0,172,174,
        3,6,3,0,173,172,1,0,0,0,173,174,1,0,0,0,174,178,1,0,0,0,175,177,
        3,12,6,0,176,175,1,0,0,0,177,180,1,0,0,0,178,176,1,0,0,0,178,179,
        1,0,0,0,179,184,1,0,0,0,180,178,1,0,0,0,181,183,3,60,30,0,182,181,
        1,0,0,0,183,186,1,0,0,0,184,182,1,0,0,0,184,185,1,0,0,0,185,191,
        1,0,0,0,186,184,1,0,0,0,187,190,3,62,31,0,188,190,3,66,33,0,189,
        187,1,0,0,0,189,188,1,0,0,0,190,193,1,0,0,0,191,189,1,0,0,0,191,
        192,1,0,0,0,192,199,1,0,0,0,193,191,1,0,0,0,194,195,3,86,43,0,195,
        196,5,90,0,0,196,200,1,0,0,0,197,198,5,11,0,0,198,200,5,90,0,0,199,
        194,1,0,0,0,199,197,1,0,0,0,200,5,1,0,0,0,201,202,5,5,0,0,202,207,
        3,8,4,0,203,204,5,86,0,0,204,206,3,8,4,0,205,203,1,0,0,0,206,209,
        1,0,0,0,207,205,1,0,0,0,207,208,1,0,0,0,208,210,1,0,0,0,209,207,
        1,0,0,0,210,211,5,88,0,0,211,7,1,0,0,0,212,217,5,95,0,0,213,214,
        5,90,0,0,214,216,5,95,0,0,215,213,1,0,0,0,216,219,1,0,0,0,217,215,
        1,0,0,0,217,218,1,0,0,0,218,9,1,0,0,0,219,217,1,0,0,0,220,222,3,
        12,6,0,221,220,1,0,0,0,222,225,1,0,0,0,223,221,1,0,0,0,223,224,1,
        0,0,0,224,229,1,0,0,0,225,223,1,0,0,0,226,228,3,60,30,0,227,226,
        1,0,0,0,228,231,1,0,0,0,229,227,1,0,0,0,229,230,1,0,0,0,230,236,
        1,0,0,0,231,229,1,0,0,0,232,235,3,62,31,0,233,235,3,66,33,0,234,
        232,1,0,0,0,234,233,1,0,0,0,235,238,1,0,0,0,236,234,1,0,0,0,236,
        237,1,0,0,0,237,239,1,0,0,0,238,236,1,0,0,0,239,240,3,86,43,0,240,
        11,1,0,0,0,241,245,3,14,7,0,242,245,3,18,9,0,243,245,3,78,39,0,244,
        241,1,0,0,0,244,242,1,0,0,0,244,243,1,0,0,0,245,13,1,0,0,0,246,248,
        5,7,0,0,247,249,3,16,8,0,248,247,1,0,0,0,249,250,1,0,0,0,250,248,
        1,0,0,0,250,251,1,0,0,0,251,15,1,0,0,0,252,253,5,95,0,0,253,254,
        5,74,0,0,254,255,3,112,56,0,255,256,5,88,0,0,256,17,1,0,0,0,257,
        259,5,8,0,0,258,260,3,20,10,0,259,258,1,0,0,0,260,261,1,0,0,0,261,
        259,1,0,0,0,261,262,1,0,0,0,262,19,1,0,0,0,263,264,3,22,11,0,264,
        265,5,74,0,0,265,266,3,24,12,0,266,267,5,88,0,0,267,21,1,0,0,0,268,
        269,7,0,0,0,269,23,1,0,0,0,270,278,3,84,42,0,271,278,3,26,13,0,272,
        278,3,28,14,0,273,278,3,32,16,0,274,278,3,34,17,0,275,278,3,36,18,
        0,276,278,3,38,19,0,277,270,1,0,0,0,277,271,1,0,0,0,277,272,1,0,
        0,0,277,273,1,0,0,0,277,274,1,0,0,0,277,275,1,0,0,0,277,276,1,0,
        0,0,278,25,1,0,0,0,279,280,3,30,15,0,280,281,5,89,0,0,281,282,3,
        30,15,0,282,27,1,0,0,0,283,284,5,81,0,0,284,285,3,84,42,0,285,29,
        1,0,0,0,286,288,7,1,0,0,287,286,1,0,0,0,287,288,1,0,0,0,288,289,
        1,0,0,0,289,290,3,132,66,0,290,31,1,0,0,0,291,292,5,82,0,0,292,293,
        3,82,41,0,293,294,5,83,0,0,294,33,1,0,0,0,295,299,5,24,0,0,296,298,
        3,44,22,0,297,296,1,0,0,0,298,301,1,0,0,0,299,297,1,0,0,0,299,300,
        1,0,0,0,300,302,1,0,0,0,301,299,1,0,0,0,302,303,5,11,0,0,303,35,
        1,0,0,0,304,305,5,25,0,0,305,306,5,84,0,0,306,307,3,112,56,0,307,
        308,5,89,0,0,308,309,3,112,56,0,309,310,5,85,0,0,310,311,5,26,0,
        0,311,312,3,84,42,0,312,37,1,0,0,0,313,318,5,27,0,0,314,315,5,82,
        0,0,315,316,3,84,42,0,316,317,5,83,0,0,317,319,1,0,0,0,318,314,1,
        0,0,0,318,319,1,0,0,0,319,323,1,0,0,0,320,322,3,40,20,0,321,320,
        1,0,0,0,322,325,1,0,0,0,323,321,1,0,0,0,323,324,1,0,0,0,324,326,
        1,0,0,0,325,323,1,0,0,0,326,327,5,11,0,0,327,39,1,0,0,0,328,333,
        3,42,21,0,329,333,3,44,22,0,330,333,3,54,27,0,331,333,3,46,23,0,
        332,328,1,0,0,0,332,329,1,0,0,0,332,330,1,0,0,0,332,331,1,0,0,0,
        333,41,1,0,0,0,334,335,7,2,0,0,335,43,1,0,0,0,336,337,3,82,41,0,
        337,338,5,87,0,0,338,339,3,84,42,0,339,340,5,88,0,0,340,45,1,0,0,
        0,341,342,5,32,0,0,342,344,5,95,0,0,343,345,3,48,24,0,344,343,1,
        0,0,0,344,345,1,0,0,0,345,346,1,0,0,0,346,347,5,87,0,0,347,351,3,
        84,42,0,348,350,3,50,25,0,349,348,1,0,0,0,350,353,1,0,0,0,351,349,
        1,0,0,0,351,352,1,0,0,0,352,354,1,0,0,0,353,351,1,0,0,0,354,355,
        5,88,0,0,355,47,1,0,0,0,356,358,5,84,0,0,357,359,3,72,36,0,358,357,
        1,0,0,0,358,359,1,0,0,0,359,360,1,0,0,0,360,361,5,85,0,0,361,49,
        1,0,0,0,362,363,5,33,0,0,363,372,3,52,26,0,364,365,5,34,0,0,365,
        372,3,52,26,0,366,367,5,35,0,0,367,372,7,3,0,0,368,369,5,36,0,0,
        369,372,3,112,56,0,370,372,5,37,0,0,371,362,1,0,0,0,371,364,1,0,
        0,0,371,366,1,0,0,0,371,368,1,0,0,0,371,370,1,0,0,0,372,51,1,0,0,
        0,373,378,5,95,0,0,374,375,5,90,0,0,375,377,5,95,0,0,376,374,1,0,
        0,0,377,380,1,0,0,0,378,376,1,0,0,0,378,379,1,0,0,0,379,53,1,0,0,
        0,380,378,1,0,0,0,381,383,5,27,0,0,382,381,1,0,0,0,382,383,1,0,0,
        0,383,384,1,0,0,0,384,385,3,68,34,0,385,387,5,95,0,0,386,388,3,70,
        35,0,387,386,1,0,0,0,387,388,1,0,0,0,388,391,1,0,0,0,389,390,5,87,
        0,0,390,392,3,84,42,0,391,389,1,0,0,0,391,392,1,0,0,0,392,393,1,
        0,0,0,393,397,5,88,0,0,394,396,3,56,28,0,395,394,1,0,0,0,396,399,
        1,0,0,0,397,395,1,0,0,0,397,398,1,0,0,0,398,55,1,0,0,0,399,397,1,
        0,0,0,400,401,7,4,0,0,401,402,5,88,0,0,402,57,1,0,0,0,403,404,7,
        5,0,0,404,406,5,95,0,0,405,407,3,70,35,0,406,405,1,0,0,0,406,407,
        1,0,0,0,407,410,1,0,0,0,408,409,5,87,0,0,409,411,3,84,42,0,410,408,
        1,0,0,0,410,411,1,0,0,0,411,412,1,0,0,0,412,413,5,88,0,0,413,59,
        1,0,0,0,414,415,7,5,0,0,415,417,5,95,0,0,416,418,3,70,35,0,417,416,
        1,0,0,0,417,418,1,0,0,0,418,421,1,0,0,0,419,420,5,87,0,0,420,422,
        3,84,42,0,421,419,1,0,0,0,421,422,1,0,0,0,422,423,1,0,0,0,423,425,
        5,88,0,0,424,426,3,64,32,0,425,424,1,0,0,0,426,427,1,0,0,0,427,425,
        1,0,0,0,427,428,1,0,0,0,428,61,1,0,0,0,429,430,7,5,0,0,430,432,5,
        95,0,0,431,433,3,70,35,0,432,431,1,0,0,0,432,433,1,0,0,0,433,436,
        1,0,0,0,434,435,5,87,0,0,435,437,3,84,42,0,436,434,1,0,0,0,436,437,
        1,0,0,0,437,438,1,0,0,0,438,439,5,88,0,0,439,440,3,76,38,0,440,441,
        5,88,0,0,441,63,1,0,0,0,442,443,7,6,0,0,443,444,5,88,0,0,444,65,
        1,0,0,0,445,447,5,27,0,0,446,445,1,0,0,0,446,447,1,0,0,0,447,448,
        1,0,0,0,448,449,3,68,34,0,449,450,5,95,0,0,450,451,5,90,0,0,451,
        453,5,95,0,0,452,454,3,70,35,0,453,452,1,0,0,0,453,454,1,0,0,0,454,
        457,1,0,0,0,455,456,5,87,0,0,456,458,3,84,42,0,457,455,1,0,0,0,457,
        458,1,0,0,0,458,459,1,0,0,0,459,460,5,88,0,0,460,461,3,76,38,0,461,
        462,5,88,0,0,462,67,1,0,0,0,463,464,7,7,0,0,464,69,1,0,0,0,465,467,
        5,82,0,0,466,468,3,72,36,0,467,466,1,0,0,0,467,468,1,0,0,0,468,469,
        1,0,0,0,469,470,5,83,0,0,470,71,1,0,0,0,471,476,3,74,37,0,472,473,
        5,88,0,0,473,475,3,74,37,0,474,472,1,0,0,0,475,478,1,0,0,0,476,474,
        1,0,0,0,476,477,1,0,0,0,477,73,1,0,0,0,478,476,1,0,0,0,479,481,7,
        8,0,0,480,479,1,0,0,0,480,481,1,0,0,0,481,482,1,0,0,0,482,483,3,
        82,41,0,483,484,5,87,0,0,484,485,3,84,42,0,485,75,1,0,0,0,486,488,
        3,78,39,0,487,486,1,0,0,0,487,488,1,0,0,0,488,489,1,0,0,0,489,490,
        3,86,43,0,490,77,1,0,0,0,491,493,5,9,0,0,492,494,3,80,40,0,493,492,
        1,0,0,0,494,495,1,0,0,0,495,493,1,0,0,0,495,496,1,0,0,0,496,79,1,
        0,0,0,497,498,3,82,41,0,498,499,5,87,0,0,499,502,3,84,42,0,500,501,
        5,70,0,0,501,503,3,112,56,0,502,500,1,0,0,0,502,503,1,0,0,0,503,
        504,1,0,0,0,504,505,5,88,0,0,505,81,1,0,0,0,506,511,5,95,0,0,507,
        508,5,86,0,0,508,510,5,95,0,0,509,507,1,0,0,0,510,513,1,0,0,0,511,
        509,1,0,0,0,511,512,1,0,0,0,512,83,1,0,0,0,513,511,1,0,0,0,514,515,
        7,0,0,0,515,85,1,0,0,0,516,518,5,10,0,0,517,519,3,88,44,0,518,517,
        1,0,0,0,518,519,1,0,0,0,519,520,1,0,0,0,520,521,5,11,0,0,521,87,
        1,0,0,0,522,527,3,90,45,0,523,524,5,88,0,0,524,526,3,90,45,0,525,
        523,1,0,0,0,526,529,1,0,0,0,527,525,1,0,0,0,527,528,1,0,0,0,528,
        531,1,0,0,0,529,527,1,0,0,0,530,532,5,88,0,0,531,530,1,0,0,0,531,
        532,1,0,0,0,532,89,1,0,0,0,533,544,3,86,43,0,534,544,3,92,46,0,535,
        544,3,96,48,0,536,544,3,94,47,0,537,544,3,98,49,0,538,544,3,100,
        50,0,539,544,3,102,51,0,540,544,3,104,52,0,541,544,5,22,0,0,542,
        544,5,23,0,0,543,533,1,0,0,0,543,534,1,0,0,0,543,535,1,0,0,0,543,
        536,1,0,0,0,543,537,1,0,0,0,543,538,1,0,0,0,543,539,1,0,0,0,543,
        540,1,0,0,0,543,541,1,0,0,0,543,542,1,0,0,0,544,91,1,0,0,0,545,546,
        3,106,53,0,546,547,5,70,0,0,547,548,3,112,56,0,548,93,1,0,0,0,549,
        555,3,106,53,0,550,552,5,82,0,0,551,553,3,110,55,0,552,551,1,0,0,
        0,552,553,1,0,0,0,553,554,1,0,0,0,554,556,5,83,0,0,555,550,1,0,0,
        0,555,556,1,0,0,0,556,95,1,0,0,0,557,566,5,53,0,0,558,564,5,95,0,
        0,559,561,5,82,0,0,560,562,3,110,55,0,561,560,1,0,0,0,561,562,1,
        0,0,0,562,563,1,0,0,0,563,565,5,83,0,0,564,559,1,0,0,0,564,565,1,
        0,0,0,565,567,1,0,0,0,566,558,1,0,0,0,566,567,1,0,0,0,567,97,1,0,
        0,0,568,569,5,12,0,0,569,570,3,112,56,0,570,571,5,13,0,0,571,574,
        3,90,45,0,572,573,5,14,0,0,573,575,3,90,45,0,574,572,1,0,0,0,574,
        575,1,0,0,0,575,99,1,0,0,0,576,577,5,15,0,0,577,578,3,112,56,0,578,
        579,5,16,0,0,579,580,3,90,45,0,580,101,1,0,0,0,581,583,5,17,0,0,
        582,584,3,88,44,0,583,582,1,0,0,0,583,584,1,0,0,0,584,585,1,0,0,
        0,585,586,5,18,0,0,586,587,3,112,56,0,587,103,1,0,0,0,588,589,5,
        19,0,0,589,590,5,95,0,0,590,591,5,70,0,0,591,592,3,112,56,0,592,
        593,7,9,0,0,593,594,3,112,56,0,594,595,5,16,0,0,595,596,3,90,45,
        0,596,105,1,0,0,0,597,601,7,10,0,0,598,600,3,108,54,0,599,598,1,
        0,0,0,600,603,1,0,0,0,601,599,1,0,0,0,601,602,1,0,0,0,602,107,1,
        0,0,0,603,601,1,0,0,0,604,605,5,90,0,0,605,611,5,95,0,0,606,607,
        5,84,0,0,607,608,3,112,56,0,608,609,5,85,0,0,609,611,1,0,0,0,610,
        604,1,0,0,0,610,606,1,0,0,0,611,109,1,0,0,0,612,617,3,112,56,0,613,
        614,5,86,0,0,614,616,3,112,56,0,615,613,1,0,0,0,616,619,1,0,0,0,
        617,615,1,0,0,0,617,618,1,0,0,0,618,111,1,0,0,0,619,617,1,0,0,0,
        620,621,3,114,57,0,621,113,1,0,0,0,622,627,3,116,58,0,623,624,7,
        11,0,0,624,626,3,116,58,0,625,623,1,0,0,0,626,629,1,0,0,0,627,625,
        1,0,0,0,627,628,1,0,0,0,628,115,1,0,0,0,629,627,1,0,0,0,630,635,
        3,118,59,0,631,632,5,66,0,0,632,634,3,118,59,0,633,631,1,0,0,0,634,
        637,1,0,0,0,635,633,1,0,0,0,635,636,1,0,0,0,636,117,1,0,0,0,637,
        635,1,0,0,0,638,641,3,120,60,0,639,640,7,12,0,0,640,642,3,120,60,
        0,641,639,1,0,0,0,641,642,1,0,0,0,642,119,1,0,0,0,643,648,3,122,
        61,0,644,645,7,1,0,0,645,647,3,122,61,0,646,644,1,0,0,0,647,650,
        1,0,0,0,648,646,1,0,0,0,648,649,1,0,0,0,649,121,1,0,0,0,650,648,
        1,0,0,0,651,656,3,124,62,0,652,653,7,13,0,0,653,655,3,124,62,0,654,
        652,1,0,0,0,655,658,1,0,0,0,656,654,1,0,0,0,656,657,1,0,0,0,657,
        123,1,0,0,0,658,656,1,0,0,0,659,660,7,14,0,0,660,663,3,124,62,0,
        661,663,3,126,63,0,662,659,1,0,0,0,662,661,1,0,0,0,663,125,1,0,0,
        0,664,683,3,132,66,0,665,683,5,94,0,0,666,683,5,61,0,0,667,683,5,
        62,0,0,668,683,5,63,0,0,669,683,3,128,64,0,670,671,3,106,53,0,671,
        673,5,82,0,0,672,674,3,110,55,0,673,672,1,0,0,0,673,674,1,0,0,0,
        674,675,1,0,0,0,675,676,5,83,0,0,676,683,1,0,0,0,677,683,3,106,53,
        0,678,679,5,82,0,0,679,680,3,112,56,0,680,681,5,83,0,0,681,683,1,
        0,0,0,682,664,1,0,0,0,682,665,1,0,0,0,682,666,1,0,0,0,682,667,1,
        0,0,0,682,668,1,0,0,0,682,669,1,0,0,0,682,670,1,0,0,0,682,677,1,
        0,0,0,682,678,1,0,0,0,683,127,1,0,0,0,684,685,3,130,65,0,685,686,
        5,82,0,0,686,687,3,112,56,0,687,688,5,83,0,0,688,129,1,0,0,0,689,
        690,7,15,0,0,690,131,1,0,0,0,691,692,7,16,0,0,692,133,1,0,0,0,74,
        136,146,157,162,168,173,178,184,189,191,199,207,217,223,229,234,
        236,244,250,261,277,287,299,318,323,332,344,351,358,371,378,382,
        387,391,397,406,410,417,421,427,432,436,446,453,457,467,476,480,
        487,495,502,511,518,527,531,543,552,555,561,564,566,574,583,601,
        610,617,627,635,641,648,656,662,673,682
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
                     "'RECORD'", "'ARRAY'", "'OF'", "'CLASS'", "'PRIVATE'", 
                     "'PROTECTED'", "'PUBLIC'", "'PUBLISHED'", "'PROPERTY'", 
                     "'READ'", "'WRITE'", "'STORED'", "'DEFAULT'", "'NODEFAULT'", 
                     "'PROCEDURE'", "'FUNCTION'", "'CONSTRUCTOR'", "'DESTRUCTOR'", 
                     "'VIRTUAL'", "'OVERRIDE'", "'CDECL'", "'EXTERNAL'", 
                     "'FORWARD'", "'STATIC'", "'ABSTRACT'", "'OVERLOAD'", 
                     "'REINTRODUCE'", "'INLINE'", "'DYNAMIC'", "'INHERITED'", 
                     "'INTEGER'", "'BYTE'", "'CHAR'", "'BOOLEAN'", "'POINTER'", 
                     "'STRING'", "'DOUBLE'", "'TRUE'", "'FALSE'", "'NIL'", 
                     "'DIV'", "'MOD'", "'AND'", "'OR'", "'XOR'", "'NOT'", 
                     "':='", "'<='", "'>='", "'<>'", "'='", "'<'", "'>'", 
                     "'+'", "'-'", "'*'", "'/'", "'^'", "'('", "')'", "'['", 
                     "']'", "','", "':'", "';'", "'..'", "'.'" ]

    symbolicNames = [ "<INVALID>", "PROGRAM", "UNIT", "INTERFACE", "IMPLEMENTATION", 
                      "USES", "LIBRARY", "CONST", "TYPE", "VAR", "BEGIN", 
                      "END", "IF", "THEN", "ELSE", "WHILE", "DO", "REPEAT", 
                      "UNTIL", "FOR", "TO", "DOWNTO", "BREAK", "CONTINUE", 
                      "RECORD", "ARRAY", "OF", "CLASS", "PRIVATE", "PROTECTED", 
                      "PUBLIC", "PUBLISHED", "PROPERTY", "READ", "WRITE", 
                      "STORED", "DEFAULT", "NODEFAULT", "PROCEDURE", "FUNCTION", 
                      "CONSTRUCTOR", "DESTRUCTOR", "VIRTUAL", "OVERRIDE", 
                      "CDECL", "EXTERNAL", "FORWARD", "STATIC", "ABSTRACT", 
                      "OVERLOAD", "REINTRODUCE", "INLINE", "DYNAMIC", "INHERITED", 
                      "INTEGER_TYPE", "BYTE_TYPE", "CHAR_TYPE", "BOOLEAN_TYPE", 
                      "POINTER_TYPE", "STRING_TYPE", "DOUBLE_TYPE", "TRUE", 
                      "FALSE", "NIL", "DIV", "MOD", "AND", "OR", "XOR", 
                      "NOT", "ASSIGN", "LE", "GE", "NE", "EQ", "LT", "GT", 
                      "PLUS", "MINUS", "STAR", "SLASH", "CARET", "LPAREN", 
                      "RPAREN", "LBRACK", "RBRACK", "COMMA", "COLON", "SEMI", 
                      "DOTDOT", "DOT", "HEX_INTEGER", "BINARY_INTEGER", 
                      "DECIMAL_INTEGER", "STRING_LITERAL", "IDENTIFIER", 
                      "BRACE_COMMENT", "PAREN_COMMENT", "LINE_COMMENT", 
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
    RULE_globalRoutineImplementation = 31
    RULE_routineDirective = 32
    RULE_methodImplementation = 33
    RULE_routineKind = 34
    RULE_formalParameters = 35
    RULE_formalParameterList = 36
    RULE_formalParameterGroup = 37
    RULE_routineBlock = 38
    RULE_varSection = 39
    RULE_varDeclaration = 40
    RULE_identifierList = 41
    RULE_typeIdentifier = 42
    RULE_compoundStatement = 43
    RULE_statementSequence = 44
    RULE_statement = 45
    RULE_assignmentStatement = 46
    RULE_callStatement = 47
    RULE_inheritedStatement = 48
    RULE_ifStatement = 49
    RULE_whileStatement = 50
    RULE_repeatStatement = 51
    RULE_forStatement = 52
    RULE_designator = 53
    RULE_designatorSuffix = 54
    RULE_argumentList = 55
    RULE_expression = 56
    RULE_orExpression = 57
    RULE_andExpression = 58
    RULE_comparisonExpression = 59
    RULE_additiveExpression = 60
    RULE_multiplicativeExpression = 61
    RULE_unaryExpression = 62
    RULE_primaryExpression = 63
    RULE_typeCastExpression = 64
    RULE_builtinCastType = 65
    RULE_integerLiteral = 66

    ruleNames =  [ "compilationUnit", "programUnit", "unitUnit", "usesClause", 
                   "qualifiedIdentifier", "block", "declarationSection", 
                   "constSection", "constDefinition", "typeSection", "typeDefinition", 
                   "typeName", "typeSpecification", "subrangeType", "pointerType", 
                   "signedIntegerLiteral", "enumType", "recordType", "arrayType", 
                   "classType", "classMember", "visibilitySpecifier", "fieldDeclaration", 
                   "propertyDeclaration", "propertyIndexParameters", "propertySpecifier", 
                   "propertyAccessor", "methodDeclaration", "methodDirective", 
                   "globalRoutinePrototype", "globalRoutineDeclaration", 
                   "globalRoutineImplementation", "routineDirective", "methodImplementation", 
                   "routineKind", "formalParameters", "formalParameterList", 
                   "formalParameterGroup", "routineBlock", "varSection", 
                   "varDeclaration", "identifierList", "typeIdentifier", 
                   "compoundStatement", "statementSequence", "statement", 
                   "assignmentStatement", "callStatement", "inheritedStatement", 
                   "ifStatement", "whileStatement", "repeatStatement", "forStatement", 
                   "designator", "designatorSuffix", "argumentList", "expression", 
                   "orExpression", "andExpression", "comparisonExpression", 
                   "additiveExpression", "multiplicativeExpression", "unaryExpression", 
                   "primaryExpression", "typeCastExpression", "builtinCastType", 
                   "integerLiteral" ]

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
    RECORD=24
    ARRAY=25
    OF=26
    CLASS=27
    PRIVATE=28
    PROTECTED=29
    PUBLIC=30
    PUBLISHED=31
    PROPERTY=32
    READ=33
    WRITE=34
    STORED=35
    DEFAULT=36
    NODEFAULT=37
    PROCEDURE=38
    FUNCTION=39
    CONSTRUCTOR=40
    DESTRUCTOR=41
    VIRTUAL=42
    OVERRIDE=43
    CDECL=44
    EXTERNAL=45
    FORWARD=46
    STATIC=47
    ABSTRACT=48
    OVERLOAD=49
    REINTRODUCE=50
    INLINE=51
    DYNAMIC=52
    INHERITED=53
    INTEGER_TYPE=54
    BYTE_TYPE=55
    CHAR_TYPE=56
    BOOLEAN_TYPE=57
    POINTER_TYPE=58
    STRING_TYPE=59
    DOUBLE_TYPE=60
    TRUE=61
    FALSE=62
    NIL=63
    DIV=64
    MOD=65
    AND=66
    OR=67
    XOR=68
    NOT=69
    ASSIGN=70
    LE=71
    GE=72
    NE=73
    EQ=74
    LT=75
    GT=76
    PLUS=77
    MINUS=78
    STAR=79
    SLASH=80
    CARET=81
    LPAREN=82
    RPAREN=83
    LBRACK=84
    RBRACK=85
    COMMA=86
    COLON=87
    SEMI=88
    DOTDOT=89
    DOT=90
    HEX_INTEGER=91
    BINARY_INTEGER=92
    DECIMAL_INTEGER=93
    STRING_LITERAL=94
    IDENTIFIER=95
    BRACE_COMMENT=96
    PAREN_COMMENT=97
    LINE_COMMENT=98
    WS=99

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
            self.state = 136
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [1]:
                self.state = 134
                self.programUnit()
                pass
            elif token in [2]:
                self.state = 135
                self.unitUnit()
                pass
            else:
                raise NoViableAltException(self)

            self.state = 138
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
            self.state = 140
            self.match(C64PascalParser.PROGRAM)
            self.state = 141
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 146
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==82:
                self.state = 142
                self.match(C64PascalParser.LPAREN)
                self.state = 143
                self.identifierList()
                self.state = 144
                self.match(C64PascalParser.RPAREN)


            self.state = 148
            self.match(C64PascalParser.SEMI)
            self.state = 149
            self.block()
            self.state = 150
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
            self.state = 152
            self.match(C64PascalParser.UNIT)
            self.state = 153
            self.qualifiedIdentifier()
            self.state = 154
            self.match(C64PascalParser.SEMI)
            self.state = 155
            self.match(C64PascalParser.INTERFACE)
            self.state = 157
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 156
                self.usesClause()


            self.state = 162
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 896) != 0):
                self.state = 159
                self.declarationSection()
                self.state = 164
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 168
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==38 or _la==39:
                self.state = 165
                self.globalRoutinePrototype()
                self.state = 170
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 171
            self.match(C64PascalParser.IMPLEMENTATION)
            self.state = 173
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==5:
                self.state = 172
                self.usesClause()


            self.state = 178
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 896) != 0):
                self.state = 175
                self.declarationSection()
                self.state = 180
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 184
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,7,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 181
                    self.globalRoutineDeclaration() 
                self.state = 186
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,7,self._ctx)

            self.state = 191
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 4123302821888) != 0):
                self.state = 189
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input,8,self._ctx)
                if la_ == 1:
                    self.state = 187
                    self.globalRoutineImplementation()
                    pass

                elif la_ == 2:
                    self.state = 188
                    self.methodImplementation()
                    pass


                self.state = 193
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 199
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [10]:
                self.state = 194
                self.compoundStatement()
                self.state = 195
                self.match(C64PascalParser.DOT)
                pass
            elif token in [11]:
                self.state = 197
                self.match(C64PascalParser.END)
                self.state = 198
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
            self.state = 201
            self.match(C64PascalParser.USES)
            self.state = 202
            self.qualifiedIdentifier()
            self.state = 207
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==86:
                self.state = 203
                self.match(C64PascalParser.COMMA)
                self.state = 204
                self.qualifiedIdentifier()
                self.state = 209
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 210
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
            self.state = 212
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 217
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==90:
                self.state = 213
                self.match(C64PascalParser.DOT)
                self.state = 214
                self.match(C64PascalParser.IDENTIFIER)
                self.state = 219
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
            self.state = 223
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 896) != 0):
                self.state = 220
                self.declarationSection()
                self.state = 225
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 229
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,14,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 226
                    self.globalRoutineDeclaration() 
                self.state = 231
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,14,self._ctx)

            self.state = 236
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 4123302821888) != 0):
                self.state = 234
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input,15,self._ctx)
                if la_ == 1:
                    self.state = 232
                    self.globalRoutineImplementation()
                    pass

                elif la_ == 2:
                    self.state = 233
                    self.methodImplementation()
                    pass


                self.state = 238
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 239
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
            self.state = 244
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [7]:
                self.enterOuterAlt(localctx, 1)
                self.state = 241
                self.constSection()
                pass
            elif token in [8]:
                self.enterOuterAlt(localctx, 2)
                self.state = 242
                self.typeSection()
                pass
            elif token in [9]:
                self.enterOuterAlt(localctx, 3)
                self.state = 243
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
            self.state = 246
            self.match(C64PascalParser.CONST)
            self.state = 248 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 247
                self.constDefinition()
                self.state = 250 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==95):
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
            self.state = 252
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 253
            self.match(C64PascalParser.EQ)
            self.state = 254
            self.expression()
            self.state = 255
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
            self.state = 257
            self.match(C64PascalParser.TYPE)
            self.state = 259 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 258
                self.typeDefinition()
                self.state = 261 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (((((_la - 54)) & ~0x3f) == 0 and ((1 << (_la - 54)) & 2199023255679) != 0)):
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
            self.state = 263
            self.typeName()
            self.state = 264
            self.match(C64PascalParser.EQ)
            self.state = 265
            self.typeSpecification()
            self.state = 266
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
            self.state = 268
            _la = self._input.LA(1)
            if not(((((_la - 54)) & ~0x3f) == 0 and ((1 << (_la - 54)) & 2199023255679) != 0)):
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
            self.state = 277
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [54, 55, 56, 57, 58, 59, 60, 95]:
                self.enterOuterAlt(localctx, 1)
                self.state = 270
                self.typeIdentifier()
                pass
            elif token in [77, 78, 91, 92, 93]:
                self.enterOuterAlt(localctx, 2)
                self.state = 271
                self.subrangeType()
                pass
            elif token in [81]:
                self.enterOuterAlt(localctx, 3)
                self.state = 272
                self.pointerType()
                pass
            elif token in [82]:
                self.enterOuterAlt(localctx, 4)
                self.state = 273
                self.enumType()
                pass
            elif token in [24]:
                self.enterOuterAlt(localctx, 5)
                self.state = 274
                self.recordType()
                pass
            elif token in [25]:
                self.enterOuterAlt(localctx, 6)
                self.state = 275
                self.arrayType()
                pass
            elif token in [27]:
                self.enterOuterAlt(localctx, 7)
                self.state = 276
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
            self.state = 279
            self.signedIntegerLiteral()
            self.state = 280
            self.match(C64PascalParser.DOTDOT)
            self.state = 281
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
            self.state = 283
            self.match(C64PascalParser.CARET)
            self.state = 284
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
            self.state = 287
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==77 or _la==78:
                self.state = 286
                _la = self._input.LA(1)
                if not(_la==77 or _la==78):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()


            self.state = 289
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
            self.state = 291
            self.match(C64PascalParser.LPAREN)
            self.state = 292
            self.identifierList()
            self.state = 293
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
            self.state = 295
            self.match(C64PascalParser.RECORD)
            self.state = 299
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==95:
                self.state = 296
                self.fieldDeclaration()
                self.state = 301
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 302
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
            self.state = 304
            self.match(C64PascalParser.ARRAY)
            self.state = 305
            self.match(C64PascalParser.LBRACK)
            self.state = 306
            self.expression()
            self.state = 307
            self.match(C64PascalParser.DOTDOT)
            self.state = 308
            self.expression()
            self.state = 309
            self.match(C64PascalParser.RBRACK)
            self.state = 310
            self.match(C64PascalParser.OF)
            self.state = 311
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
            self.state = 313
            self.match(C64PascalParser.CLASS)
            self.state = 318
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==82:
                self.state = 314
                self.match(C64PascalParser.LPAREN)
                self.state = 315
                self.typeIdentifier()
                self.state = 316
                self.match(C64PascalParser.RPAREN)


            self.state = 323
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 4131624321024) != 0) or _la==95:
                self.state = 320
                self.classMember()
                self.state = 325
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 326
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
            self.state = 332
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [28, 29, 30, 31]:
                self.enterOuterAlt(localctx, 1)
                self.state = 328
                self.visibilitySpecifier()
                pass
            elif token in [95]:
                self.enterOuterAlt(localctx, 2)
                self.state = 329
                self.fieldDeclaration()
                pass
            elif token in [27, 38, 39, 40, 41]:
                self.enterOuterAlt(localctx, 3)
                self.state = 330
                self.methodDeclaration()
                pass
            elif token in [32]:
                self.enterOuterAlt(localctx, 4)
                self.state = 331
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
            self.state = 334
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 4026531840) != 0)):
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
            self.state = 336
            self.identifierList()
            self.state = 337
            self.match(C64PascalParser.COLON)
            self.state = 338
            self.typeIdentifier()
            self.state = 339
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
            self.state = 341
            self.match(C64PascalParser.PROPERTY)
            self.state = 342
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 344
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==84:
                self.state = 343
                self.propertyIndexParameters()


            self.state = 346
            self.match(C64PascalParser.COLON)
            self.state = 347
            self.typeIdentifier()
            self.state = 351
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 266287972352) != 0):
                self.state = 348
                self.propertySpecifier()
                self.state = 353
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 354
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
            self.state = 356
            self.match(C64PascalParser.LBRACK)
            self.state = 358
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==7 or _la==9 or _la==95:
                self.state = 357
                self.formalParameterList()


            self.state = 360
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
            self.state = 371
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [33]:
                self.enterOuterAlt(localctx, 1)
                self.state = 362
                self.match(C64PascalParser.READ)
                self.state = 363
                self.propertyAccessor()
                pass
            elif token in [34]:
                self.enterOuterAlt(localctx, 2)
                self.state = 364
                self.match(C64PascalParser.WRITE)
                self.state = 365
                self.propertyAccessor()
                pass
            elif token in [35]:
                self.enterOuterAlt(localctx, 3)
                self.state = 366
                self.match(C64PascalParser.STORED)
                self.state = 367
                _la = self._input.LA(1)
                if not(((((_la - 61)) & ~0x3f) == 0 and ((1 << (_la - 61)) & 17179869187) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                pass
            elif token in [36]:
                self.enterOuterAlt(localctx, 4)
                self.state = 368
                self.match(C64PascalParser.DEFAULT)
                self.state = 369
                self.expression()
                pass
            elif token in [37]:
                self.enterOuterAlt(localctx, 5)
                self.state = 370
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
            self.state = 373
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 378
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==90:
                self.state = 374
                self.match(C64PascalParser.DOT)
                self.state = 375
                self.match(C64PascalParser.IDENTIFIER)
                self.state = 380
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
            self.state = 382
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==27:
                self.state = 381
                self.match(C64PascalParser.CLASS)


            self.state = 384
            self.routineKind()
            self.state = 385
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 387
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==82:
                self.state = 386
                self.formalParameters()


            self.state = 391
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==87:
                self.state = 389
                self.match(C64PascalParser.COLON)
                self.state = 390
                self.typeIdentifier()


            self.state = 393
            self.match(C64PascalParser.SEMI)
            self.state = 397
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 8967616836141056) != 0):
                self.state = 394
                self.methodDirective()
                self.state = 399
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
            self.state = 400
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 8967616836141056) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 401
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
            self.state = 403
            _la = self._input.LA(1)
            if not(_la==38 or _la==39):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 404
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 406
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==82:
                self.state = 405
                self.formalParameters()


            self.state = 410
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==87:
                self.state = 408
                self.match(C64PascalParser.COLON)
                self.state = 409
                self.typeIdentifier()


            self.state = 412
            self.match(C64PascalParser.SEMI)
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


        def routineDirective(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.RoutineDirectiveContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.RoutineDirectiveContext,i)


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
            if not(_la==38 or _la==39):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 415
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 417
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==82:
                self.state = 416
                self.formalParameters()


            self.state = 421
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==87:
                self.state = 419
                self.match(C64PascalParser.COLON)
                self.state = 420
                self.typeIdentifier()


            self.state = 423
            self.match(C64PascalParser.SEMI)
            self.state = 425 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 424
                self.routineDirective()
                self.state = 427 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not ((((_la) & ~0x3f) == 0 and ((1 << _la) & 123145302310912) != 0)):
                    break

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
        self.enterRule(localctx, 62, self.RULE_globalRoutineImplementation)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 429
            _la = self._input.LA(1)
            if not(_la==38 or _la==39):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 430
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 432
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==82:
                self.state = 431
                self.formalParameters()


            self.state = 436
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==87:
                self.state = 434
                self.match(C64PascalParser.COLON)
                self.state = 435
                self.typeIdentifier()


            self.state = 438
            self.match(C64PascalParser.SEMI)
            self.state = 439
            self.routineBlock()
            self.state = 440
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RoutineDirectiveContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def CDECL(self):
            return self.getToken(C64PascalParser.CDECL, 0)

        def EXTERNAL(self):
            return self.getToken(C64PascalParser.EXTERNAL, 0)

        def FORWARD(self):
            return self.getToken(C64PascalParser.FORWARD, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_routineDirective

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRoutineDirective" ):
                listener.enterRoutineDirective(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRoutineDirective" ):
                listener.exitRoutineDirective(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRoutineDirective" ):
                return visitor.visitRoutineDirective(self)
            else:
                return visitor.visitChildren(self)




    def routineDirective(self):

        localctx = C64PascalParser.RoutineDirectiveContext(self, self._ctx, self.state)
        self.enterRule(localctx, 64, self.RULE_routineDirective)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 442
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 123145302310912) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 443
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
        self.enterRule(localctx, 66, self.RULE_methodImplementation)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 446
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==27:
                self.state = 445
                self.match(C64PascalParser.CLASS)


            self.state = 448
            self.routineKind()
            self.state = 449
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 450
            self.match(C64PascalParser.DOT)
            self.state = 451
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 453
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==82:
                self.state = 452
                self.formalParameters()


            self.state = 457
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==87:
                self.state = 455
                self.match(C64PascalParser.COLON)
                self.state = 456
                self.typeIdentifier()


            self.state = 459
            self.match(C64PascalParser.SEMI)
            self.state = 460
            self.routineBlock()
            self.state = 461
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
        self.enterRule(localctx, 68, self.RULE_routineKind)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 463
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 4123168604160) != 0)):
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
        self.enterRule(localctx, 70, self.RULE_formalParameters)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 465
            self.match(C64PascalParser.LPAREN)
            self.state = 467
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==7 or _la==9 or _la==95:
                self.state = 466
                self.formalParameterList()


            self.state = 469
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
        self.enterRule(localctx, 72, self.RULE_formalParameterList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 471
            self.formalParameterGroup()
            self.state = 476
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==88:
                self.state = 472
                self.match(C64PascalParser.SEMI)
                self.state = 473
                self.formalParameterGroup()
                self.state = 478
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
        self.enterRule(localctx, 74, self.RULE_formalParameterGroup)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 480
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==7 or _la==9:
                self.state = 479
                _la = self._input.LA(1)
                if not(_la==7 or _la==9):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()


            self.state = 482
            self.identifierList()
            self.state = 483
            self.match(C64PascalParser.COLON)
            self.state = 484
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
        self.enterRule(localctx, 76, self.RULE_routineBlock)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 487
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==9:
                self.state = 486
                self.varSection()


            self.state = 489
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
        self.enterRule(localctx, 78, self.RULE_varSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 491
            self.match(C64PascalParser.VAR)
            self.state = 493 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 492
                self.varDeclaration()
                self.state = 495 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==95):
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
        self.enterRule(localctx, 80, self.RULE_varDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 497
            self.identifierList()
            self.state = 498
            self.match(C64PascalParser.COLON)
            self.state = 499
            self.typeIdentifier()
            self.state = 502
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==70:
                self.state = 500
                self.match(C64PascalParser.ASSIGN)
                self.state = 501
                self.expression()


            self.state = 504
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
        self.enterRule(localctx, 82, self.RULE_identifierList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 506
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 511
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==86:
                self.state = 507
                self.match(C64PascalParser.COMMA)
                self.state = 508
                self.match(C64PascalParser.IDENTIFIER)
                self.state = 513
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
        self.enterRule(localctx, 84, self.RULE_typeIdentifier)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 514
            _la = self._input.LA(1)
            if not(((((_la - 54)) & ~0x3f) == 0 and ((1 << (_la - 54)) & 2199023255679) != 0)):
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
        self.enterRule(localctx, 86, self.RULE_compoundStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 516
            self.match(C64PascalParser.BEGIN)
            self.state = 518
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & -9214364837586758656) != 0) or _la==95:
                self.state = 517
                self.statementSequence()


            self.state = 520
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
        self.enterRule(localctx, 88, self.RULE_statementSequence)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 522
            self.statement()
            self.state = 527
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,53,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 523
                    self.match(C64PascalParser.SEMI)
                    self.state = 524
                    self.statement() 
                self.state = 529
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,53,self._ctx)

            self.state = 531
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==88:
                self.state = 530
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
        self.enterRule(localctx, 90, self.RULE_statement)
        try:
            self.state = 543
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,55,self._ctx)
            if la_ == 1:
                localctx = C64PascalParser.CompoundStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 533
                self.compoundStatement()
                pass

            elif la_ == 2:
                localctx = C64PascalParser.AssignmentStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 534
                self.assignmentStatement()
                pass

            elif la_ == 3:
                localctx = C64PascalParser.InheritedStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 535
                self.inheritedStatement()
                pass

            elif la_ == 4:
                localctx = C64PascalParser.CallStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 536
                self.callStatement()
                pass

            elif la_ == 5:
                localctx = C64PascalParser.IfStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 537
                self.ifStatement()
                pass

            elif la_ == 6:
                localctx = C64PascalParser.WhileStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 538
                self.whileStatement()
                pass

            elif la_ == 7:
                localctx = C64PascalParser.RepeatStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 539
                self.repeatStatement()
                pass

            elif la_ == 8:
                localctx = C64PascalParser.ForStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 8)
                self.state = 540
                self.forStatement()
                pass

            elif la_ == 9:
                localctx = C64PascalParser.BreakStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 9)
                self.state = 541
                self.match(C64PascalParser.BREAK)
                pass

            elif la_ == 10:
                localctx = C64PascalParser.ContinueStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 10)
                self.state = 542
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
        self.enterRule(localctx, 92, self.RULE_assignmentStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 545
            self.designator()
            self.state = 546
            self.match(C64PascalParser.ASSIGN)
            self.state = 547
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
        self.enterRule(localctx, 94, self.RULE_callStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 549
            self.designator()
            self.state = 555
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==82:
                self.state = 550
                self.match(C64PascalParser.LPAREN)
                self.state = 552
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if ((((_la - 54)) & ~0x3f) == 0 and ((1 << (_la - 54)) & 4260901192703) != 0):
                    self.state = 551
                    self.argumentList()


                self.state = 554
                self.match(C64PascalParser.RPAREN)


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
        self.enterRule(localctx, 96, self.RULE_inheritedStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 557
            self.match(C64PascalParser.INHERITED)
            self.state = 566
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==95:
                self.state = 558
                self.match(C64PascalParser.IDENTIFIER)
                self.state = 564
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==82:
                    self.state = 559
                    self.match(C64PascalParser.LPAREN)
                    self.state = 561
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if ((((_la - 54)) & ~0x3f) == 0 and ((1 << (_la - 54)) & 4260901192703) != 0):
                        self.state = 560
                        self.argumentList()


                    self.state = 563
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
        self.enterRule(localctx, 98, self.RULE_ifStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 568
            self.match(C64PascalParser.IF)
            self.state = 569
            self.expression()
            self.state = 570
            self.match(C64PascalParser.THEN)
            self.state = 571
            self.statement()
            self.state = 574
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,61,self._ctx)
            if la_ == 1:
                self.state = 572
                self.match(C64PascalParser.ELSE)
                self.state = 573
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
        self.enterRule(localctx, 100, self.RULE_whileStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 576
            self.match(C64PascalParser.WHILE)
            self.state = 577
            self.expression()
            self.state = 578
            self.match(C64PascalParser.DO)
            self.state = 579
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
        self.enterRule(localctx, 102, self.RULE_repeatStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 581
            self.match(C64PascalParser.REPEAT)
            self.state = 583
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & -9214364837586758656) != 0) or _la==95:
                self.state = 582
                self.statementSequence()


            self.state = 585
            self.match(C64PascalParser.UNTIL)
            self.state = 586
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
        self.enterRule(localctx, 104, self.RULE_forStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 588
            self.match(C64PascalParser.FOR)
            self.state = 589
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 590
            self.match(C64PascalParser.ASSIGN)
            self.state = 591
            self.expression()
            self.state = 592
            _la = self._input.LA(1)
            if not(_la==20 or _la==21):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 593
            self.expression()
            self.state = 594
            self.match(C64PascalParser.DO)
            self.state = 595
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
        self.enterRule(localctx, 106, self.RULE_designator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 597
            _la = self._input.LA(1)
            if not(_la==63 or _la==95):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 601
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==84 or _la==90:
                self.state = 598
                self.designatorSuffix()
                self.state = 603
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
        self.enterRule(localctx, 108, self.RULE_designatorSuffix)
        try:
            self.state = 610
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [90]:
                self.enterOuterAlt(localctx, 1)
                self.state = 604
                self.match(C64PascalParser.DOT)
                self.state = 605
                self.match(C64PascalParser.IDENTIFIER)
                pass
            elif token in [84]:
                self.enterOuterAlt(localctx, 2)
                self.state = 606
                self.match(C64PascalParser.LBRACK)
                self.state = 607
                self.expression()
                self.state = 608
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
        self.enterRule(localctx, 110, self.RULE_argumentList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 612
            self.expression()
            self.state = 617
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==86:
                self.state = 613
                self.match(C64PascalParser.COMMA)
                self.state = 614
                self.expression()
                self.state = 619
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
        self.enterRule(localctx, 112, self.RULE_expression)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 620
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
        self.enterRule(localctx, 114, self.RULE_orExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 622
            self.andExpression()
            self.state = 627
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==67 or _la==68:
                self.state = 623
                _la = self._input.LA(1)
                if not(_la==67 or _la==68):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 624
                self.andExpression()
                self.state = 629
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
        self.enterRule(localctx, 116, self.RULE_andExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 630
            self.comparisonExpression()
            self.state = 635
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==66:
                self.state = 631
                self.match(C64PascalParser.AND)
                self.state = 632
                self.comparisonExpression()
                self.state = 637
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
        self.enterRule(localctx, 118, self.RULE_comparisonExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 638
            self.additiveExpression()
            self.state = 641
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if ((((_la - 71)) & ~0x3f) == 0 and ((1 << (_la - 71)) & 63) != 0):
                self.state = 639
                _la = self._input.LA(1)
                if not(((((_la - 71)) & ~0x3f) == 0 and ((1 << (_la - 71)) & 63) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 640
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
        self.enterRule(localctx, 120, self.RULE_additiveExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 643
            self.multiplicativeExpression()
            self.state = 648
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==77 or _la==78:
                self.state = 644
                _la = self._input.LA(1)
                if not(_la==77 or _la==78):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 645
                self.multiplicativeExpression()
                self.state = 650
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
        self.enterRule(localctx, 122, self.RULE_multiplicativeExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 651
            self.unaryExpression()
            self.state = 656
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while ((((_la - 64)) & ~0x3f) == 0 and ((1 << (_la - 64)) & 98307) != 0):
                self.state = 652
                _la = self._input.LA(1)
                if not(((((_la - 64)) & ~0x3f) == 0 and ((1 << (_la - 64)) & 98307) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 653
                self.unaryExpression()
                self.state = 658
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
        self.enterRule(localctx, 124, self.RULE_unaryExpression)
        self._la = 0 # Token type
        try:
            self.state = 662
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [69, 77, 78]:
                self.enterOuterAlt(localctx, 1)
                self.state = 659
                _la = self._input.LA(1)
                if not(((((_la - 69)) & ~0x3f) == 0 and ((1 << (_la - 69)) & 769) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 660
                self.unaryExpression()
                pass
            elif token in [54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 82, 91, 92, 93, 94, 95]:
                self.enterOuterAlt(localctx, 2)
                self.state = 661
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
        self.enterRule(localctx, 126, self.RULE_primaryExpression)
        self._la = 0 # Token type
        try:
            self.state = 682
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,73,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 664
                self.integerLiteral()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 665
                self.match(C64PascalParser.STRING_LITERAL)
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 666
                self.match(C64PascalParser.TRUE)
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 667
                self.match(C64PascalParser.FALSE)
                pass

            elif la_ == 5:
                self.enterOuterAlt(localctx, 5)
                self.state = 668
                self.match(C64PascalParser.NIL)
                pass

            elif la_ == 6:
                self.enterOuterAlt(localctx, 6)
                self.state = 669
                self.typeCastExpression()
                pass

            elif la_ == 7:
                self.enterOuterAlt(localctx, 7)
                self.state = 670
                self.designator()
                self.state = 671
                self.match(C64PascalParser.LPAREN)
                self.state = 673
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if ((((_la - 54)) & ~0x3f) == 0 and ((1 << (_la - 54)) & 4260901192703) != 0):
                    self.state = 672
                    self.argumentList()


                self.state = 675
                self.match(C64PascalParser.RPAREN)
                pass

            elif la_ == 8:
                self.enterOuterAlt(localctx, 8)
                self.state = 677
                self.designator()
                pass

            elif la_ == 9:
                self.enterOuterAlt(localctx, 9)
                self.state = 678
                self.match(C64PascalParser.LPAREN)
                self.state = 679
                self.expression()
                self.state = 680
                self.match(C64PascalParser.RPAREN)
                pass


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
        self.enterRule(localctx, 128, self.RULE_typeCastExpression)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 684
            self.builtinCastType()
            self.state = 685
            self.match(C64PascalParser.LPAREN)
            self.state = 686
            self.expression()
            self.state = 687
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
        self.enterRule(localctx, 130, self.RULE_builtinCastType)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 689
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 2287828610704211968) != 0)):
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
        self.enterRule(localctx, 132, self.RULE_integerLiteral)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 691
            _la = self._input.LA(1)
            if not(((((_la - 91)) & ~0x3f) == 0 and ((1 << (_la - 91)) & 7) != 0)):
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





