#
# OpenStreetMap
#
$Dir = $PSScriptRoot
$py = $Dir + "\" + "run.py"
$ini = $Dir + "\" + "run.ini"
python $py $ini
