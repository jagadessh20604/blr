from PIL import Image, ImageDraw, ImageFont
import os

def create_pwa_icon(size, filename, background_color="#4ECDC4", text_color="#FFFFFF", char="🍜"):
    """Creates a simple PWA icon with a background color and a character."""
    img = Image.new('RGB', (size, size), color=background_color)
    draw = ImageDraw.Draw(img)

    # Attempt to load a font, fallback to default if not found
    try:
        # Adjust font size based on icon size
        font_size = int(size * 0.6)
        # Use a common system font path or Pillow's default
        try:
            # Try a common Linux/macOS path
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except IOError:
            try:
                # Try a common Windows path
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                print(f"Warning: Could not load preferred font. Using default font for {filename}.")
                # Fallback to Pillow's default font if others fail
                font_size = int(size * 0.8) # Default font might need different sizing
                font = ImageFont.load_default(size=font_size) # Requires Pillow 10+

    except Exception as e:
        print(f"Error loading font: {e}. Using basic default.")
        font = ImageFont.load_default() # Absolute fallback

    # Calculate text position
    try:
        # Use textbbox for better centering with modern Pillow
        bbox = draw.textbbox((0, 0), char, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) / 2 - bbox[0]
        y = (size - text_height) / 2 - bbox[1]

    except AttributeError: # Fallback for older Pillow versions without textbbox
         # Deprecated approach, less accurate
         text_width, text_height = draw.textsize(char, font=font)
         x = (size - text_width) / 2
         y = (size - text_height) / 2

    # Draw the text
    draw.text((x, y), char, fill=text_color, font=font)

    # Ensure the directory exists (root in this case)
    os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
    img.save(filename)
    print(f"Created {filename}")

# Create icons
create_pwa_icon(192, "icon-192x192.png")
create_pwa_icon(512, "icon-512x512.png") 