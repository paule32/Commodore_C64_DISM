::msgfmt -o dbase.mo dbase.po
::msgfmt -o doxygen.mo doxygen.po

pyrcc5 -o de_locales_rc.py de_locales.qrc
pyrcc5 -o images_rc.py images_rc.qrc
