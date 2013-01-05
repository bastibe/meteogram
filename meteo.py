from urllib.parse import urlencode
from urllib.request import urlopen
import json
import xml.etree.ElementTree as ET
# from datetime import strptime
import datetime
# from time import strptime
from matplotlib.dates import date2num, num2date, AutoDateLocator
from matplotlib.pyplot import *
import matplotlib.ticker as ticker
from numpy import array, linspace

def retrieve_position_google(address):
    """
    Retrieve the latitude and longitude for an address using the
    Google Maps API. Only return the first result.

    Note that this is using the Google Maps API which is only supposed
    to be used if you also display a Google Map.

    documentation at http://code.google.com/apis/maps/documentation/geocoding/
    """

    url = "http://maps.googleapis.com/maps/api/geocode/json"
    params = {'address':address, 'sensor':'true'}

    complete_url = "%s?%s" % (url, urlencode(params))
    request = urlopen(complete_url)
    result = json.loads(request.read().decode('utf-8'))

    return(result['results'][0]['geometry']['location'])

def retrieve_position_mapquest(address):
    """
    Retrieve the latitude and longitude for an address using the
    MapQuest API. Only return the first result.

    Note that the mapquest API requires an API key. The one used here
    apparently expired. For unknown reasons.

    documentation at http://www.mapquestapi.com/geocoding/
    """
    app_key = 'Fmjtd%7Cluuan96zn1%2Cb0%3Do5-96bgg6'
    url = 'http://www.mapquestapi.com/geocoding/v1/address'
    params = {'key':app_key, 'location':address, 'thumbMaps':'false',
              'inFormat':'kvp', 'outFormat':'json'}

    complete_url = "%s?%s" % (url, urlencode(params))
    request = urlopen(complete_url)
    result = json.loads(request.read().decode('utf-8'))

    latLng = result['results'][0]['locations'][0]['latLng']
    return({'lat':latLng['lat'], 'lon':latLng['lng']})

def retrieve_position_openmapquest(address):
    """
    Retrieve the latitude and longitude for an address using the open
    MapQuest API. Only return the first result.

    documentation at http://open.mapquestapi.com/geocoding/
    """
    url = 'http://open.mapquestapi.com/geocoding/v1/address'
    params = {'location':address, 'thumbMaps':'false',
              'inFormat':'kvp', 'outFormat':'json'}

    complete_url = "%s?%s" % (url, urlencode(params))
    request = urlopen(complete_url)
    result = json.loads(request.read().decode('utf-8'))

    latLng = result['results'][0]['locations'][0]['latLng']
    return({'lat':latLng['lat'], 'lon':latLng['lng']})

def XML_timestring_to_time(string):
    """
    Convert yr.no timestamps to a Python time
    """
    return(datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%SZ"))

def XML_time_node_to_dict(node):
    """
    Convert one yr.no weather node to a Python dictionary
    """
    get_child_attribs = lambda name: node.findall('.//%s'%name)[0].attrib
    from_time = XML_timestring_to_time(node.attrib['from'])
    to_time = XML_timestring_to_time(node.attrib['to'])

    if to_time.hour-from_time.hour == 0:
        # complex data every hour
        return({'time':{'from':from_time, 'to':to_time},
                'temperature':get_child_attribs('temperature'),
                'windDirection':get_child_attribs('windDirection'),
                'windSpeed':get_child_attribs('windSpeed'),
                'humidity':get_child_attribs('humidity'),
                'pressure':get_child_attribs('pressure'),
                'cloudiness':get_child_attribs('cloudiness'),
                'fog':get_child_attribs('fog'),
                'lowClouds':get_child_attribs('lowClouds'),
                'mediumClouds':get_child_attribs('mediumClouds'),
                'highClouds':get_child_attribs('highClouds')})
    else:
        # precipitation data for different hour interval
        return({'time':{'from':from_time, 'to':to_time},
                'precipitation':get_child_attribs('precipitation'),
                'symbol':get_child_attribs('symbol')})

def retrieve_weather_yrno(latLng):
    """
    Retrieve weather data from yr.no for a given latitude/longitude

    documentation at http://api.yr.no/weatherapi/locationforecast/1.8/documentation
    """
    url = 'http://api.yr.no/weatherapi/locationforecast/1.8/'

    complete_url = "%s?%s" % (url, urlencode(latLng))
    request = urlopen(complete_url)
    result = request.read().decode('utf-8')
    root = ET.fromstring(result)

    return [XML_time_node_to_dict(node) for node in root.findall('.//time')]

def format_date(date):
    """
    convert a numeric date to a date string
    """
    return num2date(date).strftime('%Y-%m-%d')

def extract_value(element, label):
    """
    extract a time and value item from a named weather element
    """
    return (date2num(element['time']['from']),
            float(element[label]['value']))

def extract_percent(element, label):
    """
    extract a time and percent item from a named weather element
    """
    return (date2num(element['time']['from']),
            float(element[label]['percent']))

def extract_precipitation(element):
    """
    extract from_time and to_time and precipitation data from element
    """
    return (date2num(element['time']['from']),
            float(element['precipitation']['minvalue']),
            float(element['precipitation']['value']),
            float(element['precipitation']['maxvalue']))

def is_hourly_precipitation(element):
    """
    check if the element contains precipitation of a one hour interval
    """
    return ('precipitation' in element and
            element['time']['to'].hour-element['time']['from'].hour == 1)

def plot_clouds(ax, weather_data):
    """
    plot a single plot containing high, mid, low clouds and fog
    """
    # high clouds
    high_clouds = [extract_percent(e, 'highClouds') for e in weather_data if 'highClouds' in e]
    time, high_clouds = zip(*high_clouds)
    fill_between(time, array(high_clouds)/200+3,
                 -array(high_clouds)/200+3,
                 color='lightgrey', axes=ax)
    # medium clouds
    medium_clouds = [extract_percent(e, 'mediumClouds') for e in weather_data if 'mediumClouds' in e]
    time, medium_clouds = zip(*medium_clouds)
    fill_between(time, array(medium_clouds)/200+2,
                 -array(medium_clouds)/200+2,
                 color='darkgrey', axes=ax)
    # low clouds
    low_clouds = [extract_percent(e, 'lowClouds') for e in weather_data if 'lowClouds' in e]
    time, low_clouds = zip(*low_clouds)
    fill_between(time, array(low_clouds)/200+1,
                 -array(low_clouds)/200+1,
                 color='grey', axes=ax)
    # fog
    fog = [extract_percent(e, 'fog') for e in weather_data if 'fog' in e]
    time, fog = zip(*fog)
    fill_between(time, array(fog)/200, color='darkgrey', axes=ax)
    # no x ticks, one y tick per cloud type
    ax.get_xticks([])
    ax.set_yticks([0, 1, 2, 3])
    ax.set_yticklabels(['fog', 'low', 'med', 'high'])

def plot_temperature(ax, weather_data, color):
    """
    plot a single plot containing a temperature curve and a
    date-formatted x axis
    """
    temperature = [extract_value(e,'temperature') for e in weather_data if 'temperature' in e]
    time, temperature = zip(*temperature)
    plot_date(time, temperature, label='temperature', linestyle='-', axes=ax, color=color)
    # one x tick per day
    # num_days = num2date(max(time)).day-num2date(min(time)).day+1
    # ax.set_xticks(linspace(min(time), max(time), num_days))
    # diagonal x ticks
    ax.set_xticklabels([format_date(d) for d in ax.get_xticks()], rotation=45)

def plot_precipitation(ax, weather_data, color):
    """
    plot a series of plots containing precipitation estimates
    """
    precipitation = [extract_precipitation(e) for e in weather_data if is_hourly_precipitation(e)]
    time, min_precip, mean_precip, max_precip = zip(*precipitation)
    bar(time, mean_precip, width=0.1, bottom=0, color=color, edgecolor=color)

def plot_meteogram(address):
    """
    plot a meteogram for a given address
    """

    # fetch todays weather
    latLng = retrieve_position_openmapquest(address)
    weather_data = retrieve_weather_yrno(latLng)

    fig = figure()
    # plot clouds
    subplots_adjust(bottom=0.2, hspace=0)
    cloud_ax = subplot2grid((6, 1), (0, 0))
    plot_clouds(cloud_ax, weather_data)

    # plot temperature
    temp_ax = subplot2grid((6, 1), (1, 0), rowspan=5)
    plot_temperature(temp_ax, weather_data, 'b')
    # skip top y tick (because of fog)
    temp_ax.set_yticks(array(temp_ax.get_yticks())[:-1])
    # make all left y labels blue
    for label in temp_ax.get_yticklabels():
        label.set_color('b')

    # synchronize x plot range in cloud plot and temp plot
    cloud_ax.set_xlim(*temp_ax.get_xlim())

    # plot precipitation inside temp plot
    precip_ax = temp_ax.twinx()
    plot_precipitation(precip_ax, weather_data, '#add8e6')
    # plot only in the buttom third
    precip_ax.set_ylim(top=precip_ax.get_ylim()[1]*3)
    # make all left y labels blue
    for label in precip_ax.get_yticklabels():
        label.set_color('#add8e6')

    legend()
    return(fig)

if __name__ == '__main__':
    fig = plot_meteogram('Oldenburg, Germany')
    show(fig)
