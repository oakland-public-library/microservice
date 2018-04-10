
var branches = window.branches;
var map = window.map;
var L = window.L;

function addMarkers() {
    for (var b in branches) {
        var branch = branches[b];
        var marker = L.marker(branch.latlon, {color: 'red'}).addTo(map);
        marker.bindPopup(branch.name);
    }
}

window.onload = function() {
    addMarkers();
    var latlngs = [
        branches['west'].latlon,
        branches['piedmont'].latlon,
        branches['montclair'].latlon
    ];
    var polyline = L.polyline(latlngs, {color: '#ff0044', weight: 6}).addTo(map);
};
