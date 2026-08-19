# Configurar Git para automatizar el etiquetado y commits
git checkout master
(Get-Content CHANGELOG.md) -replace 'v16.85.0-alpha', 'v16.85.0' | Set-Content CHANGELOG.md
git commit -am "chore(release): bump version to v16.85.0 (Stable)"
git tag -f v16.85.0

git checkout beta
(Get-Content CHANGELOG.md) -replace 'v16.85.0-alpha', 'v16.85.0-beta' | Set-Content CHANGELOG.md
git commit -am "chore(release): bump version to v16.85.0-beta"
git tag -f v16.85.0-beta

git checkout rc
(Get-Content CHANGELOG.md) -replace 'v16.85.0-alpha', 'v16.85.0-rc' | Set-Content CHANGELOG.md
git commit -am "chore(release): bump version to v16.85.0-rc"
git tag -f v16.85.0-rc

git checkout alfa
(Get-Content CHANGELOG.md) -replace 'v18.25.14', 'v18.25.15-alpha' | Set-Content CHANGELOG.md
git commit -am "chore(release): bump version to v18.25.15-alpha"
git tag -f v18.25.15-alpha

# Subir todos los cambios y tags
git push origin master beta rc alfa --tags -f
git checkout master
