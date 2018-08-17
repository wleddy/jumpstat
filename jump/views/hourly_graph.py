

def hourly_graph(hourly_data,**kwargs):
    """
    Returns a fully formated, ready to eat snippet of html for 
    a simple bar chart of bike usage
    
    hourly_data is a dictionary in the form:
    
    {'start_date': 'a date string','end_date: 'a date string, 'days': nnumber of days in report,
        'hours': [ hours 0-23 in the order to report], 
        'trips':[ int values of trips for each our ], 'bikes': [ int values of bike counts for each hour],
        'max_bikes': highest in 'bikes', 'max_trips': highest in 'trips', 
    }
    or None if no data was available
    """
    
    if hourly_data:
        # setup some values to set the overall look
        options ={
            'bar_width': 7,
            'bar_max_height':80,
            'bar_set_spacer':1,
            'bar_bikes_color':'red',
            'bar_trips_color':'blue',
            'bikes_scale':.5,
            'trips_scale':0,
            
        }
        options['graph_box_width'] = int(((options['bar_width'] * 2) + options['bar_set_spacer']) * 24 * 1)
        options['graph_box_height'] = options['bar_max_height'] + 50
        if hourly_data['max_bikes'] > 0:
            options['bikes_scale'] = options['bar_max_height'] / hourly_data['max_bikes']
        else:
            options['bikes_scale'] = 0
            
        if hourly_data['max_trips'] > 0:
            options['trips_scale'] = options['bar_max_height'] / hourly_data['max_trips']
        else:
            options['trips_scale'] = 0
        
        out = '<div id="hourly-graph">'
        out += get_style(hourly_data,options)
        out += get_html(hourly_data)
        
        return out + '</div>'
        
        
    return ""
    
    
    
def get_style(hourly_data,options):
    """Return the style bit"""
    
    style = """<style>
                #hourly-graph {{
                    position:relative;
                    left:10px;
                    margin: 0 auto;
                    height:{}px;
                    width:{}px;
                }}
                .bar, .bar2 {{
                    position:absolute;
                    display:inline-block;
                    width:{}px;
                    margin:0;
                    padding:0;
                    border:none;
                }}
                .bar {{background-color:{};}}
                .bar2 {{background-color:{};}}
                """.format(options['graph_box_height'],
                    options['graph_box_width'], 
                    options['bar_width'],
                    options['bar_bikes_color'],
                    options['bar_trips_color'],
                    
                    )
                
    bar_style = ''
    import pdb
    for x in range(24):
        bikes = hourly_data['bikes']
        trips = hourly_data['trips']
        if bikes[x] > 0 or trips[0] > 0:
            #pdb.set_trace()
            pass
        if x == 0:
            bikes_left = 0
            trips_left = options['bar_width']
        else:
            bikes_left = (((options['bar_width']*2 ) + options['bar_set_spacer']) * x)
            trips_left = options['bar_width'] + bikes_left
        bike_bar_height = int(round(bikes[x] * options['bikes_scale'],0))
        trip_bar_height = int(round(trips[x] * options['bikes_scale'],0))
        bar_style += '    .loc-1-{col} {{left:{left}px;height:{height}px;margin-top:{top}px;}}\n'.format(
            col=x+1,
            left=bikes_left,
            height=bike_bar_height,
            top=options['bar_max_height'] - bike_bar_height,
           )
        bar_style += '    .loc-2-{col} {{left:{left}px;height:{height}px;margin-top:{top}px;}}\n'.format(
            col=x+1,
            left=trips_left,
            height=trip_bar_height,
            top=options['bar_max_height'] - trip_bar_height,
           )
    style += bar_style
    
    title1 = options['bar_max_height'] + 2
    title2 = title1 + 10
    title3 = title2 + 10
    title4 = title3 +10
    
    style += """\n.bike-color-box, .trip-color-box {{
                    display:inline-block;
                    width:1em;
                    background-color:{bar_bikes_color};
                }}
                .trip-color-box {{
                    background-color:{bar_trips_color};
                }}
                .col-title1, .col-title2, .col-title3, .col-title4 {{
                    display:inline-block;
                    position:absolute;
                    margin-top:{title1}px;
                    text-align:center;
                    font-size:10px;
                    width:14px;
                }}
                
                .col-title2 {{margin-top:{title2}px;}}
                .col-title3 {{margin-top:{title3}px;}}
                .col-title4 {{margin-top:{title4}px;}}
            </style>
        """.format(
            graph_box_width=options['graph_box_width'],
            bar_trips_color=options['bar_trips_color'],
            bar_bikes_color=options['bar_bikes_color'],
            title1 = title1,
            title2 = title2,
            title3 = title3,
            title4 = title4,
        )

    return style
    
def get_html(hourly_data):
    html = ''
    for x in range(24):
        html += '<p class="bar loc-1-{x}"></p>\n<p class="bar2 loc-2-{x}"></p>\n'.format(x=x+1)
        
    noon = "Noon"
    mid = "mid "
    for row in range(4):
        for x in range(24):
            hour = hourly_data['hours'][x]
            if hour == 0:
                hour = mid[row]
            elif hour == 12:
                hour = noon[row]
            elif row > 0:
                hour = None
            if hour != None:
                html += '<p class="col-title{} loc-1-{}">{}</p>\n'.format(row+1,x+1,hour)
        

    return html