#!/bin/bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
    printf 'Usage : %s "/chemin/NXNative Dashboard.app" "/chemin/NXNative Dashboard.dmg"\n' "$0" >&2
    exit 2
fi

app=$1
dmg=$2
dist=$(dirname "$dmg")
staging=$(mktemp -d "$dist/.dmg-staging.XXXXXX")
mount=$(mktemp -d "$dist/.dmg-mount.XXXXXX")
attached=0

cleanup() {
    if [ "$attached" -eq 1 ]; then
        hdiutil detach "$mount" -quiet >/dev/null 2>&1 || true
    fi
    rm -rf "$staging" "$mount"
}
trap cleanup EXIT

check_bundle() {
    local bundle=$1 relative path
    while IFS= read -r relative; do
        path=$bundle/$relative
        case "$relative" in
            Contents|Contents/MacOS|Contents/Resources|Contents/_CodeSignature)
                if [ ! -d "$path" ] || [ -L "$path" ]; then
                    printf 'Entrée interdite dans le bundle : %s\n' "$relative" >&2
                    return 1
                fi
                ;;
            Contents/Info.plist|Contents/MacOS/NXNativeDashboard|Contents/Resources/AppIcon.icns|Contents/_CodeSignature/*)
                if [ ! -f "$path" ] || [ -L "$path" ]; then
                    printf 'Entrée interdite dans le bundle : %s\n' "$relative" >&2
                    return 1
                fi
                ;;
            *)
                printf 'Entrée interdite dans le bundle : %s\n' "$relative" >&2
                return 1
                ;;
        esac
    done < <(cd "$bundle" && find . -mindepth 1 -print | sed 's#^\./##')
}

check_bundle "$app"
test -x "$app/Contents/MacOS/NXNativeDashboard"

ditto "$app" "$staging/NXNative Dashboard.app"
ln -s /Applications "$staging/Applications"
hdiutil create -ov -format UDZO -volname "NXNative Dashboard" -srcfolder "$staging" "$dmg"

hdiutil attach -nobrowse -readonly -mountpoint "$mount" "$dmg"
attached=1
expected=$'./Applications\n./NXNative Dashboard.app'
actual=$(cd "$mount" && find . -mindepth 1 -maxdepth 1 -print | LC_ALL=C sort)
if [ "$actual" != "$expected" ]; then
    printf 'Contenu racine inattendu du DMG :\n%s\n' "$actual" >&2
    exit 1
fi
test -L "$mount/Applications"
test "$(readlink "$mount/Applications")" = /Applications
check_bundle "$mount/NXNative Dashboard.app"
diff -r "$app" "$mount/NXNative Dashboard.app"
hdiutil detach "$mount" -quiet
attached=0

printf 'DMG vérifié : %s\n' "$dmg"
