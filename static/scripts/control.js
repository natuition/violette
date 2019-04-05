// auto update step and force values on the page
let step_xy = document.getElementById("step-xy");
let force_xy = document.getElementById("force-xy");
let step_z = document.getElementById("step-z");
let force_z = document.getElementById("force-z");

let step_xy_value = document.getElementById("step-xy-value");
let force_xy_value = document.getElementById("force-xy-value");
let step_z_value = document.getElementById("step-z-value");
let force_z_value = document.getElementById("force-z-value");

step_xy_value.innerHTML = step_xy.value;
force_xy_value.innerHTML = force_xy.value;
step_z_value.innerHTML = step_z.value;
force_z_value.innerHTML = force_z.value;

step_xy.oninput = function () {step_xy_value.innerHTML = this.value;}
force_xy.oninput = function () {force_xy_value.innerHTML = this.value;}
step_z.oninput = function () {step_z_value.innerHTML = this.value;}
force_z.oninput = function () {force_z_value.innerHTML = this.value;}

// buttons handlers and data sending/receiving
let socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('connect', function() {
    let get_page_data = function(step_axis, force_axis) {
        let step = Number(document.getElementById(step_axis).value);
		let force = Number(document.getElementById(force_axis).value);
		return {S: step, F: force}
    }

    let send_values = function(values) {
        console.log("Sending: " + JSON.stringify(values));
        socket.emit('command', values);
    }

    // x left -s
    let on_x_left_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy", "force-xy");
        send_values({X: -data["S"], F: data["F"]});
    }
    // x right +s
    let on_x_right_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy", "force-xy");
        send_values({X: data["S"], F: data["F"]});
    }
    // y forward +s
    let on_y_forward_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy", "force-xy");
        send_values({Y: data["S"], F: data["F"]});
    }
    // y backward -s
    let on_y_backward_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy", "force-xy");
        send_values({Y: -data["S"], F: data["F"]});
    }
    // z up +s
    let on_z_up_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-z", "force-z");
        send_values({Z: data["S"], F: data["F"]});
    }
    // z down -s
    let on_z_down_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-z", "force-z");
        send_values({Z: -data["S"], F: data["F"]});
    }

    let on_left = $('#move-left').on('click', on_x_left_btn);
    let on_right = $('#move-right').on('click', on_x_right_btn);
    let on_forward = $('#move-forward').on('click', on_y_forward_btn);
    let on_backward = $('#move-backward').on('click', on_y_backward_btn);
    let on_up = $('#move-up').on('click', on_z_up_btn);
    let on_down = $('#move-down').on('click', on_z_down_btn);
    // let on_stop = $('#stop').on('click', on_stop_btn);
});

socket.on('response', function(msg) {
	console.log("Got response:", msg);

	if (typeof msg !== 'undefined') {
		$('h3').remove();
		$('div.message_holder').remove;
		$('div.message_holder').append('<div>' + msg + '</div>');
    }
});
