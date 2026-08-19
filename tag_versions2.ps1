$git = "C:\Users\adria\AppData\Local\GitHubDesktop\app-3.6.3\resources\app\git\cmd\git.exe"

& $git config --global user.email "bot@moonbot.local"
& $git config --global user.name "Moonbot Auto"

& $git checkout master
(Get-Content CHANGELOG.md) -replace 'v16.85.0-alpha', 'v16.85.0' | Set-Content CHANGELOG.md
& $git commit -am "chore(release): registrar version v16.85.0 estable"
& $git tag -f v16.85.0

& $git checkout beta
(Get-Content CHANGELOG.md) -replace 'v16.85.0-alpha', 'v16.85.0-beta' | Set-Content CHANGELOG.md
& $git commit -am "chore(release): registrar version v16.85.0-beta"
& $git tag -f v16.85.0-beta

& $git checkout rc
(Get-Content CHANGELOG.md) -replace 'v16.85.0-alpha', 'v16.85.0-rc' | Set-Content CHANGELOG.md
& $git commit -am "chore(release): registrar version v16.85.0-rc"
& $git tag -f v16.85.0-rc

& $git checkout alfa
(Get-Content CHANGELOG.md) -replace 'v18.25.14', 'v18.25.15-alpha' | Set-Content CHANGELOG.md
& $git commit -am "chore(release): registrar version v18.25.15-alpha"
& $git tag -f v18.25.15-alpha

& $git push origin master beta rc alfa --tags -f
& $git checkout master
