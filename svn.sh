svn(){
    if [ "$1" = "ci" ]; then
        svn up
        if [ $? -ne 0 ]; then
            exit 1
        fi
        tad -m .
    fi
    command svn "$@"
}
