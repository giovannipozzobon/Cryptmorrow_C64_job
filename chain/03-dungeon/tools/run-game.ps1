param(
    [ValidateSet('Build','Play','Verify')][string]$Mode = 'Play',
    [ValidateSet('6581','8580')][string]$Model = '6581',
    [string]$Python = '',
    [string]$Assembler = '',
    [string]$Vice = ''
)
# Cryptmorrow: build a step of the book, or the complete game, and play
# it in VICE. Run it from the folder of a step (chain/NN-name) or from
# the root of the package, the complete game (game/):
#   Build   write the data (game/assets/build_assets.py), check that no
#           line of the sources is longer than 60 characters
#           (tools/check_lines.py) and assemble with 64tass into
#           game/build: cryptmorrow.prg, .lst and .lbl;
#   Play    build, then start the program in VICE (x64sc): a PAL C64
#           with the SID chosen by -Model, joystick 2 on the keypad;
#   Verify  build, then run the test of the complete game
#           (tests/verify_game.py), from the root of the package.
# 64tass, x64sc and python are looked for on the PATH; -Assembler,
# -Vice and -Python give their full paths instead.
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent

function Find-Tool([string]$Given, [string[]]$Names, [string]$Switch) {
    if ($Given) {
        if (!(Test-Path -LiteralPath $Given)) { throw "Not found: $Given" }
        return $Given
    }
    foreach ($name in $Names) {
        $found = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($found) { return $found.Source }
    }
    throw "$($Names[0]) is not on the PATH: add its folder to the PATH, or give its full path with $Switch."
}

$Python = Find-Tool $Python @('python', 'python3', 'py') '-Python'
$Assembler = Find-Tool $Assembler @('64tass') '-Assembler'
if ($Mode -ne 'Build') { $Vice = Find-Tool $Vice @('x64sc') '-Vice' }
Push-Location $root
try {
    New-Item -ItemType Directory -Force -Path 'game/build' | Out-Null
    & $Python 'game/assets/build_assets.py'
    if ($LASTEXITCODE -ne 0) { throw 'The data of game/assets could not be built: see the message above.' }
    & $Python 'tools/check_lines.py'
    if ($LASTEXITCODE -ne 0) { throw 'A line of the sources is longer than 60 characters.' }
    & $Assembler --cbm-prg -Wall -Werror --vice-labels-numeric -l game/build/cryptmorrow.lbl -L game/build/cryptmorrow.lst -o game/build/cryptmorrow.prg game/src/main.asm
    if ($LASTEXITCODE -ne 0) { throw '64tass stopped: its message names the file and the line.' }
    if ($Mode -eq 'Build') {
        if (Test-Path -LiteralPath 'tools/memory_map.py') {
            & $Python 'tools/memory_map.py'
            if ($LASTEXITCODE -ne 0) { throw 'The memory map could not be made.' }
        }
    } elseif ($Mode -eq 'Play') {
        $engine = @{ '6581' = '256'; '8580' = '257' }[$Model]
        $arguments = @('-default','-pal','-sound','-sidenginemodel',$engine,'+VICIIvcache',
            '-autostartprgmode','1','-joydev2','1','-autostart','game/build/cryptmorrow.prg')
        Start-Process -FilePath $Vice -ArgumentList $arguments -WorkingDirectory $root
    } elseif ($Mode -eq 'Verify') {
        if (!(Test-Path -LiteralPath 'tests/verify_game.py')) {
            throw 'Verify works from the root of the package. For a step, run python tests/verify_step.py or tests/verify_game.py there (chapter 14).'
        }
        & $Python 'tests/verify_game.py' --vice $Vice
        if ($LASTEXITCODE -ne 0) { throw 'The test of the game failed: see evidence/game-test.json.' }
    }
} finally {
    Pop-Location
}
