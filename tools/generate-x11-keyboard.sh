#!/usr/bin/env bash
#
# Generates /etc/X11/xorg.conf.d/00-keyboard.conf from /etc/vconsole.conf
# Requires root privileges to write to /etc/X11/xorg.conf.d/

set -euo pipefail

VCONSOLE_FILE="/etc/vconsole.conf"
XORG_CONF_DIR="/etc/X11/xorg.conf.d"
OUTPUT_FILE="${XORG_CONF_DIR}/00-keyboard.conf"

# Ensure root permissions
if [[ $EUID -ne 0 ]]; then
    echo "Error: This script must be run as root." >&2
    exit 1
fi

if [[ ! -f "$VCONSOLE_FILE" ]]; then
    echo "Error: $VCONSOLE_FILE does not exist." >&2
    exit 1
fi

# Source vconsole variables safely
# Expected variables: KEYMAP, XKBLAYOUT, XKBMODEL, XKBVARIANT, XKBOPTIONS
KEYMAP=""
XKBLAYOUT=""
XKBMODEL=""
XKBVARIANT=""
XKBOPTIONS=""

while IFS='=' read -r key val || [[ -n "$key" ]]; do
    # Strip comments and trim whitespace
    key=$(echo "$key" | sed -e 's/#.*//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    val=$(echo "$val" | sed -e 's/#.*//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["\x27]//' -e 's/["\x27]$//')
    
    case "$key" in
        KEYMAP)     KEYMAP="$val" ;;
        XKBLAYOUT)  XKBLAYOUT="$val" ;;
        XKBMODEL)   XKBMODEL="$val" ;;
        XKBVARIANT) XKBVARIANT="$val" ;;
        XKBOPTIONS) XKBOPTIONS="$val" ;;
    esac
done < "$VCONSOLE_FILE"

# If XKBLAYOUT is not explicitly set in vconsole.conf, derive it from KEYMAP
if [[ -z "$XKBLAYOUT" ]]; then
    case "$KEYMAP" in
        de*|de-latin1*)
            XKBLAYOUT="de"
            [[ "$KEYMAP" =~ nodeadkeys ]] && XKBVARIANT="nodeadkeys"
            ;;
        fr*|fr-latin*)
            XKBLAYOUT="fr"
            ;;
        es*)
            XKBLAYOUT="es"
            ;;
        it*)
            XKBLAYOUT="it"
            ;;
        uk*)
            XKBLAYOUT="gb"
            ;;
        us*)
            XKBLAYOUT="us"
            ;;
        *)
            # Fall back to stripping suffixes or using KEYMAP directly if simple 2-letter code
            XKBLAYOUT="${KEYMAP%%-*}"
            [[ -z "$XKBLAYOUT" ]] && XKBLAYOUT="us"
            ;;
    esac
fi

# Ensure default values if still unset
[[ -z "$XKBMODEL" ]] && XKBMODEL="pc105"

# Ensure output directory exists
mkdir -p "$XORG_CONF_DIR"

# Write the Xorg InputClass configuration file
cat <<EOF > "$OUTPUT_FILE"
# Generated automatically from /etc/vconsole.conf
Section "InputClass"
        Identifier "system-keyboard"
        MatchIsKeyboard "on"
        Option "XkbLayout" "$XKBLAYOUT"
        Option "XkbModel" "$XKBMODEL"
EOF

# Append optional fields only if they have values
if [[ -n "$XKBVARIANT" ]]; then
    echo "        Option \"XkbVariant\" \"$XKBVARIANT\"" >> "$OUTPUT_FILE"
fi

if [[ -n "$XKBOPTIONS" ]]; then
    echo "        Option \"XkbOptions\" \"$XKBOPTIONS\"" >> "$OUTPUT_FILE"
fi

echo "EndSection" >> "$OUTPUT_FILE"

echo "Successfully created $OUTPUT_FILE with layout '$XKBLAYOUT' (model: $XKBMODEL)."
