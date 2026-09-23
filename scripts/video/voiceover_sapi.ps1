$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$out = Join-Path $root 'runs\delivery\video\voice_raw'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$lines = @(
  'At three A M, mid ocean, one engineer may be watching an entire ship.',
  'N Vidia D G X Spark is the local compute behind Ship Mind, powered by the G B ten Grace Blackwell Superchip and unified memory.',
  'It combines acoustic changes, gauge readings, radar detections, sonar evidence, and route deviation into one evidence bound briefing.',
  'Ask how things are now. The local Kwen model, served by V L L M on Spark, answers with evidence and keeps the human in review.',
  'D G X Spark, N Vidia Agent Skills, Deep Stream, Step Fun, Kwen, and V L L M form one reproducible agent workload.',
  'Synthetic inputs. Real Spark compute. Intelligence stays on board. Ship Mind.'
)
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Zira Desktop')
$s.Rate = -2
$s.Volume = 100
for ($i = 0; $i -lt $lines.Count; $i++) {
  $path = Join-Path $out ('segment-{0:D2}.wav' -f ($i + 1))
  $s.SetOutputToWaveFile($path)
  $s.Speak($lines[$i])
  $s.SetOutputToNull()
}
$s.Dispose()
Write-Output $out
