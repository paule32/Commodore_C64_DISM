% -------------------------------------------------------------------
% Intent Knowledge Base
% (c) 2026 by Jens Kallup - paule32
% all rights reserved.
% -------------------------------------------------------------------
%
% extern input:   wie.heißt.du
% intern input:   [wie, heisst, du]
% -------------------------------------------------------------------

% -------------------------------------------------------------------
% Application default settings ...
% -------------------------------------------------------------------
set_stream(user_output, encoding(cp1252)).  % Windows code page

% -------------------------------------------------------------------
% Intent Definitionen
% -------------------------------------------------------------------
intent(ask_name_informal).
intent(ask_name_formal).
intent(ask_name_general).

intent(greeting).
intent(goodbye).
intent(ask_status).
intent(ask_identity).
intent(thanks).

% -------------------------------------------------------------------
% Intent Beschreibungen
% -------------------------------------------------------------------
intent_description(ask_name_informal, 'Der Benutzer fragt informell nach dem Namen.').
intent_description(ask_name_formal,   'Der Benutzer fragt höflich nach dem Namen.').
intent_description(ask_name_general,  'Der Benutzer fragt allgemein nach einem Namen.').
intent_description(greeting,          'Der Benutzer begrüßt das System.').
intent_description(goodbye,           'Der Benutzer verabschiedet sich.').
intent_description(ask_status,        'Der Benutzer fragt nach dem Befinden.').
intent_description(ask_identity,      'Der Benutzer fragt, wer oder was das System ist.').
intent_description(thanks,            'Der Benutzer bedankt sich.').

% -------------------------------------------------------------------
% Fragewörter
% -------------------------------------------------------------------
word(wie, question).
word(was, question).
word(wer, question).
word(wo, question).
word(wann, question).
word(warum, question).
word(welche, question).
word(welcher, question).
word(welches, question).

% -------------------------------------------------------------------
% Personalpronomen
% -------------------------------------------------------------------
word(ich, pronoun).
word(du, pronoun).
word(er, pronoun).
word(sie, pronoun).
word(wir, pronoun).
word(ihr, pronoun).

% -------------------------------------------------------------------
% Besitz
% -------------------------------------------------------------------
word(mein, possessive).
word(meine, possessive).
word(dein, possessive).
word(deine, possessive).
word(ihr, possessive).
word(ihre, possessive).

% -------------------------------------------------------------------
% Verben
% -------------------------------------------------------------------
word(heisst, verb).
word(heissen, verb).
word(ist, verb).
word(sind, verb).
word(geht, verb).
word(bist, verb).
word(hast, verb).
word(haben, verb).
word(kannst, verb).
word(koennen, verb).

% -------------------------------------------------------------------
semantic(heisst, name).
semantic(heissen, name).
semantic(name, name).

semantic(du, informal).
semantic(dein, informal).

semantic(sie, formal).
semantic(ihr, formal).

semantic(wie, question).
semantic(wer, question).
semantic(was, question).

% -------------------------------------------------------------------
% Wortliste -> Semantikliste
% -------------------------------------------------------------------
semantic_list([], []).
semantic_list(
    [Word    | Words],
    [Meaning | Meanings]
    ) :-
    semantic     (Word , Meaning ),
    semantic_list(Words, Meanings).

% -------------------------------------------------------------------
% ASK_NAME_INFORMAL
% -------------------------------------------------------------------
utterance(ask_name_informal, [wie, heisst, du]).
utterance(ask_name_informal, [wie, ist, dein, name]).
utterance(ask_name_informal, [was, ist, dein, name]).
utterance(ask_name_informal, [wer, bist, du]).
utterance(ask_name_informal, [sag, mir, deinen, namen]).

% -------------------------------------------------------------------
% ASK_NAME_FORMAL
% -------------------------------------------------------------------
utterance(ask_name_formal, [wie, heissen, sie]).
utterance(ask_name_formal, [wie, ist, ihr, name]).
utterance(ask_name_formal, [was, ist, ihr, name]).
utterance(ask_name_formal, [wer, sind, sie]).

% -------------------------------------------------------------------
% ASK_NAME_GENERAL
% -------------------------------------------------------------------
utterance(ask_name_general, [wie, heisst]).
utterance(ask_name_general, [wie, heissen]).

% -------------------------------------------------------------------
% Begrüßungen
utterance(greeting, [hallo]).
utterance(greeting, [hi]).
utterance(greeting, [hey]).
utterance(greeting, [guten, morgen]).
utterance(greeting, [guten, tag]).
utterance(greeting, [guten, abend]).
utterance(greeting, [servus]).

% Verabschiedungen
utterance(goodbye, [tschüss]).
utterance(goodbye, [auf, wiedersehen]).
utterance(goodbye, [bis, später]).
utterance(goodbye, [bis, bald]).
utterance(goodbye, [bye]).

% Befinden
utterance(ask_status, [wie, geht, es, dir]).
utterance(ask_status, [wie, gehts]).
utterance(ask_status, [wie, geht, es]).
utterance(ask_status, [alles, gut]).
utterance(ask_status, [wie, fühlst, du, dich]).

% Identität
utterance(ask_identity, [wer, bist, du]).
utterance(ask_identity, [was, bist, du]).
utterance(ask_identity, [was, kannst, du]).
utterance(ask_identity, [wer, seid, ihr]).

% -------------------------------------------------------------------
response(ask_name_informal, 'Ich heiße dBase2Many.').
response(ask_name_informal, 'Mein Name ist dBase2Many.').

response(ask_name_formal, 'Ich heiße dBase2Many.').
response(ask_name_formal, 'Mein Name ist dBase2Many.').

response(greeting, 'Hallo!').
response(greeting, 'Guten Tag!').
response(greeting, 'Hallo, wie kann ich helfen?').

response(goodbye, 'Auf Wiedersehen!').
response(goodbye, 'Bis bald!').

response(ask_status, 'Mir geht es gut.').
response(ask_status, 'Danke der Nachfrage.').

response(ask_identity, 'Ich bin ein dialogorientiertes System.' ).

response(thanks, 'Gern geschehen.').
response(thanks, 'Keine Ursache.' ).

% -------------------------------------------------------------------
%detect_intent(Words, Intent) :-
%    utterance(Intent, Words).

respond(Words, Answer) :-
    detect_intent(Words, Intent),
    response(Intent, Answer).

% -------------------------------------------------------------------
dot_utterance(ask_name_informal, 'wie.heißt.du').
dot_utterance(ask_name_informal, 'wie.ist.dein.name').

dot_utterance(ask_name_formal,   'wie.heißen.sie').
dot_utterance(ask_name_formal,   'wie.ist.ihr.name').

dot_utterance(ask_status, 'wie.geht.es.dir').

dot_utterance(greeting, 'guten.tag').

% -------------------------------------------------------------------
intent_rule([question, name, informal], ask_name_informal).
intent_rule([question, name, formal  ], ask_name_formal).

% -------------------------------------------------------------------
detect_intent(Words, Intent) :-
    semantic_list(Words, Semantics),
    intent_rule(Semantics, Intent).

% -------------------------------------------------------------------
%?- detect_intent([wie, heisst, du], Intent).
%?- detect_intent([wie, heissen, sie], Intent).
%?- respond([wie, heisst, du], Answer).
