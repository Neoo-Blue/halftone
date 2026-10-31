#!/bin/sh
# Prints one host's health as JSON for the paper's Other machines desk. Read only. POSIX sh, so it runs on a NAS or a Pi.
# Copy it to the host as ~/.paper-stats.sh and lock the paper's key to it, one line in ~/.ssh/authorized_keys, so that key can run this and nothing else:
#   command="sh .paper-stats.sh",restrict ssh-ed25519 AAAA... paper
read -r l1 l5 l15 _ </proc/loadavg
up=$(cut -d. -f1 /proc/uptime)
cores=$(grep -c ^processor /proc/cpuinfo)
memt=$(awk '/^MemTotal:/{print $2}' /proc/meminfo)
mema=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
cpu() { awk '/^cpu /{print $2+$3+$4+$5+$6+$7+$8+$9, $5+$6}' /proc/stat; }
set -- $(cpu); t1=$1; i1=$2; sleep 1; set -- $(cpu); t2=$1; i2=$2
busy=$(awk -v t=$((t2 - t1)) -v i=$((i2 - i1)) 'BEGIN{printf "%.1f", (t > 0 ? (t - i) * 100 / t : 0)}')
temp=null
[ -r /sys/class/thermal/thermal_zone0/temp ] && temp=$(awk '{printf "%.1f", $1 / 1000}' /sys/class/thermal/thermal_zone0/temp)
[ -n "$temp" ] || temp=null
disks=$(df -kP 2>/dev/null | awk 'NR > 1 && $1 ~ /^\// && $2 > 1048576 && !seen[$1]++ {gsub(/[\\"]/, "\\\\&", $6); printf "%s{\"mount\":\"%s\",\"total\":%s,\"used\":%s}", s, $6, $2, $3; s = ","}')
raid=0
[ -r /proc/mdstat ] && raid=$(grep -c '\[[U]*_[U_]*\]' /proc/mdstat)
failed=$(systemctl --failed --no-legend --plain 2>/dev/null | awk '{sub(/\.service$/, "", $1); gsub(/[\\"]/, "\\\\&", $1); printf "%s\"%s\"", s, $1; s = ","}')
printf '{"load":[%s,%s,%s],"uptime":%s,"cores":%s,"mem_total":%s,"mem_avail":%s,"cpu":%s,"temp":%s,"disks":[%s],"raid_degraded":%s,"failed_units":[%s]}\n' \
  "$l1" "$l5" "$l15" "$up" "$cores" "$memt" "$mema" "$busy" "$temp" "$disks" "$raid" "$failed"
