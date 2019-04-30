// response messages block
let response_messages = document.getElementById('response_messages');

// extraction auto update step and force values on the page
let step_xy_input = document.getElementById("step-xy-input");
let step_xy_range = document.getElementById("step-xy-range");
let force_xy_input = document.getElementById("force-xy-input");
let force_xy_range = document.getElementById("force-xy-range");
let step_z_input = document.getElementById("step-z-input");
let step_z_range = document.getElementById("step-z-range");
let force_z_input = document.getElementById("force-z-input");
let force_z_range = document.getElementById("force-z-range");

// extraction - apply changes from one input to another
step_xy_input.oninput = function () {if (this.value !== "") {step_xy_range.value = this.value;}}
step_xy_range.oninput = function () {step_xy_input.value = this.value;}
force_xy_input.oninput = function () {if (this.value !== "") {force_xy_range.value = this.value;}}
force_xy_range.oninput = function () {force_xy_input.value = this.value;}
step_z_input.oninput = function () {if (this.value !== "") {step_z_range.value = this.value;}}
step_z_range.oninput = function () {step_z_input.value = this.value;}
force_z_input.oninput = function () {if (this.value !== "") {force_z_range.value = this.value;}}
force_z_range.oninput = function () {force_z_input.value = this.value;}

// navigation auto update step and force values on the page
let motion_step_input = document.getElementById("motion-step-input");
let motion_step_range = document.getElementById("motion-step-range");
let motion_force_input = document.getElementById("motion-force-input");
let motion_force_range = document.getElementById("motion-force-range");
let turning_step_input = document.getElementById("turning-step-input");
let turning_step_range = document.getElementById("turning-step-range");
let turning_force_input = document.getElementById("turning-force-input");
let turning_force_range = document.getElementById("turning-force-range");

// extraction - apply changes from one input to another
motion_step_input.oninput = function () {if (this.value !== "") {motion_step_range.value = this.value;}}
motion_step_range.oninput = function () {motion_step_input.value = this.value;}
motion_force_input.oninput = function () {if (this.value !== "") {motion_force_range.value = this.value;}}
motion_force_range.oninput = function () {motion_force_input.value = this.value;}
turning_step_input.oninput = function () {if (this.value !== "") {turning_step_range.value = this.value;}}
turning_step_range.oninput = function () {turning_step_input.value = this.value;}
turning_force_input.oninput = function () {if (this.value !== "") {turning_force_range.value = this.value;}}
turning_force_range.oninput = function () {turning_force_input.value = this.value;}


// buttons handlers and data sending/receiving
let socket = io.connect('http://' + document.domain + ':' + location.port);

function send_values(params) {
    console.log("Sending: " + JSON.stringify(params));
    socket.emit('command', params);
}

function get_page_data(step_axis_id, force_axis_id) {
    let step = Number(document.getElementById(step_axis_id).value);
    let force = Number(document.getElementById(force_axis_id).value);
    return {S: step, F: force}
}

socket.on('connect', function() {
    // x left -s
    let on_x_left_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy-range", "force-xy-range");
        send_values({
            command_handler: "extraction-move",
            X: -data["S"],
            F: data["F"]});
    }
    // x right +s
    let on_x_right_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy-range", "force-xy-range");
        send_values({
            command_handler: "extraction-move",
            X: data["S"],
            F: data["F"]});
    }
    // y forward +s
    let on_y_forward_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy-range", "force-xy-range");
        send_values({
            command_handler: "extraction-move",
            Y: data["S"],
            F: data["F"]});
    }
    // y backward -s
    let on_y_backward_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-xy-range", "force-xy-range");
        send_values({
            command_handler: "extraction-move",
            Y: -data["S"],
            F: data["F"]});
    }
    // z up +s
    let on_z_up_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-z-range", "force-z-range");
        send_values({
            command_handler: "extraction-move",
            Z: data["S"],
            F: data["F"]});
    }
    // z down -s
    let on_z_down_btn = function(event) {
        event.preventDefault();
        data = get_page_data("step-z-range", "force-z-range");
        send_values({
            command_handler: "extraction-move",
            Z: -data["S"],
            F: data["F"]});
    }

    let on_left = $('#move-left').on('click', on_x_left_btn);
    let on_right = $('#move-right').on('click', on_x_right_btn);
    let on_forward = $('#move-forward').on('click', on_y_forward_btn);
    let on_backward = $('#move-backward').on('click', on_y_backward_btn);
    let on_up = $('#move-up').on('click', on_z_up_btn);
    let on_down = $('#move-down').on('click', on_z_down_btn);
});

function on_enable_disable_engines_btn(event, command){
    send_values({
        command_handler: "enable_disable_engines",
        command: command
    });
}

function on_send_raw_gcode_btn(){
    let g_code_input = document.getElementById("raw_gcode_input");
    let g_code = g_code_input.value;
    g_code_input.value = "";
    send_values({
        command_handler: "raw_g_code",
        raw_g_code: g_code
    });
}

function scrollToBottom() {
    // scroll response messages to bottom
	response_messages.scrollTop = response_messages.scrollHeight;
}

function add_message(msg) {
    let shouldScroll = response_messages.scrollTop + response_messages.clientHeight === response_messages.scrollHeight;

	let para = document.createElement("div");
	let node = document.createTextNode(msg);
	para.appendChild(node);
	response_messages.appendChild(para);

    if (!shouldScroll) {scrollToBottom();}
}

function update_visualization(x, y, z) {
    let img = document.getElementById("base");
    let canvas = document.getElementById("canvas");
    let ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, 613, 450);
    ctx.font = "15px Arial";
    ctx.drawImage(img, 10, 10);
    ctx.fillText(`Current coordinates: X=${x} Y=${y} Z=${z}`, 10, 20);
    ctx.fillRect(x + 194, 240 - y, 20, 20);
}

// on manual set Z axis btn handler
function on_z_current_assign_btn(event) {
    let z_current = Number(document.getElementById("z-current-input").value);
    if (z_current !== "") {
        send_values({
                command_handler: "set-z-current",
                z_current: z_current});
    }
}

// NAVIGATION
function on_navigation_right_btn(event) {
    event.preventDefault();
    data = get_page_data("turning-step-range", "turning-force-range");
    send_values({
        command_handler: "navigation_turning",
        E: data["S"],
        F: data["F"]});
}

function on_navigation_left_btn(event) {
    event.preventDefault();
    data = get_page_data("turning-step-range", "turning-force-range");
    send_values({
        command_handler: "navigation_turning",
        E: -data["S"],
        F: data["F"]});
}

function on_navigation_forward_btn(event) {
    event.preventDefault();
    data = get_page_data("motion-step-range", "motion-force-range");
    send_values({
        command_handler: "navigation_motion",
        E: data["S"],
        F: data["F"]});
}

function on_navigation_backward_btn(event) {
    event.preventDefault();
    data = get_page_data("motion-step-range", "motion-force-range");
    send_values({
        command_handler: "navigation_motion",
        E: -data["S"],
        F: data["F"]});
}

function on_align_wheels_center_btn(event) {
    event.preventDefault();
    data = get_page_data("motion-step-range", "motion-force-range");
    send_values({
        command_handler: "align_wheels_center",
        F: data["F"]});
}

// control tabs switch handler
function on_tab_btn(event, tab_name) {
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

// SOCKET RESPONSE
socket.on('response', function(response_params) {
    update_visualization(response_params["X"], response_params["Y"], response_params["Z"]);
    let msg = "";
    if ("error_message" in response_params) {
        msg = "Response: executed g-code: " + response_params["executed_g_code"] + " - error: " + response_params["error_message"];
    }
    else {
        msg = "Response: executed g-code: " + response_params["executed_g_code"] + " - resp. msg.: " + response_params["response_message"];
    }

    console.log(msg);
    add_message(msg);
});

// corkscrew current position area
window.onload = function() {
    var c = document.getElementById("canvas");
    var ctx = c.getContext("2d");
    var img = document.getElementById("base");
    ctx.drawImage(img, 10, 10);
    ctx.lineWidth = 2;
    ctx.fillRect(181, 150, 20, 20);
}

// response messages
scrollToBottom();
