param(
    [string]$OutputPath = '',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $defaultOutputPathBase64 = 'RTpcUFBUXOivvuS7tlzmoKHkvIHlkIjkvZxc5YyX5Lqs56eR5oqA5aSn5a2mXDIwMjZcYXNzZXRzXFJ1eWlEaWZ5LeacrOWcsOWujOaVtOeJiC56aXA='
    $OutputPath = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($defaultOutputPathBase64))
}
$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDir = [System.IO.Path]::GetDirectoryName($outputFullPath)

if (-not (Test-Path -LiteralPath $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

if ((Test-Path -LiteralPath $outputFullPath) -and -not $Force) {
    throw "Output already exists. Re-run with -Force to overwrite: $outputFullPath"
}

$excludedRelativeDirs = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
@(
    '.git',
    '.codegraph',
    '.codex',
    'docker/volumes/app',
    'docker/volumes/certbot',
    'docker/volumes/db',
    'docker/volumes/myscale',
    'docker/volumes/oceanbase',
    'docker/volumes/opensearch',
    'docker/volumes/plugin_daemon',
    'docker/volumes/redis',
    'docker/volumes/sandbox/dependencies',
    'docker/volumes/weaviate',
    'node_modules',
    '.next',
    'dist',
    'build',
    'out',
    'coverage',
    'playwright-report',
    'test-results',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.pnpm-store',
    '.vitest-attachments',
    'web/.vitest-reports',
    'scripts/stress-test/reports',
    'scripts/stress-test/setup/config'
) | ForEach-Object { [void]$excludedRelativeDirs.Add($_) }

$excludedDirNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
@(
    'node_modules',
    '.next',
    'dist',
    'build',
    'out',
    'coverage',
    'playwright-report',
    'test-results',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.pnpm-store'
) | ForEach-Object { [void]$excludedDirNames.Add($_) }

$excludedFileNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
@(
    'docker-verify-page.png'
) | ForEach-Object { [void]$excludedFileNames.Add($_) }

function Get-RelativeZipPath {
    param([string]$Path)

    $rootUri = [System.Uri]::new($repoRoot.TrimEnd('\') + '\')
    $pathUri = [System.Uri]::new($Path)
    $relative = [System.Uri]::UnescapeDataString($rootUri.MakeRelativeUri($pathUri).ToString())
    return $relative.Replace('\', '/')
}

function Test-ExcludedDirectory {
    param([System.IO.DirectoryInfo]$Directory)

    $relative = Get-RelativeZipPath $Directory.FullName
    if ($excludedRelativeDirs.Contains($relative)) {
        return $true
    }

    foreach ($excludedRelativeDir in $excludedRelativeDirs) {
        if ($relative.StartsWith("$excludedRelativeDir/", [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }

    return $excludedDirNames.Contains($Directory.Name)
}

function Test-ExcludedFile {
    param([System.IO.FileInfo]$File)

    if ($excludedFileNames.Contains($File.Name)) {
        return $true
    }

    if ($File.Extension -eq '.log') {
        return $true
    }

    return $false
}

if (Test-Path -LiteralPath $outputFullPath) {
    Remove-Item -LiteralPath $outputFullPath -Force
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$fileCount = 0
$totalBytes = 0L
$zipStream = [System.IO.File]::Open($outputFullPath, [System.IO.FileMode]::CreateNew)

try {
    $archive = [System.IO.Compression.ZipArchive]::new($zipStream, [System.IO.Compression.ZipArchiveMode]::Create, $false)
    try {
        $pending = [System.Collections.Generic.Stack[System.IO.DirectoryInfo]]::new()
        $pending.Push([System.IO.DirectoryInfo]::new($repoRoot))

        while ($pending.Count -gt 0) {
            $directory = $pending.Pop()

            foreach ($childDirectory in $directory.EnumerateDirectories()) {
                if (-not (Test-ExcludedDirectory $childDirectory)) {
                    $pending.Push($childDirectory)
                }
            }

            foreach ($file in $directory.EnumerateFiles()) {
                if (Test-ExcludedFile $file) {
                    continue
                }

                $entryName = Get-RelativeZipPath $file.FullName
                $entry = $archive.CreateEntry($entryName, [System.IO.Compression.CompressionLevel]::Optimal)
                $entry.LastWriteTime = $file.LastWriteTime

                $entryStream = $entry.Open()
                $sourceStream = $file.OpenRead()
                try {
                    $sourceStream.CopyTo($entryStream)
                }
                finally {
                    $sourceStream.Dispose()
                    $entryStream.Dispose()
                }

                $fileCount += 1
                $totalBytes += $file.Length
            }
        }
    }
    finally {
        $archive.Dispose()
    }
}
finally {
    $zipStream.Dispose()
}

$zipItem = Get-Item -LiteralPath $outputFullPath
[PSCustomObject]@{
    OutputPath = $zipItem.FullName
    ZipBytes = $zipItem.Length
    SourceFiles = $fileCount
    SourceBytes = $totalBytes
}
