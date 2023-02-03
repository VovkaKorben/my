cd C:\ais\my\
del ais.exe
@rem C:\msys64\mingw64\bin\gcc.exe -Wall -g File2.cpp -oais.exe -L.\lib -lsigil.dll -I.\include
C:\msys64\mingw64\bin\g++.exe -Wall -g File2.cpp -oais.exe -L.\lib -lsigil.dll -I.\include


@rem gcc -Wall -g x.cpp -o x.exe -L./lib -lsigil.dll -lstdc++ -I./include
@rem -l.\lib\libsigil.dll.a
@rem	-L.\lib
@rem                "-IC:\\ais\\sigil",
@rem                "-l\\lib\\libsigil.dll.a",
@rem                // "-l C:\\ais\\sigil\\libsigil.dll
pause