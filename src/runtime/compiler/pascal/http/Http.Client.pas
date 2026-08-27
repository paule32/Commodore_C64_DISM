// ---------------------------------------------------------------------------
// File:   Http.Client.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
unit Http.Client;

interface
uses System, Windows;

type
    THttpResponse = class(TObject)
    public
        constructor Create;
        destructor Destroy; override;
    end;
    
type
    THttpClient = class(TObject)
    private
        FResponse: THttpResponse;
        FAUrl: String;
        FAPort: Word;
    protected
        function GetResponse: THttpResponse;
        procedure SetResponse(AObject: THttpResponse);
    public
        constructor Create;
        constructor Create(AUrl: String);
        constructor Create(AUrl: String; APort: Word);
        destructor Destroy; override;
    published
        property URL: String read FAUrl write FAUrl;
        property Port: Word read FAPort write FAPort;
        property Response: THttpResponse read GetResponse write SetResponse;
    end;

implementation
const DLL_FILE = 'libruntime_mini.dll';

{ THttpResponse }

constructor THttpResponse.Create;
begin
    inherited Create;
end;
destructor THttpResponse.Destroy;
begin
    inherited Destroy;
end;

{ THttpClient }

constructor THttpClient.Create;
begin
    inherited Create;
end;
constructor THttpClient.Create(AUrl: String);
begin
    inherited Create;
    FAUrl := AUrl;
    FAPort := 80;
    try
        FResponse := THttpResponse.Create;
    except
        WriteLn('error: not enough memory.');
        FResponse.Free;
        ExitProcess(1);
    end;
end;
constructor THttpClient.Create(AUrl: String; APort: Word);
begin
    inherited Create;
    FAUrl  := AUrl;
    FAPort := Word(APort);
end;
destructor THttpClient.Destroy;
begin
    FResponse.Free;
    inherited Destroy;
end;

procedure THttpClient.SetResponse(AObject: THttpResponse);
begin
    try
        if (AObject <> nil) and (FResponse <> AObject) then
        begin
            FResponse.Free;
            FResponse := AObject;
        end;
    except
        WriteLn('error: not enough memory.');
        ExitProcess(1);
    end;
end;

function THttpClient.GetResponse: THttpResponse;
begin
end;

end.
