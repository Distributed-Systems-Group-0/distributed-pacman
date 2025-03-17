/**
 * Maze Class
 * - Generates a structured and beautiful maze
 * - Ensures all areas are reachable (no closed-off sections)
 * - Places more dots and 50% fewer walls
 */

class Maze {
  constructor(rows, cols) {
    this.rows = rows;
    this.cols = cols;
    this.grid = this.generatePerfectMaze();
    this.dots = [];
    this.powerPellets = [];
    this.populateDotsAndPellets();
  }

  /**
   * Generates a perfect maze using the Recursive Backtracking algorithm.
   * - Ensures every open space is connected (no closed grids).
   * - Reduces walls by 50% to create a more open maze.
   */
  generatePerfectMaze() {
    let grid = Array.from({ length: this.rows }, () => Array(this.cols).fill(1));

    function carvePath(x, y) {
      grid[x][y] = 0; // Make path
      let directions = shuffle([
        { x: -2, y: 0 }, { x: 2, y: 0 },
        { x: 0, y: -2 }, { x: 0, y: 2 }
      ]);

      for (let { x: dx, y: dy } of directions) {
        let nx = x + dx, ny = y + dy;
        if (nx > 0 && ny > 0 && nx < grid.length - 1 && ny < grid[0].length - 1 && grid[nx][ny] === 1) {
          grid[nx - dx / 2][ny - dy / 2] = 0; // Remove wall between
          carvePath(nx, ny);
        }
      }
    }

    carvePath(1, 1); // Start maze generation at (1,1)

    // Reduce wall density by 50% (randomly clear some walls)
    for (let i = 1; i < this.rows - 1; i++) {
      for (let j = 1; j < this.cols - 1; j++) {
        if (grid[i][j] === 1 && random(1) < 0.5) {
          grid[i][j] = 0; // Remove extra walls
        }
      }
    }

    // Ensure open exit paths
    grid[1][0] = 0; // Entry
    grid[this.rows - 2][this.cols - 1] = 0; // Exit
    return grid;
  }

  /**
   * Places dots and power pellets more densely
   */
  populateDotsAndPellets() {
    for (let i = 1; i < this.rows - 1; i++) {
      for (let j = 1; j < this.cols - 1; j++) {
        if (this.grid[i][j] === 0) {
          if ((i % 5 === 0 && j % 5 === 0) || random(1) < 0.1) { // More power pellets
            this.powerPellets.push({ x: i, y: j });
          } else if (random(1) < 0.9) { // More dots (80% of open spaces)
            this.dots.push({ x: i, y: j });
          }
        }
      }
    }
  }

  /**
   * Renders the maze beautifully
   */
  display() {
    for (let i = 0; i < this.rows; i++) {
      for (let j = 0; j < this.cols; j++) {
        if (this.grid[i][j] === 1) {
          fill(30, 144, 255); // Nice Blue Walls
          stroke(0);
          rect(i * 20, j * 20, 20, 20, 5); // Rounded Walls
        }
      }
    }

    // Draw dots and power pellets
    fill(255, 204, 0);
    this.dots.forEach(dot => ellipse(dot.x * 20 + 10, dot.y * 20 + 10, 5));

    fill(255, 0, 0);
    this.powerPellets.forEach(pellet => ellipse(pellet.x * 20 + 10, pellet.y * 20 + 10, 10));
  }
}
