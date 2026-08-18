param(
  [string]$SourceMap = "C:\Users\delib\Downloads\ChatGPT Image 17 de ago. de 2026, 00_29_52.png",
  [string]$SourceItems = "C:\Users\delib\Downloads\ChatGPT Image 17 de ago. de 2026, 00_29_33.png"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
$magick = (Get-Command magick -ErrorAction Stop).Source
$vault = (Resolve-Path "$PSScriptRoot\..\..").Path
$outRoot = Join-Path $vault "zz_media\ui\icons"
$mapOut = Join-Path $outRoot "map"
$itemOut = Join-Path $outRoot "items"
New-Item -ItemType Directory -Force -Path $mapOut,$itemOut | Out-Null

$manifest = [System.Collections.Generic.List[object]]::new()
function Add-Crop {
  param([string]$Source,[string]$Category,[string]$Name,[int]$X,[int]$Y,[int]$Width,[int]$Height)
  $safe = ($Name.ToLowerInvariant() -replace "[^a-z0-9]+", "-").Trim("-")
  $dir = if ($Category -eq "map") { $mapOut } else { $itemOut }
  $relative = "zz_media/ui/icons/$Category/$safe.png"
  $destination = Join-Path $vault $relative.Replace("/", "\")
  $sourceBitmap = [System.Drawing.Bitmap]::new($Source)
  try {
    $inset = 8
    $cropWidth = $Width - ($inset * 2)
    $cropHeight = $Height - ($inset * 2)
    $crop = [System.Drawing.Bitmap]::new($cropWidth, $cropHeight, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($crop)
    try { $graphics.DrawImage($sourceBitmap, [System.Drawing.Rectangle]::new(0,0,$cropWidth,$cropHeight), [System.Drawing.Rectangle]::new($X+$inset,$Y+$inset,$cropWidth,$cropHeight), [System.Drawing.GraphicsUnit]::Pixel) }
    finally { $graphics.Dispose() }
    # A prancha usa papel quente como fundo; manter uma amostra fixa evita
    # que uma borda escura seja escolhida como referência do flood-fill.
    $corner=[System.Drawing.Color]::FromArgb(255,235,215,180)
    $isPaper = {
      param($pixel)
      if ($pixel.A -eq 0) { return $false }
      $dr=$pixel.R-$corner.R; $dg=$pixel.G-$corner.G; $db=$pixel.B-$corner.B
      $distance=[Math]::Sqrt($dr*$dr+$dg*$dg+$db*$db)
      return $distance -lt 72 -or ($pixel.R -gt 185 -and $pixel.G -gt 165 -and $pixel.B -gt 125 -and $pixel.R-$pixel.B -gt 24)
    }
    $visited = New-Object bool[] ($cropWidth*$cropHeight)
    $queue = [System.Collections.Generic.Queue[int]]::new()
    for($x=0;$x -lt $cropWidth;$x++){ $queue.Enqueue($x); $queue.Enqueue(($cropHeight-1)*$cropWidth+$x) }
    for($y=1;$y -lt ($cropHeight-1);$y++){ $queue.Enqueue($y*$cropWidth); $queue.Enqueue($y*$cropWidth+$cropWidth-1) }
    while($queue.Count -gt 0){
      $index=$queue.Dequeue(); if($visited[$index]){continue}; $visited[$index]=$true
      $px=$index % $cropWidth; $py=[Math]::Floor($index / $cropWidth); $pixel=$crop.GetPixel($px,$py)
      if(-not (& $isPaper $pixel)){continue}; $crop.SetPixel($px,$py,[System.Drawing.Color]::FromArgb(0,$pixel.R,$pixel.G,$pixel.B))
      if($px -gt 0){$queue.Enqueue($index-1)}; if($px -lt $cropWidth-1){$queue.Enqueue($index+1)}; if($py -gt 0){$queue.Enqueue($index-$cropWidth)}; if($py -lt $cropHeight-1){$queue.Enqueue($index+$cropWidth)}
    }
    $crop.Save($destination, [System.Drawing.Imaging.ImageFormat]::Png)
    $crop.Dispose()
  }
  finally { $sourceBitmap.Dispose() }
  $manifest.Add([ordered]@{ id=$safe; name=$Name; category=$Category; path=$relative })
}

$territories = @("Earthropo","Nimalia","Floresta de Avenor","Vale Dourado","Bosque Sussurrante","Mar da Neblina","Costa dos Naufragios","Lago Prateado","Montanhas Geladas","Passagem de Korr","Montanhas do Dragao","Terras de Morghul")
$territoryCenters = @(@(116,318),@(260,318),@(404,318),@(548,318),@(116,493),@(260,493),@(404,493),@(548,493),@(116,680),@(260,680),@(404,680),@(548,680))
for ($i = 0; $i -lt $territories.Count; $i++) { $c=$territoryCenters[$i]; Add-Crop $SourceMap "map" $territories[$i] ($c[0]-61) ($c[1]-75) 122 150 }
$locations = @("Nimalis","Porto de Nimalia","Mare Baixa","Bairro Nobre","Bairro dos Forasteiros","Mercado Central","Casa da Moeda de Nimalia","O Frasco Afogado","Leth'valora","Ruinas de Valthor","Fortaleza de Gharok","Fortaleza Abandonada de Avenor","Santuario de Elaris","Porto de Zevran","Antiga Estrada Esquecida")
$locationCenters = @(@(766,318),@(904,318),@(1042,318),@(1180,318),@(1318,318),@(766,493),@(904,493),@(1042,493),@(1180,493),@(1318,493),@(766,680),@(904,680),@(1042,680),@(1180,680),@(1318,680))
for ($i = 0; $i -lt $locations.Count; $i++) { $c=$locationCenters[$i]; Add-Crop $SourceMap "map" $locations[$i] ($c[0]-61) ($c[1]-75) 122 150 }
$types = @("Capital","Cidade","Bairro","Porto","Fortaleza","Santuario","Ruina","Estrada","Floresta","Vale","Lago","Costa","Mar","Montanha","Regiao")
for ($i = 0; $i -lt $types.Count; $i++) { $x=48 + $i*88; Add-Crop $SourceMap "map" $types[$i] $x 855 82 104 }

$weaponRows = @(
  @("Adaga","Alabarda","Azagaia","Bordao Cajado","Chicote","Cimitarra","Espada Bastarda","Espada Curta","Espada Larga","Espada Longa",84,230,100,115),
  @("Falcao","Foice de Mao","Lanca Curta","Lanca Longa","Maca","Machado","Machado de Arremesso","Machado de Batalha","Mangual","Martelo",84,385,100,115),
  @("Martelo de Batalha","Montante","Picareta","Porrete","Sabre","Tridente",84,544,100,108)
)
foreach ($row in $weaponRows) { $names=$row[0..($row.Count-5)]; $baseX=[int]$row[$row.Count-4]; $y=[int]$row[$row.Count-3]; $w=[int]$row[$row.Count-2]; $h=[int]$row[$row.Count-1]; for($i=0;$i -lt $names.Count;$i++){ Add-Crop $SourceItems "items" $names[$i] ($baseX-45+$i*100) ($y-65) $w $h } }
$ranged = @("Arco Curto","Arco Longo","Besta de Mao","Besta","Dardo","Flecha","Flecha Improvisada")
for($i=0;$i -lt $ranged.Count;$i++){ Add-Crop $SourceItems "items" $ranged[$i] (25+$i*83) 620 78 108 }
$armor = @("Armadura Acolchoada","Armadura de Couro","Armadura de Couro Batido","Cota de Malha","Armadura de Placas","Armadura Completa","Broquel","Escudo de Madeira","Escudo de Aco","Escudo Torre")
for($i=0;$i -lt 5;$i++){ Add-Crop $SourceItems "items" $armor[$i] (630+$i*78) 620 76 108 }
for($i=5;$i -lt $armor.Count;$i++){ Add-Crop $SourceItems "items" $armor[$i] (630+($i-5)*78) 770 76 108 }
$basic = @("Arpeu","Corda","Giz","Mochila","Odre","Pederneira","Tocha","Vara de 3 m")
for($i=0;$i -lt $basic.Count;$i++){ Add-Crop $SourceItems "items" $basic[$i] (24+$i*68) 770 64 108 }
$explorer = @("Apito","Escada de Corda","Frasco de Oleo","Lanterna Furta-Fogo","Pa Picareta","Pe de Cabra","Pena Tinta","Pergaminhos","Racao de Viagem","Rede","Saco de Dormir","Tenda")
for($i=0;$i -lt $explorer.Count;$i++){ Add-Crop $SourceItems "items" $explorer[$i] (20+$i*86) 965 82 108 }
$thief = @("Cadeado","Estrepe","Ferramentas de Arrombamento","Ferramentas de Desarme de Armadilhas","Vela")
for($i=0;$i -lt $thief.Count;$i++){ Add-Crop $SourceItems "items" $thief[$i] (72+$i*200) 1135 150 108 }
$specials = @("Acido","Agua Benta","Antitoxina","Bastao Solar","Fogo de Alquimista","Ima","Incenso","Pedra Trovao")
for($i=0;$i -lt $specials.Count;$i++){ Add-Crop $SourceItems "items" $specials[$i] (35+$i*126) 1290 108 120 }

$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $outRoot "catalog.json") -Encoding UTF8
Write-Host "Icones extraidos: $($manifest.Count)"
