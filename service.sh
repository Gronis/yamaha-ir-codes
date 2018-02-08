
get_is_playing(){
    STATUS=$(curl http://127.0.0.1/api/v1/getstate 2> /dev/null);
    STATUS=$(echo $STATUS | grep play);
    IS_PLAYING=${#STATUS};
    IS_PLAYING=$(($IS_PLAYING > 10 ? 1 : 0))
    echo $IS_PLAYING
}

was_playing=0
is_playing=0

while true; do
    was_playing=$is_playing
    is_playing=$(get_is_playing)
    (( $is_playing == 0)) && (( $was_playing == 1 )); stop_playing=$((1-$?));
    (( $is_playing == 1)) && (( $was_playing == 0 )); start_playing=$((1-$?));
    if [ $start_playing -eq 1 ]; then
        echo "started"
        irsend SEND_ONCE RECEIVER_2064_MAIN POWER_POWER_ON
        sleep 0.1
        irsend SEND_ONCE RECEIVER_2064_MAIN INPUT_HDMI1
    fi

    if [ $stop_playing -eq 1 ]; then
        echo "stopped"
    fi
    sleep 1

done
