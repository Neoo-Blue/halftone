#!/bin/sh
# Prints one host's health as JSON for the paper's Other machines desk. Read only. POSIX sh, so it runs on a NAS or a Pi.
# Copy it to the host as ~/.paper-stats.sh and lock the paper's key to it, one line in ~/.ssh/authorized_keys, so that key can run this and nothing else:
#   command="sh .paper-stats.sh",restrict ssh-ed25519 AAAA... paper
read -r l1 l5 l15 _ </proc/loadavg
up=$(cut -d. -f1 /proc/uptime)
cores=$(grep -c ^processor /proc/cpuinfo)
memt=$(awk '/^MemTotal:/{print $2}' /proc/meminfo)
mema=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
cpu() { awk '/^cpu /{print $2+$3+$4+$5+$6+$7+$8+$9, $5+$6, $6}' /proc/stat; }
set -- $(cpu); t1=$1; i1=$2; w1=$3; sleep 1; set -- $(cpu); t2=$1; i2=$2; w2=$3
busy=$(awk -v t=$((t2 - t1)) -v i=$((i2 - i1)) 'BEGIN{printf "%.1f", (t > 0 ? (t - i) * 100 / t : 0)}')
io=$(awk -v t=$((t2 - t1)) -v w=$((w2 - w1)) 'BEGIN{printf "%.1f", (t > 0 ? w * 100 / t : 0)}')
# Running totals since boot. The paper turns them into rates between readings.
set -- $(awk -F'[: ]+' 'NR > 2 { sub(/^ +/, ""); if ($1 !~ /^(lo|docker|veth|br-|virbr|tap|fwbr|fwln|fwpr|sit|tun|wg|tailscale)/) { rx += $2; tx += $10 } } END { printf "%.0f %.0f", rx, tx }' /proc/net/dev 2>/dev/null)
rx=${1:-0}; tx=${2:-0}
set -- $(awk '$3 ~ /^(sd[a-z]+|sata[0-9]+|nvme[0-9]+n[0-9]+|vd[a-z]+|xvd[a-z]+|mmcblk[0-9]+)$/ { rd += $6; wr += $10 } END { printf "%.0f %.0f", rd * 512, wr * 512 }' /proc/diskstats 2>/dev/null)
rd=${1:-0}; wr=${2:-0}
top=$(ps -eo pcpu=,pmem=,comm= 2>/dev/null | sort -rn | head -5 | awk '{ c = $1; m = $2; $1 = ""; $2 = ""; sub(/^ +/, ""); gsub(/[\\"]/, "\\\\&"); printf "%s{\"cpu\":%s,\"mem\":%s,\"name\":\"%s\"}", s, c + 0, m + 0, $0; s = "," }')
temp=null
[ -r /sys/class/thermal/thermal_zone0/temp ] && temp=$(awk '{printf "%.1f", $1 / 1000}' /sys/class/thermal/thermal_zone0/temp)
[ -n "$temp" ] || temp=null
disks=$(df -kP 2>/dev/null | awk 'NR > 1 && $1 ~ /^\// && $2 > 1048576 && !seen[$1]++ {gsub(/[\\"]/, "\\\\&", $6); printf "%s{\"mount\":\"%s\",\"total\":%s,\"used\":%s}", s, $6, $2, $3; s = ","}')
raid=0
[ -r /proc/mdstat ] && raid=$(grep -c '\[[U]*_[U_]*\]' /proc/mdstat)
failed=$(systemctl --failed --no-legend --plain 2>/dev/null | awk '{sub(/\.service$/, "", $1); gsub(/[\\"]/, "\\\\&", $1); printf "%s\"%s\"", s, $1; s = ","}')
# Only where this user can read Docker. Nothing is printed otherwise, and the paper leaves it off the page.
containers=$(timeout 3 docker ps -a --format '{{.Names}}|{{.State}}|{{.Status}}' 2>/dev/null | head -60 | awk -F'|' '{gsub(/[\\"]/, "\\\\&"); printf "%s{\"name\":\"%s\",\"state\":\"%s\",\"status\":\"%s\"}", s, $1, $2, $3; s = ","}')
printf '{"load":[%s,%s,%s],"uptime":%s,"cores":%s,"mem_total":%s,"mem_avail":%s,"cpu":%s,"io":%s,"temp":%s,"net":[%s,%s],"diskio":[%s,%s],"top":[%s],"containers":[%s],"disks":[%s],"raid_degraded":%s,"failed_units":[%s]}\n' \
  "$l1" "$l5" "$l15" "$up" "$cores" "$memt" "$mema" "$busy" "$io" "$temp" "$rx" "$tx" "$rd" "$wr" "$top" "$containers" "$disks" "$raid" "$failed"
