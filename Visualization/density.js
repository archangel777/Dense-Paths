var map;
var polylines;
var polygons;
var markers;
var lat_offset = 0.00142;
var lng_offset = 0.0062;

var myStyle = [
   {
     featureType: "all",
     elementType: "labels",
     stylers: [
       { visibility: "off" }
     ]
   },{
     featureType: "transit",
     stylers: [
        { visibility: "off" }
      ]
   },{
     featureType: "road",
     elementType: "geometry",
     stylers: [
        { visibility: "simplified" }
      ]
   }
 ];

function initMap() {
  map = new google.maps.Map(document.getElementById('map'), {
    mapTypeControlOptions: {
      mapTypeIds: ['mystyle', google.maps.MapTypeId.ROADMAP, google.maps.MapTypeId.TERRAIN]
    },
    center: {lat: 39.9, lng: 116.4},
    zoom: 12,
    mapTypeId: 'mystyle',
  });

  map.mapTypes.set('mystyle', new google.maps.StyledMapType(myStyle, { name: 'My Style' }));
}

function clearMap() {
  for (x in polylines) {
    polylines[x].setMap(null);
  }
  polylines = [];
  for (x in markers) {
    markers[x].setMap(null);
  }
  markers = [];
  Edge.edgeList = [];
  console.log('clear');
}

function readSingleFile(evt) {
  //Retrieve the first (and only!) File from the FileList object
  var f = evt.target.files[0];

  if (f) {
    var r = new FileReader();
    r.filename = f.name;
    r.onload = function(e) {
      var contents = e.target.result;
      clearMap();
      splt = e.target.filename.split('_');
      hour = splt[splt.length-1].split('.')[0];
      document.getElementById('hour').innerHTML = hour + ':00 to ' + hour + ':59';
      if (e.target.filename.includes('clear') || e.target.filename.includes('hot') || e.target.filename.includes('traj')) {
        processData(contents);
      }
      if (e.target.filename.includes('edges')) {
        processEdges(contents);
      }
    }
    r.readAsText(f);
  } else {
    alert("Failed to load file");
  }
}
document.getElementById('fileinput').addEventListener('change', readSingleFile, false);

function Edge(_id, from, to, density) {
  self = {
    id: _id,
    from: from,
    to: to,
    dens: density
  }
  Edge.edgeList.push(self);
  Edge.sorted = false;
  return self;
}

Edge.edgeList = [];

Edge.sort = function() {
  Edge.edgeList.sort(function(a, b) {
    return a.dens - b.dens;
  });
  Edge.sorted = true;
}

Edge.getMax = function() {
  if (!Edge.sorted) {
    Edge.sort();
  }
  return Edge.edgeList[Edge.edgeList.length - 1].dens;
}

Edge.calculateRelativeDensities = function() {
  maxDens = Edge.getMax();
  console.log(maxDens);
  for (key in Edge.edgeList) {
    e = Edge.edgeList[key];
    e.relDens = e.dens/maxDens;
  }
}

function processEdges(contents) {
  var isRelative = false;
  var BOTTOM_REL = 0.2;
  var TOP_REL = 0.4;
  var BOTTOM_ABS = 4;
  var TOP_ABS = 15;
  var raw_edges = contents.split('\n');
  for (e in raw_edges) {
    if (raw_edges[e] !== '') {
      splt = raw_edges[e].split(";");
      Edge(
        splt[0],
        {lat: parseFloat(splt[1]) + lat_offset, lng: parseFloat(splt[2]) + lng_offset},
        {lat: parseFloat(splt[3]) + lat_offset, lng: parseFloat(splt[4]) + lng_offset},
        parseFloat(splt[5])
      );
    }
  }

  Edge.calculateRelativeDensities();

  console.log(Edge.edgeList[0].dens + "|" + Edge.edgeList[Edge.edgeList.length - 1].dens);

  for (key in Edge.edgeList) {
    edge = Edge.edgeList[key];
    // Visualization paramethers
    var color = '#FF0000';
    var lineSize = 3;
    var opct = edge.relDens;
    // Drawing markers
    if ((edge.relDens > TOP_REL && isRelative) || (edge.dens > TOP_ABS && !isRelative)) {
      color = '#0000FF';
      lineSize = 6;
      opct = 1;
      lat_avg = (edge.from.lat + edge.to.lat)/2;
      lng_avg = (edge.from.lng + edge.to.lng)/2;
      var marker = new google.maps.Marker({
        position: {lat: lat_avg, lng: lng_avg},
        title: toString(edge.relDens)
      });
      //marker.setMap(map);
      //markers.push(marker);
    }
    // Drawing lines
    if ((edge.relDens >= BOTTOM_REL && isRelative) || (edge.dens >= BOTTOM_ABS && !isRelative)) {
    //if (edge.dens >= 10) {
      var path = new google.maps.Polyline({
        path: [edge.from, edge.to],
        geodesic: true,
        strokeColor: color,
        strokeOpacity: opct,
        strokeWeight: lineSize
      });
      path.setMap(map);
      polylines.push(path);
    }
  }
}

function processData(contents) {
  var trajectories = contents.split('\n');
  var datalist = [];
  for (x in trajectories) {
    datalist.push(trajectories[x].split(";"));
  }
  var lats = [];
  var lngs = [];
  for (x in datalist) {
    lataux = [];
    lngaux = [];
    for (var i = 1; i < datalist[x].length; i++) {
      if (i%2 !== 0) {
        lataux.push(parseFloat(datalist[x][i]) + lat_offset);
      } else {
        lngaux.push(parseFloat(datalist[x][i]) + lng_offset);
      }
    }
    lats.push(lataux);
    lngs.push(lngaux);
  }
  var trajectoryList = [];
  for (var i = 0; i < lats.length; i++) {
    coordinateList = [];
    for (var j = 0; j < lats[i].length; j++) {
      coordinateList.push({lat: lats[i][j], lng: lngs[i][j]});
    }
    trajectoryList.push(coordinateList);
  }
  console.log(trajectoryList);

  for (x in trajectoryList) {
    var path = new google.maps.Polyline({
      path: trajectoryList[x],
      geodesic: true,
      strokeColor: '#FF0000',
      strokeOpacity: 1,
      strokeWeight: 3
    });
    path.setMap(map);
    polylines.push(path);
  }
  console.log('ok');
}
