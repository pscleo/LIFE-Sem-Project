@echo off
set COMPILER=cl 
				set COMPFLAGS=/c  /GR /W3 /EHs /nologo /MD /D_CRT_SECURE_NO_DEPRECATE /D_SCL_SECURE_NO_DEPRECATE /D_SECURE_SCL=0   /DMATLAB_MEX_FILE -I"C:\Program Files (x86)\MATLAB\R2014a\extern\include" -I"C:\Program Files (x86)\MATLAB\R2014a\simulink\include"  /D_CRT_SECURE_NO_DEPRECATE /D_SCL_SECURE_NO_DEPRECATE /D_SECURE_SCL=0   /DMATLAB_MEX_FILE  /DMATLAB_MEX_FILE 
				set OPTIMFLAGS=/O2 /Oy- /DNDEBUG 
				set DEBUGFLAGS=/Z7 
				set LINKER=link 
				set LINKFLAGS= /nologo /manifest  /incremental:NO /export:%ENTRYPOINT% /DLL /LIBPATH:"C:\Program Files (x86)\MATLAB\R2014a\extern\lib\win32\microsoft" libmx.lib libmex.lib libmat.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib  /EXPORT:mexFunction 
				set LINKDEBUGFLAGS=/debug /PDB:"%OUTDIR%%MEX_NAME%.mexw32.pdb" 
				set NAME_OUTPUT=/out:"%OUTDIR%%MEX_NAME%%MEX_EXT%"
set PATH=C:\Program Files (x86)\Microsoft Visual Studio 11.0\VC\Bin;C:\Program Files (x86)\Microsoft Visual Studio 11.0\VC\Bin\VCPackages;C:\Program Files (x86)\Microsoft Visual Studio 11.0\Common7\IDE;C:\Program Files (x86)\Microsoft Visual Studio 11.0\Common7\Tools;C:\Program Files (x86)\Windows Kits\8.0\\bin\x86;;%MATLAB_BIN%;%PATH%
set INCLUDE=C:\Program Files (x86)\Microsoft Visual Studio 11.0\VC\INCLUDE;C:\Program Files (x86)\Windows Kits\8.0\\include\shared;C:\Program Files (x86)\Windows Kits\8.0\\include\um;C:\Program Files (x86)\Windows Kits\8.0\\include\winrt;;C:\Program Files (x86)\MATLAB\R2014a\extern\include;%INCLUDE%
set LIB=C:\Program Files (x86)\Microsoft Visual Studio 11.0\VC\LIB;C:\Program Files (x86)\Microsoft Visual Studio 11.0\VC\ATLMFC\LIB;C:\Program Files (x86)\Windows Kits\8.0\\lib\win8\um\x86;;%LIB%
set LIBPATH=C:\Program Files (x86)\Microsoft Visual Studio 11.0\VC\Lib;C:\Program Files (x86)\Microsoft Visual Studio 11.0\VC\ATLMFC\LIB;C:\Program Files (x86)\Windows Kits\8.0\\lib\win8\um\x86;C:\Program Files (x86)\MATLAB\R2014a\extern\lib\win32;;%LIBPATH%

nmake -f AttitudeLoop_sfun.mak
