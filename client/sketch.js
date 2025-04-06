
let inpt, bttn, screen, socket, gameState, lastKey, server;

function setup() {
    createCanvas(windowWidth, windowHeight);
    frameRate(60);
    inpt = createInput();
    inpt.position(20, 20);
    inpt.attribute("placeholder", "username");
    bttn = createButton("play");
    bttn.position(30 + inpt.width, 20);
    screen = 0;
    gameState = null;
    lastKey = "";
    server = "";
    let connect = (reattempts = 1) => {
        socket = new WebSocket("/ws/pacman?username=" + inpt.value());

        socket.onopen = () => {
            screen = 1;
        };
        socket.onclose = () => {
            if (reattempts > 0) {
                setTimeout(() => {
                    connect(reattempts - 1);
                }, 100);
            } else {
                screen = 0;
            }
        };
        socket.onmessage = (event) => {
            // handle different messages
            let message = JSON.parse(event.data);
            if (message.type === "gamestate") {
                gameState = message.content;
                server = message.sender;
            }
        };
        socket.onerror = (event) => {
            //
        };
    };
    bttn.mousePressed(connect);
}

function keyPressed() {
    if (screen === 1 && lastKey != key) {
        try {
            socket.send(key);
        } catch (err) {
            console.log("cant send key press");
        }
        lastKey = key;
    }
}

function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
}

function draw() {
    background(0);
    switch (screen) {
        case 0:
            inpt.show();
            bttn.show();
            break;
        case 1:
            inpt.hide();
            bttn.hide();
            let frameWidth = min(windowWidth, 500);
            let frameHeight = frameWidth * 2;
            let margin = frameWidth / 10;
            let mazeWidth = frameWidth - margin * 2;
            let tileSize = mazeWidth / maze[0].length;
            let mazeHeight = tileSize * maze.length;
            drawMaze(margin, margin, tileSize);
            if (gameState != null) {
                for (let pac in gameState) {
                    drawPacman(margin, margin, tileSize, gameState[pac]);
                }
            }
            noStroke();
            fill(255, 255, 255);
            textAlign(LEFT, TOP);
            textSize(tileSize * 3 / 4);
            text("SERVER UUID: " + server, margin + tileSize, margin + mazeHeight + tileSize * 1);
    }
}

function drawPacman(mx, my, ts, gs) {
    noStroke();
    fill(255, 255, 0);
    let x = mx + (gs.smoothX % maze[0].length) * ts + ts / 2;
    let y = my + (gs.smoothY % maze.length) * ts + ts / 2;
    let g = Math.abs(gs.f - 10) / 10;
    if (g === 0) g = 1 / 10;
    let a1 = g * HALF_PI / 2 + HALF_PI * max(gs.d - 1, 0);
    let a2 = g * - HALF_PI / 2 + HALF_PI * max(gs.d - 1, 0);
    arc(x, y, ts * 3 / 2, ts * 3 / 2, a1, a2, PIE);
    textSize(ts);
    x = mx + (gs.smoothX % maze[0].length) * ts;
    y = my + (gs.smoothY % maze.length) * ts - ts * 2;
    text(gs.username, x, y);
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