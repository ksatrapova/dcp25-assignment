import py5  # Import the py5 graphics library

def setup():
    py5.size(400, 400)  

def draw():
    py5.background(255)  # White background
    py5.fill(100, 150, 255)  # Blue fill 
    py5.no_stroke()
    py5.circle(py5.width / 2, py5.height / 2, 100)  # Draws a circle

if __name__ == "__main__":
    py5.run_sketch()  # Run the sketch
