if not exist samples (
    mkdir samples
    cd samples
    if not exist deu (
        mkdir deu
        cd deu
        if not exist wav (
          mkdir wav
          cd ..
        )
    )
    if not exist enu (
        mkdir enu
        cd enu
        if not exist wav (
          mkdir wav
          cd ../..
        )
    )
)

rem echo duu. | ./piper.exe --model de_DE-thorsten-low.onnx --output_file samples/deu/wav/du.wav
python speechConvert.py --text "Guten"          -a GUTEN        -l de_DE --quality low -gz -oc samples/deu/deutsch.spc
python speechConvert.py --text "Guten Morgen"   -a GUTENMORGEN  -l de_DE --quality low -gz -oc samples/deu/deutsch.spc
python speechConvert.py --text "heute"          -a HEUTE        -l de_DE --quality low -gz -oc samples/deu/deutsch.spc
python speechConvert.py --text "Morgen"         -a MORGEN       -l de_DE --quality low -gz -oc samples/deu/deutsch.spc
