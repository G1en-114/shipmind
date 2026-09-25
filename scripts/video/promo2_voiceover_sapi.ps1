$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$out = Join-Path $root 'runs\delivery\video\promo2_voice_raw'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$lines = @(
  '凌晨三点，一次陌生振动打破了船舶稳定的节奏。',
  'ShipMind 不从结论开始。它先保存声学、表盘、雷达与航线的原始观测。',
  '每一条异常，都能回到时间、来源和计算过程。',
  '同一事件会在不同阈值下逐级比较。哪里仍是信号，哪里开始值得关注，一目了然。',
  '它给出的不是一个武断答案，而是观察、推断与行动三层判断尺度。',
  '这些判断由 DGX Spark 上的本地模型、Agent Skills、DeepStream、Qwen 与 vLLM 共同完成。',
  '过程被记录，失败不会被隐藏，关键变化交给值班人员复核。',
  'AI 辅助不等于自动定论。它让分散信号成为可复核的判断，让每一次值守更安全、更从容。ShipMind。'
)
$speaker = New-Object -ComObject SAPI.SpVoice
$voiceToken = $speaker.GetVoices() | Where-Object { $_.GetDescription() -like 'Microsoft Huihui*' } | Select-Object -First 1
if ($null -eq $voiceToken) { throw 'Microsoft Huihui Desktop voice is unavailable.' }
$speaker.Voice = $voiceToken
$speaker.Rate = -1
$speaker.Volume = 100
for ($i = 0; $i -lt $lines.Count; $i++) {
  $path = Join-Path $out ('segment-{0:D2}.wav' -f ($i + 1))
  $stream = New-Object -ComObject SAPI.SpFileStream
  $stream.Format.Type = 22
  $stream.Open($path, 3, $false)
  $speaker.AudioOutputStream = $stream
  $speaker.Speak($lines[$i])
  $stream.Close()
  $speaker.AudioOutputStream = $null
}
Write-Output $out
