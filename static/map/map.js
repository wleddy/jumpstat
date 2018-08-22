/**
 * jumpstat Map Implementation
 *
 * @param mapboxProjectId
 * @param mapboxAccessToken
 * @param mapDivId
 * @constructor
 */
	
function JumpMap(mapboxProjectId, mapboxAccessToken, mapDivId) {
	// create a layerGroup each for pushpin and canvas markers
	this.pushPinLayer = new L.LayerGroup();
	this.canvasLayer = new L.LayerGroup();
	initialZoom = 2;
    this.map = L.map(mapDivId, {
        center: [43.551253, -121.488683],
        zoom: initialZoom,
    });
	
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
        '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
        zoom: this.map.options.zoom,
        id: mapboxProjectId,
        accessToken: mapboxAccessToken
    }).addTo(this.map);

    if (L.markerClusterGroup !== undefined) {
        this.cluster = L.markerClusterGroup();
    }
	
    this.geocodes = [];
    this.locations = [];
}

function getJumpIcon(){
    var jumpIcon = L.icon({
    iconUrl: '/static/map/images/jumpMarker-8.png',
    iconSize: [8, 8],
    iconAnchor: [4, 4],
    popupAnchor: [2, 2],
    });        
    return jumpIcon
}


JumpMap.prototype = {
    
    constructor: JumpMap,
    
	/**
	Add markers using JSON object
	*
	* @param JSON object with all marker data
	* @param url of error response page
	*
	*/
    
	markerData: {},
    local_locations: [],
    
	addMarkersFromJSON: function(data,errorPage){
		var parseError =false;
		var errorMess = '';
		var mapIcon = getJumpIcon();

		try{
			markerData = JSON.parse(data);
            markerData.frame_start_time = 0;
            markerData.frame_end_time = 0;
            
		}catch(errorMess){
			alert("err '" + errorMess + "'");
			parseError = true;
		}
		if(!parseError){			
			for (var i = 0; i < markerData.markers.length; i++) {
			    data = markerData.markers[i]
                /*
                Each marker element is an array as:
                    lng,
                    lat,
                    starting_time_code,
                    ending_time_code
                */
				if(	data.length == 4 && 
					!this.mapHasMarkerAt(data[0],data[1])
					){
					
					var options = {};
					var draggable = false;
					if (data.draggable != undefined){
						draggable = (data.draggable == true );
					}
					options.draggable = draggable;
					options.icon = mapIcon
					var marker = L.marker([data[1], data[0]],options);
                    // all markers are hidden by default
					marker.setOpacity(0);
                    
					this.pushNewLocation(data,marker)
                    
					//this.setDragFunction(marker);
					
                    /*
					popper = "Unnamed Location"
					if (data.popup != undefined) {
						popper = data.popup;
					} else {
						if(data.locationName != undefined){
							popper = data.locationName;
						}
					
					} // bindPopup
					marker.bindPopup(popper);
					*/
                    
                    /*
					if (data.divIcon != undefined){
						var divIcon = new L.DivIcon({
					        className: 'divIcon',
					        html: data.divIcon,
							iconAnchor: new L.Point(20, 80),
							popupAnchor: new L.Point(0, -80),
					    });
    					marker.options.icon = divIcon;
					}
                    */
                    
                    
					// Put the maker into the cluster layer if reqested
					if (markerData.cluster === true) {
			            this.cluster.addLayer(marker);
			        } 
					// add the marker (layer) to the pushPinLayer LayerGroup
					this.pushPinLayer.addLayer(marker);
					
				} // Have minimal Data
					
			} // end for: all markers created
            this.pushPinLayer.addTo(this.map)
            
			if (markerData.cluster === true) {
				this.pushPinLayer = this.cluster;
			}
			this.setZoomFunction(this.map,this.pushPinLayer,this.canvasLayer);
			//this.map.setZoom(initialZoom-1);
            

	        if (markerData.zoomToFit === undefined || markerData.zoomToFit != false) {
					this.zoomToFitAllMarkers();
	        } else {
	            // Show the whole world
				this.map.fitWorld();
	        }
            
            local_locations = this.locations;
            // Play the animation
            if (markerData.frame_duration != undefined) {
                if (markerData.seconds_per_frame === undefined){
                    markerData.seconds_per_frame = 2;
                }
                this.animation();
                this.animator = setInterval(this.animation, markerData.seconds_per_frame * 1000);
            }
				
		}else{
			// error parsing JSON data
			// go to error page
			document.location = errorPage + errorMess + "/";
		}
		// end of addMarkersFromJSON()
	},
		
    /**
     * Push a new location to the locations array.
     * Also pushes the location lat/lon to the geocodes array (used to zoom map to markers).
     *
     * @param locationName
     * @param latitude
     * @param longitude
     * @param tripCount
     */
    pushNewLocation: function(sighting,marker) {
        this.locations.push(
            {
                lng: sighting[0],
                lat: sighting[1],
                starting_time_code: sighting[2],
                ending_time_code: sighting[3],
                marker: marker
            });

        this.geocodes.push([this.locations[this.locations.length -1].lat, this.locations[this.locations.length -1].lng]);
    },

	mapHasMarkerAt: function (lng,lat){
	    // Check if trip location already exists
	    for (var trip in this.locations) {
            if (this.locations.lat == lat && this.locations.lng == lng) {
                // if the location already exists return true
                return true;
	        }
	    }
		return false
	},
    
    animation: function(){
        markerData.frame_start_time = markerData.frame_end_time;
        markerData.frame_end_time = markerData.frame_end_time + markerData.frame_duration;
        if (markerData.frame_end_time > markerData.total_seconds) {
            // go to the begining
            markerData.frame_start_time = 0;
            markerData.frame_end_time = markerData.frame_duration;
        }
        //id="display_date"></span> <span id="display_time"
        the_time = markerData.frame_start_time / 3600;
        if (the_time < 0){ the_time = 0;}
        hours = Math.trunc(the_time);
        minutes = Math.trunc((the_time - hours)*60);
        
        $('#display_time').text('Time: '+("00" + hours.toString()).substr(-2)+ ":" + ("00" + minutes.toString()).substr(-2))
        if (local_locations == undefined){
            local_locations = this.locations;
        }
            for (var y=0; y<local_locations.length; y++){
                // check every marker
                my_loc = local_locations[y]
                if (local_locations[y].starting_time_code <= markerData.frame_start_time &&
                    local_locations[y].ending_time_code >= markerData.frame_end_time                           
                    ) {
                        local_locations[y].marker.setOpacity(1);
                    } else {
                        local_locations[y].marker.setOpacity(0);
                    }
            }
    },

    /**
     * Zoom the map to fit the location markers.
     */
    zoomToFitAllMarkers: function() {
        var bounds = new L.LatLngBounds(this.geocodes);
		this.map.fitBounds(bounds);
    },
	setDragFunction: function(theMarker){
		var self = this;
        /*
		// 'draggable' is in the 'options' object
        if (theMarker.options.draggable === true) {
            // Add drag event handler
            theMarker.on('dragend', function (event) {
                var marker = event.target;
                var position = marker.getLatLng();

                self.updateFormLocationFields("latitude", "longitude", position.lat, position.lng);
            });
		} */
    },
	setZoomFunction: function(theMap,clusterLayer,canvasLayer){
		if(theMap != undefined){
			theMap.on("zoomend", function (event) {
				var theZoom = theMap.getZoom()
                /*
				if (theZoom > this.options.flowMarkerMinZoom) {
					clusterLayer.remove();
					canvasLayer.addTo(theMap);
				} else {
					canvasLayer.remove();
					clusterLayer.addTo(theMap);
				}
                */
			});
		}
	}
};

