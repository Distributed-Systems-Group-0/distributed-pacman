let maze, player, game;
let ghosts = []; // Ensure ghosts is initialized globally

function setup() {
  createCanvas(500, 500);
  ghosts = []; // Reinitialize ghosts before game starts
  initializeGame(); // Call after ghosts is initialized
}

function draw() {
  background(0);

  if (game.gameOver) {
    game.displayGameOver();
    return;
  }

  maze.display();
  game.display();
  player.update();
  game.checkCollisions();

  ghosts.forEach((ghost, index) => {
    if (ghost.shouldDespawn()) {
        console.log(`👻 Ghost at (${ghost.x}, ${ghost.y}) despawned, replacing with new ghost`);

        // Generate a new random position for the ghost
        let newX = floor(random(1, maze.rows - 1));
        let newY = floor(random(1, maze.cols - 1));

        // Replace the old ghost with a new one at a random position
        ghosts[index] = new Ghost(newX, newY, random([0, 1, 2, 3]));

        console.log(`👻 New ghost spawned at (${newX}, ${newY})`);
    }
    });


  // Update all ghosts
  for (let ghost of ghosts) {
    ghost.update(player.x, player.y);
  }
}

/**
 * Initializes or resets the entire game state
 */
function initializeGame() {
  maze = new Maze(25, 25);
  player = new Player(1, 1);
  game = new Game(player, ghosts, maze); // Pass ghosts array correctly
  spawnGhosts(); // Spawn initial ghosts
}

/**
 * Spawns a batch of 4 new ghosts
 */
function spawnGhosts() {
  for (let i = 0; i < 4; i++) {
    ghosts.push(new Ghost(floor(random(1, 23)), floor(random(1, 23)), i));
  }
}

/**
 * Handles user input for movement and game reset
 */
 function keyPressed() {
    if (game.gameOver && keyCode === ENTER) {
      game.resetGame(); // Fully resets the game when Enter is pressed
    } else {
      player.handleInput(); // Handles movement input
    }
  }
