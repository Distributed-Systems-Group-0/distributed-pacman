
/// <reference path="global.d.ts"/>

const config = {
    inpt: null,
    bttn: null,
    lastKey: 0,
    screen: 0,
    socket: null,
    socketOpened: false,
    serverUUID: "",
    objects: {},
    pellets: {},
    username: ""
}

function setup() {
    createCanvas(windowWidth, windowHeight);
    frameRate(30);

    config.inpt = createInput();
    config.bttn = createButton("play");

    config.inpt.position(20, 20);
    config.inpt.attribute("placeholder", "username");
    config.inpt.input(() => {
        let val = config.inpt.value();
        val = val.replace(/[^0-9a-zA-Z]/g, "");
        val = val.substring(0, 7);
        config.inpt.value(val);
    });
    config.bttn.position(30 + config.inpt.width, 20);

    let connect = (reattempts = 2) => {
        let address = "/ws/pacman?username="
        config.username = config.inpt.value();
        config.socket = new WebSocket(address + config.username);
        config.socket.onopen = () => {
            config.screen = 1;
            config.socketOpened = true;
        };
        config.socket.onclose = () => {
            if (config.socketOpened === false) return;
            if (reattempts > 0) {
                const delay = (3 - reattempts) * 100;
                setTimeout(() => connect(reattempts - 1), delay);
                return;
            }

            config.screen = 0;
            config.socketOpened = false;
            reattempts = 2;

            config.objects = {};
            config.pellets = {};
        };
        config.socket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            switch (message.type) {
                case "state":
                    config.serverUUID = message.content.serverUUID;
                    for (const objectName of Object.keys(message.content.objects)) {
                        if (objectName in config.objects) {
                            config.objects[objectName].x = message.content.objects[objectName].x;
                            config.objects[objectName].y = message.content.objects[objectName].y;
                            config.objects[objectName].d = message.content.objects[objectName].d;
                        } else {
                            config.objects[objectName] = message.content.objects[objectName];
                        }
                    }
                    config.pellets = message.content.pellets;
                    const itemName = "item:player:" + config.username;
                    if (!(itemName in config.objects)) {
                        config.socket.close();
                    }
                    break;
                case "message":
                    console.log(message.content);
                    break;
                case "ping":
                    break;
                default:
                    console.log("unknown server response");
            }
        };
        config.socket.onerror = () => {
            //
        };
    };

    config.bttn.mousePressed(connect);
}

function mousePressed() {
    if (config.screen != 1) return;

    const swipeX = mouseX - windowWidth / 2;
    const swipeY = mouseY - windowHeight * 3 / 4;

    const mouseKey = Math.abs(swipeX) > Math.abs(swipeY)
        ? (swipeX > 0 ? 1 : 3)
        : (swipeY > 0 ? 2 : 4);

    if (config.lastKey === mouseKey) return;

    try {
        config.socket.send(mouseKey);
        config.lastKey = mouseKey;
    } catch (err) {
        console.log("cannot send mouse press");
    }
}

function keyPressed() {
    if (config.screen != 1) return;
    if (config.lastKey === keyCode) return;

    try {
        let keyKey;
        switch (keyCode) {
            case 39:
                keyKey = 1;
                break;
            case 40:
                keyKey = 2;
                break;
            case 37:
                keyKey = 3;
                break;
            case 38:
                keyKey = 4;
                break;
            default:
                return;
        }
        config.socket.send(keyKey);
        config.lastKey = keyKey;
    } catch (err) {
        console.log("cannot send key press");
    }
}

function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
}

function draw() {
    background(0);
    switch (config.screen) {
        case 0:
            config.inpt.show();
            config.bttn.show();
            break;
        case 1:
            config.inpt.hide();
            config.bttn.hide();

            let frameWidth = min(windowWidth, 500);
            let frameHeight = frameWidth * 2;
            let margin = frameWidth / 10;
            let mazeWidth = frameWidth - margin * 2;
            let tileSize = mazeWidth / maze[0].length;
            let mazeHeight = tileSize * maze.length;

            const itemName = "item:player:" + config.username;
            if (!(itemName in config.objects)) break;
            const item = config.objects[itemName];

            for (const objectName in config.objects) {
                const object = config.objects[objectName];
                let x = parseInt(object.x);
                let y = parseInt(object.y);
                let sx = parseFloat(object.smoothX);
                let sy = parseFloat(object.smoothY);
                if (abs(sx - x) > 0.1 || abs(sy - y) > 0.1) {
                    object.f = (parseInt(object.f) + 1) % 20;
                }
                config.objects[objectName].smoothX = lerp(sx, x, 0.15);
                config.objects[objectName].smoothY = lerp(sy, y, 0.15);
                if (abs(sx-x)>2) object.smoothX = object.x;
                if (abs(sy-y)>2) object.smoothY = object.y;
            }

            push();
            translate(-margin, 0);
            translate(-(config.objects[itemName].smoothX + 1 / 2) * tileSize, 0);
            translate(frameWidth / 2, 0);

            const currMaze = Math.floor(item.x / maze[0].length);
            drawMaze(mazeWidth * currMaze + margin, margin, tileSize);
            drawMaze(mazeWidth * (currMaze + 1) + margin, margin, tileSize);
            drawMaze(mazeWidth * (currMaze - 1) + margin, margin, tileSize);

            drawPacman(margin, margin, tileSize, item);

            for (const objectName in config.objects) {
                const object = config.objects[objectName];
                drawPacman(margin, margin, tileSize, object);
            }

            pop();

            noStroke();
            fill(0, 0, 0);
            rect(frameWidth, 0, mazeWidth * 2, frameHeight);

            textAlign(LEFT, TOP);
            noStroke();
            fill(255, 255, 255);
            textSize(tileSize);
            const abbrUUID = config.serverUUID.substring(0, 20);
            const textContent = `SERVER UUID: ${abbrUUID}...`;
            text(
                textContent,
                margin + tileSize,
                margin + mazeHeight + tileSize
            );

            // fill(255);
            // noStroke();
            // textAlign(LEFT, TOP);
            // textSize(32);
            break;
    }
}

function drawPacman(mx, my, ts, gs) {
    noStroke();
    fill(255, 255, 0);
    let x = mx + gs.smoothX * ts + ts / 2;
    let y = my + gs.smoothY * ts + ts / 2;
    let g = Math.abs(gs.f - 10) / 10;
    if (g === 0) g = 1 / 10;
    let a1 = g * HALF_PI / 2 + HALF_PI * max(gs.d - 1, 0);
    let a2 = g * - HALF_PI / 2 + HALF_PI * max(gs.d - 1, 0);
    arc(x, y, ts * 3 / 2, ts * 3 / 2, a1, a2, PIE);
    textSize(ts);
    x = mx + gs.smoothX * ts;
    y = my + gs.smoothY * ts - ts * 2;
    text(gs.username, x, y);
}

function drawMaze(mx, my, ts) {
    let x, y;
    for (let i = 0; i < maze[0].length; i++) {
        for (let j = 0; j < maze.length; j++) {
            x = mx + i * ts;
            y = my + j * ts;
            strokeWeight(ts / 10);
            noFill();
            switch (maze[j][i]) {
                case 10:
                    // empty space
                    break;
                case 11:
                    stroke(0, 0, 255);
                    arc(x + ts, y + ts, ts * 2, ts * 2, -PI, -HALF_PI);
                    arc(x + ts, y + ts, ts, ts, -PI, -HALF_PI);
                    break;
                case 12:
                    stroke(0, 0, 255);
                    line(x, y, x + ts, y);
                    line(x, y + ts / 2, x + ts, y + ts / 2);
                    break;
                case 13:
                    stroke(0, 0, 255);
                    line(x, y, x + ts, y);
                    arc(x, y + ts, ts, ts, -HALF_PI, 0);
                    break;
                case 14:
                    stroke(0, 0, 255);
                    line(x, y, x + ts, y);
                    arc(x + ts, y + ts, ts, ts, -PI, -HALF_PI);
                    break;
                case 15:
                    stroke(0, 0, 255);
                    arc(x, y + ts, ts * 2, ts * 2, -HALF_PI, 0);
                    arc(x, y + ts, ts, ts, -HALF_PI, 0);
                    break;
                case 16:
                    stroke(0, 0, 255);
                    line(x, y, x, y + ts);
                    line(x + ts / 2, y, x + ts / 2, y + ts);
                    break;
                case 17:
                    stroke(0, 0, 255);
                    line(x + ts / 2, y, x + ts / 2, y + ts);
                    break;
                case 18:
                    stroke(0, 0, 255);
                    line(x + ts / 2, y, x + ts / 2, y + ts);
                    line(x + ts, y, x + ts, y + ts);
                    break;
                case 19:
                    stroke(0, 0, 255);
                    arc(x + ts, y + ts, ts, ts, -PI, -HALF_PI);
                    break;
                case 20:
                    stroke(0, 0, 255);
                    line(x, y + ts / 2, x + ts, y + ts / 2);
                    break;
                case 21:
                    stroke(0, 0, 255);
                    arc(x, y + ts, ts, ts, -HALF_PI, 0);
                    break;
                case 22:
                    stroke(0, 0, 255);
                    arc(x + ts, y, ts, ts, HALF_PI, PI);
                    break;
                case 23:
                    stroke(0, 0, 255);
                    arc(x, y, ts, ts, 0, HALF_PI);
                    break;
                case 24:
                    stroke(0, 0, 255);
                    arc(x + ts, y, ts, ts, HALF_PI, PI);
                    arc(x + ts, y, ts * 2, ts * 2, HALF_PI, PI);
                    break;
                case 25:
                    stroke(0, 0, 255);
                    line(x, y + ts / 2, x + ts, y + ts / 2);
                    line(x, y + ts, x + ts, y + ts);
                    break;
                case 26:
                    stroke(0, 0, 255);
                    arc(x - ts / 2, y + ts * 3 / 2, ts, ts, -HALF_PI, 0);
                    arc(x - ts / 2, y + ts * 3 / 2, ts * 2, ts * 2, -HALF_PI, 0);
                    break;
                case 27:
                    stroke(0, 0, 255);
                    arc(x + ts * 3 / 2, y + ts * 3 / 2, ts, ts, -PI, -HALF_PI);
                    arc(x + ts * 3 / 2, y + ts * 3 / 2, ts * 2, ts * 2, -PI, -HALF_PI);
                    break;
                case 28:
                    stroke(0, 0, 255);
                    arc(x, y, ts, ts, 0, HALF_PI);
                    arc(x, y, ts * 2, ts * 2, 0, HALF_PI);
                    break;
                case 29:
                    stroke(0, 0, 255);
                    line(x + ts / 2, y + ts / 2, x + ts / 2, y + ts);
                    line(x, y + ts / 2, x, y + ts);
                    break;
                case 30:
                    stroke(0, 0, 255);
                    line(x + ts, y + ts / 2, x + ts, y + ts);
                    line(x + ts / 2, y + ts / 2, x + ts / 2, y + ts);
                    break;
                case 31:
                    stroke(0, 0, 255);
                    line(x, y, x, y + ts / 2);
                    line(x + ts / 2, y, x + ts / 2, y + ts / 2);
                    break;
                case 32:
                    stroke(0, 0, 255);
                    line(x + ts / 2, y + ts / 2, x + ts, y + ts / 2);
                    line(x + ts / 2, y + ts / 2, x + ts / 2, y + ts);
                    break;
                case 33:
                    stroke(255, 255, 255);
                    line(x, y + ts * 3 / 4, x + ts, y + ts * 3 / 4);
                    break;
                case 34:
                    stroke(0, 0, 255);
                    line(x, y + ts / 2, x + ts / 2, y + ts / 2);
                    line(x + ts / 2, y + ts / 2, x + ts / 2, y + ts);
                    break;
                case 35:
                    stroke(0, 0, 255);
                    line(x + ts, y, x + ts, y + ts / 2);
                    line(x + ts / 2, y, x + ts / 2, y + ts / 2);
                    break;
                case 36:
                    stroke(0, 0, 255);
                    arc(x - ts / 2, y - ts / 2, ts, ts, 0, HALF_PI);
                    arc(x - ts / 2, y - ts / 2, ts * 2, ts * 2, 0, HALF_PI);
                    break;
                case 37:
                    stroke(0, 0, 255);
                    arc(x + ts * 3 / 2, y - ts / 2, ts, ts, HALF_PI, PI);
                    arc(x + ts * 3 / 2, y - ts / 2, ts * 2, ts * 2, HALF_PI, PI);
                    break;
                case 38:
                    stroke(0, 0, 255);
                    line(x, y + ts / 2, x + ts / 2, y + ts / 2);
                    line(x, y + ts, x + ts / 2, y + ts);
                    break;
                case 39:
                    stroke(0, 0, 255);
                    line(x, y + ts / 2, x + ts / 2, y + ts / 2);
                    line(x, y, x + ts / 2, y);
                    break;
                case 40:
                    stroke(0, 0, 255);
                    line(x + ts, y + ts / 2, x + ts / 2, y + ts / 2);
                    line(x + ts, y + ts, x + ts / 2, y + ts);
                    break;
                case 41:
                    stroke(0, 0, 255);
                    line(x + ts, y + ts / 2, x + ts / 2, y + ts / 2);
                    line(x + ts, y, x + ts / 2, y);
                    break;
                case 42:
                    stroke(0, 0, 255);
                    line(x + ts / 2, y, x + ts / 2, y + ts / 2);
                    line(x + ts / 2, y + ts / 2, x + ts, y + ts / 2);
                    break;
                case 43:
                    stroke(0, 0, 255);
                    line(x + ts / 2, y, x + ts / 2, y + ts / 2);
                    line(x + ts / 2, y + ts / 2, x, y + ts / 2);
                    break;
                case 44:
                    stroke(0, 0, 255);
                    line(x, y, x, y + ts);
                    arc(x + ts, y, ts, ts, HALF_PI, PI);
                    break;
                case 45:
                    stroke(0, 0, 255);
                    line(x, y, x, y + ts);
                    arc(x + ts, y + ts, ts, ts, -PI, -HALF_PI);
                    break;
                case 46:
                    stroke(0, 0, 255);
                    line(x + ts, y, x + ts, y + ts);
                    arc(x, y, ts, ts, 0, HALF_PI);
                    break;
                case 47:
                    stroke(0, 0, 255);
                    line(x + ts, y, x + ts, y + ts);
                    arc(x, y + ts, ts, ts, -HALF_PI, 0);
                    break;
            }
        }
    }
}

const maze = [
    [11, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 13, 14, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 15],
    [16, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 17, 17, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 18],
    [16, 10, 19, 20, 20, 21, 10, 19, 20, 20, 20, 21, 10, 17, 17, 10, 19, 20, 20, 20, 21, 10, 19, 20, 20, 21, 10, 18],
    [16, 10, 17, 10, 10, 17, 10, 17, 10, 10, 10, 17, 10, 17, 17, 10, 17, 10, 10, 10, 17, 10, 17, 10, 10, 17, 10, 18],
    [16, 10, 22, 20, 20, 23, 10, 22, 20, 20, 20, 23, 10, 22, 23, 10, 22, 20, 20, 20, 23, 10, 22, 20, 20, 23, 10, 18],
    [16, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 18],
    [16, 10, 19, 20, 20, 21, 10, 19, 21, 10, 19, 20, 20, 20, 20, 20, 20, 21, 10, 19, 21, 10, 19, 20, 20, 21, 10, 18],
    [16, 10, 22, 20, 20, 23, 10, 17, 17, 10, 22, 20, 20, 21, 19, 20, 20, 23, 10, 17, 17, 10, 22, 20, 20, 23, 10, 18],
    [16, 10, 10, 10, 10, 10, 10, 17, 17, 10, 10, 10, 10, 17, 17, 10, 10, 10, 10, 17, 17, 10, 10, 10, 10, 10, 10, 18],
    [24, 25, 25, 25, 38, 26, 10, 17, 22, 20, 20, 21, 10, 17, 17, 10, 19, 20, 20, 23, 17, 10, 27, 40, 25, 25, 25, 28],
    [10, 10, 10, 10, 10, 29, 10, 17, 19, 20, 20, 23, 10, 22, 23, 10, 22, 20, 20, 21, 17, 10, 30, 10, 10, 10, 10, 10],
    [10, 10, 10, 10, 10, 16, 10, 17, 17, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 17, 17, 10, 18, 10, 10, 10, 10, 10],
    [10, 10, 10, 10, 10, 31, 10, 17, 17, 10, 32, 25, 25, 33, 33, 25, 25, 34, 10, 17, 17, 10, 35, 10, 10, 10, 10, 10],
    [12, 12, 12, 12, 39, 36, 10, 22, 23, 10, 18, 10, 10, 10, 10, 10, 10, 16, 10, 22, 23, 10, 37, 41, 12, 12, 12, 12],
    [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 18, 10, 10, 10, 10, 10, 10, 16, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
    [25, 25, 25, 25, 38, 26, 10, 19, 21, 10, 18, 10, 10, 10, 10, 10, 10, 16, 10, 19, 21, 10, 27, 40, 25, 25, 25, 25],
    [10, 10, 10, 10, 10, 29, 10, 17, 17, 10, 42, 12, 12, 12, 12, 12, 12, 43, 10, 17, 17, 10, 30, 10, 10, 10, 10, 10],
    [10, 10, 10, 10, 10, 16, 10, 17, 17, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 17, 17, 10, 18, 10, 10, 10, 10, 10],
    [10, 10, 10, 10, 10, 31, 10, 17, 17, 10, 19, 20, 20, 20, 20, 20, 20, 21, 10, 17, 17, 10, 35, 10, 10, 10, 10, 10],
    [11, 12, 12, 12, 39, 36, 10, 22, 23, 10, 22, 20, 20, 21, 19, 20, 20, 23, 10, 22, 23, 10, 37, 41, 12, 12, 12, 15],
    [16, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 17, 17, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 18],
    [16, 10, 19, 20, 20, 21, 10, 19, 20, 20, 20, 21, 10, 17, 17, 10, 19, 20, 20, 20, 21, 10, 19, 20, 20, 21, 10, 18],
    [16, 10, 22, 20, 21, 17, 10, 22, 20, 20, 20, 23, 10, 22, 23, 10, 22, 20, 20, 20, 23, 10, 17, 19, 20, 23, 10, 18],
    [16, 10, 10, 10, 17, 17, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 17, 17, 10, 10, 10, 18],
    [44, 20, 21, 10, 17, 17, 10, 19, 21, 10, 19, 20, 20, 20, 20, 20, 20, 21, 10, 19, 21, 10, 17, 17, 10, 19, 20, 46],
    [45, 20, 23, 10, 22, 23, 10, 17, 17, 10, 22, 20, 20, 21, 19, 20, 20, 23, 10, 17, 17, 10, 22, 23, 10, 22, 20, 47],
    [16, 10, 10, 10, 10, 10, 10, 17, 17, 10, 10, 10, 10, 17, 17, 10, 10, 10, 10, 17, 17, 10, 10, 10, 10, 10, 10, 18],
    [16, 10, 19, 20, 20, 20, 20, 23, 22, 20, 20, 21, 10, 17, 17, 10, 19, 20, 20, 23, 22, 20, 20, 20, 20, 21, 10, 18],
    [16, 10, 22, 20, 20, 20, 20, 20, 20, 20, 20, 23, 10, 22, 23, 10, 22, 20, 20, 20, 20, 20, 20, 20, 20, 23, 10, 18],
    [16, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 18],
    [24, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 28]
];