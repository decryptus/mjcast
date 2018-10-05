#!/bin/sh

echo "Starting redis server ..."
redis-server > /dev/null 2>&1&
$@
