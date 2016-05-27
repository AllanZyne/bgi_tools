cd %~dp0
cl /nologo /O2 /Oi /GL /W3 cbg.c decrypt.c dsc.c /LD /link /def:arc.def /out:"arc.dll"
copy /y arc.dll ../arc.dll