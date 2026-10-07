#!/bin/zsh
# usage: four.sh <hero dir> <name>   -> <hero dir>/<name>-네방향.jpg
H="$1"; N="$2"; T="$3"
flat(){ ffmpeg -v error -y -f lavfi -i "color=c=0x3a3f46:s=1000x1000:d=1" -i "$1" -filter_complex "[0:v][1:v]overlay=0:0:shortest=1" -frames:v 1 -q:v 2 "$2"; }
flat "$H/$N.png" "$T/f0.jpg"; flat "$H/${N}_side.png" "$T/f1.jpg"; flat "$H/${N}_top.png" "$T/f2.jpg"; flat "$H/${N}_end.png" "$T/f3.jpg"
ffmpeg -v error -y -i "$T/f0.jpg" -i "$T/f1.jpg" -i "$T/f2.jpg" -i "$T/f3.jpg" -filter_complex "[0:v][1:v]hstack[a];[2:v][3:v]hstack[b];[a][b]vstack" -q:v 2 "$H/$N-네방향.jpg"
cp "$T/f0.jpg" "$H/$N-큰그림.jpg"
