/**
 * Player (Pac-Man) Class
 * - Moves based on user input
 * - Smoothly changes direction when possible
 * - Eats dots & power pellets
 */

 class Player {
    constructor(x, y) {
      this.x = x;
      this.y = y;
      this.direction = { x: 0, y: 0 }; // Current movement direction
      this.nextDirection = { x: 0, y: 0 }; // Buffer for new input
      this.speed = 5;
      this.score = 0;
      this.lives = 3;
      this.mouthOpen = true;
    }
  
    /**
     * Updates player movement and allows smooth turning
     */
    update() {
      if (frameCount % this.speed === 0) {
        let newX = this.x + this.nextDirection.x;
        let newY = this.y + this.nextDirection.y;
  
        // If next direction is valid, apply it
        if (maze.grid[newX] && maze.grid[newX][newY] === 0) {
          this.direction = { ...this.nextDirection };
        }
  
        // Move Pac-Man in the chosen direction if the path is open
        let moveX = this.x + this.direction.x;
        let moveY = this.y + this.direction.y;
  
        if (maze.grid[moveX] && maze.grid[moveX][moveY] === 0) {
          this.x = moveX;
          this.y = moveY;
        }
      }
  
      // Pac-Man mouth animation
      if (frameCount % 10 === 0) {
        this.mouthOpen = !this.mouthOpen;
      }
  
      this.display();
    }

    resetPosition() {
      this.x = 1;
      this.y = 1;
    }
  
    /**
     * Draws Pac-Man with opening & closing mouth animation
     */
    display() {
      fill(255, 255, 0);
      let startAngle = this.mouthOpen ? QUARTER_PI : 0;
      arc(this.x * 20 + 10, this.y * 20 + 10, 20, 20, startAngle, PI + startAngle);
    }
  
    /**
     * Handles user input and buffers the next direction
     */
    handleInput() {
      if (keyCode === LEFT_ARROW) this.nextDirection = { x: -1, y: 0 };
      if (keyCode === RIGHT_ARROW) this.nextDirection = { x: 1, y: 0 };
      if (keyCode === UP_ARROW) this.nextDirection = { x: 0, y: -1 };
      if (keyCode === DOWN_ARROW) this.nextDirection = { x: 0, y: 1 };
    }
  }
  