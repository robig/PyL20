

$('#svgintro').svg({onLoad: drawIntro});

var data={"pan": 50, "efx1":0, "eq": {"eq_off":0, "phase": 0, "pan":0, "eq_high":40/* 0-60*/ ,"eq_mid": 0, "eq_mid_frq":16 /* 0-96*/, "eq_low":20, "eq_lowcut":10 }};
var enableDataPoints=true;
function drawIntro(svg) { 
    svg.circle(75, 75, 50, 
        {fill: 'none', stroke: 'red', strokeWidth: 3}); 
    var g = svg.group({stroke: 'black', strokeWidth: 2}); 
    svg.line(g, 15, 75, 135, 75); 
    svg.line(g, 75, 15, 75, 135); 
}

$('.pan').svg({onLoad: drawPan});

function drawPan(svg) {
    console.log(svg);
    var value = data.pan;
    var max = 100;
    if(value > max) value = max;
    var width = 74;
    var height = 20;
    var ystart=3;
    var xstart=1;
    var x = xstart + value * width / max;
    var center = xstart + width / 2;
    svg.line(null, center, ystart-2, center, height+4, {stroke: '#171f2a', 'strokeWidth': 3}); 
    svg.line(null, x, ystart, x, height, {stroke: 'red', 'strokeWidth': 9+1}); 
    svg.line(null, x, ystart, x, height, {stroke: 'white', 'strokeWidth': 3});
}

function setPan(value) {
    data.pan = value;
    $('.pan').svg('destroy');
    $('.pan').svg({onLoad: drawPan}); 
}

function drawFx(svg) {
    var value = data.efx1;
    var max = 100;
    if(value > max) value = max;
    var width = 74;
    var height = 22;
    var ystart=2;
    var xstart=2;
    var x = xstart + value * width / max;
    var center = xstart + (x-xstart) / 2;
    svg.line(null, center, ystart, center, height, {stroke: '#23b9e6', 'strokeWidth': x}); 
    svg.line(null, x, ystart, x, height, {stroke: 'white', 'strokeWidth': 3});
}

function setFx(value) {
    data.efx1 = value;
    $('.efx1').svg('destroy');
    $('.efx1').svg({onLoad: drawFx}); 
}

setFx(10);

var b = new Binding({
	object: data,
	property: "efx1"
});

b.setRedrawCallback(evt=>{
    $('.efx1').svg('destroy');
    $('.efx1').svg({onLoad: drawFx}); 
});



function drawEq(svg) {
    var eq = data.eq;
    var max = 60;
    var frq_max = 96;
    var frq_rel = eq.eq_mid-(max/2);
    var frq_steps=8; //mid_frq 0-96
    var frq_step_val = frq_max / frq_steps;
    var values=[eq.eq_lowcut, eq.eq_low];
    var settings={"showPoints": enableDataPoints, "pointColor": "#c2ff274f", "lineColor": "#171f2a"};
    for(var i=0;i<frq_steps;i++){
        var diff = Math.max(1 - 1/2*Math.abs(i*frq_max/frq_steps - eq.eq_mid_frq)/frq_step_val, 0);
        var add= diff * frq_rel;
        var v=max/2 + add;
        //console.log("diff="+diff+ " add="+add + " v="+v);
        values.push(v);
    }
    values.push(eq.eq_high);
    
    var width = 74;
    var height = 40;
    var ystart=2;
    var xstart=2;
    var color='#b8f824';
    var step = (width-ystart)/(values.length-1);

    var points=[];
    for(var i=0; i<values.length; i++) {
        var x1=Math.floor(xstart + i*step);
        var y1=Math.floor(ystart +height -(values[i] * height / max) );
        console.log(" x=" + x1 + " y=" +y1+ " yBottom="+ Math.floor(values[i] * height / max));
        var y2=y1;
        if(i<values.length-1)
            y2=Math.floor(ystart +height -(values[i+1] * height / max) );

        points.push([x1,y1]);
        
        //svg.line(null, x1, y1, x2, y2, {stroke: color, 'strokeWidth': 2});
    }

    //Smoothen
    console.log("==========================");
    svg.line(null, 0,ystart+height/2, width, ystart+height/2, {stroke: settings.lineColor});

    var path = svg.createPath();
    //path=path.move(points[0][0], points[0][1]);
    svg.circle(null, points[0][0], points[0][1], 2, {stroke: settings.pointColor});
    var i=0;
    for(i=1; i<points.length-1;i+=2) {
        var from=points[i-1];
        var cent=points[i];
        var to=points[i+1]; 
        //path=path.line(from[0], from[1]);
        //if(i>0) path=path.smoothQ(from[0], from[1]);
        path=path.move(from[0], from[1]);
        path=path.curveQ(cent[0], cent[1], to[0], to[1]);
        console.log("i="+i + "%"+(i%4))
        if(settings.showPoints) {
            svg.circle(null, cent[0],cent[1], 2, {stroke: settings.pointColor});
            svg.circle(null, to[0],to[1], 2, {stroke: settings.pointColor});
        }
    }
    if(points[i]) {
        path=path.smoothQ(points[i][0], points[i][1]);
        //path=path.curveQ(points[i][0], points[i][1], points[i][0], points[i][1]);

        if(settings.showPoints) svg.circle(null, points[i][0], points[i][1], 2, {stroke: 'yellow'});
        //svg.polyline(null, more_points, {stroke: color, 'strokeWidth': 2});
    }

    svg.path(null, 
        path/*.move(50, 90)
        .curveC(0, 90, 0, 30, 50, 30) 
        .line(150, 30)
        .curveC(200, 30, 200, 90, 150, 90)
        .close(*/,  
        {fill: 'none', stroke: color, strokeWidth: 1});
}

function setEq(v) {
    data.eq.eq_lowcut=v[0];
    data.eq.eq_low=v[1];
    data.eq.eq_mid=v[2];
    data.eq.eq_high=v[3];
    $('.eq').svg('destroy');
    $('.eq').svg({onLoad: drawEq}); 
}
$('.eq').svg({onLoad: drawEq});

$(function() {
    $(".knob").knob({
        'displayInput': true,
        'width': 50,
        'height': 50,
        'class': 'knob',
        'knobColor': '#6c6c6c',
        'knobRadius': 23,

        'change': v=>{
            data.eq.eq_mid=v;
            var svg=$('.eq').svg('get');
            svg.clear(); drawEq(svg);
        }
    });
});