#!/usr/bin/env bash
# Apply to the in-repository vendor driver; no separate vendor workspace.
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
vendor_root="${1:-$repo_root/third_party/frcobot_ros2-v3.0.0_robotV3.9.7}"
vendor_root="$(cd -- "$vendor_root" && pwd)"
package=fairino_hardware_v3_9_7
patch_root="$repo_root/third_party"
shared_patch="$patch_root/fairino_shared_rpc.patch"
command -v patch >/dev/null

check_registration() {
    grep -Fq 'src/fairino_gripper_hardware_interface.cpp' "$1/$package/CMakeLists.txt" &&
    grep -Fq 'fairino_hardware::FairinoGripperHardwareInterface' "$1/$package/fairino_hardware.xml"
}

# A reverse dry-run is read-only. Never actually reverse an installed patch.
if (cd -- "$vendor_root" && patch --batch --fuzz=0 --dry-run -R -p1 < "$shared_patch") >/dev/null 2>&1; then
    if ! check_registration "$vendor_root"; then
        echo 'ERROR: shared source exists but gripper build/plugin registration is missing.' >&2
        exit 1
    fi
    echo 'Shared-RPC upgrade is already applied; no source files changed.'
    echo 'Rebuild the driver if it has not yet been rebuilt.'
    exit 0
fi

stage="$(mktemp -d -t fr3-patch-check.XXXXXXXX)"
trap 'rm -rf -- "$stage"' EXIT
files=(CMakeLists.txt fairino_hardware.xml
       include/fairino_hardware/fairino_hardware_interface.hpp
       src/fairino_hardware_interface.cpp)
for optional in include/fairino_hardware/fairino_gripper_hardware_interface.hpp \
                src/fairino_gripper_hardware_interface.cpp \
                include/fairino_hardware/shared_robot_connection.hpp; do
    if [[ -f "$vendor_root/$package/$optional" ]]; then files+=("$optional"); fi
done
for file in "${files[@]}"; do
    mkdir -p -- "$stage/$package/$(dirname -- "$file")"
    cp -- "$vendor_root/$package/$file" "$stage/$package/$file"
done

pending=()
for name in fairino_dual_arm_ip.patch fairino_gripper_interface.patch fairino_shared_rpc.patch; do
    if (cd -- "$stage" && patch --batch --fuzz=0 --forward --dry-run -p1 < "$patch_root/$name") >/dev/null 2>&1; then
        (cd -- "$stage" && patch --batch --fuzz=0 --forward -p1 < "$patch_root/$name")
        pending+=("$name")
    elif (cd -- "$stage" && patch --batch --fuzz=0 --dry-run -R -p1 < "$patch_root/$name") >/dev/null 2>&1; then
        echo "Already applied: $name"
    else
        echo "ERROR: baseline mismatch for $name. Original source has NOT been changed." >&2
        echo 'Do not force the patch. Check the actual source version and local edits.' >&2
        exit 1
    fi
done

check_registration "$stage"

# Archive outside source discovery; never copy another ROS package into the workspace.
backup="$(mktemp "${TMPDIR:-/tmp}/fr3-driver-backup.XXXXXXXX.tar.gz")"
tar -czf "$backup" -C "$vendor_root/$package" "${files[@]}"
echo "Source backup: $backup (copy it to a permanent location if needed)"
for name in "${pending[@]}"; do
    (cd -- "$vendor_root" &&
        patch --batch --fuzz=0 --forward --dry-run -p1 < "$patch_root/$name" &&
        patch --batch --fuzz=0 --forward -p1 < "$patch_root/$name")
done
(cd -- "$vendor_root" && patch --batch --fuzz=0 --dry-run -R -p1 < "$shared_patch")
echo 'PASS: shared-RPC source upgrade verified. Rebuild before launching.'
