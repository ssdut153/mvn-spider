if [ $1 -gt 0 ]
then
	i=1;
	while(( $i<=$1 ))
	do
		dir=mvn-spider-$i
		if [ ! -d "$dir" ]
		then
			cp -R "mvnrepository-spider" "$dir";
		fi
		cd "$dir";
		nohub python main.py &;
		cd ../;
		let "i++";
	done
else
    echo "Error num";
fi