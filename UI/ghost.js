/**
 * Ghost Class
 * - Moves randomly before chasing Pac-Man after a delay
 * - Spawns in batches of 4 and gets removed after 5 seconds
 * - After a ghost is deleted, a new batch spawns instantly
 */

class Ghost {
  constructor(x, y, index) {
    this.x = x;
    this.y = y;
    this.color = ["red", "blue", "pink", "orange"][index % 4]; // Different colored ghosts
    this.speed = 15;
    this.direction = { x: 0, y: 0 };
    this.spawnTime = frameCount; // Store the time when the ghost spawns
    this.lifetime = 300; // Ghosts live for 5 seconds (300 frames)
  }

  /**
   * Moves the ghost randomly before chasing Pac-Man after a delay
   */
  update(targetX, targetY) {
    if (frameCount % this.speed === 0) {
      let moves = [
        { x: -1, y: 0 }, { x: 1, y: 0 },
        { x: 0, y: -1 }, { x: 0, y: 1 }
      ];

      let moveChoice;
      
      if (frameCount < this.spawnTime + 100) {
        // Wander randomly for the first 100 frames
        moveChoice = random(moves.filter(move => maze.grid[this.x + move.x][this.y + move.y] === 0));
      } else {
        // After wandering, chase Pac-Man using basic AI
        let bestMove = { x: 0, y: 0, dist: Infinity };
        for (let move of moves) {
          let nx = this.x + move.x;
          let ny = this.y + move.y;
          if (maze.grid[nx][ny] === 0) {
            let distance = dist(nx, ny, targetX, targetY);
            if (distance < bestMove.dist) {
              bestMove = { ...move, dist: distance };
            }
          }
        }
        moveChoice = bestMove.dist !== Infinity ? bestMove : null;
      }

      // Move the ghost
      if (moveChoice) {
        this.x += moveChoice.x;
        this.y += moveChoice.y;
        this.direction = moveChoice;
      }
    }

    this.display(targetX, targetY);
  }

  /**
   * Draws the ghost with a rounded top and wavy bottom
   */
  display(targetX, targetY) {
    let centerX = this.x * 20 + 10;
    let centerY = this.y * 20 + 10;

    // Ghost Body
    fill(this.color);
    stroke(0);
    strokeWeight(1);
    beginShape();
    arc(centerX, centerY, 20, 20, PI, 0, CHORD); // Rounded top
    vertex(centerX + 10, centerY);
    vertex(centerX + 10, centerY + 10);
    vertex(centerX + 5, centerY + 15); // Wavy bottom
    vertex(centerX, centerY + 10);
    vertex(centerX - 5, centerY + 15);
    vertex(centerX - 10, centerY + 10);
    vertex(centerX - 10, centerY);
    endShape(CLOSE);

    // Eyes
    fill(255);
    ellipse(centerX - 4, centerY - 4, 5, 5);
    ellipse(centerX + 4, centerY - 4, 5, 5);

    // Pupils (Looking at Pac-Man)
    fill(0);
    let eyeOffsetX = constrain(targetX - this.x, -1, 1) * 2;
    let eyeOffsetY = constrain(targetY - this.y, -1, 1) * 2;
    ellipse(centerX - 4 + eyeOffsetX, centerY - 4 + eyeOffsetY, 2, 2);
    ellipse(centerX + 4 + eyeOffsetX, centerY - 4 + eyeOffsetY, 2, 2);
  }

  /**
   * Checks if the ghost should be removed after 5 seconds
   */
  shouldDespawn() {
    return frameCount > this.spawnTime + this.lifetime;
  }
}
