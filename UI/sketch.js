var username = prompt("Enter a username!")
var ws = new WebSocket(`/ws/location/`+username);
let isWsReady = false;

ws.onopen = () => {
    console.log("WebSocket connection established");
    isWsReady = true;
    // Send initial position
    ws.send(JSON.stringify({ x: pacman.x, y: pacman.y }));
};

ws.onerror = (error) => {
    console.error("WebSocket error:", error);
};

ws.onclose = () => {
    console.log("WebSocket connection closed");
    isWsReady = false;
    // Optional: Add reconnect logic here
};

ws.onmessage = (event) => {
    try {
        var message = event.data;
        print(message)
    } catch (error) {
        console.error("Error processing message:", error);
    }
};


// Define the grid (1 = wall, 0 = open space)
const grid = [
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2],
    [2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2],
    [2, 2, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 2, 2],
    [2, 2, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 2, 2],
    [2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2],
    [2, 2, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 2, 2],
    [2, 2, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 2, 2],
    [2, 2, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 2, 2],
    [2, 2, 1, 2, 2, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 2, 2, 1, 2, 2],
    [2, 2, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 2, 2],
    [2, 2, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2, 2],
    [2, 2, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 2, 2],
    [2, 2, 1, 2, 2, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 2, 2, 1, 2, 2],
    [2, 2, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 2, 2],
    [2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2],
    [2, 2, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 2, 2],
    [2, 2, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 2, 2],
    [2, 2, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 2, 2],
    [2, 2, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 2, 2],
    [2, 2, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 2, 2],
    [2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2],
    [2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
  ];

// Initialise Previous Positions
let lastSentX = -1;
let lastSentY = -1;

// Tile size for the grid
let tileSize = 30;

// Pac-Man object
let pacman = {
    x: 1, y: 1,  // Will be set randomly
    direction: " ",
    nextDirection: " ",
    smoothX: 1, smoothY: 1,
    moveDelay: 8,
    moveCounter: 0,
    mouthAngle: 20, // Start with an open mouth
    mouthDirection: 1 //direction of the mouth
};

function setup() {
    createCanvas(windowWidth, windowHeight);
    noStroke();
    frameRate(60);
    setRandomPacmanPosition();
}

function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
}

//draw() function called 60 times in a second. Each call corresponds to a frame.
function draw() {
    background(0);

    // make maze
    drawMaze()

    //adjust Pacman speed
    if (pacman.moveCounter >= pacman.moveDelay) {
        movePacman();
        pacman.moveCounter = 0;
    }
    else {
        pacman.moveCounter++;
    }

    //Adjust Pacman smooth movement
    pacman.smoothX = lerp(pacman.smoothX, pacman.x, 0.28);
    pacman.smoothY = lerp(pacman.smoothY, pacman.y, 0.28);


    animatePacmanMouth(); //this function is called 60 times a second to animate 
    // Pac-Man's mouth opening and closing by continuously modifying pacman.mouthAngle

    drawPacman(); //this function is called 60 times a second to animate. Uses mouthAngle 
    // to visually render Pac-Man as an arc (arc()) with the mouth facing the correct direction.

    //Sends position of pacman to the back-end through a POST request
    //Throttled so it doesnt send position if pac-man hasnt moved
    // postPositionURL = "/api/"+username+"/position"
    if (pacman.x !== lastSentX || pacman.y !== lastSentY) {
        // print(JSON.stringify({x: pacman.x, y: pacman.y}))
        // ws.onopen = () => ws.send(JSON.stringify({x: pacman.x, y: pacman.y}))
        if (isWsReady) {
            ws.send(JSON.stringify({ x: pacman.x, y: pacman.y }));
            lastSentX = pacman.x;
            lastSentY = pacman.y;
        }
        lastSentX = pacman.x;
        lastSentY = pacman.y;
    }
}

// Ensure Pac-Man is placed correctly in random open spaces
function setRandomPacmanPosition() {
    let openSpaces = [];
    for (let row = 0; row < grid.length; row++) {
        for (let col = 0; col < grid[row].length; col++) {
            if (grid[row][col] === 0) {
                openSpaces.push({ x: col, y: row });
            }
        }
    }

    let randomIndex = floor(random(openSpaces.length));
    let startPosition = openSpaces[randomIndex];

    pacman.x = startPosition.x;
    pacman.y = startPosition.y;
    pacman.smoothX = pacman.x;
    pacman.smoothY = pacman.y;

    console.log("Pac-Man starts at:", pacman.x, pacman.y); // Debugging line
    //Since pacman.x and pacman.y are set by setRandomPacmanPosition(), 
    // this lets us see where Pac-Man is starting.
}



//This function is called from inside of draw(). This means that this function is called 60 times
// each second. This makes sure Pac-Man's mouth is animated properly
function animatePacmanMouth() {
    //The function adjusts pacman.mouthAngle to simulate an opening and closing mouth.
    pacman.mouthAngle += pacman.mouthDirection * 2;
    //pacman.mouthAngle controls how wide Pac-Man’s mouth is open.
    //pacman.mouthDirection is either: 1 → Mouth is opening; -1 → Mouth is closing
    //Multiplying by 2 makes the mouth open/close by 2 degrees per frame.

    //MouthAngle does not reset to 20 every time animatePacmanMouth() is called.
    //pacman.mouthAngle is stored in memory and keeps its value between frames.
    //Each time draw() runs, animatePacmanMouth() modifies the existing mouthAngle, 
    //gradually increasing or decreasing it. It only resets if the entire game is 
    //restarted, not on each function call.

    if (pacman.mouthAngle >= 40 || pacman.mouthAngle <= 10) //Does not let the mouth angle to 
    //increase too much or completely close down
    { // Prevents mouth from fully closing
        pacman.mouthDirection *= -1; //mouthDirection (opening or closing) changes after 
        //the threashold mentioned in the condition
    }
}


// This function takes care of how the pacman mouth adjusts to changing direction
function drawPacman() {
    fill(255, 255, 0); // Yellow Pac-Man
    noStroke();

    let angleOffset = radians(pacman.mouthAngle);
    //Converts mouthAngle from degrees to radians, since arc() in p5.js works with radians.
    //pacman.mouthAngle is animated between 10° - 40° by animatePacmanMouth().

    let startAngle = 0, endAngle = TWO_PI;
    //TWO_PI is a full circle (360° in radians).
    //These angles define in which direction Pac-Man's mouth opens and closes.

    //This part decides the directions in which the mouth will open 
    if (pacman.direction === "RIGHT" || pacman.direction === " ")
    //If Pac-Man is Moving Right or Stationary
    {
        startAngle = angleOffset; //Right is the default direction for Pac-Man.
        //The mouth opens from the right.
        endAngle = TWO_PI - angleOffset;
        //If mouthAngle = 30°, the start angle will be 30°.
        //The end angle will be 330°, creating an opening on the right.
    }
    else if (pacman.direction === "LEFT") {
        startAngle = PI + angleOffset;
        endAngle = PI - angleOffset;
    }
    else if (pacman.direction === "UP") {
        startAngle = -HALF_PI + angleOffset;
        endAngle = -HALF_PI - angleOffset;
    }
    else if (pacman.direction === "DOWN") {
        startAngle = HALF_PI + angleOffset;
        endAngle = HALF_PI - angleOffset;
    }

    let mazeHeight = grid.length;
    let mazeWidth = grid[0].length;
    let orient = windowWidth > windowHeight;
    let tileSize = orient ? (windowHeight / mazeHeight) : (windowWidth / mazeWidth);
    let mazeMargin = orient ? (windowWidth - tileSize * mazeWidth) / 2 : (windowHeight - tileSize * mazeHeight) / 2;

    //Draws Pac-Man as a circle (arc()) with an open mouth.
    arc((orient ? mazeMargin : 0) + pacman.smoothX * tileSize + tileSize / 2,
        (orient ? 0 : mazeMargin) + pacman.smoothY * tileSize + tileSize / 2,
        tileSize * 0.8, tileSize * 0.8,
        startAngle, endAngle, PIE);
    //arc(x, y, width, height, startAngle, endAngle, PIE):
    //x = pacman.smoothX * tileSize + tileSize / 2 → Centers Pac-Man horizontally.
    //y = pacman.smoothY * tileSize + tileSize / 2 → Centers Pac-Man vertically.
    //tileSize * 0.8 → The size of Pac-Man (slightly smaller than the grid cell).
    //startAngle, endAngle → Defines the mouth opening direction.
    //PIE mode → Ensures Pac-Man is drawn as a pizza-slice shape (instead of a full circle).
}


function keyPressed() {
    if (keyCode === LEFT_ARROW) pacman.nextDirection = "LEFT";
    if (keyCode === RIGHT_ARROW) pacman.nextDirection = "RIGHT";
    if (keyCode === UP_ARROW) pacman.nextDirection = "UP";
    if (keyCode === DOWN_ARROW) pacman.nextDirection = "DOWN";
}


// Function to move Pac-Man smoothly
function movePacman() {
    let newX = pacman.x;
    let newY = pacman.y;

    if (pacman.nextDirection !== " ") {
        let tempX = pacman.x;
        let tempY = pacman.y;

        if (pacman.nextDirection === "LEFT") tempX--;
        if (pacman.nextDirection === "RIGHT") tempX++;
        if (pacman.nextDirection === "UP") tempY--;
        if (pacman.nextDirection === "DOWN") tempY++;

        if (grid[tempY][tempX] === 0) {
            pacman.direction = pacman.nextDirection;
        }
    }

    if (pacman.direction === "LEFT") newX--;
    if (pacman.direction === "RIGHT") newX++;
    if (pacman.direction === "UP") newY--;
    if (pacman.direction === "DOWN") newY++;

    if (grid[newY][newX] === 0) {
        pacman.x = newX;
        pacman.y = newY;
    }
}

function drawMaze() {
    let mazeHeight = grid.length;
    let mazeWidth = grid[0].length;
    let orient = windowWidth > windowHeight;
    let tileSize = orient ? (windowHeight / mazeHeight) : (windowWidth / mazeWidth);
    let qTileSize = tileSize / 4;
    let mazeMargin = orient ? (windowWidth - tileSize * mazeWidth) / 2 : (windowHeight - tileSize * mazeHeight) / 2;

    fill(0, 0, 0);
    stroke(0, 0, 255);
    strokeWeight(tileSize / 20);
    for (let i = 0; i < mazeWidth; i++) {
        for (let j = 0; j < mazeHeight; j++) {
            if (grid[j][i] === 1) {
                let x = (orient ? mazeMargin : 0) + i * tileSize
                let y = (orient ? 0 : mazeMargin) + j * tileSize

                // check adjacent vertical and horizontal
                if (i > 0 && grid[j][i - 1] != 1) {
                    // draw side of wall
                    line(x, y + qTileSize, x, y + tileSize - qTileSize);
                }
                if (i + 1 < mazeWidth && grid[j][i + 1] != 1) {
                    line(x + tileSize, y + qTileSize, x + tileSize, y + tileSize - qTileSize);
                }
                if (j > 0 && grid[j - 1][i] != 1) {
                    line(x + qTileSize, y, x + tileSize - qTileSize, y);
                }
                if (j + 1 < mazeHeight && grid[j + 1][i] != 1) {
                    line(x + qTileSize, y + tileSize, x + tileSize - qTileSize, y + tileSize);
                }
                // check adjacent diagonal
                if (i + 1 < mazeWidth && j > 0 && grid[j - 1][i + 1] != 1) {
                    // check adjacent vertical and horizontal
                    if (grid[j - 1][i] != 1 && grid[j][i + 1] != 1) {
                        // draw corner of wall
                        arc(x + tileSize - qTileSize, y + qTileSize, qTileSize * 2, qTileSize * 2, -HALF_PI, 0, OPEN, 50);
                    }
                    if (grid[j - 1][i] === 1 && grid[j][i + 1] === 1) {
                        arc(x + tileSize + qTileSize, y - qTileSize, qTileSize * 2, qTileSize * 2, HALF_PI, PI, OPEN, 50);
                    }
                    if (grid[j - 1][i] === 1 && grid[j][i + 1] != 1) {
                        // draw side of wall
                        line(x + tileSize, y, x + tileSize, y + qTileSize);
                    }
                    if (grid[j - 1][i] != 1 && grid[j][i + 1] === 1) {
                        line(x + tileSize - qTileSize, y, x + tileSize, y);
                    }
                }
                // check adjacent diagonal
                if (i + 1 < mazeWidth && j + 1 < mazeHeight && grid[j + 1][i + 1] != 1) {
                    // check adjacent vertical and horizontal
                    if (grid[j + 1][i] != 1 && grid[j][i + 1] != 1) {
                        // draw corner of wall
                        arc(x + tileSize - qTileSize, y + tileSize - qTileSize, qTileSize * 2, qTileSize * 2, 0, HALF_PI, OPEN, 50);
                    }
                    if (grid[j + 1][i] === 1 && grid[j][i + 1] === 1) {
                        arc(x + tileSize + qTileSize, y + tileSize + qTileSize, qTileSize * 2, qTileSize * 2, PI, PI + HALF_PI, OPEN, 50);
                    }
                    if (grid[j + 1][i] === 1 && grid[j][i + 1] != 1) {
                        // draw side of wall
                        line(x + tileSize, y + tileSize - qTileSize, x + tileSize, y + tileSize);
                    }
                    if (grid[j + 1][i] != 1 && grid[j][i + 1] === 1) {
                        line(x + tileSize - qTileSize, y + tileSize, x + tileSize, y + tileSize);
                    }
                }
                // check adjacent diagonal
                if (i > 0 && j + 1 < mazeHeight && grid[j + 1][i - 1] != 1) {
                    // check adjacent vertical and horizontal
                    if (grid[j + 1][i] != 1 && grid[j][i - 1] != 1) {
                        // draw corner of wall
                        arc(x + qTileSize, y + tileSize - qTileSize, qTileSize * 2, qTileSize * 2, HALF_PI, PI, OPEN, 50);
                    }
                    if (grid[j + 1][i] === 1 && grid[j][i - 1] === 1) {
                        arc(x - qTileSize, y + tileSize + qTileSize, qTileSize * 2, qTileSize * 2, -HALF_PI, 0, OPEN, 50);
                    }
                    if (grid[j + 1][i] === 1 && grid[j][i - 1] != 1) {
                        // draw side of wall
                        line(x, y + tileSize - qTileSize, x, y + tileSize);
                    }
                    if (grid[j + 1][i] != 1 && grid[j][i - 1] === 1) {
                        line(x, y + tileSize, x + qTileSize, y + tileSize);
                    }
                }
                // check adjacent diagonal
                if (i > 0 && j > 0 && grid[j - 1][i - 1] != 1) {
                    // check adjacent vertical and horizontal
                    if (grid[j - 1][i] != 1 && grid[j][i - 1] != 1) {
                        // draw corner of wall
                        arc(x + qTileSize, y + qTileSize, qTileSize * 2, qTileSize * 2, PI, PI + HALF_PI, OPEN, 50);
                    }
                    if (grid[j - 1][i] === 1 && grid[j][i - 1] === 1) {
                        arc(x - qTileSize, y - qTileSize, qTileSize * 2, qTileSize * 2, 0, HALF_PI, OPEN, 50);
                    }
                    if (grid[j - 1][i] === 1 && grid[j][i - 1] != 1) {
                        // draw side of wall
                        line(x, y, x, y + qTileSize);
                    }
                    if (grid[j - 1][i] != 1 && grid[j][i - 1] === 1) {
                        line(x, y, x + qTileSize, y);
                    }
                }
            }
        }
    }
}

