@echo off
rem launch.cmd -- start one vibrobeast MCP server on Windows, finding Python by itself.
rem
rem Copyright 2026 Bryant Frankford <nathanielfrankford@gmail.com> and Corwin Brust <corwin@bru.st>
rem and Contributors.  Bryant first: the finder below is his (Tavern-Setup), reshaped.
rem SPDX-License-Identifier: GPL-3.0-or-later OR LGPL-3.0-or-later
rem Written by Mentat (for Corwin; claude-opus-5-5), 2026-10-08.
rem
rem The finder is modeled on Bryant Frankford's Tavern-Setup (:TVL_FIND and :TVL_TRY in the
rem SETUP_BATCH_TEMPLATE of tavern 2.3.1, Copyright 2026 Bryant Frankford
rem <nathanielfrankford@gmail.com>, written with Alfred (for Bryant; claude-opus-5-5)): try each
rem candidate by RUNNING it, and keep the first that answers with a new enough Python.  The
rem "py -3 ... print(sys.executable)" capture below is his line, with his 3.10 floor kept.
rem
rem Claude Desktop starts this as:   cmd /d /c <plugin>\servers\launch.cmd SERVER
rem Nobody edits JSON to make it work (accessibility, Corwin's ruling D3).  The order is:
rem   1  VIBROBEAST_PYTHON, if set           (the person's own choice, used as given)
rem   2  py -3                               (the Windows Python launcher)
rem   3  python3, then python, on PATH       (skipping any under \WindowsApps\: the Store stub)
rem   4  C:\msys64\ucrt64, mingw64, clang64  (bin\python3.exe, then bin\python.exe)
rem   5  %LOCALAPPDATA%\Programs\Python\Python3*\python.exe
rem   6  %ProgramFiles%\Python3*\python.exe  (an all-users install)
rem A candidate counts only if it runs and reports Python 3.10 or newer: one floor for every
rem server, the floor of the Tavern the plugin carries (Python 3.9 reached its end of life in
rem October 2025).  An older Python that runs is remembered, so the last sentence can say "too
rem old" instead of "none found".  Nothing goes to stdout
rem but the server itself: stdout is the JSON-RPC channel, so every word from here is on stderr,
rem which the Desktop keeps in its log.
rem Spec: tests/launch-cmd-SPEC.txt.  Kit: tests/launch-cmd-tests.sh.
setlocal EnableExtensions DisableDelayedExpansion
set "VB_HERE=%~dp0"
set "VB_PY="
set "VB_CAND="
set "VB_OLD="
if "%~1"=="" goto :VB_USAGE

rem 1  VIBROBEAST_PYTHON
if defined VIBROBEAST_PYTHON call :VB_TRY_EXE "%VIBROBEAST_PYTHON%" named
if defined VB_PY goto :VB_RUN

rem 2  py -3
call :VB_TRY_PYLAUNCHER
if defined VB_PY goto :VB_RUN

rem 3  python3, then python, on PATH -- every match, in PATH order, never the WindowsApps stub
for /f "delims=" %%P in ('where python3 2^>nul') do if not defined VB_PY call :VB_TRY_EXE "%%P"
if defined VB_PY goto :VB_RUN
for /f "delims=" %%P in ('where python 2^>nul') do if not defined VB_PY call :VB_TRY_EXE "%%P"
if defined VB_PY goto :VB_RUN

rem 4  MSYS2 trees
for %%R in (ucrt64 mingw64 clang64) do if not defined VB_PY call :VB_TRY_EXE "C:\msys64\%%R\bin\python3.exe"
for %%R in (ucrt64 mingw64 clang64) do if not defined VB_PY call :VB_TRY_EXE "C:\msys64\%%R\bin\python.exe"
if defined VB_PY goto :VB_RUN

rem 5  python.org installs for this user
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if not defined VB_PY call :VB_TRY_EXE "%%~fD\python.exe"
if defined VB_PY goto :VB_RUN

rem 6  python.org installs for all users
for /d %%D in ("%ProgramFiles%\Python3*") do if not defined VB_PY call :VB_TRY_EXE "%%~fD\python.exe"
if defined VB_PY goto :VB_RUN

if defined VB_OLD goto :VB_TOO_OLD
>&2 echo vibrobeast: the %~1 server cannot start because no Python 3.10 or newer was found on this computer. Install Python 3.10 or newer from https://www.python.org/downloads/windows/ - or MSYS2's python - then restart Claude. Nothing needs editing: the plugin finds it by itself.
exit /b 1

:VB_TOO_OLD
>&2 echo vibrobeast: the %~1 server cannot start because the only Python found on this computer is too old ("%VB_OLD%"); it needs Python 3.10 or newer. Install Python 3.10 or newer from https://www.python.org/downloads/windows/ - or update MSYS2's python - then restart Claude. Nothing needs editing: the plugin finds the newer one by itself.
exit /b 1

:VB_RUN
>&2 echo vibrobeast: starting the %~1 server with "%VB_PY%"
"%VB_PY%" -I -B "%VB_HERE%launch.py" "%~1"
exit /b %errorlevel%

:VB_USAGE
>&2 echo usage: launch.cmd SERVER   or   launch.cmd --list
exit /b 2

rem ---- subroutines ------------------------------------------------------------------------
:VB_TRY_EXE
rem %1 = a full path to a python.exe (or, with %2 = named, whatever VIBROBEAST_PYTHON says: a
rem path or one command name, used as given -- no WindowsApps skip, no exist test; the person
rem chose it).  Sets VB_PY when it runs and reports Python 3.10 or newer; sets VB_OLD when it runs
rem and reports an older one (exit 3 from the probe, and only 3).
set "VB_CAND=%~1"
if not defined VB_CAND exit /b 0
if "%~2"=="named" goto :VB_PROBE
if not "%VB_CAND:\WindowsApps\=%"=="%VB_CAND%" exit /b 0
if not exist "%VB_CAND%" exit /b 0
:VB_PROBE
"%VB_CAND%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 3)" >nul 2>&1 && goto :VB_NEW_ENOUGH
if "%errorlevel%"=="3" set "VB_OLD=%VB_CAND%"
exit /b 0
:VB_NEW_ENOUGH
set "VB_PY=%VB_CAND%"
exit /b 0

:VB_TRY_PYLAUNCHER
where py >nul 2>&1 || exit /b 0
set "VB_CAND="
for /f "usebackq delims=" %%I in (`py -3 -c "import sys; print(sys.executable if sys.version_info >= (3, 10) else '')" 2^>nul`) do set "VB_CAND=%%I"
if defined VB_CAND call :VB_TRY_EXE "%VB_CAND%"
exit /b 0
