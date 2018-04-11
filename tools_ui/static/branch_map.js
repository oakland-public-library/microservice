
var branches = window.branches;
var map = window.map;
var L = window.L;

function addMarkers() {
    for (var b in branches) {
        var branch = branches[b];

        // var marker = L.marker([branch.lat, branch.lon], {color: 'red'}).addTo(map);
        var marker = L.marker([branch.lat, branch.lon], { opacity: 1.0, url: "/branch/" + branch.code });
        marker.bindTooltip("<h1>" + branch.name + "</h1><p>" + branch.address + "<br>" + branch.city_zip + "<br>" + branch.phone + "</p>", {className: "map_label", opacity: 0.95, offset: [0, 0] });
        // marker.bindPopup(branch.name + "<a href=\"/branch\">" + branch.name + "</a>");
        marker.on('click', function onClick(e) {
            window.location.href = e.target.options.url;
        });
        marker.addTo(map);
    }
}

window.onload = function() {
    addMarkers();
    var latlngs = [];
    var polyline = L.polyline(latlngs, {color: '#ff0044', weight: 6}).addTo(map);
};
