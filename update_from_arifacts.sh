for year_file in $DATA_DIR/????*ERZ_KHKW_Hagenholz_OGD.csv
do
    echo "Jahr_Monat,Kehrichtdurchsatz,Abtransp_Resprodukte,Waermeabsatz,Stromabsatz" > $DIR/temp.csv
    python $DIR/../../csv_delim.py -f "${year_file}" -d ";" -e cp1252 | tail -n +2 >> $DIR/temp.csv
    python $DIR/convert.py -f $DIR/temp.csv | tail -n +2 >> $DIR/${DATASET}.csv
    rm $DIR/temp.csv
done
