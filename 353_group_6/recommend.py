import pandas as pd
import numpy as np
import sys
from math import pi
from GPSPhoto import gpsphoto
import folium

def replace_amenity(df):
    # allocate traffic amenities
    df['amenity'] = df['amenity'].replace(['car_rental'], 'traffic')
    df['amenity'] = df['amenity'].replace(['car_sharing'], 'traffic')
    df['amenity'] = df['amenity'].replace(['bicycle_rental'], 'traffic')
    df['amenity'] = df['amenity'].replace(['boat_rental'], 'traffic')
    df['amenity'] = df['amenity'].replace(['motorcycle_rental'], 'traffic')
    df['amenity'] = df['amenity'].replace(['taxi'], 'traffic')
    # allocate gaming amenities
    df['amenity'] = df['amenity'].replace(['pub'], 'bar')
    df['amenity'] = df['amenity'].replace(['nightclub'], 'bar')
    df['amenity'] = df['amenity'].replace(['gambling'], 'casino')
    # allocate banking amenities
    df['amenity'] = df['amenity'].replace(['atm;bank'], 'bank')
    df['amenity'] = df['amenity'].replace(['motorcycle_parking'], 'parking')
    df['amenity'] = df['amenity'].replace(['parking_entrance'], 'parking')
    df['amenity'] = df['amenity'].replace(['drinking_water'], 'fountain')
    df['amenity'] = df['amenity'].replace(['doctors'], 'hospital')
    df['amenity'] = df['amenity'].replace(['storage'], 'storage_rental')
    df['amenity'] = df['amenity'].replace(['internet_cafe'], 'cafe')
    df['amenity'] = df['amenity'].replace(['chiropractor'], 'hospital')
    df['amenity'] = df['amenity'].replace(['childcare'], 'kindergarten')
    df['amenity'] = df['amenity'].replace(['post_depot'], 'post_office')
    df['amenity'] = df['amenity'].replace(['Pharmacy'], 'pharmacy')
    df['amenity'] = df['amenity'].replace(['ferry_terminal'], 'bus_station')
    df['amenity'] = df['amenity'].replace(['food_court'], 'restaurant')
    return df

def get_location(filename):
    return gpsphoto.getGPSData(filename)

def get_dis(lat1,lon1, lat2, lon2):
    p = pi / 180
    a = 0.5-np.cos((lat2 - lat1) * p)/2 + np.cos(lat1 * p) * np.cos(lat2 * p) * (1 - np.cos((lon2 - lon1) * p)) / 2
    return 12742*np.arcsin(np.sqrt(a))*1000

def get_dis_helper(one_row, start_lat, start_lon):
    lat1 = one_row['lat']
    lon1 = one_row['lon']
    lat2 = start_lat
    lon2 = start_lon
    p = pi / 180
    a = 0.5-np.cos((lat2 - lat1) * p)/2 + np.cos(lat1 * p) * np.cos(lat2 * p) * (1 - np.cos((lon2 - lon1) * p)) / 2
    return 12742*np.arcsin(np.sqrt(a))*1000

def split_on_map(data,map):
    # split amenities to different colours 
    dining = ['cafe','restaurant', 'fast_food','traffic']
    transit = ['parking','bus_station','traffic']
    gaming = ['pub', 'cinema','bar']
    shopping = ['atm', 'bank','marketplace']
    for _, row in data.iterrows():
        if row['amenity'] in dining:
            folium.Circle(
                radius=5,
                location=[row['lat'], row['lon']],
                color='red',
                fill=True
            ).add_to(map)
        if row['amenity'] in transit:
            folium.Circle(
                radius=5,
                location=[row['lat'], row['lon']],
                color='yellow',
                fill=True
            ).add_to(map)
        if row['amenity'] in gaming:
            folium.Circle(
                radius=5,
                location=[row['lat'], row['lon']],
                color='blue',
                fill=True
            ).add_to(map)
        if row['amenity'] in shopping:
            folium.Circle(
                radius=5,
                location=[row['lat'], row['lon']],
                color='green',
                fill=True
            ).add_to(map)

def get_route(start_lat,start_lon,end_lat,end_lon,amenities):
    if len(amenities) == 0:
        amenities['distance'] = None
        return amenities

    path_df = amenities[0:0]
    amenities['distance'] = amenities.apply(get_dis_helper, start_lat = start_lat, start_lon = start_lon, axis = 1)
    amenities = amenities.sort_values(by=['distance'])
    next_place = amenities.head(1)
    path_df = path_df.append(next_place,ignore_index=True)
    
    if amenities.shape[0] == 1:
        return path_df
    
    next_amen = amenities.iloc[1:,:]
    past_amen = next_place['amenity']
    next_amen = next_amen[next_amen['amenity'].isin(past_amen) == False]
    
    next_amen.drop(['distance'],axis=1)
    
    continue_path = get_route(next_place['lat'], next_place['lon'],end_lat,end_lon,next_amen)
    path_df = path_df.append(continue_path, ignore_index = True)
    
    return path_df

def compute_nearest_skytrain(lat,lon,skytrain_df):
    # Compute nearest skytrain station of given lat lon
    min_dist = float('Inf')
    min_index = None
    for index,row in skytrain_df.iterrows():
        dist = get_dis(lat, lon, row["lat"], row["lon"])
        if dist < min_dist:
            min_dist = dist
            min_index = index
    return skytrain_df.iloc[min_index,:]

def set_boundary(start_lat,start_lon,end_lat,end_lon,amenities):
    if start_lat <= end_lat :
        if start_lon <= end_lon:
            Qudrant = 'I'
        else:
            Qudrant = 'II'
    else:
        if start_lon <= end_lon:
            Qudrant = 'IV'
        else:
            Qudrant = 'III'

    if Qudrant == 'I':
        amenities = amenities[start_lat<=amenities['lat']]
        amenities = amenities[amenities['lat']<=end_lat]
        amenities = amenities[start_lon<=amenities['lon']]
        amenities = amenities[amenities['lon']<=end_lon]
    elif Qudrant == 'II':
        amenities = amenities[start_lat<=amenities['lat']]
        amenities = amenities[amenities['lat']<=end_lat]
        amenities = amenities[start_lon>=amenities['lon']]
        amenities = amenities[amenities['lon']>=end_lon]
    elif Qudrant == 'III':
        amenities = amenities[start_lat>=amenities['lat']]
        amenities = amenities[amenities['lat']>=end_lat]
        amenities = amenities[start_lon>=amenities['lon']]
        amenities = amenities[amenities['lon']>=end_lon]
    else:    
        amenities = amenities[start_lat>=amenities['lat']]
        amenities = amenities[amenities['lat']>=end_lat]
        amenities = amenities[start_lon<=amenities['lon']]
        amenities = amenities[amenities['lon']<=end_lon]
    
    return amenities

def position_amen_inrange(lat,lon,amen):
        lat2 = amen[0]       
        lon2 = amen[1]
        d = get_dis(lat, lon, lat2, lon2)
        if d < 500:
            return True

    
def main (A_image):
    # Parse the location data of the image
    location_A=get_location(A_image)
    lat_A=location_A['Latitude']
    lon_A=location_A['Longitude']
    # Load skytrain data
    skytrain_df = pd.read_csv("processed_skytrain_data.csv")
    # Caclulate the nearest skytrain station of given data
    selected_skytrain = compute_nearest_skytrain(lat_A,lon_A,skytrain_df)
    selected_skytrain_lat = selected_skytrain['lat']
    selected_skytrain_lon = selected_skytrain['lon']
    selected_skytrain_name = selected_skytrain['STATION']
    extract = ['cinema', 'clock', 'museum','park','university','beach','theatre','lake', 'shopping_centre'
        ,'conference_centre','parking','cafe','fast_food','parking','bus_station','traffic', 'arts_centre',
        'restaurant','bar','casino']
    
    #Travel method recommandation
    total_distance = get_dis(selected_skytrain_lat, selected_skytrain_lon, lat_A, lon_A)
    if total_distance < 1000:
        print('Distance less than 1000 meters, recommend walking to the destination.')
    elif total_distance > 5000:
        print('Distance more than 5000 meters, recommend driving to the destination.')
    else:
        print('Distance is between 1000 to 5000 meters, recommend cycling to the destination.')

    read_data = pd.read_json('amenities-vancouver.json.gz', lines=True)
    addition_amen = pd.read_csv('additional_amenities.csv', encoding="utf-8",sep =',')
    read_data = read_data[read_data['name'].notna()]
    read_data = read_data.drop(['timestamp','tags'], axis=1).reset_index(drop= True)
    cleaned_data_amen = replace_amenity(read_data)
    cleaned_data_amen = cleaned_data_amen[cleaned_data_amen['amenity'].isin(extract) == True]
    addition_amen = addition_amen[addition_amen['amenity'].isin(extract) == True]
    amenities = pd.concat([cleaned_data_amen,addition_amen]).reset_index(drop = True)
    amenities = amenities.drop_duplicates()
    temp = []
    for amen in amenities.itertuples(index=False):
        if position_amen_inrange(lat_A,lon_A,amen) == True:
            temp.append(amen)
    amenities = pd.DataFrame(temp) 

    skytrain_amenity = amenities[0:0]
    a_row = {'lat':selected_skytrain_lat, 'lon':selected_skytrain_lon, 'amenity':'skytrain', 'name':selected_skytrain_name}
    skytrain_amenity = skytrain_amenity.append(a_row, ignore_index=True)

    start_lat = selected_skytrain_lat
    start_lon = selected_skytrain_lon
    end_lat = lat_A
    end_lon = lon_A
    

    bounded_amenities = set_boundary(start_lat,start_lon,end_lat,end_lon,amenities)
    route = get_route(start_lat,start_lon,end_lat,end_lon,bounded_amenities)
    route = route.drop(['distance'],axis=1)
    route = route.dropna().reset_index(drop=True)
    output = skytrain_amenity.append(route, ignore_index=True)

    #All amenities map
    van_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)

    incidents = folium.map.FeatureGroup()

    latitudes = list(bounded_amenities.lat)
    longitudes = list(bounded_amenities.lon)
    labels = list(bounded_amenities.name)

    for lat, lng, label in zip(latitudes, longitudes, labels):
        folium.Marker([lat, lng], popup=label).add_to(van_map)    
        
    van_map.add_child(incidents)
        
    folium.Marker([start_lat,start_lon],
             popup='Start',icon=folium.Icon(color='red')).add_to(van_map)

    folium.Marker([lat_A,lon_A],
             popup='End',icon=folium.Icon(color='green')).add_to(van_map)
    
    split_on_map(amenities,van_map)
    van_map.save("nearby_amentities.html")

    #Recommendation map
    van_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)

    incidents = folium.map.FeatureGroup()

    latitudes = list(output.lat)
    longitudes = list(output.lon)
    labels = list(output.name)

    for lat, lng, label in zip(latitudes, longitudes, labels):
        folium.Marker([lat, lng], popup=label).add_to(van_map)    
        
    van_map.add_child(incidents)
        
    folium.Marker([start_lat,start_lon],
             popup='Start',icon=folium.Icon(color='red')).add_to(van_map)

    folium.Marker([lat_A,lon_A],
             popup='End',icon=folium.Icon(color='green')).add_to(van_map)
    
    van_map.save("recommend_amentities.html")

if __name__=='__main__':    
    A_image = sys.argv[1]

    main(A_image)