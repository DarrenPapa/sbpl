localdir="$(pwd)"
interpreter="$localdir/sbpl.py"
name="$localdir/sbpl"
chmod +x $interpreter
echo $interpreter > $name
chmod +x $name
mv $name /usr/bin
