#!/bin/bash

SCRIPTPATH="$( cd -- "$(dirname -- "$0")" >/dev/null 2>&1 ; pwd -P )"
# echo $SCRIPTPATH
python3 -m venv .venv
source $SCRIPTPATH/.venv/bin/activate

pip install -r $SCRIPTPATH/requirements.txt