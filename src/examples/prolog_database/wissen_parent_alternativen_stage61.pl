% Stage 61: Parent -> Kind-Alternativen im Wissen-Datenbank-Browser.
% Klick auf obst/3 erzeugt [obst ▼].
%   obst ▼              -> apfel, birne
%   obst -> apfel ▼     -> essbar, gesund
%   ... -> gesund ▼     -> gruen, rot

obst(apfel, gesund, rot).
obst(apfel, gesund, gruen).
obst(apfel, essbar, ja).
obst(birne, gesund, gruen).
