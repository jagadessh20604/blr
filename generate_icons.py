from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size):
    # Create a new image with a white background
    image = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw a gradient background
    for y in range(size):
        r = int(255 * (1 - y/size))  # Red component
        g = int(107 * (1 - y/size) + 205 * (y/size))  # Green component
        b = int(107 * (1 - y/size) + 196 * (y/size))  # Blue component
        draw.line([(0, y), (size, y)], fill=(r, g, b))
    
    # Draw a food icon (simple bowl)
    bowl_color = (255, 255, 255)
    bowl_size = size * 0.6
    bowl_x = size * 0.5
    bowl_y = size * 0.6
    
    # Draw bowl
    draw.ellipse([
        (bowl_x - bowl_size/2, bowl_y - bowl_size/4),
        (bowl_x + bowl_size/2, bowl_y + bowl_size/4)
    ], fill=bowl_color)
    
    # Draw steam
    steam_color = (255, 255, 255)
    for i in range(3):
        x = bowl_x - bowl_size/3 + i * bowl_size/3
        y = bowl_y - bowl_size/2
        draw.arc([
            (x - bowl_size/6, y - bowl_size/6),
            (x + bowl_size/6, y + bowl_size/6)
        ], 0, 180, fill=steam_color, width=size//20)
    
    return image

# Generate icons
sizes = [192, 512]
for size in sizes:
    icon = create_icon(size)
    icon.save(f'icon-{size}x{size}.png') 