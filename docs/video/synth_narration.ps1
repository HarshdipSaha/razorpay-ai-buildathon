# Synthesizes narration WAVs from audio/*.txt using Windows SAPI (offline, no API key).
# Converts inline [pause] / [long pause] markers into SSML <break> tags so the
# delivery has natural breath points instead of a flat read.
#
# Run from repo root:  powershell -File docs/video/synth_narration.ps1
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice("Microsoft Zira Desktop")
# Rate 1 (not -1): the first pass at -1 with an extra -8% prosody slowdown pushed the
# video to 5:22, over the brief's 5-minute limit. The pauses carry the "considered"
# feel; the base pace should stay conversational, not slow.
$synth.Rate = 1

$audioDir = Join-Path $PSScriptRoot "audio"
$files = Get-ChildItem "$audioDir\*.txt" | Sort-Object Name

function Escape-Xml([string]$s) {
    return $s.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;")
}

foreach ($f in $files) {
    $raw = (Get-Content $f.FullName -Raw).Trim()
    # Escape XML first, THEN substitute pause markers so the <break> tags survive.
    $text = Escape-Xml $raw
    $text = $text.Replace("[long pause]", '<break time="600ms"/>')
    $text = $text.Replace("[pause]", '<break time="300ms"/>')
    $ssml = @"
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
$text
</speak>
"@
    $wavPath = Join-Path $audioDir ($f.BaseName + ".wav")
    $synth.SetOutputToWaveFile($wavPath)
    $synth.SpeakSsml($ssml)
    $synth.SetOutputToNull()
    Write-Output "wrote $wavPath"
}
$synth.Dispose()
