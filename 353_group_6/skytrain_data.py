import pandas as pd
import json

def parse_coordinates(s):
    # Convert to JSON object
    json_obj = json.loads(s)
    #return it coordinates
    return json_obj["coordinates"]

def main():
    skytrain_df = pd.read_csv("rapid-transit-stations.csv",sep=";")
    # Parse coordinates
    skytrain_df['Geom'] = skytrain_df['Geom'].apply(parse_coordinates)
    # Get latitude
    skytrain_df['lon'] = skytrain_df['Geom'].apply(lambda x: x[0])
    skytrain_df['lat'] = skytrain_df['Geom'].apply(lambda x: x[1])
    # Keep necessary columns
    skytrain_df = skytrain_df[["STATION","lat","lon"]]
    skytrain_df.to_csv("processed_skytrain_data.csv",index=None)

if __name__=='__main__':
    main()