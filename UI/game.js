/**
 * Game Class
 * - Manages game state (score, lives, game over)
 * - Handles collisions between Pac-Man, ghosts, and collectibles
 * - Displays score, lives, and game over screen
 */

 class Game {
    constructor(player, ghosts, maze) {
      this.player = player;
      this.ghosts = ghosts;
      this.maze = maze;
      this.gameOver = false;
      this.lastCollisionTime = 0; // Prevent multiple collisions in a short time
      this.collisionCooldown = 60; // Cooldown (1 second = 60 frames)
    }
  
    /**
     * Displays game elements (Pac-Man, Ghosts, Score)
     */
    display() {
      this.player.display();
      for (let ghost of this.ghosts) ghost.display();
      this.displayScoreAndLives();
    }
  
    /**
     * Checks for collisions between Pac-Man and:
     * - Dots (increments score)
     * - Power Pellets (increments score more)
     * - Ghosts (reduces lives)
     */
    checkCollisions() {
      // Pac-Man eats dots
      this.maze.dots = this.maze.dots.filter(dot => {
        
        if (dot.x === this.player.x && dot.y === this.player.y) {
            console.log("FrameCount:", frameCount, "eating dots:", this.lastCollisionTime);
          this.player.score += 10;
          return false; // Remove eaten dot
        }
        return true;
      });
  
      // Pac-Man eats power pellets
      this.maze.powerPellets = this.maze.powerPellets.filter(pellet => {
        if (pellet.x === this.player.x && pellet.y === this.player.y) {
            console.log("FrameCount:", frameCount, "eatingpower pallets", this.lastCollisionTime);
          this.player.score += 50;
          return false; // Remove eaten pellet
        }
        return true;
      });
  
      // Pac-Man collides with ghosts (Lose life with cooldown)
      for (let ghost of this.ghosts) {
        let dx = this.player.x - ghost.x;
        let dy = this.player.y - ghost.y;
        let distance = Math.sqrt(dx * dx + dy * dy); // Calculate distance
    
        console.log(`Checking collision: Distance=${distance}, Player (${this.player.x},${this.player.y}), Ghost (${ghost.x},${ghost.y})`);
    
        if (distance < 0.8) { // Collision detected
          if (frameCount - this.lastCollisionTime > this.collisionCooldown) {
            this.lastCollisionTime = frameCount; // Reset collision timer
            this.player.lives--;
    
            console.log("💥 Collision detected! Lives left:", this.player.lives);
    
            if (this.player.lives <= 0) {
              this.gameOver = true;
            } else {
              // Reset Pac-Man's position after losing a life
              this.player.x = 1;
              this.player.y = 1;
    
              // Ensure the player respawns in an open space
              while (this.maze.grid[this.player.x][this.player.y] === 1) {
                this.player.x = floor(random(1, this.maze.rows - 1));
                this.player.y = floor(random(1, this.maze.cols - 1));
              }
            }
          }
        }
      }
    }
  
    /**
     * Displays score and remaining lives
     */
    displayScoreAndLives() {
      fill(255);
      textSize(20);
      textAlign(RIGHT, TOP);
      text(`Score: ${this.player.score} | Lives: ${this.player.lives}`, width - 20, 20);
    }
  
    /**
     * Displays the Game Over screen
     */
    displayGameOver() {
      background(0);
      fill(255, 0, 0);
      textSize(40);
      textAlign(CENTER, CENTER);
      text("GAME OVER", width / 2, height / 2);
      textSize(20);
      text("Press ENTER to Restart", width / 2, height / 2 + 40);
    }
  
    /**
     * Resets everything when ENTER is pressed after game over
     */
    resetGame() {
      this.player.resetPosition(); // Reset Pac-Man
      this.player.score = 0;
      this.player.lives = 3;
      this.maze = new Maze(25, 25); // Generate a new maze
        
      // Spawn new batch of 4 ghosts
      ghosts.forEach((ghost, index) => {       
        // Generate a new random position for the ghost
            let newX = floor(random(1, maze.rows - 1));
            let newY = floor(random(1, maze.cols - 1));
    
        // Replace the old ghost with a new one at a random position
            ghosts[index] = new Ghost(newX, newY, random([0, 1, 2, 3]));
        });
  
      this.gameOver = false;
      this.lastCollisionTime = 0; // Reset collision cooldown
    }
  }
  