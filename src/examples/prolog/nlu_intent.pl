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

intent(doctor_can_help).

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
% Formen ...
% -------------------------------------------------------------------
simgular([ einzeln , einzahl  ]).
plural  ([ mehrmals, mehrzahl ]).

% -------------------------------------------------------------------
% Wort Beschreibungen
% -------------------------------------------------------------------
word_description(arbeit, "für das überleben an der Aebeit arbeiten").
word_description(arbeit, "jemanden ausbilden, um die Arbeit machen zu können.").

word_description(arbeiter, "für Arbeiten notwendige, fähigen Mensch einstellen.").
word_description(arbeiter, "für Arbeiten notwendige, fähige Menschen einstellen.").

% -------------------------------------------------------------------
% Substantive ...
% -------------------------------------------------------------------
word(arbeit,       noun, [der, singular]).
word(arbeit,       noun, [die, singular]).

word(arbeiter,     noun, [der, singular]).
word(arbeiter,     noun, [die, plural  ]).

word(arbeiten,     noun, [die, plural  ]).
word(arbeitsamt,   noun, [das, singular]).
word(arznei,       noun, [die, singular]).
word(arzneien,     noun, [die, plural  ]).
word(arzt,         noun, [der, singular]).
word(band,         noun, [das, singular]).
word(bande,        noun, [die, singular]).
word(bank,         noun, [die, singular]).
word(banknote,     noun, [die, singular]).
word(baum,         noun, [der, singular]).
word(brand,        noun, [der, singular]).
word(brauerei,     noun, [die, singular]).
word(brause,       noun, [die, singular]).
word(bruder,       noun, [der, singular]).
word(chef,         noun, [der, singular]).
word(dach,         noun, [das, singular]).
word(dachfenster,  noun, [das, singular]).
word(dachrinne,    noun, [die, singular]).
word(fenster,      noun, [das, singular]).
word(freund,       noun, [der, singular]).
word(geruch,       noun, [der, singular]).
word(gerüche,      noun, [die, singular]).
word(getränk,      noun, [das, singular]).
word(getränke,     noun, [die, plural  ]).
word(haus,         noun, [das, singular]).
word(hausnummer,   noun, [die, singular]).
word(haustür,      noun, [die, singular]).
word(hauswand,     noun, [die, singular]).
word(hund,         noun, [der, singular]).
word(kollege,      noun, [der, singular]).
word(krimi,        noun, [der, singular]).
word(kriminalamt,  noun, [das, singular]).
word(kriminalität, noun, [die, singular]).
word(kuchen,       noun, [der, singular]).
word(lehrer,       noun, [der, singular]).
word(mann,         noun, [der, singular]).
word(mensch,       noun, [der, singular]).
word(nachbar,      noun, [der, singular]).

word(note,         noun, [die, singular]).
word(noten,        noun, [die, plural  ]).

word(oma,          noun, [die, singular]).
word(onkel,        noun, [der, singular]).
word(ober,         noun, [der, singular]).
word(opa,          noun, [der, singular]).

word(programm,     noun, [das, singular]).
word(programme,    noun, [die, plural  ]).

word(quelle,       noun, [die, singular]).
word(quellen,      noun, [die, plural  ]).

word(raum,         noun, [der, singular]).
word(räume,        noun, [die, plural  ]).

word(rinne,        noun, [die, singular]).
word(sohle,        noun, [die, singular]).
word(sonde,        noun, [die, singular]).

word(sonne,        noun, [die, singular]).
word(sonnen,       noun, [die, plural  ]).
word(sonntag,      noun, [der, singular]).

word(stern,        noun, [der, singular]).

word(student,      noun, [der, singular]).
word(ufer,         noun, [das, singular]).
word(vater,        noun, [der, singular]).
word(zahn,         noun, [der, singular]).
word(zahnarzt,     noun, [der, singular]).
word(zange,        noun, [die, singular]).
word(zaun,         noun, [der, singular]).
word(zug,          noun, [der, singular]).
word(zunge,        noun, [die, singular]).
word(zwischenraum, noun, [der, singular]).

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
% DOCTOR_CAN_HELP
% -------------------------------------------------------------------
utterance(doctor_can_help, [der, arzt, kann, uns, helfen]).

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
% built-ins
% -------------------------------------------------------------------
% random(X).                    % X = Integer 0 .. 2147483647
% random(Max, X).               % 0 =< X < Max, Max > 0
% random_between(Min, Max, X).  % Min =< X =< Max
% -------------------------------------------------------------------
random_list_length([], 0).

random_list_length([_|Tail], N) :-
    random_list_length(Tail, N0),
    N is N0 + 1.

random_nth0(0, [Head|_], Head).

random_nth0(N, [_|Tail], Value) :-
    N > 0,
    N1 is N - 1,
    random_nth0(N1, Tail, Value).

random_member(List, Value) :-
    random_list_length(List, Count),
    random(Count, Index),
    random_nth0(Index, List, Value).

% -------------------------------------------------------------------
%response(ask_name_informal, 'Ich heiße Conny.').
%response(ask_name_informal, 'Mein Name ist Conny.').

%response(ask_name_formal, 'Ich heiße Conny.').
%response(ask_name_formal, 'Mein Name Conny.').

response(doctor_can_help, 'Das ist richtig.').

%response(greeting, 'Hallo!').
%response(greeting, 'Guten Tag!').
%response(greeting, 'Hallo, wie kann ich helfen?').

%response(goodbye, 'Auf Wiedersehen!').
%response(goodbye, 'Bis bald!').

%response(ask_status, 'Mir geht es gut.').
%response(ask_status, 'Danke der Nachfrage.').

response(ask_identity, 'Ich bin ein dialogorientiertes System.' ).

response(thanks, 'Gern geschehen.').
response(thanks, 'Keine Ursache.' ).

random_response(ask_name_informal, Answer) :-
    random_member([
        'Ich heiße Conny.',
        'Ich heiße Frank.',
        'Ich heiße Sonny.',
        'Ich heiße Peter.'
    ],  Answer).

random_response(ask_name_formal, Answer) :-
    random_member([
        'Mein Name ist Conny.',
        'Mein Name ist Frank.',
        'Mein Name ist Sonny.',
        'Mein Name ist Peter.'
    ],  Answer).

random_response(ask_status, Answer) :-
    random_member([
        'Mir geht es gut.',
        'Danke der Nachfrage.'
    ],  Answer).

random_response(greeting, Answer) :-
    random_member([
        'Hallo!',
        'Guten Tag!',
        'Schön dich zu sehen.',
        'Hallo, wie kann ich helfen?'
    ],  Answer).

random_response(goodbye, Answer) :-
    random_member([
        'Auf Wiedersehen!',
        'Bis bald!',
        'Machs gut!'
    ],  Answer).

respond(Words, Answer) :-
    detect_intent(Words, Intent),
    random_response(Intent, Answer).

%respond(Words, Answer) :-
%    detect_intent(Words, Intent),
%    response(Intent, Answer).

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
%detect_intent(Words, Intent) :-
%    utterance(Intent, Words).

detect_intent(Words, Intent) :-
    semantic_list(Words, Semantics),
    intent_rule(Semantics, Intent).

% -------------------------------------------------------------------
% ?- detect_intent([wie, heisst, du], Intent).
% ?- detect_intent([wie, heissen, sie], Intent).
% ?- respond([wie, heisst, du], Answer).
% ?- respond([der, arzt, kann, uns, helfen], Answer).

% ?- word(arbeit, noun, Form).
% Form = [der, singular] ;
% Form = [die, singular] .

