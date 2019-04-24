// auto update step and force values on the page
let step_xy_input = document.getElementById("step-xy-input");
let step_xy_range = document.getElementById("step-xy-range");
let force_xy_input = document.getElementById("force-xy-input");
let force_xy_range = document.getElementById("force-xy-range");
let step_z_input = document.getElementById("step-z-input");
let step_z_range = document.getElementById("step-z-range");
let force_z_input = document.getElementById("force-z-input");
let force_z_range = document.getElementById("force-z-range");

// apply changes from one input to another
step_xy_input.oninput = function () {if (this.value !== "") {step_xy_range.value = this.value;}}
step_xy_range.oninput = function () {step_xy_input.value = this.value;}
force_xy_input.oninput = function () {if (this.value !== "") {force_xy_range.value = this.value;}}
force_xy_range.oninput = function () {force_xy_input.value = this.value;}
step_z_input.oninput = function () {if (this.value !== "") {step_z_range.value = this.value;}}
step_z_range.oninput = function () {step_z_input.value = this.value;}
force_z_input.oninput = function () {if (this.value !== "") {force_z_range.value = this.value;}}
force_z_range.oninput = function () {force_z_input.value = this.value;}

// buttons handlers and data sending/receiving
let socket = io.connect('http://' + document.domain + ':' + location.port);

function send_values(params) {
    console.log("Sending: " + JSON.stringify(params));
    socket.emit('command', params);
}

socket.on('connect', function() {
    let get_page_data = function(step_axis_id, force_axis_id) {
        let step = Number(document.getElementById(step_axis_id).value);
		let force = Number(document.getElementById(force_axis_id).value);
		return {S: step, F: force}
    }

    // x left -s
    let on_x_left_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy-range", "force-xy-range");
        send_values({
            command: "extraction-move",
            X: -data["S"],
            F: data["F"]});
    }
    // x right +s
    let on_x_right_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy-range", "force-xy-range");
        send_values({
            command: "extraction-move",
            X: data["S"],
            F: data["F"]});
    }
    // y forward +s
    let on_y_forward_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy-range", "force-xy-range");
        send_values({
            command: "extraction-move",
            Y: data["S"],
            F: data["F"]});
    }
    // y backward -s
    let on_y_backward_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy-range", "force-xy-range");
        send_values({
            command: "extraction-move",
            Y: -data["S"],
            F: data["F"]});
    }
    // z up +s
    let on_z_up_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-z-range", "force-z-range");
        send_values({
            command: "extraction-move",
            Z: data["S"],
            F: data["F"]});
    }
    // z down -s
    let on_z_down_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-z-range", "force-z-range");
        send_values({
            command: "extraction-move",
            Z: -data["S"],
            F: data["F"]});
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
	var xs="X=";
  var ys="Y=";
  var zs="Z=";
  var x=parseInt(msg.slice(msg.search(xs)+2, msg.search(ys)-1));
  var y=parseInt(msg.slice(msg.search(ys)+2, msg.search(zs)-1));
  var img = document.getElementById("base");
  var canvas = document.getElementById("canvas");
  var ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, 613, 450);
	ctx.drawImage(img, 10, 10);
  ctx.fillRect(x+194, 240-y, 20, 20);
  console.log("Got response:", msg);
  

	if (typeof msg !== 'undefined') {
		$('h3').remove();
		$('div.message_holder').remove;
		$('div.message_holder').append('<div>' + msg + '</div>');
    }
});

// on set Z axis btn handler
function on_z_current_assign_btn(event) {
    let z_current = Number(document.getElementById("z-current-input").value);
    if (z_current !== "") {
        send_values({
                command: "set-z-current",
                z_current: z_current});
    }
}

// control tabs switch handler
function on_tab_btn(event, tab_name) {
  // Declare all variables
  let i, tabcontent, tablinks;

  // Get all elements with class="tabcontent" and hide them
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Get all elements with class="tablinks" and remove the class "active"
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  // Show the current tab, and add an "active" class to the button that opened the tab
  document.getElementById(tab_name).style.display = "flex";
  event.currentTarget.className += " active";
}
// open default "opened" tab on page load
document.getElementById("default-opened-tab").click();
