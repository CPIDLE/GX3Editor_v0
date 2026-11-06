<#
Build a GX Works3 project from a rung spec in two versions:
  <Name>_uncompiled.gx3  ladder written by tools\gx3gen.py, not converted
  <Name>_compiled.gx3    same file after GX Works3 "Rebuild All" + save
Then reads ConvertData\Progress.txt from the saved file to report errors.

Usage:  powershell -ExecutionPolicy Bypass -File tools\build.ps1 [-Spec tools\conveyor.py] [-Name FX5U_conveyor] [-Base TEST_0.gx3]
Do not touch the mouse/keyboard while GX Works3 is being driven (~30 s).
#>
param(
    [string]$Spec = "$PSScriptRoot\conveyor.py",
    [string]$Name = 'FX5U_conveyor',
    [string]$Base = "$PSScriptRoot\..\TEST_0.gx3",
    [string]$Exe  = 'C:\Program Files (x86)\MELSOFT\GPPW3\GXW3.exe'
)
$ErrorActionPreference = 'Stop'
$root = Resolve-Path "$PSScriptRoot\.."
$uncompiled = Join-Path $root "${Name}_uncompiled.gx3"
$compiled   = Join-Path $root "${Name}_compiled.gx3"

if (Get-Process GXW3 -ErrorAction SilentlyContinue) { throw 'GX Works3 is already running. Close it first.' }

# 1. generate
& python -I $Spec (Resolve-Path $Base) $uncompiled
if ($LASTEXITCODE -ne 0) { throw 'generation failed' }
Copy-Item $uncompiled $compiled -Force

# helpers ---------------------------------------------------------------
Add-Type -AssemblyName System.Windows.Forms, UIAutomationClient, UIAutomationTypes
Add-Type @"
using System; using System.Runtime.InteropServices;
public class GxW {
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
 [DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, int f, int e);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
 [DllImport("user32.dll")] public static extern void mouse_event(int f, int x, int y, int d, int e);
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }
"@
[GxW]::SetProcessDPIAware() | Out-Null
$A = [System.Windows.Automation.AutomationElement]; $TS = [System.Windows.Automation.TreeScope]

function Focus-Gx {
    $p = Get-Process GXW3 | Where-Object MainWindowHandle -ne 0 | Select-Object -First 1
    for ($i = 0; $i -lt 5; $i++) {
        [GxW]::keybd_event(0x12, 0, 0, 0); [GxW]::keybd_event(0x12, 0, 2, 0)   # tap Alt: lifts the foreground lock
        [GxW]::ShowWindow($p.MainWindowHandle, 3) | Out-Null
        [GxW]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
        Start-Sleep -Milliseconds 600
        if ([GxW]::GetForegroundWindow() -eq $p.MainWindowHandle) { return }
    }
    throw 'could not bring GX Works3 to the foreground'
}
function Find-Dialog([string]$title) {
    $c = New-Object System.Windows.Automation.AndCondition(
        (New-Object System.Windows.Automation.PropertyCondition($A::NameProperty, $title)),
        (New-Object System.Windows.Automation.PropertyCondition($A::ClassNameProperty, '#32770')))
    return $A::RootElement.FindFirst($TS::Descendants, $c)
}
function Wait-Dialog([string]$title, [int]$timeoutSec) {
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) { $d = Find-Dialog $title; if ($d) { return $d }; Start-Sleep -Milliseconds 500 }
    return $null
}
function Click-In($dialog, [string[]]$patterns) {
    # wildcard match on the button name; keep this file ASCII-only (PowerShell 5.1 reads it as ANSI)
    $all = $dialog.FindAll($TS::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($n in $patterns) {
        $b = $all | Where-Object { $_.Current.Name -like $n } | Select-Object -First 1
        if ($b) {
            $r = $b.Current.BoundingRectangle
            [GxW]::SetCursorPos([int]($r.X + $r.Width / 2), [int]($r.Y + $r.Height / 2)); Start-Sleep -Milliseconds 200
            [GxW]::mouse_event(2, 0, 0, 0, 0); [GxW]::mouse_event(4, 0, 0, 0, 0)
            return $true
        }
    }
    return $false
}

# 2. open in GX Works3 ----------------------------------------------------
Start-Process -FilePath $Exe -ArgumentList "`"$compiled`""
$t0 = Get-Date
do { Start-Sleep 2; $p = Get-Process GXW3 -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -match [regex]::Escape("${Name}_compiled") } } until ($p -or ((Get-Date) - $t0).TotalSeconds -gt 120)
if (-not $p) { throw 'GX Works3 did not open the project' }
Start-Sleep 6
$titleBefore = (Get-Process GXW3).MainWindowTitle

# 3. Rebuild All (Shift+Alt+F4), confirm with OK ---------------------------
$dlg = $null
for ($i = 0; $i -lt 3 -and -not $dlg; $i++) {
    Focus-Gx
    [System.Windows.Forms.SendKeys]::SendWait('+%{F4}')
    $dlg = Wait-Dialog 'Rebuild All' 8
}
if (-not $dlg) { throw 'Rebuild All dialog did not appear' }
if (-not (Click-In $dlg @('OK'))) { throw 'OK button not found' }
$t0 = Get-Date
do { Start-Sleep 2; $title = (Get-Process GXW3).MainWindowTitle } until (($title -ne $titleBefore -and $title -match '\d+Step\]') -or ((Get-Date) - $t0).TotalSeconds -gt 90)
if ($title -eq $titleBefore) { throw "Rebuild All did not change the step count ($title)" }
"converted: $title"
Start-Sleep 3

# 4. close, answering Yes to "save the project?" ----------------------------
(Get-Process GXW3).CloseMainWindow() | Out-Null
$ask = Wait-Dialog 'MELSOFT GX Works3' 10
if (-not $ask) { throw 'save prompt did not appear' }
if (-not (Click-In $ask @('*(Y)*', 'Yes'))) { throw 'Yes button not found' }
$t0 = Get-Date
do { Start-Sleep 1 } until (-not (Get-Process GXW3 -ErrorAction SilentlyContinue) -or ((Get-Date) - $t0).TotalSeconds -gt 20)

# 5. report from the saved file -------------------------------------------
$py = @'
import sys, zipfile, sqlite3, tempfile, os
z = zipfile.ZipFile(sys.argv[1])
files = {i.orig_filename.replace('/', '\\'): i for i in z.infolist()}
log = z.read(files['ConvertData\\Progress.txt']).decode('utf-8-sig', 'replace')
print([l for l in log.splitlines() if 'Convert All End' in l][-1].strip('= '))
for n, i in files.items():
    if n.endswith('_LDDB.db'):
        p = os.path.join(tempfile.mkdtemp(), 'x.db'); open(p, 'wb').write(z.read(i))
        rows = sqlite3.connect(p).execute('select count(*), sum(translated) from LadderBlocks').fetchone()
        print('blocks', rows[0], 'converted', rows[1])
'@
$tmp = Join-Path $env:TEMP 'gx3_build_report.py'; Set-Content -Encoding utf8 $tmp $py
& python -I $tmp $compiled
"uncompiled: $uncompiled"
"compiled:   $compiled"
