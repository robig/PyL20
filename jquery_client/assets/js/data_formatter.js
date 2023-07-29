function format_number2(v) {
    return (Math.round(v * 100) / 100).toFixed(2);
}

function format_min_max_eq15(v) {
    return format_min_max(v, 0, 60, -15, +15);
}

function format_min_max(val, fmin, fmax, min, max) {
    var fsteps=fmax - fmin;
    var tsteps=max - min;
    var ratio = tsteps/fsteps;
    var ret = +min +ratio*(val-fmin);
    return ret>0?'+'+format_number2(ret):format_number2(ret);
}

function format_pan(v) {
    // 0-100
    return v-50;
}

function format_fxsend10(v) {
    //0-60
    if(v==0) return "-&#x221E;"; //-infinity
    if(v>=30) return format_min_max(v,30,60,0,10);
    return format_min_max(v,0,30,-60,0);
}

function format_eq_lowcut(v) {
    //0-56 to 40-600
    return format_min_max(v,0,56,40,600);
}

function format_eq_mid_frq(v){
    return format_min_max(v, 0, 60, 100, 8000);
}