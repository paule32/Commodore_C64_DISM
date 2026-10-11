% Stage 290 - allgemeine Random-Built-ins

list_length([], 0).
list_length([_|Tail], N) :-
    list_length(Tail, N0),
    N is N0 + 1.

nth0(0, [Head|_], Head).
nth0(N, [_|Tail], Value) :-
    N > 0,
    N1 is N - 1,
    nth0(N1, Tail, Value).

random_member(List, Value) :-
    list_length(List, Count),
    random(Count, Index),
    nth0(Index, List, Value).

random_response(ask_name_informal, Answer) :-
    random_member([
        'Ich heiße Conny.',
        'Ich heiße Frank.',
        'Ich heiße Sonny.',
        'Ich heiße Peter.'
    ], Answer).

respond(Words, Answer) :-
    detect_intent(Words, Intent),
    random_response(Intent, Answer).

utterance(ask_name_informal, [wie, heisst, du]).
detect_intent(Words, Intent) :-
    utterance(Intent, Words).

?- respond([wie, heisst, du], Answer).
