#!/usr/bin/env bash
# MODD2 帧序列 → mp4（ffmpeg）。在节点上运行。
# 用法：bash scripts/node_make_video.sh <序列名> [fps]
# 例：bash scripts/node_make_video.sh kope67-00-00060561-00061461 10
set -euo pipefail

SEQ=${1:?用法: node_make_video.sh <序列名> [fps]}
FPS=${2:-10}
ROOT=/home/Developer/data/modd2/video/video_data
OUT=/home/Developer/data/modd2/clips
SRC="$ROOT/$SEQ/framesRectified"

[ -d "$SRC" ] || { echo "序列不存在: $SRC"; exit 1; }
mkdir -p "$OUT"

# 只取左目（L），按文件名排序；-pattern_type glob 需要 %06d 形式，
# MODD2 帧名是 00060561L.jpg 这类，用 concat 更稳
LIST=$(mktemp)
for f in $(ls "$SRC"/*L.jpg | sort); do echo "file '$f'"; done > "$LIST"

OUTFILE="$OUT/${SEQ}_L_${FPS}fps.mp4"
ffmpeg -y -loglevel error -f concat -safe 0 -r "$FPS" -i "$LIST" \
  -c:v libx264 -pix_fmt yuv420p -crf 23 -preset veryfast \
  -movflags +faststart "$OUTFILE"

rm -f "$LIST"
python3 - "$OUTFILE" "$SEQ" "$FPS" <<'PY'
import json, subprocess, sys
from pathlib import Path
out, seq, fps = sys.argv[1], sys.argv[2], sys.argv[3]
p = Path(out)
size_mb = round(p.stat().st_size / 1e6, 1) if p.exists() else 0
# 探测时长与帧数
dur = frames = None
try:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=nb_frames,duration",
                        "-of", "json", out], capture_output=True, text=True, timeout=60)
    st = json.loads(r.stdout)["streams"][0]
    dur, frames = st.get("duration"), st.get("nb_frames")
except Exception as e:
    print("ffprobe 失败:", e)
print(json.dumps({"file": out, "size_mb": size_mb, "fps": int(fps),
                  "duration_s": dur, "frames": frames, "sequence": seq},
                 ensure_ascii=False))
PY
