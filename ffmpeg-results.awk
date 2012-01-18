BEGIN {
	FS="="
}
/height=/ { height=$2}
/width=/ {width=$2}

END { 
	print width/height 
}
