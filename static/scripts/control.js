// update step/force values on page
let step_xy = document.getElementById("step-xy");
let force_xy = document.getElementById("force-xy");
let step_value = document.getElementById("step-xy-value");
let force_value = document.getElementById("force-xy-value");
step_value.innerHTML = step_xy.value;
force_value.innerHTML = force_xy.value;

step_xy.oninput = function () {step_value.innerHTML = this.value;}
force_xy.oninput = function () {force_value.innerHTML = this.value;}

// buttons handlers and data sending/receiving
var socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('connect', function() {

    let common_handler = function(event) {
        event.preventDefault();
        let id = event.target.id;
		let step = Number(document.getElementById("step-xy").value);
		let force = Number(document.getElementById("force-xy").value);
        let x = 0;
        let y = 0;

        if (id === "move-left") {x = -step;}
        else if (id === "move-right") {x = step;}
        else if (id === "move-forward") {y = step;}
        else if (id === "move-backward") {y = -step;}
        // else if (id === "stop") {}

        console.log("Sending: X", x, "Y", y, "F", force);
        socket.emit('command', {X : x, Y : y, F: force});
    }

    let on_left = $('#move-left').on('click', common_handler);

    let on_right = $('#move-right').on('click', common_handler);

    let on_forward = $('#move-forward').on('click', common_handler);

    let on_backward = $('#move-backward').on('click', common_handler);

    // let on_stop = $('#stop').on('click', common_handler);
});

socket.on('response', function(msg) {
	console.log("Got response:", msg);

	if (typeof msg !== 'undefined') {
		$('h3').remove();
		$('div.message_holder').remove;
		$('div.message_holder').append('<div>' + msg + '</div>');
    }
});
